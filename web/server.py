"""RF Vision web-console server (RFVISION-005).

RF Vision native, stdlib only (``http.server`` + ``threading`` + the
``web/ws.py`` codec). Serves the dependency-free frontend in
``web/static/`` plus a versioned JSON API and a WebSocket event stream.

Endpoints (all JSON unless noted):
- ``GET /`` → ``web/static/react/index.html`` (React dashboard;
  legacy UI at ``/legacy``; static files under ``/static/``)
- ``GET /api/v1/health`` — liveness + contract + provenance
- ``GET /api/v1/status`` — ``system.status`` payload (+staleness)
- ``GET /api/v1/sensing/latest`` — latest ``sensing.snapshot`` envelope
  (``{"available": false}`` when none yet)
- ``GET /api/v1/telemetry`` — adapter/parser counters
- ``GET /api/v1/stream/status`` + ``POST /api/v1/stream/start|stop``
- ``POST /api/v1/source {"mode": off|fixture|simulated|live}``
- ``GET /api/v1/live`` — live session telemetry (or available:false)
- ``GET /api/v1/nodes`` — two-node telemetry (or available:false, contract v2)
- ``GET /api/v1/vision`` — RF Vision pipeline state: deterministic
  evidence + ML + tracks + spatial + XAI (or available:false; dual only,
  engineering/demonstration, never research evidence)
- ``POST /api/v1/dual/start|stop`` — backend DualNodeSession lifecycle
  (both nodes required; refuses while the single live source runs, and
  provisioning / live-source selection refuse while dual runs)
- ``POST /api/v1/live/record/start|stop`` — bounded diagnostic capture
- ``GET /api/v1/experiment|calibration|localization|xai``
- ``GET /api/v1/network`` — active laptop Wi-Fi + ESP32 compatibility
- ``POST /api/v1/network/provision`` — serial-provision ESP32-A/B
- ``GET /api/v1/rf_readiness`` — honest network→nodes→CSI→sync chain
- ``GET /ws/sensing`` (Upgrade: websocket) — envelope stream + commands:
  ``{"command": "ping"|"stream:start"|"stream:stop"|"set_source", ...}``

Data enters only via ``web/source.py`` providers and leaves only via
``web/contracts.py`` payloads. Run: ``python3 -m web.server`` (repo root).
"""

from __future__ import annotations

import json
import platform
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from web import __version__ as WEB_VERSION
from web import contracts
from web import network as network_api
from web import source as sources
from web import trials as trial_api
from web import ws as ws_codec
from web.dual_node import DualNodeSession

try:
    # Stdlib-only module; safe to import at top level.
    from sensing.confidence.confidence import DEGRADE_DERATE
except Exception:  # pragma: no cover (packaging fallback)
    DEGRADE_DERATE = 0.75

__all__ = ["DEFAULT_PORT", "ConsoleState", "ConsoleHandler",
           "build_server", "main", "BASELINE", "FIRMWARE",
           "set_dual_session", "dual_status_payload"]

DEFAULT_PORT = 8130
STALE_AFTER_S = 3.0
WS_RECV_TIMEOUT_S = 45.0

#: Validated hardware baseline surfaced by /api/v1/experiment + /hardware.
#: Receiver identity pinned by RFVISION-003R-C2 (current board).
BASELINE = {
    "esp32": "ESP32-D0WD-V3 rev 3.1",
    "receiver": "ESP32-D0WD-V3 Rev 3.1 (current board)",
    "receiver_mac": "b0:3f:d3:70:20:3c",
    "flash_mb": 4,
    "csi_stack": "Espressif ESP-CSI",
    "router": "Xiaomi Mi Router 4C/R4CM",
    "band": "2.4 GHz",
    "transport": "USB serial",
    "serial": "/dev/ttyUSB0 @ 921600 8N1",
    "host": "Ubuntu",
}

FIRMWARE = {
    "name": "csi_recv_router",
    "esp_csi_commit": "8633d67152db2808f141cc1595970aa9cf406045",
    "esp_idf": "v5.4.4 (296b6eab9445fd720e71aecb961e2d3fbca9944)",
    "identity": "UNKNOWN",  # unverifiable without reset/read-back (003)
}

STATIC_DIR = Path(__file__).resolve().parent / "static"

MIME = {".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "text/javascript; charset=utf-8",
        ".json": "application/json",
        ".png": "image/png"}


class ConsoleState:
    """Mutable console state: provider, stream pump, subscribers."""

    def __init__(self) -> None:
        self.started_at = time.time()
        self.lock = threading.Lock()
        self.provider = sources.DisconnectedProvider()
        self.streaming = False
        self.packets = 0
        self.malformed = 0
        self.last_frame_ts: Optional[float] = None
        self.last_seq: Optional[int] = None
        self.subscribers: List[Any] = []  # raw sockets
        self._pump: Optional[threading.Thread] = None
        # P1 showcase: deterministic InferenceEngine fed by the live
        # provider's sample seam. None = transport-only (deps missing or
        # non-live source) — snapshots stay honestly UNKNOWN.
        self._showcase_engine: Any = None

    # -- P1 truthful showcase (additive; never touches acquisition) ----
    def _build_showcase_engine(self) -> Any:
        """Fresh heuristic InferenceEngine, or None when unavailable.

        Guarded: numpy/scipy/sklearn/config must all import; any failure
        degrades honestly to transport-only snapshots (no exception, no
        partial wiring). Models are None by design — heuristic fallback,
        labelled as such downstream.
        """
        try:
            from config.settings import load_config
            from sensing.inference_engine import InferenceEngine
            cfg = load_config()
            return InferenceEngine(cfg, None)
        except Exception:
            return None

    def _showcase_topology(self) -> Any:
        """(node_mode, available, total, derate) from the DUAL attachment.

        No DUAL session = single-console operation. A DUAL session with a
        DISCONNECTED node = SINGLE-DEGRADED with the documented product
        derate applied to confidence (directive §8, product policy).
        """
        dual = DUAL
        if dual is None:
            return ("SINGLE", 1, 1, 1.0)
        try:
            per = dual.session_stats().get("per_node", {})
        except Exception:
            return ("UNKNOWN", 1, 1, 1.0)
        if not per:
            return ("UNKNOWN", 1, 1, 1.0)
        down = [nid for nid, node in per.items()
                if node.get("source_state") == "DISCONNECTED"]
        if down:
            return ("SINGLE-DEGRADED", 1, max(len(per), 1), DEGRADE_DERATE)
        return ("DUAL", len(per), max(len(per), 1), 1.0)

    def _maybe_enrich(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Merge P1 showcase fields into a sensing.snapshot (best effort).

        Failures (or no engine) leave the transport-only event untouched —
        enrichment must never break the broadcast pump.
        """
        with self.lock:
            engine = self._showcase_engine
        if engine is None or not isinstance(event, dict):
            return event
        if event.get("type") != "sensing.snapshot":
            return event
        try:
            node_mode, avail, total, derate = self._showcase_topology()
            quality = self.effective_state() in contracts.LIVE_LIKE_STATES
            snap = engine.showcase_snapshot(
                node_mode=node_mode, nodes_available=avail,
                nodes_total=total, data_quality_ok=quality,
                stale=False, derate=derate)
            payload = event.get("payload")
            if isinstance(payload, dict):
                payload.update(contracts.showcase_fields(**snap))
        except Exception:
            pass
        return event

    # -- source / stream control -------------------------------------
    def set_source(self, mode: str, **kwargs: Any) -> Dict[str, Any]:
        """Switch provider (raises LiveUnavailable/ContractError/FileNotFound).

        Selecting ``live`` auto-attaches a fresh P1 showcase engine via the
        provider's sample seam when the DSP stack imports; any other mode
        (or missing deps) drops the engine so snapshots stay honestly
        transport-only. One engine per live session (fresh persistence).
        """
        engine = None
        if mode == "live" and "sample_observer" not in kwargs:
            engine = self._build_showcase_engine()
            if engine is not None:
                kwargs["sample_observer"] = engine.process_sample
        provider = sources.make_provider(mode, **kwargs)
        with self.lock:
            old = self.provider
            self.provider = provider
            self._showcase_engine = engine
            self.streaming = False
            self.packets = 0
            self.malformed = 0
            self.last_frame_ts = None
            self.last_seq = None
        closer = getattr(old, "close", None)  # release serial, if held
        if callable(closer):
            try:
                closer()
            except Exception:
                pass
        return self.stream_status()

    def stream_status(self) -> Dict[str, Any]:
        """Current stream state as a contract payload."""
        with self.lock:
            provider = self.provider
            running = self.streaming
        return contracts.stream_status_payload(
            running=running, mode=provider.mode,
            source_state=self.effective_state())

    def start_stream(self) -> Dict[str, Any]:
        """Start the pump thread (idempotent)."""
        with self.lock:
            if self.streaming:
                running = True
            else:
                self.streaming = True
                running = True
                if (self._pump is None or not self._pump.is_alive()) and \
                        self.provider.mode != "off":
                    self._pump = threading.Thread(
                        target=self._pump_loop, daemon=True,
                        name="console-pump")
                    self._pump.start()
        return self.stream_status()

    def stop_stream(self) -> Dict[str, Any]:
        """Stop pumping (idempotent)."""
        with self.lock:
            self.streaming = False
        return self.stream_status()

    # -- provenance ----------------------------------------------------
    def effective_state(self) -> str:
        """Provider state with STALE override on frame timeout."""
        with self.lock:
            base = self.provider.source_state
            ts = self.last_frame_ts
            running = self.streaming
        if running and base in contracts.LIVE_LIKE_STATES + (
                "OFFLINE_FIXTURE", "SIMULATED"):
            if ts is None or (time.time() - ts) > STALE_AFTER_S:
                return "STALE"
        return base

    def frame_age_s(self) -> Optional[float]:
        """Seconds since last broadcast frame (None if never)."""
        with self.lock:
            ts = self.last_frame_ts
        return (time.time() - ts) if ts is not None else None

    # -- pump + broadcast ----------------------------------------------
    def _pump_loop(self) -> None:
        try:
            for event in self.provider.frames():
                with self.lock:
                    if not self.streaming:
                        break
                event = self._maybe_enrich(event)
                text = json.dumps(event)
                with self.lock:
                    self.packets += 1
                    self.last_frame_ts = time.time()
                    self.last_seq = event.get("seq")
                    targets = list(self.subscribers)
                dead = []
                for sock in targets:
                    try:
                        ws_codec.send_text(sock, text)
                    except Exception:
                        dead.append(sock)
                if dead:
                    with self.lock:
                        self.subscribers = [s for s in self.subscribers
                                            if s not in dead]
        except Exception:
            with self.lock:
                self.streaming = False

    def subscribe(self, sock: Any) -> None:
        """Register a WS socket for broadcasts."""
        with self.lock:
            self.subscribers.append(sock)

    def unsubscribe(self, sock: Any) -> None:
        """Remove a WS socket; best-effort close."""
        with self.lock:
            if sock in self.subscribers:
                self.subscribers.remove(sock)
        try:
            sock.close()
        except Exception:
            pass


STATE = ConsoleState()

#: Attached two-node session (None = single-node / dual not started).
#: Set via :func:`set_dual_session`; read by GET /api/v1/nodes.
DUAL = None

#: Attached RF Vision pipeline (None = no dual vision active). Built
#: best-effort in :func:`dual_start` from the existing sample seam; any
#: failure degrades to vision-unavailable with acquisition untouched.
#: Read by GET /api/v1/vision.
VISION = None

#: Attached audio-guided trial recorder (None = no trial this process).
_TRIAL = None

#: Serializes dual-session check-and-set (duplicate-start prevention).
_dual_lock = threading.Lock()

#: Session constructor (seam for focused tests; production = DualNodeSession).
_DUAL_SESSION_FACTORY = DualNodeSession

#: Forwarder draining attached dual-session frames to WS subscribers
#: (None = no dual broadcast active). Read-only fan-out: envelopes pass
#: through unchanged to the existing WS broadcast; acquisition, sync,
#: gates, and contracts are untouched.
_dual_forward: Optional[threading.Thread] = None


def _dual_broadcast_loop(session) -> None:
    """Forward live dual sensing.snapshot envelopes to WS subscribers.

    Existing dual queue -> existing WS subscriber list. Envelopes pass
    through byte-identical (node_id already tagged by the session pump).
    Backlog queued before any consumer existed is dropped via envelope
    ts so the visualization shows live RF evidence, never replay.
    Exits when the session stops (or is detached).
    """
    started = time.time()
    try:
        for _node_id, event in session.frames():
            if DUAL is not session or not isinstance(event, dict):
                break
            if event.get("type") != "sensing.snapshot":
                continue
            try:
                ts = float(event.get("ts", 0.0))
            except (TypeError, ValueError):
                ts = 0.0
            if ts < started:
                continue  # pre-consumer backlog: drop, never replay
            text = json.dumps(event)
            with STATE.lock:
                STATE.packets += 1
                STATE.last_frame_ts = time.time()
                STATE.last_seq = event.get("seq")
                targets = list(STATE.subscribers)
            dead = []
            for sock in targets:
                try:
                    ws_codec.send_text(sock, text)
                except Exception:
                    dead.append(sock)
            if dead:
                with STATE.lock:
                    STATE.subscribers = [s for s in STATE.subscribers
                                         if s not in dead]
    except Exception:
        pass


def _attach_vision(session) -> None:
    """Attach the RF Vision pipeline to a started dual session.

    Best-effort composition: per-node engines tap the existing
    ``sample_observer`` seam AFTER all acquisition bookkeeping. Any
    failure (missing deps, no model artifacts, unexpected error) leaves
    ``VISION`` as None — acquisition, sync, gates, and the WS fan-out
    are unaffected.
    """
    global VISION
    try:
        from web.vision import VisionPipeline
        pipeline = VisionPipeline(node_ids=tuple(session.node_ids))
        for nid, provider in session.providers.items():
            try:
                provider._sample_observer = pipeline.observer(nid)
            except Exception:
                pass
        VISION = pipeline
    except Exception:
        VISION = None


def _detach_vision() -> None:
    """Forget vision runtime state (dual stop)."""
    global VISION
    pipeline, VISION = VISION, None
    if pipeline is not None:
        try:
            pipeline.reset()
        except Exception:
            pass


def set_dual_session(session) -> None:
    """Attach (or detach with None) the live DualNodeSession."""
    global DUAL
    DUAL = session


def dual_start() -> Dict[str, Any]:
    """Start + attach the backend DualNodeSession (both nodes required).

    Uses the last discovered network context for the expected BSSID /
    channel (constructor defaults otherwise). Raises :class:`RuntimeError`
    when the session cannot run (live source holds ports, a session is
    already attached, or a board has no resolved device).
    """
    with _dual_lock:
        if DUAL is not None:
            raise RuntimeError("dual session already running "
                               "(POST /api/v1/dual/stop first)")
        if STATE.streaming or STATE.provider.mode == "live":
            raise RuntimeError("stop the live source first "
                               "(POST /api/v1/source {\"mode\": \"off\"}) "
                               "before starting the dual session")
        ctx = network_api.last_network()
        kwargs: Dict[str, Any] = {}
        if ctx is not None:
            if ctx.bssid:
                kwargs["expected_bssid"] = ctx.bssid
            if ctx.channel is not None:
                kwargs["expected_channel"] = ctx.channel
        session = _DUAL_SESSION_FACTORY(**kwargs)
        try:
            devices = session.start()
        except ValueError as exc:
            # Fail-fast board resolution (missing device): unavailable,
            # never a bad request — surface as a 409 via RuntimeError.
            try:
                session.stop()
            except Exception:
                pass
            raise RuntimeError(str(exc)) from exc
        except Exception:
            try:
                session.stop()
            except Exception:
                pass
            raise
        set_dual_session(session)
        global _dual_forward
        _dual_forward = threading.Thread(
            target=_dual_broadcast_loop, args=(session,),
            daemon=True, name="dual-ws-forward")
        _dual_forward.start()
        _attach_vision(session)
        return {"running": True, "nodes": list(session.node_ids),
                "devices": devices,
                "expected": {"bssid": session.expected_bssid,
                             "channel": session.expected_channel},
                "note": "poll GET /api/v1/nodes and GET "
                        "/api/v1/rf_readiness (CSI + sync gate RF READY)"}


def dual_stop() -> Dict[str, Any]:
    """Stop + detach the backend DualNodeSession (idempotent)."""
    global _TRIAL, _dual_forward
    with _dual_lock:
        session = DUAL
        if session is None:
            return {"running": False,
                    "reason": "no dual session running"}
        recorder = _TRIAL
        if recorder is not None and recorder.active:
            try:
                recorder.stop(reason="dual session stopped")
            except Exception:
                pass
        try:
            session.stop()
        finally:
            set_dual_session(None)
            _detach_vision()
            forward, _dual_forward = _dual_forward, None
        if forward is not None and forward.is_alive():
            # Session stop ends frames(); join only the exited forwarder.
            forward.join(timeout=5.0)
        return {"running": False,
                "reason": "dual session stopped; ports released"}


def trial_status_payload() -> Dict[str, Any]:
    """GET /api/v1/trials/current — active or last trial sidecar state."""
    recorder = _TRIAL
    return recorder.status() if recorder is not None else trial_api.idle_payload()


def trial_readiness() -> Dict[str, Any]:
    """Authoritative startup prerequisite, reusing GET /rf_readiness."""
    dual_info = DUAL.session_stats() if DUAL is not None else None
    return network_api.rf_readiness_payload(
        dual_info=dual_info, nodes_expected=2)


def trial_start(payload: Dict[str, Any]) -> Dict[str, Any]:
    """POST /api/v1/trials/start — begin timed dual-node raw recording."""
    global _TRIAL
    with _dual_lock:
        if DUAL is None:
            raise RuntimeError(
                "start the dual session before recording a trial")
        if _TRIAL is not None and _TRIAL.active:
            raise RuntimeError("trial already running (stop it first)")
        try:
            readiness = trial_readiness()
        except Exception as exc:
            raise RuntimeError(
                f"RF readiness could not be verified: {exc}") from exc
        if readiness.get("rf_ready") is not True:
            state = readiness.get("state") or "UNKNOWN"
            reason = (readiness.get("reason")
                      or "dual RF readiness is not satisfied")
            raise RuntimeError(
                "RF READY required to start a trial "
                f"(current: {state}) — {reason}")
        recorder = trial_api.TrialRecorder(DUAL)
        recorder.start(phases=payload.get("phases"),
                       audio_enabled=bool(
                           payload.get("audio_enabled", True)))
        _TRIAL = recorder
        return recorder.status()


def trial_stop(reason: str = "operator stopped the trial") -> Dict[str, Any]:
    """POST /api/v1/trials/stop — stop early and preserve partial captures."""
    with _dual_lock:
        recorder = _TRIAL
        if recorder is None:
            return trial_api.idle_payload()
        return recorder.stop(reason=reason)


def dual_status_payload() -> Dict[str, Any]:
    """Build the GET /api/v1/nodes payload from the attached session."""
    if DUAL is None:
        return contracts.nodes_payload(
            available=False, session=None, sync_state="UNSYNCED",
            nodes=[],
            reason="dual session not started (single-node operation)")
    info = DUAL.session_stats()
    sync = info.get("sync", {})
    entries = []
    for nid, node in info.get("per_node", {}).items():
        stream = node.get("stream", {})
        signal = node.get("signal", {})
        timing = node.get("timing", {})
        sync_n = node.get("sync", {})
        valid = int(stream.get("valid", 0))
        source_state = node.get("source_state")
        if source_state == "DISCONNECTED":
            connection = "DISCONNECTED"
        elif bool(stream.get("stale")):
            connection = "DEGRADED"
        elif source_state == "LIVE_VERIFIED":
            connection = ("SYNCED" if sync.get("state") == "SYNCED"
                          else "LIVE")
        elif source_state == "LIVE_UNVERIFIED":
            connection = "SYNCING"
        else:
            connection = "DEGRADED"
        entries.append(contracts.node_status_payload(
            node_id=nid, board_mac=node.get("board_mac", "UNKNOWN"),
            port=node.get("port", "UNKNOWN"), connection=connection,
            source_state=node.get("source_state", "DISCONNECTED"),
            csi_rate=stream.get("rate_hz"), valid=valid,
            valid_pct=stream.get("valid_pct"),
            malformed=int(stream.get("malformed", 0)),
            duplicates=int(stream.get("duplicates", 0)),
            out_of_order=int(stream.get("out_of_order", 0)),
            gaps=int(stream.get("gaps", 0)),
            rssi=signal.get("rssi_last"), channel=signal.get("channel"),
            bssid=signal.get("bssid"), tones=signal.get("tones"),
            host_pipeline_us_mean=timing.get("host_pipeline_us_mean"),
            esp_latency_us=timing.get("esp_to_host_latency_us"),
            sync_ready=bool(sync_n.get("ready", False)),
            sync_offset_ns=sync_n.get("offset_ns"),
            sync_jitter_ns=sync_n.get("jitter_ns"),
            sync_observations=int(sync_n.get("observations", 0))))
    return contracts.nodes_payload(
        available=True,
        session={"nodes": list(info.get("nodes", [])),
                 "elapsed_s": info.get("elapsed_s")},
        sync_state=sync.get("state", "UNSYNCED"), nodes=entries,
        reason=None)


class ConsoleHandler(BaseHTTPRequestHandler):
    """HTTP API + static files + WS upgrade on /ws/sensing."""

    server_version = f"RFVision-Web/{WEB_VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter logs
        pass

    # -- helpers -------------------------------------------------------
    def _json(self, obj: Any, code: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, message: str, code: int = 400) -> None:
        self._json({"error": message}, code)

    def _read_json(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    # -- routing ---------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (handler naming convention)
        path = urlparse(self.path).path
        if path == "/ws/sensing":
            self._handle_ws()
        elif path in ("/", "/react"):
            # React dashboard is the default landing page (demo-launch
            # convenience). Legacy UI preserved at /legacy and /index.html.
            self._static("react/index.html")
        elif path in ("/legacy", "/index.html"):
            self._static("index.html")
        elif path.startswith("/static/"):
            self._static(path[len("/static/"):])
        elif path == "/api/v1/health":
            node_mode = STATE._showcase_topology()[0]
            self._json(contracts.health_payload(
                status=("degraded" if node_mode == "SINGLE-DEGRADED"
                        else "ok"),
                version=WEB_VERSION,
                uptime_s=time.time() - STATE.started_at,
                source="rfvision-web", source_state=STATE.effective_state()))
        elif path == "/api/v1/status":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            stats = live.live_stats() if live is not None else None
            self._json({**contracts.status_payload(
                connection=("ONLINE" if STATE.streaming else "OFFLINE"),
                csi_rate=(stats["stream"]["rate_hz"] if stats else None),
                packets=STATE.packets,
                malformed=(stats["stream"]["malformed"]
                           if stats else STATE.malformed),
                latency_ms=None,
                model="none (heuristic)",
                source_state=STATE.effective_state()),
                "stale": STATE.effective_state() == "STALE",
                "last_frame_age_s": STATE.frame_age_s()})
        elif path == "/api/v1/sensing/latest":
            snap = STATE.provider.latest_snapshot()
            self._json({"available": snap is not None, "event": snap})
        elif path == "/api/v1/telemetry":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            if live is not None:
                stats = live.live_stats()
                rejected = dict(stats["parser"]["rejected"])
                if stats["stream"]["non_csi_lines"]:
                    rejected["non_csi"] = stats["stream"]["non_csi_lines"]
                age = stats["stream"]["last_update_age_s"]
                self._json(contracts.telemetry_payload(
                    packets=stats["stream"]["valid"],
                    malformed=stats["stream"]["malformed"],
                    rejected=rejected, last_seq=stats["stream"]["last_seq"],
                    last_update=(time.time() - age if age is not None
                                 else None)))
                return
            self._json(contracts.telemetry_payload(
                packets=STATE.packets, malformed=STATE.malformed,
                rejected={}, last_seq=STATE.last_seq,
                last_update=STATE.last_frame_ts))
        elif path == "/api/v1/stream/status":
            self._json(STATE.stream_status())
        elif path == "/api/v1/experiment":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            if live is not None:
                stats = live.live_stats()
                rec = stats["recording"]
                self._json(contracts.experiment_payload(
                    session_id=stats["session_id"],
                    software={"rfvision_web": WEB_VERSION,
                              "python": platform.python_version(),
                              "contract": str(contracts.CONTRACT_VERSION)},
                    hardware={**BASELINE, "connection":
                              ("serial open" if stats["transport"]["open"]
                               else "serial closed/idle")},
                    firmware=FIRMWARE,
                    geometry={"room_width_m": None, "room_length_m": None,
                              "configured_default_m": [5.0, 4.0],
                              "status": "UNCALIBRATED",
                              "note": "defaults are not measurements"},
                    raw_ref=({"path": rec["path"], "bytes": rec["bytes"],
                              "sha256": rec["sha256"],
                              "state": "recording" if rec["active"]
                              else "stopped"}
                             if rec["path"] else None),
                    validation="NOT_RUN"))
            else:
                self._json(contracts.experiment_payload(
                    session_id="NO_ACTIVE_SESSION",
                    software={"rfvision_web": WEB_VERSION,
                              "python": platform.python_version(),
                              "contract": str(contracts.CONTRACT_VERSION)},
                    hardware={**BASELINE, "connection": "UNKNOWN"},
                    firmware=FIRMWARE,
                    geometry={"room_width_m": None, "room_length_m": None,
                              "configured_default_m": [5.0, 4.0],
                              "status": "UNCALIBRATED",
                              "note": "defaults are not measurements"},
                    raw_ref=None, validation="NOT_RUN"))
        elif path == "/api/v1/calibration":
            self._json(contracts.calibration_payload(
                status="UNCALIBRATED", room_width_m=None,
                room_length_m=None, movement_threshold=None,
                calibrated_at=None))
        elif path == "/api/v1/localization":
            self._json(contracts.localization_payload(
                frame="link-1d", position=None, position_m=None, raw=None,
                uncertainty=None, room_width_m=None, sync="NONE",
                nodes=[{"id": "router", "role": "tx",
                        "position_m": None},
                       {"id": "esp32", "role": "rx",
                        "position_m": None}]))
        elif path == "/api/v1/xai":
            self._json(contracts.xai_payload(available=False))
        elif path == "/api/v1/nodes":
            self._json(dual_status_payload())
        elif path == "/api/v1/vision":
            pipeline = VISION
            if pipeline is None:
                self._json(contracts.vision_payload(
                    available=False,
                    reason="no dual vision pipeline attached "
                           "(POST /api/v1/dual/start first)"))
            else:
                try:
                    self._json(contracts.vision_payload(
                        available=True, vision=pipeline.snapshot()))
                except Exception as exc:
                    self._json(contracts.vision_payload(
                        available=False,
                        reason=f"vision snapshot failed: {exc}"))
        elif path == "/api/v1/network":
            self._json(network_api.network_status_payload())
        elif path == "/api/v1/rf_readiness":
            dual_info = (DUAL.session_stats() if DUAL is not None
                         else None)
            expected = (2 if (DUAL is not None or
                              STATE.provider.mode != "live")
                        else 1)
            self._json(network_api.rf_readiness_payload(
                dual_info=dual_info, nodes_expected=expected))
        elif path == "/api/v1/trials/current":
            self._json(trial_status_payload())
        elif path == "/api/v1/live":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            if live is None:
                self._json({"available": False,
                            "reason": "live provider not selected "
                            "(POST /api/v1/source {\"mode\": \"live\"})"})
            else:
                self._json(live.live_stats())
        else:
            self._error("not found", 404)

    def do_POST(self) -> None:  # noqa: N802 (handler naming convention)
        path = urlparse(self.path).path
        if path == "/api/v1/stream/start":
            self._json(STATE.start_stream())
        elif path == "/api/v1/stream/stop":
            self._json(STATE.stop_stream())
        elif path == "/api/v1/source":
            body = self._read_json()
            mode = str(body.get("mode", ""))
            if mode == "live" and DUAL is not None:
                self._error("stop the dual session first "
                            "(POST /api/v1/dual/stop) "
                            "before selecting a live source", 409)
                return
            kwargs: Dict[str, Any] = {}
            if mode == "fixture" and body.get("path"):
                kwargs["path"] = str(body["path"])
            if mode == "live":
                for key in ("port", "expected_bssid"):
                    if body.get(key):
                        kwargs[key] = str(body[key])
                for key in ("baud", "expected_channel"):
                    if body.get(key) is not None:
                        try:
                            kwargs[key] = int(body[key])
                        except (TypeError, ValueError):
                            self._error(f"bad {key}: {body[key]!r}", 400)
                            return
            try:
                self._json(STATE.set_source(mode, **kwargs))
            except sources.LiveUnavailable as exc:
                self._error(str(exc), 409)
            except (contracts.ContractError, FileNotFoundError,
                    ValueError) as exc:
                self._error(str(exc), 400)
        elif path == "/api/v1/live/record/start":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            if live is None:
                self._error("live provider not selected", 409)
                return
            body = self._read_json()
            try:
                max_s = float(body.get("max_seconds", 10.0))
            except (TypeError, ValueError):
                self._error("bad max_seconds", 400)
                return
            if not 1.0 <= max_s <= sources.LiveProvider.REC_MAX_SECONDS:
                self._error(
                    "max_seconds must be within "
                    f"[1, {sources.LiveProvider.REC_MAX_SECONDS:g}]", 400)
                return
            stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
            target = (Path.cwd() / "research-data" / "live-diag"
                      / f"live_diag_{stamp}.bin")
            try:
                started = live.start_recording(target, max_seconds=max_s)
            except sources.LiveSerialError as exc:
                self._error(str(exc), 409)
                return
            self._json({"recording": True, "path": started,
                        "max_seconds": max_s,
                        "note": "diagnostic only; never sensing evidence"})
        elif path == "/api/v1/live/record/stop":
            live = (STATE.provider if STATE.provider.mode == "live"
                    else None)
            if live is None:
                self._error("live provider not selected", 409)
                return
            info = live.stop_recording()
            self._json({"recording": False, "manifest": info})
        elif path == "/api/v1/network/provision":
            # Ports must be free and RFV_* lines must never enter the
            # CSI parser: refuse while any live source holds them.
            if DUAL is not None:
                self._error("stop the dual session first "
                            "(POST /api/v1/dual/stop) "
                            "before provisioning", 409)
                return
            if STATE.streaming or STATE.provider.mode == "live":
                self._error("stop the live source first "
                            "(POST /api/v1/source {\"mode\": \"off\"}) "
                            "before provisioning", 409)
                return
            body = self._read_json()
            ssid = body.get("ssid", "")
            password = body.get("password", "")
            node_ids = body.get("nodes")
            if node_ids is not None and not isinstance(node_ids, list):
                self._error("bad nodes: expected a list of node ids",
                            400)
                return
            try:
                self._json(network_api.provision_nodes(
                    str(ssid), str(password),
                    node_ids=([str(n) for n in node_ids]
                              if node_ids is not None else None)))
            except ValueError as exc:
                self._error(str(exc), 400)
            except RuntimeError as exc:
                self._error(str(exc), 409)
        elif path == "/api/v1/network/inspect":
            if DUAL is not None:
                self._error("stop the dual session first "
                            "(POST /api/v1/dual/stop) "
                            "before inspecting node networks", 409)
                return
            if STATE.streaming or STATE.provider.mode == "live":
                self._error("stop the live source first "
                            "(POST /api/v1/source {\"mode\": \"off\"}) "
                            "before inspecting node networks", 409)
                return
            body = self._read_json()
            node_ids = body.get("nodes")
            if node_ids is not None and not isinstance(node_ids, list):
                self._error("bad nodes: expected a list of node ids",
                            400)
                return
            try:
                self._json(network_api.inspect_nodes(
                    node_ids=([str(n) for n in node_ids]
                              if node_ids is not None else None)))
            except ValueError as exc:
                self._error(str(exc), 400)
        elif path == "/api/v1/trials/start":
            body = self._read_json()
            try:
                self._json(trial_start(body))
            except RuntimeError as exc:
                self._error(str(exc), 409)
            except ValueError as exc:
                self._error(str(exc), 400)
        elif path == "/api/v1/trials/stop":
            body = self._read_json()
            reason = str(body.get("reason") or "operator stopped the trial")
            self._json(trial_stop(reason=reason))
        elif path == "/api/v1/dual/start":
            try:
                self._json(dual_start())
            except RuntimeError as exc:
                self._error(str(exc), 409)
        elif path == "/api/v1/dual/stop":
            self._json(dual_stop())
        else:
            self._error("not found", 404)

    # -- static ----------------------------------------------------------
    def _static(self, name: str) -> None:
        target = (STATIC_DIR / name).resolve()
        if STATIC_DIR not in target.parents and target != STATIC_DIR:
            self._error("not found", 404)
            return
        if not target.is_file():
            self._error("not found", 404)
            return
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         MIME.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        if target.suffix in (".html",):
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    # -- websocket ---------------------------------------------------------
    def _handle_ws(self) -> None:
        if self.headers.get("Upgrade", "").lower() != "websocket":
            self._error("websocket upgrade required", 426)
            return
        raw = (f"{self.command} {self.path} {self.request_version}\r\n"
               + "".join(f"{k}: {v}\r\n"
                         for k, v in self.headers.items()) + "\r\n")
        try:
            _, response = ws_codec.server_handshake(raw)
        except ws_codec.WsError as exc:
            self._error(f"handshake failed: {exc}", 400)
            return
        sock = self.connection
        try:
            sock.sendall(response.encode("ascii"))
        except ConnectionError:
            return
        STATE.subscribe(sock)
        self.close_connection = True
        try:
            ws_codec.send_text(sock, json.dumps(contracts.wrap_event(
                "system.log",
                {"message": "ws connected",
                 "source_state": STATE.effective_state()},
                source="rfvision-web")))
            while True:
                _, payload = ws_codec.recv_frame(
                    sock, timeout=WS_RECV_TIMEOUT_S)
                try:
                    msg = json.loads(payload.decode("utf-8"))
                except ValueError:
                    continue
                self._ws_command(sock, msg)
        except (ws_codec.WsError, ConnectionError):
            pass
        finally:
            STATE.unsubscribe(sock)

    def _ws_command(self, sock: Any, msg: Dict[str, Any]) -> None:
        cmd = msg.get("command")
        if cmd == "ping":
            ws_codec.send_text(sock, json.dumps({"type": "pong",
                                                 "ts": time.time()}))
        elif cmd == "stream:start":
            ws_codec.send_text(sock, json.dumps(STATE.start_stream()))
        elif cmd == "stream:stop":
            ws_codec.send_text(sock, json.dumps(STATE.stop_stream()))
        elif cmd == "set_source":
            if str(msg.get("mode", "")) == "live" and DUAL is not None:
                ws_codec.send_text(sock, json.dumps(
                    {"error": "stop the dual session first "
                              "(POST /api/v1/dual/stop) "
                              "before selecting a live source"}))
                return
            try:
                result = STATE.set_source(str(msg.get("mode", "")))
            except (sources.LiveUnavailable, contracts.ContractError,
                    FileNotFoundError, ValueError) as exc:
                result = {"error": str(exc)}
            ws_codec.send_text(sock, json.dumps(result))


def build_server(port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """Build (not serve) the console server bound to 127.0.0.1:port."""
    server = ThreadingHTTPServer(("127.0.0.1", port), ConsoleHandler)
    server.daemon_threads = True
    return server


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point: ``python3 -m web.server [--port N]`` (repo root)."""
    import argparse
    parser = argparse.ArgumentParser(description="RF Vision web console")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args(argv)
    server = build_server(args.port)
    print(f"RF Vision console at http://127.0.0.1:{args.port}/ "
          f"(source=DISCONNECTED until you POST /api/v1/source)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
