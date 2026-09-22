"""Tests for concurrent two-node acquisition (no hardware).

DualNodeSession is exercised with FakeLineSource feeds; device resolution
is stubbed so the suite runs with no boards attached.
"""

from __future__ import annotations

import unittest
from pathlib import Path

import web.dual_node as dual_mod
from web import dual_node as dual
from web.live_serial import FakeLineSource

FIXTURE = (Path(__file__).resolve().parent.parent
           / "fixtures" / "live_csi" / "csi_sample_50.txt")


def _fixture_lines(n=50):
    return FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)[:n]


def _with_seq(line, seq):
    cols = line.rstrip("\n").split(",", 2)
    cols[1] = str(seq)
    return ",".join(cols) + "\n"


class DualSessionTests(unittest.TestCase):
    def setUp(self):
        self._real_resolve = dual_mod.all_nodes_resolved
        dual_mod.all_nodes_resolved = lambda: {
            "esp32-a": "/dev/ttyFAKE0", "esp32-b": "/dev/ttyFAKE1"}

    def tearDown(self):
        dual_mod.all_nodes_resolved = self._real_resolve

    def _session(self, lines_a, lines_b, pace_s=0.0, **kwargs):
        feeds = {"esp32-a": lines_a, "esp32-b": lines_b}
        params = {"gate_window_s": 60.0, "frame_hz": 1000.0,
                  "settle_s": 0.0, "sync_min_n": 8}
        params.update(kwargs)
        return dual.DualNodeSession(
            line_source_factory=lambda nid: FakeLineSource(
                feeds[nid], pace_s=pace_s),
            **params)

    def _drain(self, session, limit=200, settle_s=15.0):
        import time as _time
        session.start()
        try:
            deadline = _time.time() + settle_s
            while (any(t.is_alive() for t in session._threads)
                   and _time.time() < deadline):
                _time.sleep(0.02)
            out = []
            while len(out) < limit:
                try:
                    out.append(session._queue.get_nowait())
                except Exception:
                    break
            return out
        finally:
            session.stop()

    def test_fan_in_tags_both_nodes(self):
        session = self._session(_fixture_lines(10), _fixture_lines(10))
        events = self._drain(session, limit=30)
        by_node = {}
        for nid, _event in events:
            by_node[nid] = by_node.get(nid, 0) + 1
        self.assertEqual(set(by_node), {"esp32-a", "esp32-b"})
        stats = session.session_stats()
        self.assertEqual(list(stats["per_node"]), ["esp32-a", "esp32-b"])
        for nid, node_stats in stats["per_node"].items():
            self.assertEqual(node_stats["node_id"], nid)
            self.assertGreater(node_stats["stream"]["valid"], 0)

    def test_per_node_accounting_is_independent(self):
        base = _fixture_lines(1)[0]
        bad_b = [_with_seq(base, s) for s in (1, 2, 2, 2, 5)]
        session = self._session(_fixture_lines(10), bad_b)
        self._drain(session, limit=30)
        stats = session.session_stats()["per_node"]
        self.assertEqual(stats["esp32-b"]["stream"]["duplicates"], 2)
        self.assertEqual(stats["esp32-a"]["stream"]["duplicates"], 0)
        self.assertEqual(stats["esp32-a"]["board_mac"],
                         "b0:3f:d3:70:20:3c")
        self.assertEqual(stats["esp32-b"]["board_mac"],
                         "04:b2:47:20:1a:dc")

    def _steady_clock_lines(self, n, step_us=10000):
        # Fixture payload with an exact device-clock grid: isolates the
        # session state machine from real-capture clock wander (which the
        # estimator unit tests already cover with exact values).
        out = []
        for i, line in enumerate(_fixture_lines(n)):
            cols = line.rstrip("\n").split(",")
            cols[18] = str(137000000 + i * step_us)
            out.append(",".join(cols) + "\n")
        return out

    def test_sync_progresses_to_synced_on_stable_feeds(self):
        # Paced at the synthetic device-clock cadence so both clocks
        # advance together (stable offset, honest physics).
        session = self._session(self._steady_clock_lines(30),
                                self._steady_clock_lines(30),
                                pace_s=0.01,
                                # State-machine test: generous jitter bound
                                # (this host's sleep() pacing itself jitters
                                # ~ms-scale; the bound VALUE is covered by
                                # estimator unit tests with exact clocks).
                                sync_max_jitter_ns=20_000_000)
        self.assertEqual(session.sync_state()["state"], "UNSYNCED")
        self._drain(session, limit=80)
        state = session.sync_state()
        self.assertEqual(state["state"], "SYNCED")
        for nid, node in state["nodes"].items():
            self.assertTrue(node["ready"])
            self.assertIsNotNone(node["offset_ns"])
            self.assertIsNotNone(node["jitter_ns"])
        self.assertIn("stably mapped to host time", state["criterion"])

    def test_sync_stays_unsynced_below_min_n(self):
        session = self._session(_fixture_lines(2), _fixture_lines(2),
                                sync_min_n=1000)
        self._drain(session, limit=10)
        self.assertEqual(session.sync_state()["state"], "UNSYNCED")

    def test_timing_block_is_honest(self):
        session = self._session(_fixture_lines(10), _fixture_lines(10))
        self._drain(session, limit=30)
        for node_stats in session.session_stats()["per_node"].values():
            timing = node_stats["timing"]
            self.assertIsNone(timing["esp_to_host_latency_us"])
            self.assertIn("NOT reported as latency",
                          timing["latency_note"])
            self.assertIsNotNone(timing["host_pipeline_us_mean"])
            self.assertGreaterEqual(timing["host_pipeline_us_max"], 0)

    def test_unknown_node_rejected(self):
        with self.assertRaises(ValueError):
            dual.DualNodeSession(node_ids=("esp32-a", "esp32-zzz"))

    def test_single_node_session_supported(self):
        session = dual.DualNodeSession(
            node_ids=("esp32-a",),
            line_source_factory=lambda nid: FakeLineSource(
                _fixture_lines(10)),
            gate_window_s=60.0, frame_hz=1000.0, settle_s=0.0,
            sync_min_n=8)
        events = self._drain(session, limit=15)
        self.assertTrue(events)
        self.assertEqual({n for n, _ in events}, {"esp32-a"})


if __name__ == "__main__":
    unittest.main()
