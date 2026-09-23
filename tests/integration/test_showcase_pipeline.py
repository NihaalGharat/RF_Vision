"""P1 showcase pipeline integration (no hardware).

Verifies the full truthful chain on synthetic CSI::

    synthetic CSI_DATA lines
    → LiveProvider (validated parse/gate path + sample seam)
    → InferenceEngine (existing deterministic math, heuristic fallback)
    → showcase snapshot → contract v3 → server API → UI payload

Asserts: normal live state, degraded topology derate, disappearance
persistence shape, unavailable XAI preserved, uncalibrated confidence
labelling, and no fabricated localization. Fixture/simulated modes stay
transport-only (no inference attached).
"""

import json
import threading
import time
import unittest
import urllib.request

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from synthetic.synth import make_esp_csv_line  # noqa: E402

from web import contracts  # noqa: E402
from web import server as console  # noqa: E402
from web import source as sources  # noqa: E402
from web.live_serial import FakeLineSource  # noqa: E402
from sensing.inference_engine import InferenceEngine  # noqa: E402


def _lines(n=160, seed=11, channel=1, rssi=-52):
    return [make_esp_csv_line(seq=i + 1, seed=(seed + i * 7) % 251,
                              channel=channel, rssi=rssi)
            for i in range(n)]


def _drain(provider, limit=500):
    events = []
    for event in provider.frames():
        events.append(event)
        if len(events) >= limit:
            break
    return events


class ShowcasePipelineTests(unittest.TestCase):
    def test_live_seam_feeds_engine_without_changing_frames(self):
        engine = InferenceEngine({}, None)
        seen = []
        plain = sources.LiveProvider(line_source=FakeLineSource(_lines()))
        hooked = sources.LiveProvider(
            line_source=FakeLineSource(_lines()),
            sample_observer=lambda s: (seen.append(s),
                                       engine.process_sample(s)))
        plain_events = _drain(plain)
        hooked_events = _drain(hooked)
        # Same validated frames with or without the seam attached...
        self.assertEqual(len(plain_events), len(hooked_events))
        for a, b in zip(plain_events, hooked_events):
            self.assertEqual(a["payload"]["rssi"], b["payload"]["rssi"])
            self.assertEqual(a["payload"]["amplitudes"],
                             b["payload"]["amplitudes"])
        # ...and the engine actually saw every valid sample.
        self.assertGreater(len(seen), 100)
        snap = engine.showcase_snapshot()
        contracts.showcase_fields(**snap)  # must validate
        self.assertEqual(snap["confidence_calibration"], "UNCALIBRATED")

    def test_observer_exception_never_breaks_capture(self):
        def bad(sample):
            raise RuntimeError("showcase bug")
        provider = sources.LiveProvider(line_source=FakeLineSource(_lines()),
                                        sample_observer=bad)
        events = _drain(provider)
        self.assertGreater(len(events), 0)

    def test_degraded_topology_derates(self):
        engine = InferenceEngine({}, None)
        provider = sources.LiveProvider(
            line_source=FakeLineSource(_lines()),
            sample_observer=engine.process_sample)
        _drain(provider)
        full = engine.showcase_snapshot()
        degraded = engine.showcase_snapshot(
            node_mode="SINGLE-DEGRADED", nodes_available=1, nodes_total=2,
            derate=0.75)
        self.assertEqual(degraded["node_mode"], "SINGLE-DEGRADED")
        contracts.showcase_fields(**degraded)
        if full["rf_evidence_confidence"] is not None:
            self.assertLessEqual(degraded["rf_evidence_confidence"],
                                 full["rf_evidence_confidence"])

    def test_fixture_mode_stays_transport_only(self):
        state = console.ConsoleState()
        state.set_source("fixture")
        self.assertIsNone(state._showcase_engine)


class ShowcaseServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        cls.port = sock.getsockname()[1]
        sock.close()
        cls.server = console.build_server(cls.port)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path, obj):
        req = urllib.request.Request(
            self.base + path, data=json.dumps(obj).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path):
        with urllib.request.urlopen(self.base + path,
                                    timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_live_api_carries_showcase_fields(self):
        # Paced lines: frames decimate at ~10 Hz while the engine needs
        # dozens of samples before its first windowed output — an instant
        # burst would drain before any inference exists.
        console.STATE.set_source(
            "live", line_source=FakeLineSource(_lines(n=400),
                                               pace_s=0.005))
        try:
            console.STATE.start_stream()
            deadline = time.time() + 15.0
            payload = None
            while time.time() < deadline:
                data = self._get("/api/v1/sensing/latest")
                if data.get("available"):
                    payload = data["event"]["payload"]
                    if payload.get("provenance") == "RF-INFERRED":
                        break
                time.sleep(0.2)
            self.assertIsNotNone(payload, "no live snapshot served")
            # Transport honesty preserved...
            self.assertIn(payload["source_state"],
                          ("LIVE_VERIFIED", "LIVE_UNVERIFIED"))
            self.assertFalse(payload["validated"])
            # ...showcase layer present and honest.
            self.assertIn(payload["presence_state"],
                          contracts.PRESENCE_STATES)
            self.assertEqual(payload["confidence_calibration"],
                             "UNCALIBRATED")
            self.assertEqual(payload["provenance"], "RF-INFERRED")
            self.assertIn(payload["node_mode"], contracts.NODE_MODES)
            self.assertIn("Evidence:", payload["evidence_statement"])
            self.assertIsInstance(payload["trail"], list)
            # No fabricated localization: position stays None without
            # trained models; trail holds only measured 1-D values.
            self.assertIsNone(payload["position"])
            # XAI endpoint still honestly unavailable.
            xai = self._get("/api/v1/xai")
            self.assertFalse(xai["available"])
            # Health stays a valid contract.
            health = self._get("/api/v1/health")
            self.assertIn(health["status"], ("ok", "degraded"))
            self.assertEqual(health["contract"],
                             contracts.CONTRACT_VERSION)
        finally:
            console.STATE.stop_stream()
            pump = console.STATE._pump
            if pump is not None:
                pump.join(timeout=5.0)
            console.STATE.set_source("off")

    def test_simulated_mode_has_no_showcase(self):
        console.STATE.set_source("simulated")
        try:
            console.STATE.start_stream()
            deadline = time.time() + 10.0
            payload = None
            while time.time() < deadline:
                data = self._get("/api/v1/sensing/latest")
                if data.get("available"):
                    payload = data["event"]["payload"]
                    break
                time.sleep(0.2)
            self.assertIsNotNone(payload)
            self.assertEqual(payload["presence_state"], "UNKNOWN")
            self.assertIsNone(payload["rf_evidence_confidence"])
        finally:
            console.STATE.stop_stream()
            pump = console.STATE._pump
            if pump is not None:
                pump.join(timeout=5.0)
            console.STATE.set_source("off")


if __name__ == "__main__":
    unittest.main()
