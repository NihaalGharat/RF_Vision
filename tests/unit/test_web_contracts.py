"""Contract tests for the RF Vision web console (RFVISION-005).

Covers operation §21: schema validity, source-state handling, stale-data
handling, disconnect handling, malformed messages, empty states, fixture
playback, visualization input shapes, localization uncertainty shape, and
the XAI availability state. Stdlib only.
"""

from __future__ import annotations

import json
import re
import socket
import unittest
from pathlib import Path

from web import contracts
from web.contracts import ContractError
from web import source as sources
from web import ws as ws_codec


def _snapshot(**overrides):
    base = {"presence": "UNKNOWN", "presence_prob": None,
            "movement": "UNKNOWN", "movement_prob": None,
            "position": None, "position_m": None, "confidence": None,
            "validated": False}
    base.update(overrides)
    return contracts.sensing_snapshot_payload(**base)


class SourceStateTests(unittest.TestCase):
    """Every view state token must be known; live/synthetic never mix."""

    def test_all_states_accepted(self):
        for state in ("LIVE_VERIFIED", "LIVE_UNVERIFIED", "OFFLINE_FIXTURE",
                      "SIMULATED", "STALE", "DISCONNECTED"):
            self.assertEqual(contracts.require_source_state(state), state)

    def test_unknown_state_rejected(self):
        for bad in ("LIVE", "live_verified", "", "MOCK", None, 42):
            with self.assertRaises(ContractError):
                contracts.require_source_state(bad)

    def test_non_live_states_require_badge(self):
        for state in contracts.NON_LIVE_STATES:
            self.assertNotIn(state, contracts.LIVE_LIKE_STATES)


class PayloadSchemaTests(unittest.TestCase):
    """Each REST payload validates its fields and rejects garbage."""

    def test_health(self):
        payload = contracts.health_payload(
            status="ok", version="0.1.0", uptime_s=3.5, source="rfvision-web",
            source_state="DISCONNECTED")
        self.assertEqual(payload["contract"], contracts.CONTRACT_VERSION)
        with self.assertRaises(ContractError):
            contracts.health_payload(status="fine", version="0.1.0",
                                     uptime_s=1.0, source="x",
                                     source_state="DISCONNECTED")

    def test_status_unknowns_stay_unknown(self):
        payload = contracts.status_payload(
            connection="OFFLINE", csi_rate=None, packets=0, malformed=0,
            latency_ms=None, model="none (heuristic)",
            source_state="DISCONNECTED")
        self.assertIsNone(payload["csi_rate"])
        self.assertIsNone(payload["latency_ms"])
        with self.assertRaises(ContractError):
            contracts.status_payload(connection="SORTA", csi_rate=1.0,
                                     packets=0, malformed=0, latency_ms=1.0,
                                     model="x", source_state="DISCONNECTED")

    def test_sensing_snapshot_ranges(self):
        payload = _snapshot(presence="PERSON", presence_prob=0.8,
                            movement="MOVING", movement_prob=0.7,
                            position=0.4, confidence=0.8,
                            rssi=-50.0, amplitudes=[1.0, 2.0])
        self.assertEqual(payload["presence"], "PERSON")
        with self.assertRaises(ContractError):  # prob outside [0,1]
            _snapshot(presence_prob=1.5)
        with self.assertRaises(ContractError):  # position outside [0,1]
            _snapshot(position=1.2)
        with self.assertRaises(ContractError):  # bad label
            _snapshot(presence="MAYBE")

    def test_telemetry(self):
        payload = contracts.telemetry_payload(
            packets=10, malformed=1, rejected={"malformed": 1},
            last_seq=10, last_update=123.0)
        self.assertEqual(payload["rejected"], {"malformed": 1})

    def test_stream_modes(self):
        for mode in ("fixture", "simulated", "live", "off"):
            contracts.stream_status_payload(running=True, mode=mode,
                                            source_state="DISCONNECTED")
        with self.assertRaises(ContractError):
            contracts.stream_status_payload(running=True, mode="quantum",
                                            source_state="DISCONNECTED")

    def test_experiment_unknowns(self):
        payload = contracts.experiment_payload(
            session_id="NO_ACTIVE_SESSION", software={"a": "b"},
            hardware={"esp32": "ESP32-D0WD-V3 rev 3.1"},
            firmware={"identity": "UNKNOWN"},
            geometry={"room_width_m": None, "status": "UNCALIBRATED"},
            raw_ref=None, validation="NOT_RUN")
        self.assertIsNone(payload["raw_ref"])
        self.assertIsNone(payload["geometry"]["room_width_m"])

    def test_calibration(self):
        payload = contracts.calibration_payload(
            status="UNCALIBRATED", room_width_m=None, room_length_m=None,
            movement_threshold=None, calibrated_at=None)
        self.assertEqual(payload["status"], "UNCALIBRATED")

    def test_localization_1d_only(self):
        payload = contracts.localization_payload(
            frame="link-1d", position=0.4, position_m=2.0, raw=0.45,
            uncertainty=0.1, room_width_m=5.0, sync="NONE", nodes=[])
        self.assertEqual(payload["frame"], "link-1d")
        with self.assertRaises(ContractError):  # 2-D not defined
            contracts.localization_payload(
                frame="room-2d", position=None, position_m=None, raw=None,
                uncertainty=None, room_width_m=None, sync="NONE", nodes=[])
        with self.assertRaises(ContractError):  # negative uncertainty
            contracts.localization_payload(
                frame="link-1d", position=None, position_m=None, raw=None,
                uncertainty=-1.0, room_width_m=None, sync="NONE", nodes=[])

    def test_xai_unavailable_by_default(self):
        payload = contracts.xai_payload(available=False)
        self.assertEqual(payload, {"available": False,
                                   "status": "NOT AVAILABLE"})
        with self.assertRaises(ContractError):  # scores without caveats
            contracts.xai_payload(available=True, method="rf_impurity",
                                  caveats="", scores={"a": 0.1})


class EnvelopeTests(unittest.TestCase):
    """Stream-carried events must embed provenance; malformed rejected."""

    def _event_text(self, payload):
        return json.dumps(contracts.wrap_event("sensing.snapshot", payload,
                                               source="test"))

    def test_valid_snapshot_envelope(self):
        payload = _snapshot()
        payload["source_state"] = "OFFLINE_FIXTURE"
        obj = contracts.validate_envelope(self._event_text(payload))
        self.assertEqual(obj["type"], "sensing.snapshot")

    def test_missing_source_state_rejected(self):
        with self.assertRaises(ContractError):
            contracts.validate_envelope(self._event_text(_snapshot()))

    def test_bad_source_state_rejected(self):
        payload = _snapshot()
        payload["source_state"] = "LIVE"
        with self.assertRaises(ContractError):
            contracts.validate_envelope(self._event_text(payload))

    def test_malformed_inputs_rejected(self):
        for bad in ("not json", "[1,2]", '{"schema": 99}', '{"type": "nope"}',
                    json.dumps({"schema": 1, "type": "system.log"})):
            with self.assertRaises(ContractError):
                contracts.validate_envelope(bad)

    def test_unknown_event_type_rejected(self):
        with self.assertRaises(ContractError):
            contracts.wrap_event("mind.meld", {})


class ProviderTests(unittest.TestCase):
    """Disconnect/fixture/simulated/live-gate behavior."""

    def test_disconnected_emits_nothing(self):
        provider = sources.DisconnectedProvider()
        self.assertEqual(list(provider.frames()), [])
        self.assertIsNone(provider.latest_snapshot())
        self.assertEqual(provider.source_state, "DISCONNECTED")

    def test_fixture_replays_valid_envelopes(self):
        provider = sources.FixtureProvider(
            sources.FIXTURE_DIR / "offline_demo.jsonl")
        self.assertGreater(len(provider), 0)
        gen = provider.frames(loop=False)
        first = next(gen)
        self.assertEqual(first["type"], "sensing.snapshot")
        self.assertEqual(first["payload"]["source_state"], "OFFLINE_FIXTURE")
        # Presence/activity are UNKNOWN (unvalidated) in the fixture.
        self.assertEqual(first["payload"]["presence"], "UNKNOWN")
        self.assertEqual(first["payload"]["movement"], "UNKNOWN")
        # Amplitudes are a non-empty numeric visualization vector.
        amps = first["payload"]["amplitudes"]
        self.assertTrue(amps and all(isinstance(v, float) for v in amps))

    def test_fixture_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            sources.FixtureProvider(sources.FIXTURE_DIR / "nope.jsonl")

    def test_simulated_labels_simulated(self):
        provider = sources.SimulatedProvider(seed=7)
        event = next(provider.frames())
        self.assertEqual(event["payload"]["source_state"], "SIMULATED")
        self.assertFalse(event["payload"]["validated"])

    def test_live_binds_unverified(self):
        # RFVISION-009: the live path binds to the validated receiver.
        # Construction never touches hardware; sessions start UNVERIFIED.
        provider = sources.LiveProvider(
            line_source=sources.FakeLineSource([]))
        self.assertEqual(provider.mode, "live")
        self.assertEqual(provider.source_state, "LIVE_UNVERIFIED")
        bound = sources.make_provider(
            "live", line_source=sources.FakeLineSource([]))
        self.assertEqual(bound.mode, "live")
        with self.assertRaises(ContractError):
            sources.make_provider("quantum")


class WsCodecTests(unittest.TestCase):
    """RFC 6455 server codec: handshake vector + frame round-trip."""

    def test_accept_vector(self):
        # RFC 6455 §1.3 example vector.
        self.assertEqual(ws_codec.accept_key("dGhlIHNhbXBsZSBub25jZQ=="),
                         "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")

    def test_handshake_rejects_non_upgrade(self):
        with self.assertRaises(ws_codec.WsError):
            ws_codec.server_handshake("GET /x HTTP/1.1\r\nHost: h\r\n\r\n")

    def test_text_round_trip_over_socketpair(self):
        client, server = socket.socketpair()
        try:
            ws_codec.send_text(server, "hello")
            # Read raw server bytes on the client side and parse as a
            # server-to-client frame (unmasked, opcode text).
            hdr = client.recv(2)
            self.assertEqual(hdr[0], 0x81)
            body = client.recv(hdr[1] & 0x7F)
            self.assertEqual(body, b"hello")
        finally:
            client.close()
            server.close()

    def test_recv_masked_client_frame(self):
        client, server = socket.socketpair()
        try:
            payload = b"ping-1"
            mask = b"\x11\x22\x33\x44"
            masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            client.sendall(bytes([0x81, 0x80 | len(payload)]) + mask
                           + masked)
            opcode, out = ws_codec.recv_frame(server, timeout=5.0)
            self.assertEqual(opcode, ws_codec.OPCODE_TEXT)
            self.assertEqual(out, payload)
        finally:
            client.close()
            server.close()


class FrontendHygieneTests(unittest.TestCase):
    """Static guards: relative imports resolve, no CDN/floating deps."""

    STATIC = Path(__file__).resolve().parent.parent.parent / "web" / "static"

    def test_relative_imports_resolve(self):
        pattern = re.compile(r"""from\s+["'](\.[^"']+)["']""")
        checked = 0
        for path in sorted(self.STATIC.rglob("*.js")):
            if "vendor" in path.parts:
                continue
            for match in pattern.finditer(path.read_text(encoding="utf-8")):
                spec = match.group(1)
                if spec.startswith("three"):
                    continue  # importmap-provided (pinned local vendor)
                target = (path.parent / spec).resolve()
                self.assertTrue(target.is_file(),
                                f"{path.name} imports missing {spec}")
                checked += 1
        self.assertGreater(checked, 10)

    def test_no_cdn_or_remote_imports(self):
        for path in sorted(self.STATIC.rglob("*.js")):
            if "vendor" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("https://", text, f"{path.name} has remote URL")
            self.assertNotIn("http://", text, f"{path.name} has remote URL")
        html = (self.STATIC / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("https://", html, "index.html must not use CDNs")
        self.assertIn("/static/vendor/three.module.js", html)


if __name__ == "__main__":
    unittest.main()
