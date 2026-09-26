"""Unknown-WiFi web integration: discovery, provisioning, RF readiness.

Additive backend for the "CONNECT RF NODES" workflow (stdlib only).
Wires ``csi.transport`` (network_context / provisioning / rf_readiness)
to three JSON routes; no existing endpoint or payload shape is changed:

* ``GET /api/v1/network`` — active laptop Wi-Fi + compatibility
  (never contains passwords; discovery outputs contain none).
* ``POST /api/v1/network/provision {"ssid","password"[,"nodes"]}`` —
  serial provisioning of ESP32-A/B to the active network. Refuses with
  409 while the live stream runs (ports must be free; RFV_* lines must
  never enter the CSI parser). Responses and errors never echo the
  password.
* ``GET /api/v1/rf_readiness`` — honest chain evaluation
  (network → nodes → CSI → sync → RF READY).

The live CSI provider must be stopped before provisioning and
restarted after (with ``expected_bssid``/``expected_channel`` of the
new network) — enforced by the busy-guard, documented in responses.
"""

from __future__ import annotations

import os
import select
import termios
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from csi.transport import network_context as netctx
from csi.transport import provisioning as prov
from csi.transport import rf_readiness as readiness
from csi.transport.nodes import NODES, all_nodes_resolved

__all__ = [
    "network_status_payload",
    "rf_readiness_payload",
    "provision_nodes",
    "last_network",
]

#: 921600 8N1 raw — mirrors web/live_serial.py (no modem control, so the
#: boards never reset when the port is opened for provisioning).
_BAUD_RATE = 921600

_lock = threading.Lock()
_last_network: Optional[netctx.NetworkContext] = None


def last_network() -> Optional[netctx.NetworkContext]:
    """Most recently observed network context (session-change tracking)."""
    with _lock:
        return _last_network


def _remember(ctx: Optional[netctx.NetworkContext]) -> None:
    global _last_network
    with _lock:
        if ctx is not None:
            _last_network = ctx


def network_status_payload(
    discover: Callable[..., Any] = netctx.discover_active_network,
) -> Dict[str, Any]:
    """Build the GET /api/v1/network payload (password-free by design)."""
    state, ctx, reason = discover()
    _remember(ctx)
    network: Optional[Dict[str, Any]] = None
    if ctx is not None:
        network = {
            "interface": ctx.interface,
            "ssid": ctx.ssid,
            "bssid": ctx.bssid,
            "channel": ctx.channel,
            "frequency_mhz": ctx.frequency_mhz,
            "band": ctx.band,
            "gateway": ctx.gateway,
            "subnet": ctx.subnet,
            "discovered_at": ctx.discovered_at,
        }
    return {"state": state, "reason": reason, "network": network,
            "esp32_band": netctx.ESP32_SUPPORTED_BAND}


def _node_checks_from_dual(info: Dict[str, Any],
                            ctx: Optional[netctx.NetworkContext],
                            ) -> List[readiness.NodeCheck]:
    """Translate DualNodeSession.session_stats() into NodeChecks."""
    checks: List[readiness.NodeCheck] = []
    per_node = info.get("per_node", {}) or {}
    want_bssid = (ctx.bssid.lower() if ctx and ctx.bssid else None)
    want_channel = ctx.channel if ctx else None
    for nid, node in per_node.items():
        stream = node.get("stream", {}) or {}
        signal = node.get("signal", {}) or {}
        have_bssid = str(signal.get("bssid", "") or "").lower()
        have_channel = signal.get("channel")
        checks.append(readiness.NodeCheck(
            node_id=nid,
            identity_ok=bool(node.get("board_mac"))
            and node.get("board_mac") != "UNKNOWN",
            reachable=node.get("source_state") in (
                "LIVE_VERIFIED", "LIVE_UNVERIFIED"),
            csi_available=int(stream.get("valid", 0) or 0) > 0,
            bssid_match=(want_bssid is not None
                         and have_bssid == want_bssid),
            channel_match=(want_channel is not None
                           and have_channel == want_channel),
            source_verified=node.get("source_state") == "LIVE_VERIFIED",
        ))
    return checks


def rf_readiness_payload(
    discover: Callable[..., Any] = netctx.discover_active_network,
    dual_info: Optional[Dict[str, Any]] = None,
    nodes_expected: int = 2,
) -> Dict[str, Any]:
    """Build the GET /api/v1/rf_readiness payload."""
    state, ctx, reason = discover()
    previous = last_network()
    changed, change_reason = netctx.network_changed(previous, ctx)
    # First observation establishes the session baseline (no prior claim
    # to invalidate); afterwards any change forces re-verification.
    if previous is None:
        changed = False
        change_reason = ("session network baseline set" if ctx is not None
                         else "no prior network observed")
    _remember(ctx)
    if dual_info is None:
        result = readiness.evaluate_rf_readiness(
            network_state=state, network_reason=reason,
            nodes_expected=nodes_expected, nodes=[],
            network_changed_flag=changed)
    else:
        sync_state = str((dual_info.get("sync", {}) or {}).get(
            "state", "UNSYNCED"))
        result = readiness.evaluate_rf_readiness(
            network_state=state, network_reason=reason,
            nodes_expected=nodes_expected,
            nodes=_node_checks_from_dual(dual_info, ctx),
            sync_state=sync_state,
            network_changed_flag=changed)
    payload: Dict[str, Any] = {
        "state": result.state, "rf_ready": result.rf_ready,
        "reason": result.reason, "degraded": result.degraded,
        "network": ({"ssid": ctx.ssid, "bssid": ctx.bssid,
                     "channel": ctx.channel, "band": ctx.band}
                    if ctx else None),
        "network_change": {"changed": changed, "reason": change_reason},
    }
    return payload


class _SerialProvisionPort:
    """Minimal raw serial line port (open/write/read/close, no DTR reset).

    Mirrors the termios discipline of ``web/live_serial.py``: O_NONBLOCK
    + raw 8N1, never asserts modem-control lines.
    """

    def __init__(self, device: str) -> None:
        self.device = device
        self._fd: Optional[int] = None

    def open(self) -> None:
        fd = os.open(self.device, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        try:
            attrs = termios.tcgetattr(fd)
            attrs[0] &= ~(termios.IGNBRK | termios.IXON | termios.IXOFF)
            attrs[1] &= ~termios.OPOST
            attrs[2] &= ~(termios.CSIZE | termios.PARENB)
            attrs[2] |= termios.CS8 | termios.CREAD | termios.CLOCAL
            attrs[3] &= ~(termios.ICANON | termios.ECHO | termios.ISIG)
            attrs[4] = termios.B921600
            attrs[5] = termios.B921600
            termios.tcsetattr(fd, termios.TCSANOW, attrs)
        except Exception:
            os.close(fd)
            raise
        self._fd = fd
        self._buf = b""

    def write_line(self, line: str) -> None:
        assert self._fd is not None
        os.write(self._fd, (line + "\n").encode("utf-8", "replace"))

    def read_line(self, timeout: float) -> Optional[str]:
        assert self._fd is not None
        deadline = time.monotonic() + max(0.0, timeout)
        while True:
            if b"\n" in self._buf:
                raw, _, rest = self._buf.partition(b"\n")
                self._buf = rest
                return raw.decode("utf-8", "replace")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            ready, _, _ = select.select([self._fd], [], [], remaining)
            if not ready:
                return None
            try:
                chunk = os.read(self._fd, 4096)
            except OSError:
                return None
            if not chunk:
                return None
            self._buf += chunk

    def close(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None


def provision_nodes(ssid: str, password: str,
                    node_ids: Optional[List[str]] = None,
                    timeout_s: float = 20.0,
                    port_factory: Optional[Callable[[str], Any]] = None,
                    ) -> Dict[str, Any]:
    """Provision ESP32 nodes to an SSID over USB serial (password-safe).

    Returns ``{"state","nodes":[...], "reason"}``. Raises
    :class:`ValueError` for bad input (incl. unknown node ids) and
    :class:`RuntimeError` when a board has no resolved device. The
    password never appears in results, reasons, or tracebacks — every
    failure string passes through :func:`provisioning.redact`.
    """
    targets = list(node_ids) if node_ids else ["esp32-a", "esp32-b"]
    unknown = [n for n in targets if n not in NODES]
    if unknown:
        raise ValueError(f"unknown node ids: {unknown}")
    creds = prov.Credentials(ssid, password)
    secrets = [ssid, *creds.secrets()]
    try:
        devices = all_nodes_resolved()
    except Exception as exc:
        creds.clear()
        raise RuntimeError(prov.redact(
            f"node resolution failed: {exc}", secrets)) from exc
    session = prov.ProvisioningSession(targets)
    results: List[Dict[str, Any]] = []
    try:
        for nid in targets:
            device = devices.get(nid)
            if not device:
                results.append({"node_id": nid, "state": "NODE_MISSING",
                                "reason": f"no resolved device for {nid}"})
                continue
            port = (port_factory(device) if port_factory is not None
                    else _SerialProvisionPort(device))
            try:
                port.open()
                res = session.provision_node(
                    nid, creds, port.write_line, port.read_line,
                    timeout_s=timeout_s)
            except OSError as exc:
                res = prov.ProvResult(
                    node_id=nid, state="PROVISIONING_FAILED",
                    reason=prov.redact(
                        f"serial I/O failed for {nid}: {exc}", secrets))
            finally:
                try:
                    port.close()
                except Exception:
                    pass
            results.append({"node_id": res.node_id, "state": res.state,
                            "status": dict(res.status),
                            "reason": prov.redact(res.reason, secrets)})
    finally:
        creds.clear()
    failed = [r for r in results if r["state"] != "PROVISIONED"]
    if failed:
        names = ", ".join(r["node_id"] for r in failed)
        return {"state": "PROVISIONING_FAILED", "nodes": results,
                "reason": f"provisioning failed for: {names}; "
                          f"nodes keep prior credentials; retry or "
                          f"re-check serial connections"}
    return {"state": "NODES_CONNECTING", "nodes": results,
            "reason": "credentials stored; nodes reconnecting — verify "
                      "via GET /api/v1/rf_readiness (CSI + sync gate RF "
                      "READY, never association alone)"}
