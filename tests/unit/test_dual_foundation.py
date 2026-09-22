"""Tests for the two-node sensing foundation (no hardware).

Covers: host ingress timestamps (ts_host_ns, monotonic, ingress-ordered),
sequence-quality accounting (gaps/duplicates/out-of-order), and node
identity resolution. All sessions run on FakeLineSource.
"""

from __future__ import annotations

import time
import unittest
from pathlib import Path

from csi.parser.esp_csv_adapter import EspCsvAdapter, parse_esp_csv_line
from csi.transport.nodes import NODE_A, NODE_B, all_nodes_resolved
from web import source as sources
from web.live_serial import FakeLineSource

FIXTURE = (Path(__file__).resolve().parent.parent
           / "fixtures" / "live_csi" / "csi_sample_50.txt")


def _fixture_lines():
    return FIXTURE.read_text(encoding="utf-8").splitlines(keepends=True)


def _with_seq(line, seq):
    cols = line.rstrip("\n").split(",", 2)
    cols[1] = str(seq)
    return ",".join(cols) + "\n"


def _provider(lines, **kwargs):
    params = {"line_source": FakeLineSource(lines),
              "gate_window_s": 60.0, "frame_hz": 1000.0, "settle_s": 0.0}
    params.update(kwargs)
    return sources.LiveProvider(**params)


class HostTimestampTests(unittest.TestCase):
    def test_adapter_stamps_monotonic_ns_by_default(self):
        line = _fixture_lines()[0]
        before = time.monotonic_ns()
        sample = parse_esp_csv_line(line)
        after = time.monotonic_ns()
        self.assertIsNotNone(sample.ts_host_ns)
        self.assertGreaterEqual(sample.ts_host_ns, before)
        self.assertLessEqual(sample.ts_host_ns, after)

    def test_adapter_honours_caller_ingress_stamp(self):
        line = _fixture_lines()[0]
        sample = parse_esp_csv_line(line, ts_host_ns=123456789)
        self.assertEqual(sample.ts_host_ns, 123456789)

    def test_adapter_handle_line_passes_stamp(self):
        adapter = EspCsvAdapter()
        sample = adapter.handle_line(_fixture_lines()[0], time.time(),
                                     ts_host_ns=424242)
        self.assertEqual(sample.ts_host_ns, 424242)

    def test_provider_samples_carry_ingress_ordered_stamps(self):
        provider = _provider(_fixture_lines()[:5])
        list(provider.frames())
        stamps = [s.ts_host_ns for s in
                  [provider._last_sample] if s is not None]
        self.assertTrue(stamps and stamps[0] is not None)
        # FakeLineSource stamps each line at yield: provider must propagate.
        src = provider._factory_source
        self.assertIsNotNone(src.last_line_rx_ns)

    def test_fake_source_exposes_last_line_rx_ns(self):
        src = FakeLineSource(_fixture_lines()[:2])
        self.assertIsNone(src.last_line_rx_ns)
        src.open()
        list(src.iter_lines())
        self.assertIsNotNone(src.last_line_rx_ns)

    def test_ts_local_preserved_alongside_ns_stamp(self):
        sample = parse_esp_csv_line(_fixture_lines()[0], 1700000000.0,
                                    ts_host_ns=99)
        self.assertEqual(sample.ts_local, 1700000000.0)
        self.assertEqual(sample.ts_host_ns, 99)


class SequenceQualityTests(unittest.TestCase):
    def test_gap_duplicate_out_of_order_counted(self):
        base = _fixture_lines()[0]
        lines = [
            _with_seq(base, 10),
            _with_seq(base, 11),
            _with_seq(base, 14),   # gap: 12, 13 missing
            _with_seq(base, 14),   # duplicate
            _with_seq(base, 12),   # out-of-order (late arrival)
            _with_seq(base, 15),
        ]
        provider = _provider(lines)
        list(provider.frames())
        stream = provider.live_stats()["stream"]
        self.assertEqual(stream["valid"], 6)
        self.assertEqual(stream["gaps"], 1)
        self.assertEqual(stream["missing"], [12, 13])
        self.assertEqual(stream["duplicates"], 1)
        self.assertEqual(stream["out_of_order"], 1)
        # _last_seq stays anchored to the newest sequence seen.
        self.assertEqual(stream["last_seq"], 15)

    def test_clean_stream_has_zero_quality_flags(self):
        lines = [_with_seq(_fixture_lines()[0], s) for s in range(1, 11)]
        provider = _provider(lines)
        list(provider.frames())
        stream = provider.live_stats()["stream"]
        self.assertEqual(stream["gaps"], 0)
        self.assertEqual(stream["duplicates"], 0)
        self.assertEqual(stream["out_of_order"], 0)

    def test_duplicate_does_not_move_last_seq(self):
        base = _fixture_lines()[0]
        lines = [_with_seq(base, 5), _with_seq(base, 5),
                 _with_seq(base, 5)]
        provider = _provider(lines)
        list(provider.frames())
        stream = provider.live_stats()["stream"]
        self.assertEqual(stream["duplicates"], 2)
        self.assertEqual(stream["last_seq"], 5)
        self.assertEqual(stream["gaps"], 0)


class NodeIdentityConfigTests(unittest.TestCase):
    def test_known_nodes_have_stable_paths_and_macs(self):
        self.assertEqual((NODE_A.by_path, NODE_A.board_mac),
                         ("usb-0:5.4", "b0:3f:d3:70:20:3c"))
        self.assertEqual((NODE_B.by_path, NODE_B.board_mac),
                         ("usb-0:1", "04:b2:47:20:1a:dc"))

    def test_all_nodes_resolved_reports_gaps(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception) as ctx:
                all_nodes_resolved(by_path_root=tmp)
            self.assertIn("esp32", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
