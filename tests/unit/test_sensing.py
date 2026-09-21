"""Unit tests: sensing modules (presence, motion, activity, state)."""

import unittest

import numpy as np

from sensing.activity.activity import MOVING_THRESHOLD, label_activity
from sensing.motion.motion import MovementDetector
from sensing.presence.presence import PresenceSmoother, decide_presence
from sensing.state.state import SystemState


class TestPresence(unittest.TestCase):
    def test_decide(self):
        self.assertEqual(decide_presence(0.9), "PERSON")
        self.assertEqual(decide_presence(0.1), "EMPTY")
        self.assertEqual(decide_presence(0.5), "PERSON")  # threshold inclusive

    def test_smoother_math(self):
        sm = PresenceSmoother(alpha=0.5, threshold=0.5)
        p, label = sm.update(1.0)
        self.assertEqual((p, label), (1.0, "PERSON"))
        p, label = sm.update(0.0)  # 0.5*0 + 0.5*1 = 0.5 -> PERSON
        self.assertAlmostEqual(p, 0.5)
        self.assertEqual(label, "PERSON")
        p, label = sm.update(0.0)  # 0.25 -> EMPTY
        self.assertAlmostEqual(p, 0.25)
        self.assertEqual(label, "EMPTY")

    def test_smoother_clamps_and_resets(self):
        sm = PresenceSmoother()
        sm.update(99.0)
        self.assertEqual(sm.smoothed, 1.0)
        sm.reset()
        self.assertIsNone(sm.smoothed)

    def test_bad_alpha(self):
        with self.assertRaises(ValueError):
            PresenceSmoother(alpha=0.0)


class TestMotionActivity(unittest.TestCase):
    def test_label(self):
        self.assertEqual(label_activity(0.9), "MOVING")
        self.assertEqual(label_activity(0.1), "STATIC")
        self.assertEqual(label_activity(MOVING_THRESHOLD), "MOVING")

    def test_detector_smoke(self):
        det = MovementDetector({})
        names = ["move_rel_activity"]
        p1 = det.update(np.array([10.0]), names)  # high activity
        p2 = det.update(np.array([0.0]), names)   # quiet
        self.assertGreaterEqual(p1, 0.0)
        self.assertLessEqual(p2, 1.0)

    def test_detector_missing_feature(self):
        det = MovementDetector({})
        p = det.update(np.array([0.0]), ["nope"])
        self.assertGreaterEqual(p, 0.0)

    def test_state_defaults(self):
        s = SystemState()
        self.assertEqual(s.connection, "OFFLINE")
        self.assertEqual(s.presence_label, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
