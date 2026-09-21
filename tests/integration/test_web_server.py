"""Server integration tests for the RF Vision web console (RFVISION-005).

Spins up ``web/server.py`` on an ephemeral loopback port (stdlib only) and
exercises: static serving, every REST endpoint's contract shape, source
switching incl. the live gate, stream start/stop, and a real RFC 6455
WebSocket handshake followed by fixture frames with valid provenance.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import threading
import time
import unittest
import urllib.error
import urllib.request

from web import contracts
from web import server as console


def _free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class ConsoleServerTests(unittest.TestCase):
    """End-to-end HTTP + WS against a live test server."""

    @classmethod
    def setUpClass(cls):
        # Isolate mutable console state per test-class run.
        cls.state = console.ConsoleState()
        cls._orig_state = console.STATE
        console.STATE = cls.state
        cls.port = _free_port()
        cls.server = console.build_server(cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)
        console.STATE = cls._orig_state

    # -- helpers ------------------------------------------------------
    def get(self, path):
        try:
            with urllib.request.urlopen(self.base + path) as res:
                return res.status, json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, {"_http_error": exc.code}

    def post(self, path, body=None):
        data = json.dumps(body or {}).encode()
        req = urllib.request.Request(self.base + path, data=data,
                                     headers={"Content-Type":
                                              "application/json"})
        try:
            with urllib.request.urlopen(req) as res:
                return res.status, json.loads(res.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode())

    # -- tests ----------------------------------------------------------
    def test_index_and_static(self):
        with urllib.request.urlopen(self.base + "/") as res:
            html = res.read().decode()
        self.assertIn("RF VISION", html)
        self.assertIn("/static/js/app.js", html)
        with urllib.request.urlopen(self.base + "/static/js/store.js") as res:
            self.assertIn("SourceStore", res.read().decode())
        with urllib.request.urlopen(self.base + "/static/vendor/three.module.js") as res:
            self.assertIn("REVISION = '160'", res.read().decode()[:2000])

    def test_health_shape(self):
        code, data = self.get("/api/v1/health")
        self.assertEqual(code, 200)
        self.assertEqual(data["contract"], contracts.CONTRACT_VERSION)
        contracts.require_source_state(data["source_state"])

    def test_status_reports_disconnected_initially(self):
        # Order-independent: force the disconnected baseline first.
        self.post("/api/v1/stream/stop")
        self.post("/api/v1/source", {"mode": "off"})
        code, data = self.get("/api/v1/status")
        self.assertEqual(code, 200)
        self.assertEqual(data["connection"], "OFFLINE")
        self.assertIsNone(data["csi_rate"])
        self.assertEqual(data["source_state"], "DISCONNECTED")

    def test_latest_empty_before_stream(self):
        self.post("/api/v1/stream/stop")
        self.post("/api/v1/source", {"mode": "off"})
        code, data = self.get("/api/v1/sensing/latest")
        self.assertEqual(code, 200)
        self.assertFalse(data["available"])
        self.assertIsNone(data["event"])

    def test_live_source_refused(self):
        code, data = self.post("/api/v1/source", {"mode": "live"})
        self.assertEqual(code, 409)
        self.assertIn("003R", data["error"])

    def test_bad_source_rejected(self):
        code, _ = self.post("/api/v1/source", {"mode": "quantum"})
        self.assertEqual(code, 400)

    def test_fixture_source_and_stream(self):
        code, data = self.post("/api/v1/source", {"mode": "fixture"})
        self.assertEqual(code, 200)
        self.assertEqual(data["source_state"], "OFFLINE_FIXTURE")
        code, data = self.post("/api/v1/stream/start")
        self.assertTrue(data["running"])
        time.sleep(0.6)  # let the pump broadcast a few frames
        code, latest = self.get("/api/v1/sensing/latest")
        self.assertTrue(latest["available"])
        event = latest["event"]
        contracts.validate_envelope(json.dumps(event))
        self.assertEqual(event["payload"]["source_state"], "OFFLINE_FIXTURE")
        code, data = self.post("/api/v1/stream/stop")
        self.assertFalse(data["running"])

    def test_simulated_source(self):
        code, data = self.post("/api/v1/source", {"mode": "simulated"})
        self.assertEqual(code, 200)
        self.assertEqual(data["source_state"], "SIMULATED")

    def test_experiment_calibration_localization_xai(self):
        _, exp = self.get("/api/v1/experiment")
        self.assertEqual(exp["session_id"], "NO_ACTIVE_SESSION")
        self.assertEqual(exp["validation"], "NOT_RUN")
        self.assertIsNone(exp["geometry"]["room_width_m"])
        self.assertEqual(exp["firmware"]["identity"], "UNKNOWN")
        _, cal = self.get("/api/v1/calibration")
        self.assertEqual(cal["status"], "UNCALIBRATED")
        _, loc = self.get("/api/v1/localization")
        self.assertEqual(loc["frame"], "link-1d")
        self.assertIsNone(loc["position"])
        _, xai = self.get("/api/v1/xai")
        self.assertEqual(xai, {"available": False, "status": "NOT AVAILABLE"})

    def test_websocket_handshake_and_fixture_frames(self):
        self.post("/api/v1/source", {"mode": "fixture"})
        self.post("/api/v1/stream/start")
        try:
            sock = socket.create_connection(("127.0.0.1", self.port),
                                            timeout=10)
            key = base64.b64encode(os.urandom(16)).decode()
            sock.sendall(
                ("GET /ws/sensing HTTP/1.1\r\n"
                 "Host: 127.0.0.1\r\n"
                 "Upgrade: websocket\r\n"
                 "Connection: Upgrade\r\n"
                 f"Sec-WebSocket-Key: {key}\r\n"
                 "Sec-WebSocket-Version: 13\r\n\r\n").encode())
            response = b""
            while b"\r\n\r\n" not in response:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
            header = response.decode("ascii", "replace")
            self.assertIn("101 Switching Protocols", header)
            self.assertIn(console.ws_codec.accept_key(key), header)
            # Read frames until a sensing.snapshot arrives (skip log hello).
            sock.settimeout(10)
            seen_snapshot = False
            for _ in range(10):
                hdr = sock.recv(2)
                length = hdr[1] & 0x7F
                if length == 126:
                    length = int.from_bytes(sock.recv(2), "big")
                payload = b""
                while len(payload) < length:
                    payload += sock.recv(length - len(payload))
                msg = json.loads(payload.decode())
                if msg.get("type") == "sensing.snapshot":
                    contracts.validate_envelope(json.dumps(msg))
                    self.assertEqual(msg["payload"]["source_state"],
                                     "OFFLINE_FIXTURE")
                    seen_snapshot = True
                    break
            self.assertTrue(seen_snapshot, "no sensing.snapshot received")
            sock.close()
        finally:
            self.post("/api/v1/stream/stop")

    def test_ws_rejects_plain_http(self):
        code, _ = self.get("/ws/sensing")
        self.assertEqual(code, 426)


if __name__ == "__main__":
    unittest.main()
