"""RF Vision web-console server (RFVISION-005).

RF Vision native, stdlib only (``http.server`` + ``threading`` + the
``web/ws.py`` codec). Serves the dependency-free frontend in
``web/static/`` plus a versioned JSON API and a WebSocket event stream.

Endpoints (all JSON unless noted):
- ``GET /`` → ``web/static/index.html`` (static files under ``/static/``)
- ``GET /api/v1/health`` — liveness + contract + provenance
- ``GET /api/v1/status`` — ``system.status`` payload (+staleness)
- ``GET /api/v1/sensing/latest`` — latest ``sensing.snapshot`` envelope
  (``{"available": false}`` when none yet)
- ``GET /api/v1/telemetry`` — adapter/parser counters
- ``GET /api/v1/stream/status`` + ``POST /api/v1/stream/start|stop``
- ``POST /api/v1/source {"mode": off|fixture|simulated|live}``
  (``live`` is refused until RFVISION-003R)
- ``GET /api/v1/experiment|calibration|localization|xai``
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
from web import source as sources
from web import ws as ws_codec

__all__ = ["DEFAULT_PORT", "ConsoleState", "ConsoleHandler",
           "build_server", "main", "BASELINE", "FIRMWARE"]

DEFAULT_PORT = 8130
STALE_AFTER_S = 3.0

#: Validated hardware baseline surfaced by /api/v1/experiment + /hardware.
BASELINE = {
    "esp32": "ESP32-D0WD-V3 rev 3.1",
    "flash_mb": 4,
    "csi_stack": "Espressif ESP-CSI",
    "router": "Xiaomi Mi Router 4C/R4CM",
    "band": "2.4 GHz",
    "transport": "USB serial",
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

    # -- source / stream control -------------------------------------
    def set_source(self, mode: str, **kwargs: Any) -> Dict[str, Any]:
        """Switch provider (raises LiveUnavailable/ContractError/FileNotFound)."""
        provider = sources.make_provider(mode, **kwargs)
        with self.lock:
            self.provider = provider
            self.streaming = False
            self.packets = 0
            self.last_frame_ts = None
            self.last_seq = None
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
        elif path in ("/", "/index.html"):
            self._static("index.html")
        elif path.startswith("/static/"):
            self._static(path[len("/static/"):])
        elif path == "/api/v1/health":
            self._json(contracts.health_payload(
                status="ok", version=WEB_VERSION,
                uptime_s=time.time() - STATE.started_at,
                source="rfvision-web", source_state=STATE.effective_state()))
        elif path == "/api/v1/status":
            self._json({**contracts.status_payload(
                connection=("ONLINE" if STATE.streaming else "OFFLINE"),
                csi_rate=None, packets=STATE.packets,
                malformed=STATE.malformed, latency_ms=None,
                model="none (heuristic)",
                source_state=STATE.effective_state()),
                "stale": STATE.effective_state() == "STALE",
                "last_frame_age_s": STATE.frame_age_s()})
        elif path == "/api/v1/sensing/latest":
            snap = STATE.provider.latest_snapshot()
            self._json({"available": snap is not None, "event": snap})
        elif path == "/api/v1/telemetry":
            self._json(contracts.telemetry_payload(
                packets=STATE.packets, malformed=STATE.malformed,
                rejected={}, last_seq=STATE.last_seq,
                last_update=STATE.last_frame_ts))
        elif path == "/api/v1/stream/status":
            self._json(STATE.stream_status())
        elif path == "/api/v1/experiment":
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
            kwargs: Dict[str, Any] = {}
            if mode == "fixture" and body.get("path"):
                kwargs["path"] = str(body["path"])
            try:
                self._json(STATE.set_source(mode, **kwargs))
            except sources.LiveUnavailable as exc:
                self._error(str(exc), 409)
            except (contracts.ContractError, FileNotFoundError,
                    ValueError) as exc:
                self._error(str(exc), 400)
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
        sock.sendall(response.encode("ascii"))
        STATE.subscribe(sock)
        self.close_connection = True
        try:
            ws_codec.send_text(sock, json.dumps(contracts.wrap_event(
                "system.log",
                {"message": "ws connected",
                 "source_state": STATE.effective_state()},
                source="rfvision-web")))
            while True:
                _, payload = ws_codec.recv_frame(sock, timeout=30.0)
                try:
                    msg = json.loads(payload.decode("utf-8"))
                except ValueError:
                    continue
                self._ws_command(sock, msg)
        except ws_codec.WsError:
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
