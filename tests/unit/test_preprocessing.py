"""Unit tests: preprocessing (accept/reject logic, bug regressions)."""

import copy
import time
import unittest

import numpy as np

from csi.parser.csi_parser import parse_line
from dsp.preprocessing.preprocessing import (
    PreprocessConfig,
    Preprocessor,
    clean_phase,
    hampel_filter,
)
from tests.synthetic.synth import make_json_line


def _sample(seed=0, **kw):
    obj = make_json_line(seed=seed, **kw)
    return parse_line(obj.split("#CSI ", 1)[1], time.time())


def _cfg(**kw):
    base = {"smoothing": "none", "lowpass_enabled": False}
    base.update(kw)
    return PreprocessConfig(**base)


class TestPreprocessor(unittest.TestCase):
    def test_accepts_synthetic_128B(self):
        p = Preprocessor(_cfg())
        out = p.process(_sample(seed=1))
        self.assertIsNotNone(out)
        self.assertEqual(len(out), 54)
        # Regression: accepted must increment exactly once per sample.
        self.assertEqual(p.stats.accepted, 1)
        self.assertEqual(p.stats.total_seen, 1)

    def test_first_word_trim_keeps_packet(self):
        import json
        d = json.loads(make_json_line(seed=1).split("#CSI ", 1)[1])
        d["first_word_invalid"] = 1
        d["csi"] = list(range(-64, 68))[:132]  # even, >= valid set
        d["csi"] = [int(v) for v in d["csi"]]
        d["csi_len"] = len(d["csi"])
        s = parse_line(json.dumps(d), time.time())
        p = Preprocessor(_cfg())
        out = p.process(s)
        self.assertIsNotNone(out)
        self.assertEqual(p.stats.first_word_invalid, 1)

    def test_rx_state_reject(self):
        import json
        d = json.loads(make_json_line().split("#CSI ", 1)[1])
        d["rx_state"] = 7
        s = parse_line(json.dumps(d), time.time())
        self.assertIsNone(Preprocessor(_cfg()).process(s))

    def test_cwb_reject_and_telemetry(self):
        import json
        d = json.loads(make_json_line().split("#CSI ", 1)[1])
        d["cwb"] = 1
        s = parse_line(json.dumps(d), time.time())
        p = Preprocessor(_cfg())
        self.assertIsNone(p.process(s))
        self.assertEqual(p.stats.bandwidth_mismatch, 1)

    def test_legacy_config_alias(self):
        cfg = PreprocessConfig.from_config(
            {"csi": {"drop_first_word_invalid": False}, "sample_rate": 60})
        self.assertFalse(cfg.trim_first_word_invalid)
        cfg2 = PreprocessConfig.from_config(
            {"csi": {"trim_first_word_invalid": False}, "sample_rate": 60})
        self.assertFalse(cfg2.trim_first_word_invalid)
        cfg3 = PreprocessConfig.from_config({})
        self.assertTrue(cfg3.trim_first_word_invalid)

    def test_gap_reset(self):
        p = Preprocessor(_cfg(max_gap_seconds=0.5))
        s1 = _sample(seed=1)
        p.process(s1)
        s2 = _sample(seed=2)
        s2.ts_local = s1.ts_local + 10.0
        p.process(s2)
        self.assertEqual(p.stats.gap_resets, 1)

    def test_hampel_spike(self):
        # Column with spread (MAD > 0) plus one spike: spike is replaced by
        # the window median. (A constant column has MAD == 0 and is left
        # untouched by design -- see hampel_filter docstring.)
        window = np.array([[1.0, 1.0], [2.0, 1.0], [1.0, 1.0], [2.0, 1.0],
                           [100.0, 1.0], [1.0, 1.0], [2.0, 1.0], [1.0, 1.0],
                           [2.0, 1.0]])
        out = hampel_filter(window, threshold=3.5, axis=0)
        self.assertAlmostEqual(out[4, 0], 2.0)  # median of the column
        self.assertAlmostEqual(out[0, 0], 1.0)  # inliers untouched

    def test_clean_phase_shape(self):
        m = np.random.default_rng(0).uniform(-np.pi, np.pi, size=(5, 8))
        out = clean_phase(m)
        self.assertEqual(out.shape, (5, 8))
        self.assertTrue(np.isfinite(out).all())


if __name__ == "__main__":
    unittest.main()
