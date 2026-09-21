"""Integration: synthetic wire -> parse -> preprocess -> features."""

import time
import unittest

import numpy as np

from csi.parser.csi_parser import parse_line
from csi.parser.esp_csv_adapter import parse_esp_csv_line
from csi.validation.validators import validate_sample
from dsp.features.feature_extraction import (
    FeatureConfig,
    FeatureExtractor,
)
from dsp.preprocessing.preprocessing import (
    PreprocessConfig,
    Preprocessor,
)
from tests.synthetic.synth import make_esp_csv_line, make_json_line


def _feed(line_maker, n=80, seed=0):
    pre = Preprocessor(PreprocessConfig(smoothing="ema",
                                        lowpass_enabled=False))
    ext = FeatureExtractor(FeatureConfig(), pre.cfg)
    vec = None
    accepted = 0
    for i in range(n):
        if line_maker == "json":
            s = parse_line(
                make_json_line(seed=seed + i).split("#CSI ", 1)[1],
                1700000000.0 + i / 60.0)
        else:
            s = parse_esp_csv_line(
                make_esp_csv_line(seq=i + 1, seed=seed + i),
                local_ts=1700000000.0 + i / 100.0)
        rep = validate_sample(s)
        self_assert_ok = rep.ok  # documented ranges must hold for synth
        assert self_assert_ok, rep.warnings
        amp = pre.process(s)
        if amp is None:
            continue
        accepted += 1
        out = ext.update(amp, s.rssi, s.ts_local)
        if out is not None:
            vec = out
    return pre, ext, vec, accepted


class TestPipeline(unittest.TestCase):
    def test_json_path_end_to_end(self):
        pre, ext, vec, accepted = _feed("json")
        self.assertGreater(accepted, 64)
        self.assertIsNotNone(vec)
        self.assertEqual(len(vec.values), 180)
        self.assertEqual(pre.stats.accepted, accepted)

    def test_csv_path_end_to_end(self):
        pre, ext, vec, accepted = _feed("csv")
        self.assertGreater(accepted, 64)
        self.assertIsNotNone(vec)
        self.assertEqual(len(vec.values), 180)

    def test_both_paths_agree(self):
        _, _, vec_json, _ = _feed("json", n=80, seed=5)
        _, _, vec_csv, _ = _feed("csv", n=80, seed=5)
        # Same seeds -> same I/Q -> same amplitudes modulo firmware header
        # differences live only in metadata, not in the payload.
        np.testing.assert_allclose(vec_json.values, vec_csv.values,
                                   rtol=1e-9)


if __name__ == "__main__":
    unittest.main()
