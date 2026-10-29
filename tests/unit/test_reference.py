"""Unit tests: explicit per-node reference-relative amplitude diagnostics."""

import unittest

import numpy as np

from sensing.reference import (
    ReferenceConfig,
    ReferenceState,
    ReferenceTracker,
)


def _tracker(**kwargs):
    defaults = dict(min_samples=4, min_valid_fraction=0.5,
                    stale_after_s=300.0, disturbance_z=3.0,
                    scale_floor=1e-6)
    defaults.update(kwargs)
    return ReferenceTracker(ReferenceConfig(**defaults))


def _capture(tracker, vector, count=5, now=0.0):
    return tracker.capture([np.asarray(vector, dtype=float)] * count,
                           now=now)


class TestReferenceDiagnostics(unittest.TestCase):
    def test_constant_reference_has_near_zero_disturbance(self):
        tracker = _tracker()
        _capture(tracker, np.full(4, 10.0))
        result = tracker.evaluate(np.full(4, 10.0), now=1.0)
        self.assertEqual(result.state, ReferenceState.VALID)
        self.assertAlmostEqual(result.gain_offset, 1.0)
        self.assertLess(result.disturbance_energy, 1e-20)
        self.assertEqual(result.disturbed_tone_fraction, 0.0)
        np.testing.assert_allclose(result.relative_amplitude, 1.0)

    def test_global_gain_shift_is_separate_from_structure(self):
        tracker = _tracker()
        _capture(tracker, np.full(8, 10.0))
        result = tracker.evaluate(np.full(8, 20.0), now=1.0)
        self.assertEqual(result.state, ReferenceState.VALID)
        self.assertAlmostEqual(result.gain_offset, 2.0)
        self.assertLess(result.disturbance_energy, 1e-20)
        self.assertEqual(result.disturbed_tone_fraction, 0.0)

    def test_subset_change_drives_structural_diagnostics(self):
        tracker = _tracker()
        _capture(tracker, np.full(8, 10.0))
        current = np.full(8, 10.0)
        current[:2] = 20.0
        result = tracker.evaluate(current, now=1.0)
        self.assertEqual(result.state, ReferenceState.VALID)
        self.assertAlmostEqual(result.gain_offset, 1.0)
        self.assertGreater(result.disturbance_energy, 0.0)
        self.assertGreater(result.disturbed_tone_fraction, 0.0)
        self.assertLessEqual(result.disturbed_tone_fraction, 1.0)

    def test_tone_dropout_is_explicit_and_coverage_aware(self):
        tracker = _tracker()
        _capture(tracker, np.full(8, 10.0))

        one_missing = np.full(8, 10.0)
        one_missing[3] = np.nan
        partial = tracker.evaluate(one_missing, now=1.0)
        self.assertEqual(partial.state, ReferenceState.VALID)
        self.assertEqual(partial.compared_tones, 7)
        self.assertAlmostEqual(partial.coverage, 7.0 / 8.0)
        self.assertTrue(np.isnan(partial.relative_amplitude[3]))

        many_missing = np.full(8, 10.0)
        many_missing[:5] = np.nan
        insufficient = tracker.evaluate(many_missing, now=1.0)
        self.assertEqual(insufficient.state, ReferenceState.INVALID)
        self.assertIsNone(insufficient.disturbance_energy)
        self.assertLess(insufficient.coverage, 0.5)

    def test_nan_inf_and_zero_are_rejected_without_exception(self):
        tracker = _tracker()
        _capture(tracker, np.full(4, 10.0))
        result = tracker.evaluate(
            np.array([np.nan, np.inf, 0.0, -1.0]), now=1.0)
        self.assertEqual(result.state, ReferenceState.INVALID)
        self.assertEqual(result.compared_tones, 0)
        self.assertIsNone(result.relative_amplitude)
        self.assertIsNone(result.gain_offset)

    def test_no_reference_is_absent(self):
        tracker = _tracker()
        result = tracker.evaluate(np.full(4, 10.0), now=100.0)
        self.assertEqual(result.state, ReferenceState.ABSENT)
        self.assertEqual(result.reference_sample_count, 0)
        self.assertIsNone(result.reference_age_s)

    def test_insufficient_reference_samples_are_immature(self):
        tracker = _tracker(min_samples=4)
        _capture(tracker, np.full(4, 10.0), count=2)
        result = tracker.evaluate(np.full(4, 10.0), now=1.0)
        self.assertEqual(result.state, ReferenceState.IMMATURE)
        self.assertEqual(result.reference_sample_count, 2)
        self.assertIsNone(result.disturbance_energy)

    def test_stale_reference_is_reported_but_not_neutralized(self):
        tracker = _tracker(min_samples=2, stale_after_s=10.0)
        _capture(tracker, np.full(4, 10.0), count=2, now=100.0)
        result = tracker.evaluate(np.full(4, 10.0), now=111.0)
        self.assertEqual(result.state, ReferenceState.STALE)
        self.assertAlmostEqual(result.reference_age_s, 11.0)
        self.assertIsNotNone(result.disturbance_energy)
        self.assertIn("exceeds", result.reason)

    def test_reset_removes_previous_reference(self):
        tracker = _tracker()
        _capture(tracker, np.full(4, 10.0))
        self.assertEqual(tracker.state(now=1.0), ReferenceState.VALID)
        tracker.reset()
        self.assertIsNone(tracker.profile)
        self.assertEqual(tracker.evaluate(np.full(4, 10.0), now=1.0).state,
                         ReferenceState.ABSENT)

    def test_identical_input_is_deterministic(self):
        current = np.array([10.0, 11.0, 9.0, 12.0])
        results = []
        for _ in range(2):
            tracker = _tracker()
            _capture(tracker, np.full(4, 10.0))
            results.append(tracker.evaluate(current, now=2.0))
        first, second = results
        self.assertEqual(first.state, second.state)
        self.assertEqual(first.gain_offset, second.gain_offset)
        self.assertEqual(first.disturbance_energy,
                         second.disturbance_energy)
        self.assertEqual(first.disturbed_tone_fraction,
                         second.disturbed_tone_fraction)
        np.testing.assert_array_equal(first.relative_amplitude,
                                      second.relative_amplitude)

    def test_incompatible_vector_shape_is_invalid_not_fatal(self):
        tracker = _tracker()
        _capture(tracker, np.full(8, 10.0))
        short = tracker.evaluate(np.full(7, 10.0), now=1.0)
        self.assertEqual(short.state, ReferenceState.INVALID)
        self.assertIn("8", short.reason)
        scalar = tracker.evaluate(10.0, now=1.0)
        self.assertEqual(scalar.state, ReferenceState.INVALID)

    def test_evaluation_never_modifies_the_reference(self):
        tracker = _tracker()
        _capture(tracker, np.full(4, 10.0))
        before = tracker.profile
        center_before = before.center.copy()
        counts_before = before.tone_counts.copy()

        tracker.evaluate(np.full(4, 50.0), now=1.0)
        tracker.evaluate(np.full(4, 10.0), now=2.0)

        self.assertIs(tracker.profile, before)
        np.testing.assert_array_equal(tracker.profile.center, center_before)
        np.testing.assert_array_equal(tracker.profile.tone_counts,
                                      counts_before)
        self.assertLess(
            tracker.evaluate(np.full(4, 10.0), now=3.0).disturbance_energy,
            1e-20)


if __name__ == "__main__":
    unittest.main()
