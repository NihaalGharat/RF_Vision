"""RF Vision web-interface data contracts (RFVISION-005).

RF Vision native, stdlib only. Defines the JSON payloads served by
``web/server.py`` and consumed by ``web/static/js/*``. Every payload schema
derives from ``docs/architecture/RFVISION_DATA_SCHEMA.md`` and
``unity/integration/MESSAGE_FORMATS.md`` — RuView contributed only the
architectural concept (grouped status/sensing/stream endpoints + explicit
source-state provenance; see ``docs/third_party/RUVIEW_*.md``).

Source transparency (mandatory): every live-data view carries one of
``SOURCE_STATES``. Simulated/fixture data must never be presentable as live.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from realtime.protocol.event_envelope import (
    EVENT_TYPES,
    EventError,
    make_event,
    parse_event,
)

__all__ = [
    "CONTRACT_VERSION",
    "SOURCE_STATES",
    "ContractError",
    "require_source_state",
    "health_payload",
    "status_payload",
    "sensing_snapshot_payload",
    "telemetry_payload",
    "stream_status_payload",
    "experiment_payload",
    "calibration_payload",
    "localization_payload",
    "xai_payload",
    "showcase_fields",
    "PRESENCE_STATES",
    "NODE_MODES",
    "SHOWCASE_PROVENANCE",
    "node_status_payload",
    "nodes_payload",
    "validate_envelope",
]

#: Contract version served at GET /api/v1/health (bump on payload change).
#: v2 adds the two-node ``/api/v1/nodes`` payloads (additive: every v1
#: builder keeps its exact shape).
#: v3 adds the additive P1 showcase fields to ``sensing.snapshot``
#: (presence_state, RF evidence confidence, provenance, node mode,
#: evidence statement, 1-D trail) — all optional, all default to
#: "no inference", so v2 payloads remain valid v3 payloads.
CONTRACT_VERSION = 3

#: P1 showcase presence states (UNKNOWN = no inference attached; the
#: transport-only path never claims a human state).
PRESENCE_STATES = (
    "ABSENT",
    "DETECTED",
    "MOVING",
    "STATIONARY",
    "LOW_CONFIDENCE",
    "EXITING",
    "UNKNOWN",
)

#: Showcase node modes (UNKNOWN = no showcase attached).
NODE_MODES = (
    "UNKNOWN",
    "SINGLE",
    "DUAL",
    "SINGLE-DEGRADED",
)

#: Showcase provenance tokens.
SHOWCASE_PROVENANCE = (
    "UNKNOWN",
    "TRANSPORT",
    "RF-INFERRED",
)

#: Allowed data-provenance states (operation §6). No other value may be
#: emitted or accepted.
SOURCE_STATES = (
    "LIVE_VERIFIED",
    "LIVE_UNVERIFIED",
    "OFFLINE_FIXTURE",
    "SIMULATED",
    "STALE",
    "DISCONNECTED",
)

#: States in which frames may animate as if live.
LIVE_LIKE_STATES = ("LIVE_VERIFIED", "LIVE_UNVERIFIED")

#: States that must ALWAYS carry a visible non-live badge.
NON_LIVE_STATES = (
    "OFFLINE_FIXTURE",
    "SIMULATED",
    "STALE",
    "DISCONNECTED",
)


class ContractError(ValueError):
    """Raised when a payload violates its contract."""


def require_source_state(state: str) -> str:
    """Validate a source-state token (raises ContractError)."""
    if state not in SOURCE_STATES:
        raise ContractError(f"unknown source state: {state!r}")
    return state


def _num(value: Any, name: str, allow_none: bool = False) -> Optional[float]:
    if value is None and allow_none:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{name} must be a number, got {value!r}")
    return float(value)


def health_payload(*, status: str, version: str, uptime_s: float,
                   source: str, source_state: str,
                   contract: int = CONTRACT_VERSION) -> Dict[str, Any]:
    """GET /api/v1/health — liveness + provenance."""
    if status not in ("ok", "degraded"):
        raise ContractError(f"bad health status: {status!r}")
    return {
        "status": status,
        "version": str(version),
        "uptime_s": _num(uptime_s, "uptime_s"),
        "contract": int(contract),
        "source": str(source),
        "source_state": require_source_state(source_state),
    }


def status_payload(*, connection: str, csi_rate: Optional[float],
                   packets: int, malformed: int,
                   latency_ms: Optional[float], model: str,
                   source_state: str) -> Dict[str, Any]:
    """GET /api/v1/status — ``system.status`` payload + provenance."""
    if connection not in ("ONLINE", "OFFLINE"):
        raise ContractError(f"bad connection: {connection!r}")
    return {
        "connection": connection,
        "csi_rate": _num(csi_rate, "csi_rate", allow_none=True),
        "packets": int(packets),
        "malformed": int(malformed),
        "latency_ms": _num(latency_ms, "latency_ms", allow_none=True),
        "model": str(model),
        "source_state": require_source_state(source_state),
    }


def sensing_snapshot_payload(*, presence: str, presence_prob: Optional[float],
                             movement: str, movement_prob: Optional[float],
                             position: Optional[float],
                             position_m: Optional[float],
                             confidence: Optional[float],
                             rssi: Optional[float] = None,
                             amplitudes: Optional[List[float]] = None,
                             phases: Optional[List[float]] = None,
                             validated: bool = False) -> Dict[str, Any]:
    """GET /api/v1/sensing/latest payload.

    Presence/activity are UI FIELDS ONLY until experimentally validated —
    ``validated=False`` (default) obliges the UI to render them as
    unvalidated estimates, never conclusions.
    """
    if presence not in ("PERSON", "EMPTY", "UNKNOWN"):
        raise ContractError(f"bad presence: {presence!r}")
    if movement not in ("MOVING", "STATIC", "UNKNOWN"):
        raise ContractError(f"bad movement: {movement!r}")
    for name, val in (("presence_prob", presence_prob),
                      ("movement_prob", movement_prob),
                      ("confidence", confidence)):
        if val is not None:
            val = _num(val, name)
            if not 0.0 <= val <= 1.0:
                raise ContractError(f"{name} outside [0,1]: {val}")
    if position is not None and not 0.0 <= float(position) <= 1.0:
        raise ContractError(f"position outside [0,1]: {position!r}")
    if amplitudes is not None and not all(
            isinstance(v, (int, float)) for v in amplitudes):
        raise ContractError("amplitudes must be numbers")
    if phases is not None and not all(
            isinstance(v, (int, float)) for v in phases):
        raise ContractError("phases must be numbers")
    return {
        "presence": presence,
        "presence_prob": presence_prob,
        "movement": movement,
        "movement_prob": movement_prob,
        "position": position,
        "position_m": position_m,
        "confidence": confidence,
        "rssi": rssi,
        "amplitudes": amplitudes,
        "phases": phases,
        "validated": bool(validated),
    }


def showcase_fields(*, presence_state: str = "UNKNOWN",
                     rf_evidence_confidence: Optional[float] = None,
                     confidence_calibration: str = "UNCALIBRATED",
                     provenance: str = "UNKNOWN",
                     node_mode: str = "UNKNOWN",
                     evidence_statement: Optional[str] = None,
                     trail: Optional[List[float]] = None) -> Dict[str, Any]:
    """P1 showcase layer for ``sensing.snapshot`` (contract v3, additive).

    Every field defaults to "no inference" so transport-only payloads
    (``LiveProvider`` without an attached showcase engine) stay exactly
    as honest as v2: UNKNOWN presence_state, no confidence, TRANSPORT or
    UNKNOWN provenance. ``rf_evidence_confidence`` must be None (not 0)
    when no score exists; the UI renders None as "no confidence".
    """
    if presence_state not in PRESENCE_STATES:
        raise ContractError(f"bad presence_state: {presence_state!r}")
    if rf_evidence_confidence is not None:
        rf_evidence_confidence = _num(
            rf_evidence_confidence, "rf_evidence_confidence")
        if not 0.0 <= rf_evidence_confidence <= 1.0:
            raise ContractError(
                "rf_evidence_confidence outside [0,1]: "
                f"{rf_evidence_confidence}")
    if confidence_calibration != "UNCALIBRATED":
        raise ContractError(
            "confidence_calibration must be UNCALIBRATED until a "
            "calibration study exists; "
            f"got {confidence_calibration!r}")
    if provenance not in SHOWCASE_PROVENANCE:
        raise ContractError(f"bad provenance: {provenance!r}")
    if node_mode not in NODE_MODES:
        raise ContractError(f"bad node_mode: {node_mode!r}")
    clean_trail = None
    if trail is not None:
        clean_trail = [float(v) for v in trail]
        if not all(0.0 <= v <= 1.0 for v in clean_trail):
            raise ContractError("trail positions must be in [0,1]")
    return {
        "presence_state": presence_state,
        "rf_evidence_confidence": rf_evidence_confidence,
        "confidence_calibration": confidence_calibration,
        "provenance": provenance,
        "node_mode": node_mode,
        "evidence_statement": evidence_statement,
        "trail": clean_trail if clean_trail is not None else [],
    }


def telemetry_payload(*, packets: int, malformed: int,
                      rejected: Dict[str, int],
                      last_seq: Optional[int],
                      last_update: Optional[float]) -> Dict[str, Any]:
    """GET /api/v1/telemetry — adapter/parser counters."""
    if not isinstance(rejected, dict):
        raise ContractError("rejected must be an object")
    return {
        "packets": int(packets),
        "malformed": int(malformed),
        "rejected": {str(k): int(v) for k, v in rejected.items()},
        "last_seq": last_seq,
        "last_update": last_update,
    }


def stream_status_payload(*, running: bool, mode: str,
                          source_state: str) -> Dict[str, Any]:
    """GET /api/v1/stream/status + POST start/stop responses."""
    if mode not in ("fixture", "simulated", "live", "off"):
        raise ContractError(f"bad stream mode: {mode!r}")
    return {
        "running": bool(running),
        "mode": mode,
        "source_state": require_source_state(source_state),
    }


def experiment_payload(*, session_id: str, software: Dict[str, str],
                       hardware: Dict[str, Any], firmware: Dict[str, Any],
                       geometry: Dict[str, Any],
                       raw_ref: Optional[Dict[str, Any]],
                       validation: str) -> Dict[str, Any]:
    """GET /api/v1/experiment — session provenance (UNKNOWN stays UNKNOWN)."""
    if validation not in ("NOT_RUN", "PASS", "FAIL", "INCONCLUSIVE"):
        raise ContractError(f"bad validation: {validation!r}")
    return {
        "session_id": str(session_id),
        "software": dict(software),
        "hardware": dict(hardware),
        "firmware": dict(firmware),
        "geometry": dict(geometry),
        "raw_ref": raw_ref,
        "validation": validation,
    }


def calibration_payload(*, status: str, room_width_m: Optional[float],
                        room_length_m: Optional[float],
                        movement_threshold: Optional[float],
                        calibrated_at: Optional[float],
                        method: str = "guided") -> Dict[str, Any]:
    """GET /api/v1/calibration — calibration state."""
    if status not in ("CALIBRATED", "UNCALIBRATED", "STALE"):
        raise ContractError(f"bad calibration status: {status!r}")
    return {
        "status": status,
        "room_width_m": room_width_m,
        "room_length_m": room_length_m,
        "movement_threshold": movement_threshold,
        "calibrated_at": calibrated_at,
        "method": method,
    }


def localization_payload(*, frame: str, position: Optional[float],
                         position_m: Optional[float], raw: Optional[float],
                         uncertainty: Optional[float],
                         room_width_m: Optional[float],
                         sync: str, nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """GET /api/v1/localization — 1-D link only (2-D/3-D reserved)."""
    if frame != "link-1d":
        raise ContractError("only frame 'link-1d' is defined")
    if sync not in ("NONE", "UNSYNCED", "SYNCED"):
        raise ContractError(f"bad sync: {sync!r}")
    if position is not None and not 0.0 <= float(position) <= 1.0:
        raise ContractError(f"position outside [0,1]: {position!r}")
    if uncertainty is not None and float(uncertainty) < 0:
        raise ContractError("uncertainty must be >= 0")
    return {
        "frame": frame,
        "position": position,
        "position_m": position_m,
        "raw": raw,
        "uncertainty": uncertainty,
        "room_width_m": room_width_m,
        "sync": sync,
        "nodes": list(nodes),
    }


def xai_payload(*, available: bool, method: Optional[str] = None,
                caveats: Optional[str] = None,
                scores: Optional[Dict[str, float]] = None,
                top_k: Optional[List[str]] = None) -> Dict[str, Any]:
    """GET /api/v1/xai — NOT AVAILABLE until a validated explanation exists.

    When ``available`` is False the UI must render NOT AVAILABLE; scores
    must never be fabricated.
    """
    if not available:
        return {"available": False, "status": "NOT AVAILABLE"}
    if method not in ("rf_impurity", "permutation"):
        raise ContractError(f"bad XAI method: {method!r}")
    if not caveats:
        raise ContractError("validated explanations must carry caveats")
    return {
        "available": True,
        "method": method,
        "caveats": caveats,
        "scores": dict(scores or {}),
        "top_k": list(top_k or []),
    }


def node_status_payload(*, node_id: str, board_mac: str, port: str,
                          connection: str, source_state: str,
                          csi_rate: Optional[float],
                          valid: int, valid_pct: Optional[float],
                          malformed: int, duplicates: int,
                          out_of_order: int, gaps: int,
                          rssi: Optional[float],
                          channel: Optional[int], bssid: Optional[str],
                          tones: Optional[int],
                          host_pipeline_us_mean: Optional[float],
                          esp_latency_us: Optional[float] = None,
                          sync_ready: bool = False,
                          sync_offset_ns: Optional[float] = None,
                          sync_jitter_ns: Optional[float] = None,
                          sync_observations: int = 0) -> Dict[str, Any]:
    """GET /api/v1/nodes → one entry per receiver node (contract v2).

    All metrics are measured; ``esp_latency_us`` is None until a common
    clock supports a real estimate (never fabricated). ``sync_*`` comes
    from the node's offset estimator.
    """
    if connection not in ("LIVE", "SYNCING", "SYNCED", "DEGRADED",
                          "DISCONNECTED", "STANDBY"):
        raise ContractError(f"bad node connection: {connection!r}")
    if valid_pct is not None and not 0.0 <= float(valid_pct) <= 100.0:
        raise ContractError(f"valid_pct outside [0,100]: {valid_pct!r}")
    return {
        "node_id": str(node_id),
        "board_mac": str(board_mac),
        "port": str(port),
        "connection": connection,
        "source_state": require_source_state(source_state),
        "csi_rate": _num(csi_rate, "csi_rate", allow_none=True),
        "valid": int(valid),
        "valid_pct": valid_pct,
        "malformed": int(malformed),
        "duplicates": int(duplicates),
        "out_of_order": int(out_of_order),
        "gaps": int(gaps),
        "rssi": rssi,
        "channel": channel,
        "bssid": bssid,
        "tones": tones,
        "host_pipeline_us_mean": host_pipeline_us_mean,
        "esp_latency_us": esp_latency_us,
        "sync_ready": bool(sync_ready),
        "sync_offset_ns": sync_offset_ns,
        "sync_jitter_ns": sync_jitter_ns,
        "sync_observations": int(sync_observations),
    }


def nodes_payload(*, available: bool, session: Optional[Dict[str, Any]],
                    sync_state: str = "UNSYNCED",
                    nodes: Optional[List[Dict[str, Any]]] = None,
                    reason: Optional[str] = None) -> Dict[str, Any]:
    """GET /api/v1/nodes — dual-session telemetry (contract v2)."""
    if sync_state not in ("UNSYNCED", "SYNCING", "SYNCED"):
        raise ContractError(f"bad sync_state: {sync_state!r}")
    return {
        "available": bool(available),
        "sync_state": sync_state,
        "nodes": list(nodes or []),
        "session": session,
        "reason": reason,
    }


def validate_envelope(text: str) -> Dict[str, Any]:
    """Validate a WS/event-bus message envelope (raises ContractError).

    Accepts the native ``RealtimeEvent`` envelope; additionally requires a
    ``source_state`` member inside the payload for stream-carried events so
    the UI can never render a frame without provenance.
    """
    try:
        obj = parse_event(text)
    except EventError as exc:
        raise ContractError(str(exc)) from exc
    if obj["type"] in ("sensing.snapshot", "localization.update",
                       "system.status"):
        state = obj["payload"].get("source_state")
        if state not in SOURCE_STATES:
            raise ContractError(
                f"{obj['type']} payload missing valid source_state")
    return obj


def wrap_event(event_type: str, payload: Dict[str, Any], *,
               source: str = "rfvision-web", seq: int = 0) -> Dict[str, Any]:
    """Build a validated outgoing event (raises ContractError/EventError)."""
    if event_type not in EVENT_TYPES:
        raise ContractError(f"unknown event type: {event_type!r}")
    return make_event(event_type, payload, source=source, seq=seq)
