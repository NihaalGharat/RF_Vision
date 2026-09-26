"""ESP32 Wi-Fi provisioning orchestration (host side, stdlib only).

Replaces the permanent build-time credential assumption (Kconfig-baked
SSID/password consumed by ``example_connect()``) with a runtime serial
provisioning flow over the EXISTING USB-serial transport — no new
hardware, no SoftAP/BLE framework, no reflash for every new network.

Wire protocol (ASCII lines, ``\\n`` terminated; tolerant to ``\\r\\n``):

Host → node::

    RFV_PROV_BEGIN
    RFV_SSID:<ssid>          (1..32 chars, anything except newline)
    RFV_PASS:<password>      (0..64 chars, anything except newline)
    RFV_PROV_COMMIT          (persist to NVS + reconnect)
    RFV_PROV_ABORT           (discard staged credentials)
    RFV_NET_STATUS           (query current association at any time)

Node → host::

    RFV_OK <token>           (BEGIN / SSID / PASS / STORED / CONNECTED)
    RFV_ERR <reason>         (machine-readable, no secrets)
    RFV_NET ssid=<s> bssid=<m> channel=<c> ip=<a>   (never a password)

Firmware counterpart: ``firmware/esp32/csi_recv_router/main/app_main.c``
(NVS ``rfvision`` namespace + UART RX task; Kconfig values remain the
fallback when no runtime credentials are stored).

Security discipline (mandatory, tested):
* passwords live only in :class:`Credentials` (redacted ``repr``);
* NEVER written to logs, API responses, research captures, or exceptions;
* :func:`redact` strips staged secrets from any diagnostic string.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

__all__ = [
    "PROV_STATES",
    "Credentials",
    "CredentialsError",
    "ProvisioningError",
    "ProvisioningSession",
    "parse_response",
    "parse_status_line",
    "redact",
]

#: Provisioning pipeline states (subset of the RF readiness vocabulary).
PROV_STATES = (
    "CREDENTIAL_REQUIRED",
    "PROVISIONING",
    "NODES_CONNECTING",
    "PROVISIONED",
    "PROVISIONING_FAILED",
)

_MAX_SSID_LEN = 32
_MAX_PASS_LEN = 64
_READ_TIMEOUT_S = 15.0


class CredentialsError(ValueError):
    """Raised for invalid SSID/password input (before any I/O)."""


class ProvisioningError(RuntimeError):
    """Raised when node provisioning fails (never carries the password)."""


class Credentials:
    """In-memory Wi-Fi credentials with redaction-by-default.

    The password is write-once readable ONLY by the provisioning sender;
    ``repr``/``str`` never expose it.
    """

    __slots__ = ("ssid", "_password")

    def __init__(self, ssid: str, password: str) -> None:
        if not isinstance(ssid, str) or not 1 <= len(ssid) <= _MAX_SSID_LEN:
            raise CredentialsError(
                f"ssid must be 1..{_MAX_SSID_LEN} chars "
                f"(got length {len(ssid) if isinstance(ssid, str) else '?'})")
        if "\n" in ssid or "\r" in ssid:
            raise CredentialsError("ssid must not contain newlines")
        if not isinstance(password, str) or len(password) > _MAX_PASS_LEN:
            raise CredentialsError(
                f"password must be 0..{_MAX_PASS_LEN} chars")
        if "\n" in password or "\r" in password:
            raise CredentialsError("password must not contain newlines")
        self.ssid = ssid
        self._password = password

    @property
    def password(self) -> str:
        """Sender-only access to the secret."""
        return self._password

    def clear(self) -> None:
        """Drop the secret from memory (best effort)."""
        self._password = ""

    def secrets(self) -> List[str]:
        """Secret strings that must never appear in diagnostics."""
        return [self._password] if self._password else []

    def __repr__(self) -> str:  # pragma: no cover (trivial, yet tested)
        return (f"Credentials(ssid={self.ssid!r}, "
                f"password={'***' if self._password else '<empty>'})")

    __str__ = __repr__


def redact(text: str, secrets: List[str]) -> str:
    """Replace every occurrence of each secret with ``***``."""
    clean = text
    for secret in secrets:
        if secret:
            clean = clean.replace(secret, "***")
    return clean


def parse_response(line: str) -> Dict[str, str]:
    """Parse one node response line (``RFV_OK`` / ``RFV_ERR`` / ``RFV_NET``).

    Raises :class:`ProvisioningError` for ``RFV_ERR`` and
    :class:`ValueError` for unrecognized lines (e.g. interleaved
    ``CSI_DATA`` — the caller must route those back to the CSI parser,
    never treat them as provisioning failures).
    """
    text = line.strip()
    if text.startswith("RFV_OK"):
        return {"kind": "ok", "token": text[len("RFV_OK"):].strip()}
    if text.startswith("RFV_ERR"):
        raise ProvisioningError(
            f"node rejected provisioning: {text[len('RFV_ERR'):].strip()}")
    if text.startswith("RFV_NET"):
        return {"kind": "status", **parse_status_line(text)}
    raise ValueError(f"not a provisioning response: {text[:60]!r}")


def parse_status_line(line: str) -> Dict[str, str]:
    """Parse ``RFV_NET ssid=<s> bssid=<m> channel=<c> ip=<a>``."""
    text = line.strip()
    if not text.startswith("RFV_NET"):
        raise ValueError("not a status line")
    out: Dict[str, str] = {}
    for token in text.split()[1:]:
        if "=" in token:
            key, _, value = token.partition("=")
            out[key] = value
    for required in ("ssid", "bssid", "channel", "ip"):
        if required not in out:
            raise ValueError(f"status line missing {required}")
    return out


@dataclass
class ProvResult:
    """Outcome of one node's provisioning exchange (no secrets)."""

    node_id: str
    state: str  # PROVISIONED | PROVISIONING_FAILED
    status: Dict[str, str] = field(default_factory=dict)
    reason: str = ""


class ProvisioningSession:
    """One unknown-network provisioning run for a set of nodes.

    Serial I/O is fully injected (``write_line`` / ``read_line``) so the
    exchange is unit-testable without hardware and the CSI parser never
    sees provisioning traffic.
    """

    def __init__(self, node_ids: List[str]) -> None:
        if not node_ids:
            raise CredentialsError("at least one node id is required")
        self.node_ids = list(node_ids)
        self.state = "CREDENTIAL_REQUIRED"

    def provision_node(
        self,
        node_id: str,
        creds: Credentials,
        write_line: Callable[[str], None],
        read_line: Callable[[float], Optional[str]],
        timeout_s: float = _READ_TIMEOUT_S,
    ) -> ProvResult:
        """Run the wire exchange for one node; return its result.

        ``write_line`` sends one protocol line (without terminator);
        ``read_line`` returns the next node line or None on timeout.
        Non-protocol lines (e.g. ``CSI_DATA``) are skipped, never fatal.
        """
        self.state = "PROVISIONING"
        secrets = [creds.ssid, *creds.secrets()]
        staged = [f"RFV_SSID:{creds.ssid}", "RFV_PASS:<redacted>"]
        try:
            self._exchange(write_line, read_line, creds, timeout_s)
        except (ProvisioningError, TimeoutError, OSError, ValueError) as exc:
            self.state = "PROVISIONING_FAILED"
            safe = redact(f"provisioning {node_id} failed: {exc}", secrets)
            return ProvResult(node_id=node_id,
                              state="PROVISIONING_FAILED", reason=safe)
        self.state = "NODES_CONNECTING"
        try:
            status = self._await_status(read_line, timeout_s)
        except (ProvisioningError, TimeoutError, OSError, ValueError) as exc:
            self.state = "PROVISIONING_FAILED"
            safe = redact(f"node {node_id} stored credentials but "
                          f"reconnect unconfirmed: {exc}", secrets)
            return ProvResult(node_id=node_id,
                              state="PROVISIONING_FAILED", reason=safe)
        _ = staged  # staged transcript stays local; never returned/logged
        return ProvResult(node_id=node_id, state="PROVISIONED",
                          status=status,
                          reason=f"node {node_id} associated: "
                                 f"{status.get('ssid')} "
                                 f"{status.get('bssid')} "
                                 f"ch{status.get('channel')}")

    # -- internals -----------------------------------------------------
    def _expect_ok(self, write_line: Callable[[str], None],
                   read_line: Callable[[float], Optional[str]],
                   timeout_s: float, want: str, resend: str) -> str:
        deadline = time.monotonic() + timeout_s
        last_rfv = time.monotonic()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"no node response while awaiting {want}")
            # The node's RFV_OK reply can be lost when in-flight CSI
            # output interleaves with it (ROM ets_printf has no
            # cross-task line atomicity). All stage commands are
            # idempotent on the node, so retransmit until an RFV_
            # line arrives; the node's quiet window keeps later
            # replies clean.
            if time.monotonic() - last_rfv >= 3.0:
                write_line(resend)
                last_rfv = time.monotonic()
            line = read_line(remaining)
            if line is None:
                raise TimeoutError(
                    f"node silent while awaiting {want}")
            text = line.strip()
            if not text.startswith("RFV_"):
                continue  # interleaved console/CSI output: skip, never fatal
            last_rfv = time.monotonic()
            parsed = parse_response(text)
            if parsed["kind"] == "ok":
                return parsed["token"]
            # status lines interleaved mid-exchange are informational
            continue

    def _exchange(self, write_line: Callable[[str], None],
                  read_line: Callable[[float], Optional[str]],
                  creds: Credentials, timeout_s: float) -> None:
        write_line("RFV_PROV_BEGIN")
        self._expect_ok(write_line, read_line, timeout_s, "BEGIN",
                        "RFV_PROV_BEGIN")
        write_line(f"RFV_SSID:{creds.ssid}")
        self._expect_ok(write_line, read_line, timeout_s, "SSID",
                        f"RFV_SSID:{creds.ssid}")
        # The secret travels ONLY on this local USB-serial write; it is
        # never logged, never returned, never stored host-side.
        write_line(f"RFV_PASS:{creds.password}")
        self._expect_ok(write_line, read_line, timeout_s, "PASS",
                        f"RFV_PASS:{creds.password}")
        write_line("RFV_PROV_COMMIT")
        self._expect_ok(write_line, read_line, timeout_s, "STORED",
                        "RFV_PROV_COMMIT")

    def _await_status(self, read_line: Callable[[float], Optional[str]],
                      timeout_s: float) -> Dict[str, str]:
        deadline = time.monotonic() + timeout_s
        last_rfv = time.monotonic()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("node reconnect status not received")
            line = read_line(remaining)
            if line is None:
                raise TimeoutError("node silent after COMMIT")
            text = line.strip()
            if text.startswith("RFV_NET"):
                return parse_status_line(text)
            if text.startswith("RFV_ERR"):
                parse_response(text)  # raises ProvisioningError
            # RFV_OK CONNECTED and stray lines: keep waiting for RFV_NET
            continue
