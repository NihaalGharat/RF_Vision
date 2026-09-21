"""Live-provider tests (RFVISION-009). Stdlib only + fixtures/mocks.

Covers: live binding, session gate, state transitions, stale detection,
malformed handling (counted, never silent), serial disconnect,
latest-frame buffering, lossless recording, and envelope schema.
No hardware: all sessions run on FakeLineSource, mostly replaying the
genuine C1 fixture (tests/fixtures/live_csi/csi_sample_50.txt).
"""

from __future__ import annotations

import hashlib
import json
import time
import unittest
from pathlib import Path

from web import contracts
from web import source as sources
from web.live_serial import FakeLineSource

FIXTURE = (Path(__file__).resolve().parent.parent
           / "fixtures" / "live_csi" / "csi_sample_50.txt")
EXPECTED_BSSID = "8c:53:c3:5b:e1:59"


def _fixture_lines():
    return FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)


def _provider(lines, **kwargs):
    params = {"line_source": FakeLineSource(lines),
              "gate_window_s": 60.0, "frame_hz": 1000.0, "settle_s": 0.0}
    params.update(kwargs)
    return sources.LiveProvider(**params)


class LiveBindingTests(unittest.TestCase):
    def test_constructs_unverified_without_hardware(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource([]))
        self.assertEqual(provider.mode, "live")
        self.assertEqual(provider.source_state, "LIVE_UNVERIFIED")
        self.assertIsNone(provider.latest_snapshot())

    def test_make_provider_live(self):
        provider = sources.make_provider(
            "live", line_source=FakeLineSource([]))
        self.assertEqual(provider.mode, "live")


class IngestAccountingTests(unittest.TestCase):
    def test_counts_valid_malformed_non_csi_exactly(self):
        good = _fixture_lines()
        bad = ["CSI_DATA,1,2,3\n",  # wrong column count
               "CSI_DATA," + ",".join(["x"] * 24) + "\n"]  # non-integers
        other = ["ready\n", "some boot text\n"]  # non-CSI (blanks ignored)
        provider = _provider(good + bad + other + ["\n"])
        events = list(provider.frames())
        stats = provider.live_stats()
        self.assertEqual(stats["stream"]["valid"], 50)
        self.assertEqual(stats["stream"]["malformed"], len(bad))
        self.assertEqual(stats["stream"]["non_csi_lines"], 2)
        self.assertEqual(stats["parser"]["parsed"], 50)
        self.assertGreaterEqual(
            stats["parser"]["rejected"].get("malformed", 0), len(bad))
        self.assertTrue(events)  # valid frames still flow past garbage

    def test_malformed_surfaced_never_silent(self):
        provider = _provider(["CSI_DATA,1,2,3\n"])
        list(provider.frames())
        stats = provider.live_stats()
        self.assertEqual(stats["stream"]["malformed"], 1)
        self.assertTrue(stats["parser"]["recent_malformed"])

    def test_sequence_gaps_counted(self):
        lines = _fixture_lines()
        provider = _provider(lines[::2])  # drop every other line → gaps
        list(provider.frames())
        stats = provider.live_stats()
        self.assertEqual(stats["stream"]["valid"], 25)
        self.assertGreater(stats["stream"]["gaps"], 0)
        self.assertTrue(stats["stream"]["missing"])


class GateTests(unittest.TestCase):
    def test_gate_promotes_paced_genuine_session(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource(_fixture_lines(), pace_s=0.02),
            gate_window_s=0.5, frame_hz=50.0, settle_s=0.0)
        events = list(provider.frames())
        self.assertTrue(events)
        self.assertEqual(provider.source_state, "LIVE_VERIFIED")
        stats = provider.live_stats()
        self.assertTrue(stats["gate"]["passed"])
        self.assertEqual(stats["gate"]["reasons"],
                         ["all session-gate checks passed"])
        self.assertEqual(stats["signal"]["channels_seen"], [1])
        self.assertEqual(stats["signal"]["bssids_seen"], [EXPECTED_BSSID])
        self.assertIsNotNone(stats["stream"]["rate_hz"])
        self.assertGreaterEqual(stats["stream"]["valid_pct"], 99.0)

    def test_gate_fails_wrong_bssid(self):
        lines = [ln.replace(EXPECTED_BSSID, "00:11:22:33:44:55")
                 for ln in _fixture_lines()]
        provider = sources.LiveProvider(
            line_source=FakeLineSource(lines, pace_s=0.02),
            gate_window_s=0.5, frame_hz=50.0, settle_s=0.0)
        list(provider.frames())
        self.assertEqual(provider.source_state, "LIVE_UNVERIFIED")
        stats = provider.live_stats()
        self.assertFalse(stats["gate"]["passed"])
        self.assertTrue(any("BSSID" in r for r in stats["gate"]["reasons"]))

    def test_gate_fails_wrong_channel(self):
        provider = _provider(_fixture_lines(), expected_channel=6,
                             gate_window_s=0.0)
        list(provider.frames())
        stats = provider.live_stats()
        self.assertFalse(stats["gate"]["passed"])

    def test_duplication_storm_blocks_gate(self):
        line = _fixture_lines()[0]
        provider = _provider([line] * 60, gate_window_s=0.0)
        list(provider.frames())
        stats = provider.live_stats()
        self.assertTrue(stats["duplication"]["storm"])
        self.assertFalse(stats["gate"]["passed"])
        self.assertTrue(any("storm" in r
                            for r in stats["gate"]["reasons"]))
        self.assertEqual(provider.source_state, "LIVE_UNVERIFIED")

    def test_no_data_never_promotes(self):
        provider = _provider([], gate_window_s=0.0)
        self.assertEqual(list(provider.frames()), [])
        self.assertFalse(provider.live_stats()["gate"]["passed"])

    def test_settle_then_promote_despite_open_transient(self):
        # Open-transient storm first, then clean paced stream: the
        # validation window starts on clean air, promotes, and the
        # pre-gate storm stays visible (never hidden). The genuine run
        # outlasts the trailing throughput window so the burst ages out.
        transient = [_fixture_lines()[0]] * 35
        genuine = _fixture_lines() * 5  # 250 lines @ ~67 Hz ≈ 3.7 s
        # Realistic burst profile: instant replay burst, then paced stream.
        pace = lambda i: 0.0 if i < len(transient) else 0.015
        provider = sources.LiveProvider(
            line_source=FakeLineSource(transient + genuine, pace_s=pace),
            gate_window_s=0.3, frame_hz=50.0, settle_s=0.2)
        events = list(provider.frames())
        self.assertTrue(events)
        self.assertEqual(provider.source_state, "LIVE_VERIFIED")
        stats = provider.live_stats()
        self.assertTrue(stats["gate"]["passed"])
        self.assertTrue(stats["gate"]["settled"])
        self.assertTrue(stats["gate"]["pre_gate_storm"])
        self.assertTrue(stats["duplication"]["storm"])

    def test_storm_inside_window_demotes_session(self):
        # Genuine start passes the gate, then a NEW storm epoch trips:
        # the session must demote back to UNVERIFIED with the cause shown.
        genuine = _fixture_lines()[:10]
        storm = [_fixture_lines()[0]] * 40
        provider = sources.LiveProvider(
            line_source=FakeLineSource(genuine + storm, pace_s=0.02),
            gate_window_s=0.0, frame_hz=50.0, settle_s=0.0)
        list(provider.frames())
        stats = provider.live_stats()
        self.assertTrue(stats["gate"]["settled"])
        self.assertFalse(stats["gate"]["passed"])
        self.assertTrue(any("demoted" in r
                            for r in stats["gate"]["reasons"]))
        self.assertEqual(provider.source_state, "LIVE_UNVERIFIED")


class StateTransitionTests(unittest.TestCase):
    def test_unverified_then_verified_across_frames(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource(_fixture_lines(), pace_s=0.02),
            gate_window_s=0.5, frame_hz=50.0, settle_s=0.0)
        events = list(provider.frames())
        states = [ev["payload"]["source_state"] for ev in events]
        self.assertTrue(states)
        self.assertEqual(states[0], "LIVE_UNVERIFIED")
        self.assertEqual(states[-1], "LIVE_VERIFIED")
        self.assertIn("LIVE_VERIFIED", states)

    def test_transport_death_before_data_is_disconnected(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource(["ready\n"], raise_after=0,
                                       raise_message="port gone"),
            gate_window_s=60.0)
        self.assertEqual(list(provider.frames()), [])
        stats = provider.live_stats()
        self.assertEqual(stats["transport"]["error"], "port gone")
        self.assertEqual(provider.source_state, "DISCONNECTED")

    def test_stale_flag_after_clean_end(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource(_fixture_lines()[:5]),
            gate_window_s=60.0, frame_hz=1000.0, stale_after_s=0.2)
        list(provider.frames())
        time.sleep(0.35)
        stats = provider.live_stats()
        self.assertTrue(stats["stream"]["stale"])
        self.assertGreater(stats["stream"]["last_update_age_s"], 0.2)


class BufferingTests(unittest.TestCase):
    def test_latest_frame_decimation(self):
        provider = sources.LiveProvider(
            line_source=FakeLineSource(_fixture_lines(), pace_s=0.02),
            gate_window_s=60.0, frame_hz=5.0)
        events = list(provider.frames())
        stats = provider.live_stats()
        seqs = [ev["seq"] for ev in events]
        # Decimated: fewer envelopes than records, newer samples skip ahead.
        self.assertLess(len(events), stats["stream"]["valid"])
        self.assertEqual(seqs, sorted(seqs))
        self.assertTrue(any(b - a > 1 for a, b in zip(seqs, seqs[1:])))
        self.assertLessEqual(seqs[-1], stats["stream"]["last_seq"])

    def test_rolling_buffers_bounded(self):
        provider = _provider(_fixture_lines() * 4, frame_hz=1000.0)
        list(provider.frames())
        self.assertLessEqual(len(provider._arrivals),
                             provider.RATE_WINDOW_N)
        self.assertLessEqual(len(provider._rssi), provider.RSSI_WINDOW_N)


class RecordingTests(unittest.TestCase):
    def test_recording_is_lossless(self):
        import tempfile
        lines = (_fixture_lines()[:10] + ["CSI_DATA,1,2,3\n", "ready\n"]
                 + _fixture_lines()[10:15])
        provider = _provider(lines)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "diag.bin"
            provider.start_recording(target, max_seconds=30)
            list(provider.frames())
            info = provider.stop_recording()
            self.assertEqual(info["path"], str(target))
            self.assertEqual(info["bytes"], target.stat().st_size)
            self.assertEqual(info["sha256"],
                             hashlib.sha256(target.read_bytes()).hexdigest())
            recorded = target.read_text(encoding="utf-8").splitlines(
                keepends=True)
            self.assertEqual(len(recorded), len(lines))
            for want, got in zip(lines, recorded):
                self.assertEqual(got, want if want.endswith("\n")
                                 else want + "\n")


class SchemaTests(unittest.TestCase):
    def test_every_frame_validates_and_claims_nothing(self):
        provider = _provider(_fixture_lines())
        events = list(provider.frames())
        self.assertTrue(events)
        for event in events:
            obj = contracts.validate_envelope(json.dumps(event))
            payload = obj["payload"]
            self.assertIn(payload["source_state"], contracts.SOURCE_STATES)
            self.assertEqual(payload["presence"], "UNKNOWN")
            self.assertEqual(payload["movement"], "UNKNOWN")
            self.assertIsNone(payload["position"])
            self.assertFalse(payload["validated"])
            self.assertIsNone(payload["phases"])  # phase gated
            self.assertTrue(len(payload["amplitudes"]) >= 60)


class ServerWiringTests(unittest.TestCase):
    def test_console_accepts_live_source(self):
        from web import server as srv
        state = srv.ConsoleState()
        status = state.set_source(
            "live", line_source=FakeLineSource(_fixture_lines()))
        self.assertEqual(status["mode"], "live")
        self.assertEqual(state.provider.mode, "live")
        self.assertEqual(state.effective_state(), "LIVE_UNVERIFIED")

    def test_console_closes_serial_on_switch(self):
        from web import server as srv
        state = srv.ConsoleState()
        fake = FakeLineSource(_fixture_lines())
        state.set_source("live", line_source=fake)
        provider = state.provider
        provider._begin_session()  # session holds the port open
        self.assertTrue(fake.is_open)
        state.set_source("off")  # must release without error
        self.assertTrue(fake.closed)
        self.assertEqual(state.provider.mode, "off")


if __name__ == "__main__":
    unittest.main()
