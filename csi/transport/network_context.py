"""Laptop active-WiFi discovery and network-context representation.

Read-only host module (stdlib only). The laptop's currently active Wi-Fi
connection is the source of truth for which network the user wants RF
Vision to use — the hard-coded home SSID/BSSID/channel are defaults,
never assumptions.

What this module does:
* discover the active Wi-Fi via read-only OS queries (``nmcli``/``iw``/
  ``ip`` — never changes any network state);
* represent it as a session-aware :class:`NetworkContext`;
* judge 2.4/5 GHz compatibility against the validated ESP32-D0WD-V3
  acquisition path (2.4 GHz only);
* detect mid-session network changes;
* opportunistically flag client/AP-isolation suspicion from the ARP
  neighbour table (ESTIMATED grade — never a firm diagnosis).

What this module NEVER does:
* store, log, or return Wi-Fi passwords (discovery outputs contain none);
* switch networks, touch credentials, or open serial ports.

All OS interaction goes through an injectable ``runner`` callable so
tests run fully offline with canned outputs.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

__all__ = [
    "NETWORK_STATES",
    "ESP32_SUPPORTED_BAND",
    "NetworkContext",
    "NetworkDiscoveryError",
    "discover_active_network",
    "network_changed",
    "check_client_isolation",
]

#: Network-level states (subset of the RF readiness vocabulary owned by
#: ``csi.transport.rf_readiness``; repeated here so discovery can be used
#: standalone).
NETWORK_STATES = (
    "NO_NETWORK",
    "NETWORK_DETECTED",
    "NETWORK_UNSUPPORTED",
)

#: Validated ESP32 acquisition hardware supports 2.4 GHz only
#: (ESP32-D0WD-V3, 802.11 b/g/n; see docs/hardware/BASELINE.md).
ESP32_SUPPORTED_BAND = "2.4GHz"


class NetworkDiscoveryError(RuntimeError):
    """Raised when discovery cannot determine the active network."""


@dataclass(frozen=True)
class NetworkContext:
    """Smallest useful representation of the laptop's active Wi-Fi.

    Session-aware: ``discovered_at`` pins the observation to a point in
    time so mid-session changes are detectable via :func:`network_changed`.
    Contains no credentials — discovery outputs never include passwords.
    """

    interface: str
    ssid: str
    bssid: str
    channel: Optional[int]
    frequency_mhz: Optional[int]
    band: str  # "2.4GHz" | "5GHz" | "6GHz" | "UNKNOWN"
    bandwidth_mhz: Optional[int] = None
    gateway: Optional[str] = None
    subnet: Optional[str] = None
    discovered_at: float = 0.0
    source: str = "nmcli"

    def compatible(self) -> Tuple[bool, str]:
        """Judge ESP32-D0WD-V3 acquisition compatibility (honest gate)."""
        if self.band != "2.4GHz" or self.frequency_mhz is None:
            return (False,
                    f"band {self.band} unsupported: ESP32-D0WD-V3 "
                    f"acquisition requires {ESP32_SUPPORTED_BAND}")
        if self.channel is not None and not 1 <= self.channel <= 13:
            return (False,
                    f"channel {self.channel} unsupported: ESP32-D0WD-V3 "
                    f"supports 2.4 GHz channels 1-13")
        return (True, "2.4 GHz network within ESP32-D0WD-V3 support")


def _default_runner(argv: List[str], timeout_s: float = 5.0) -> str:
    """Run a read-only OS query; return stdout ("" on any failure)."""
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout_s)
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def _split_nmcli(line: str) -> List[str]:
    """Split a ``nmcli -t`` line on unescaped colons (SSID may embed ``:``)."""
    fields: List[str] = []
    current: List[str] = []
    escaped = False
    for char in line:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append("".join(current))
            current = []
        else:
            current.append(char)
    fields.append("".join(current))
    return fields


def _band_channel_from_freq(freq_mhz: Optional[int]) -> Tuple[str, Optional[int]]:
    """Map frequency to (band, channel); UNKNOWN when unparseable."""
    if freq_mhz is None:
        return ("UNKNOWN", None)
    if 2400 <= freq_mhz <= 2500:
        return ("2.4GHz", (freq_mhz - 2407) // 5)
    if 5150 <= freq_mhz <= 5925:
        return ("5GHz", None)
    if 5945 <= freq_mhz <= 7125:
        return ("6GHz", None)
    return ("UNKNOWN", None)


def _parse_freq(text: str) -> Optional[int]:
    """Parse ``2412 MHz``-style frequency tokens."""
    token = text.strip().split()[0] if text.strip() else ""
    try:
        return int(token)
    except ValueError:
        return None


def discover_active_network(
    runner: Callable[[List[str], float], str] = _default_runner,
) -> Tuple[str, Optional[NetworkContext], str]:
    """Discover the laptop's active Wi-Fi (read-only).

    Returns ``(state, context, reason)`` where state is one of
    ``NO_NETWORK`` / ``NETWORK_DETECTED`` / ``NETWORK_UNSUPPORTED``.
    Never raises on missing tools — absence of evidence is reported as
    ``NO_NETWORK`` with an honest reason, never guessed.
    """
    # 1. Which interface carries an active wifi connection?
    status_out = runner(
        ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION",
         "device", "status"], 5.0)
    iface = ""
    for raw in status_out.splitlines():
        parts = _split_nmcli(raw.strip())
        if len(parts) >= 3 and parts[1] == "wifi" and parts[2] == "connected":
            iface = parts[0]
            break
    if not iface:
        return ("NO_NETWORK", None,
                "no active wifi connection reported by nmcli")

    # 2. Active AP detail (IN-USE marker; --rescan no keeps this passive).
    ssid = ""
    bssid = ""
    freq: Optional[int] = None
    wifi_out = runner(
        ["nmcli", "-t", "-f", "IN-USE,SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY",
         "dev", "wifi", "list", "ifname", iface, "--rescan", "no"], 8.0)
    for raw in wifi_out.splitlines():
        parts = _split_nmcli(raw.strip())
        if len(parts) >= 7 and parts[0] == "*":
            ssid = parts[1]
            bssid = parts[2].lower()
            freq = _parse_freq(parts[4])
            break
    if not ssid or not bssid:
        # Fallback: `iw` link (no rescan, fully passive).
        iw_out = runner(["iw", "dev", iface, "link"], 5.0)
        for raw in iw_out.splitlines():
            line = raw.strip()
            if line.startswith("SSID:"):
                ssid = line.split("SSID:", 1)[1].strip()
            elif line.startswith("Connected to"):
                bssid = line.split("Connected to", 1)[1].strip().split()[0].lower()
            elif line.startswith("freq:"):
                try:
                    freq = int(line.split("freq:", 1)[1].strip().split()[0])
                except ValueError:
                    freq = None
        if not ssid or not bssid:
            return ("NO_NETWORK", None,
                    f"interface {iface} connected but active AP "
                    f"details unavailable (ssid={bool(ssid)})")

    # 3. Gateway / subnet (provenance only, best effort).
    gateway: Optional[str] = None
    route_out = runner(["ip", "route", "show", "default"], 5.0)
    for raw in route_out.splitlines():
        tokens = raw.split()
        if ("default" in tokens and "via" in tokens
                and f"dev {iface}" in raw):
            try:
                gateway = tokens[tokens.index("via") + 1]
            except IndexError:
                gateway = None
            break
    subnet: Optional[str] = None
    addr_out = runner(["ip", "-o", "-f", "inet", "addr", "show",
                       "dev", iface], 5.0)
    for raw in addr_out.splitlines():
        tokens = raw.split()
        if "inet" in tokens:
            try:
                subnet = tokens[tokens.index("inet") + 1]
            except IndexError:
                subnet = None
            break

    band, channel = _band_channel_from_freq(freq)
    ctx = NetworkContext(
        interface=iface, ssid=ssid, bssid=bssid, channel=channel,
        frequency_mhz=freq, band=band, bandwidth_mhz=None,
        gateway=gateway, subnet=subnet,
        discovered_at=time.time(), source="nmcli")
    ok, reason = ctx.compatible()
    if ok:
        return ("NETWORK_DETECTED", ctx, reason)
    return ("NETWORK_UNSUPPORTED", ctx, reason)


def network_changed(old: Optional[NetworkContext],
                    new: Optional[NetworkContext]) -> Tuple[bool, str]:
    """Detect mid-session network changes (SSID/BSSID/iface/channel).

    Any difference in the identity-bearing fields invalidates a prior
    RF READY claim — the caller must re-verify, never silently continue.
    """
    if old is None or new is None:
        return (True, "network context missing (session not established)")
    for field in ("ssid", "bssid", "interface", "channel"):
        if getattr(old, field) != getattr(new, field):
            return (True,
                    f"network changed: {field} "
                    f"{getattr(old, field)!r} -> {getattr(new, field)!r}")
    return (False, "active network unchanged")


def check_client_isolation(
    node_ips: List[str],
    runner: Callable[[List[str], float], str] = _default_runner,
) -> Tuple[bool, str]:
    """Opportunistic client/AP-isolation suspicion from ARP neighbours.

    Inspects ``ip neigh show`` only (passive). Returns
    ``(suspected, detail)``. A ``True`` result is ESTIMATED grade:
    consistent with isolation, never proof of it — the caller must not
    misclassify it as a firmware failure.
    """
    ips = [ip for ip in node_ips if ip]
    if not ips:
        return (False, "no node IPs known; isolation check not applicable "
                       "(serial transport unaffected)")
    out = runner(["ip", "neigh", "show"], 5.0)
    states: Dict[str, str] = {}
    for raw in out.splitlines():
        tokens = raw.split()
        # Format: "<ip> dev <iface> lladdr <mac> <STATE> [...]"
        if len(tokens) >= 6 and tokens[1] == "dev" and "lladdr" in tokens:
            states[tokens[0]] = tokens[-1].upper()
    if not states:
        return (False, "neighbour table unreadable; isolation UNKNOWN "
                       "(serial transport unaffected)")
    bad = [ip for ip in ips
           if states.get(ip, "MISSING") in ("FAILED", "INCOMPLETE", "MISSING")]
    if len(bad) == len(ips):
        return (True,
                f"all node IPs unreachable at L2 ({', '.join(bad)}); "
                f"client/AP isolation suspected (ESTIMATED)")
    return (False, "at least one node IP has a live neighbour entry")
