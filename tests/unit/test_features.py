"""Unit tests: feature extraction contract (180-d vector)."""

import time
import unittest

import numpy as np

from csi.parser.csi_parser import parse_line
from dsp.features.feature_extraction import (
    FeatureConfig,
    FeatureExtractor,
)
from dsp.preprocessing.preprocessing import (
    PreprocessConfig,
    Preprocessor,
)
from tests.synthetic.synth import make_json_line


class TestFeatures(unittest.TestCase):
    def _stream(self, n=80, seed=0):
        pre = Preprocessor(PreprocessConfig(smoothing="none",
                                            lowpass_enabled=False))
        ext = FeatureExtractor(FeatureConfig(), pre.cfg)
        vec = None
        for i in range(n):
            s = parse_line(
                make_json_line(seed=seed + i).split("#CSI ", 1)[1],
                1700000000.0 + i * (1.0 / 60.0))
            amp = pre.process(s)
            self.assertIsNotNone(amp)
            vec = ext.update(amp, s.rssi, s.ts_local) or vec
        return ext, vec

    def test_vector_contract(self):
        ext, vec = self._stream()
        self.assertIsNotNone(vec)
        self.assertEqual(len(vec.values), len(vec.names))
        self.assertEqual(len(vec.values), 180)
        self.assertEqual(vec.window_samples, 64)
        self.assertTrue(np.isfinite(vec.values).all())

    def test_feature_names_stable(self):
        ext = FeatureExtractor(FeatureConfig(), None)
        names = ext.feature_names()
        self.assertEqual(len(names), 180)
        self.assertIn("move_rel_activity", names)
        self.assertEqual(names, ext.feature_names())

    def test_window_filling_returns_none(self):
        pre = Preprocessor(PreprocessConfig(smoothing="none",
                                            lowpass_enabled=False))
        ext = FeatureExtractor(FeatureConfig(window_size=64), pre.cfg)
        s = parse_line(make_json_line().split("#CSI ", 1)[1], time.time())
        amp = pre.process(s)
        self.assertIsNone(ext.update(amp, s.rssi, s.ts_local))


if __name__ == "__main__":
    unittest.main()
