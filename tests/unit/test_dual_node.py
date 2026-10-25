"""Tests for concurrent two-node acquisition (no hardware).

DualNodeSession is exercised with FakeLineSource feeds; device resolution
is stubbed so the suite runs with no boards attached.
"""

from __future__ import annotations

import time
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


class _SteadyClockSource(FakeLineSource):
    """Fake source with deterministic host ingress spacing for sync tests."""

    STEP_NS = 10_000_000

    def iter_lines(self):
        base = time.monotonic_ns() - len(self._lines) * self.STEP_NS
        for idx, line in enumerate(super().iter_lines()):
            self.last_line_rx_ns = base + idx * self.STEP_NS
            yield line


class DualSessionTests(unittest.TestCase):
    def setUp(self):
        self._real_resolve = dual_mod.all_nodes_resolved
        dual_mod.all_nodes_resolved = lambda: {
            "esp32-a": "/dev/ttyFAKE0", "esp32-b": "/dev/ttyFAKE1"}

    def tearDown(self):
        dual_mod.all_nodes_resolved = self._real_resolve

    def _session(self, lines_a, lines_b, pace_s=0.0,
                 source_cls=FakeLineSource, **kwargs):
        feeds = {"esp32-a": lines_a, "esp32-b": lines_b}
        params = {"gate_window_s": 60.0, "frame_hz": 1000.0,
                  "settle_s": 0.0, "sync_min_n": 8}
        params.update(kwargs)
        return dual.DualNodeSession(
            line_source_factory=lambda nid: source_cls(
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
        base = _fixture_lines()
        first_seq = int(base[0].split(",")[1])
        out = []
        for i in range(n):
            cols = base[i % len(base)].rstrip("\n").split(",")
            cols[1] = str(first_seq + i)
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

    def test_sync_requires_fresh_data_and_recovers(self):
        session = self._session(self._steady_clock_lines(70),
                                self._steady_clock_lines(70),
                                source_cls=_SteadyClockSource,
                                sync_min_n=64)
        self._drain(session, limit=80)
        self.assertEqual(session.sync_state()["state"], "SYNCED")
        for node in session.session_stats()["per_node"].values():
            self.assertTrue(node["sync"]["ready"])
        old = time.time() - 10.0
        for stale_ids in (("esp32-a",), ("esp32-b",),
                          ("esp32-a", "esp32-b")):
            for nid, provider in session.providers.items():
                provider._last_valid_ts = (
                    old if nid in stale_ids else time.time())
            state = session.sync_state()
            self.assertEqual(state["state"], "UNSYNCED")
            for nid in stale_ids:
                self.assertFalse(state["nodes"][nid]["ready"])
            stats = session.session_stats()["per_node"]
            for nid in stale_ids:
                self.assertFalse(stats[nid]["sync"]["ready"])
        for provider in session.providers.values():
            provider._last_valid_ts = time.time()
        self.assertEqual(session.sync_state()["state"], "SYNCED")
        for node in session.session_stats()["per_node"].values():
            self.assertTrue(node["sync"]["ready"])

    def test_stale_node_is_unsynced_in_status_payload(self):
        session = self._session(self._steady_clock_lines(70),
                                self._steady_clock_lines(70),
                                source_cls=_SteadyClockSource,
                                sync_min_n=64)
        self._drain(session, limit=80)
        self.assertEqual(session.sync_state()["state"], "SYNCED")

        from web import server
        original = server.DUAL
        server.DUAL = session
        try:
            fresh = server.dual_status_payload()
            self.assertEqual(fresh["sync_state"], "SYNCED")
            self.assertTrue(all(n["sync_ready"] for n in fresh["nodes"]))

            session.providers["esp32-a"]._last_valid_ts = time.time() - 10.0
            self.assertEqual(session.sync_state()["state"], "UNSYNCED")
            stale = server.dual_status_payload()
            self.assertEqual(stale["sync_state"], "UNSYNCED")
            by_id = {n["node_id"]: n for n in stale["nodes"]}
            self.assertEqual(by_id["esp32-a"]["connection"], "DEGRADED")
            self.assertFalse(by_id["esp32-a"]["sync_ready"])
            self.assertTrue(by_id["esp32-b"]["sync_ready"])

            session.providers["esp32-a"]._last_valid_ts = time.time()
            recovered = server.dual_status_payload()
            self.assertEqual(recovered["sync_state"], "SYNCED")
            self.assertTrue(all(n["sync_ready"] for n in recovered["nodes"]))
        finally:
            server.DUAL = original

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


class DualStatusMappingTests(unittest.TestCase):
    def _payload(self, source_state="LIVE_VERIFIED", stale=False,
                 sync="SYNCED", valid=10):
        def node(nid):
            return {
                "node_id": nid, "board_mac": "b0:3f:d3:70:20:3c",
                "port": "/dev/ttyUSB0", "source_state": source_state,
                "stream": {"valid": valid, "stale": stale,
                           "rate_hz": 75.0, "valid_pct": 99.0,
                           "malformed": 0, "duplicates": 0,
                           "out_of_order": 0, "gaps": 0},
                "signal": {"rssi_last": -50.0, "channel": 6,
                           "bssid": "aa:bb:cc:dd:ee:ff", "tones": 64},
                "timing": {"host_pipeline_us_mean": 1.0},
                "sync": {"ready": sync == "SYNCED", "offset_ns": 1.0,
                         "jitter_ns": 1.0, "observations": 64},
            }
        info = {"nodes": ["esp32-a", "esp32-b"], "elapsed_s": 1.0,
                "per_node": {"esp32-a": node("esp32-a"),
                             "esp32-b": node("esp32-b")},
                "sync": {"state": sync}}

        class FakeDual:
            def session_stats(self):
                return info

        from web import server
        original = server.DUAL
        server.DUAL = FakeDual()
        try:
            return server.dual_status_payload()
        finally:
            server.DUAL = original

    def test_disconnected_wins_over_stale(self):
        payload = self._payload(source_state="DISCONNECTED", stale=True,
                                sync="UNSYNCED", valid=0)
        node = payload["nodes"][0]
        self.assertEqual(node["connection"], "DISCONNECTED")
        self.assertEqual(node["source_state"], "DISCONNECTED")

    def test_stale_verified_is_degraded(self):
        payload = self._payload(stale=True, sync="SYNCED")
        node = payload["nodes"][0]
        self.assertEqual(node["connection"], "DEGRADED")
        self.assertEqual(node["source_state"], "LIVE_VERIFIED")

    def test_fresh_verified_maps_to_synced_or_live(self):
        self.assertEqual(self._payload(sync="SYNCED")["nodes"][0]["connection"],
                         "SYNCED")
        self.assertEqual(self._payload(sync="SYNCING")["nodes"][0]["connection"],
                         "LIVE")

    def test_fresh_unverified_maps_to_syncing(self):
        payload = self._payload(source_state="LIVE_UNVERIFIED",
                                sync="UNSYNCED")
        self.assertEqual(payload["nodes"][0]["connection"], "SYNCING")


if __name__ == "__main__":
    unittest.main()
