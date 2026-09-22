"""Unit tests: localization (geometry, 1-D tracker, clock sync)."""

import unittest

from localization.geometry.geometry import (
    clamp01,
    link_length_m,
    metres_to_position,
    position_to_metres,
)
from localization.positioning.position_1d import Position1D
from localization.synchronization.sync import ClockOffsetEstimator
from localization.tracking.position_filter import PositionFilter


class TestGeometry(unittest.TestCase):
    def test_mapping(self):
        self.assertAlmostEqual(position_to_metres(0.0, 5.0), 0.0)
        self.assertAlmostEqual(position_to_metres(1.0, 5.0), 5.0)
        self.assertAlmostEqual(position_to_metres(0.5, 4.0), 2.0)
        self.assertAlmostEqual(metres_to_position(2.5, 5.0), 0.5)
        self.assertEqual(clamp01(9.9), 1.0)
        self.assertEqual(clamp01(-2.0), 0.0)
        with self.assertRaises(ValueError):
            link_length_m(0.0)


class TestPosition1D(unittest.TestCase):
    def test_update(self):
        tracker = Position1D({"smoothing_factor": 0.35, "room_width": 5.0})
        out = tracker.update(0.4, 1000.0)
        self.assertIsNotNone(out)
        self.assertAlmostEqual(out["position"], 0.4)
        self.assertAlmostEqual(out["position_m"], 2.0)
        self.assertIsNone(tracker.update(None, 1001.0))
        tracker.reset()

    def test_filter_smooths(self):
        f = PositionFilter()
        a = f.filter(0.0, 0.0)
        b = f.filter(1.0, 0.1)
        self.assertGreater(b, a)
        self.assertLess(b, 1.0)


class TestSync(unittest.TestCase):
    def test_offset_median(self):
        est = ClockOffsetEstimator(window=8)
        self.assertIsNone(est.offset)
        for i in range(5):
            est.observe(device_ts=1000.0 + i, host_ts=5000.0 + i)
        self.assertAlmostEqual(est.offset, 4000.0)
        self.assertAlmostEqual(est.device_to_host(1010.0), 5010.0)
        est.reset()
        self.assertIsNone(est.offset)

    def test_outlier_rejected_by_median(self):
        est = ClockOffsetEstimator(window=5)
        for _ in range(4):
            est.observe(0.0, 100.0)
        est.observe(0.0, 99999.0)
        self.assertAlmostEqual(est.offset, 100.0)

    def test_jitter_none_then_mad(self):
        est = ClockOffsetEstimator(window=8)
        self.assertIsNone(est.jitter)
        est.observe(0.0, 100.0)
        self.assertIsNone(est.jitter)
        for v in (100.0, 102.0, 98.0):
            est.observe(0.0, v)
        # window = [100,100,102,98] → median 100, MAD = median(0,0,2,2) = 1
        self.assertAlmostEqual(est.jitter, 1.0)

    def test_jitter_robust_to_outlier(self):
        est = ClockOffsetEstimator(window=5)
        for _ in range(4):
            est.observe(0.0, 100.0)
        est.observe(0.0, 99999.0)
        self.assertAlmostEqual(est.jitter, 0.0)

    def test_drift_zero_for_locked_clocks(self):
        est = ClockOffsetEstimator(window=8)
        self.assertIsNone(est.drift_per_sample)
        for i in range(6):
            est.observe(device_ts=1000.0 + i, host_ts=5000.0 + i)
        self.assertAlmostEqual(est.drift_per_sample, 0.0)

    def test_drift_detects_rate_mismatch(self):
        est = ClockOffsetEstimator(window=10)
        for i in range(8):  # host gains 0.5 units per device unit
            est.observe(device_ts=float(i), host_ts=100.0 + 1.5 * i)
        self.assertAlmostEqual(est.drift_per_sample, 0.5)

    def test_stable_predicate(self):
        est = ClockOffsetEstimator(window=8)
        self.assertFalse(est.stable(max_jitter=5.0, min_n=4))
        for v in (100.0, 102.0, 100.0):
            est.observe(0.0, v)
        self.assertFalse(est.stable(max_jitter=5.0, min_n=4))
        est.observe(0.0, 98.0)  # window MAD = 1.0
        self.assertTrue(est.stable(max_jitter=5.0, min_n=4))
        self.assertFalse(est.stable(max_jitter=0.5, min_n=4))
        est.reset()
        self.assertEqual(est.n, 0)
        self.assertFalse(est.stable(max_jitter=5.0, min_n=4))


if __name__ == "__main__":
    unittest.main()
