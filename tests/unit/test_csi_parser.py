"""Unit tests: JSON CSI parser (I/Q math, validation, errors)."""

import time
import unittest

import numpy as np

from csi.parser.csi_parser import (
    VALID_SUBCARRIERS_20MHZ,
    PacketError,
    amplitude,
    parse_line,
    phase,
    raw_to_complex,
    valid_amplitude,
)
from tests.synthetic.synth import make_iq, make_json_line


def _sample(**kw):
    return parse_line(make_json_line(**kw).split("#CSI ", 1)[1], time.time())


class TestCsiParser(unittest.TestCase):
    def test_good_line(self):
        s = _sample(seq=5, seed=1)
        self.assertEqual(s.seq, 5)
        self.assertEqual(s.n_subcarriers, 64)

    def test_blank_and_status_lines(self):
        self.assertIsNone(parse_line("   ", time.time()))
        self.assertIsNone(parse_line("#STAT uptime=1", time.time()))

    def test_malformed_json(self):
        with self.assertRaises(PacketError):
            parse_line("{not json", time.time())

    def test_missing_field(self):
        with self.assertRaises(PacketError):
            parse_line('{"timestamp": 1}', time.time())

    def test_csi_len_mismatch(self):
        obj = make_json_line().split("#CSI ", 1)[1]
        import json
        d = json.loads(obj)
        d["csi_len"] = 4
        with self.assertRaises(PacketError):
            parse_line(json.dumps(d), time.time())

    def test_iq_math_on_known_vector(self):
        # (real, imag) = (3, 4) -> amp 5, angle atan2(4, 3).
        import json
        d = json.loads(make_json_line().split("#CSI ", 1)[1])
        d["csi"] = [3, 4] * 64
        d["csi_len"] = 128
        s = parse_line(json.dumps(d), time.time())
        np.testing.assert_allclose(amplitude(s)[:4], [5.0] * 4)
        np.testing.assert_allclose(phase(s)[:4], [np.arctan2(4, 3)] * 4)

    def test_first_word_trim(self):
        raw = np.arange(132, dtype=np.int8)
        out = raw_to_complex(raw, first_word_invalid=True)
        self.assertEqual(len(out), 64)  # (132 - 4) / 2
        with self.assertRaises(PacketError):
            raw_to_complex(np.arange(2, dtype=np.int8),
                           first_word_invalid=True)

    def test_valid_mask_size(self):
        self.assertEqual(len(VALID_SUBCARRIERS_20MHZ), 54)
        s = _sample(seed=2)
        self.assertEqual(len(valid_amplitude(s)), 54)

    def test_make_iq_deterministic(self):
        self.assertEqual(make_iq(seed=9), make_iq(seed=9))
        self.assertNotEqual(make_iq(seed=9), make_iq(seed=10))


if __name__ == "__main__":
    unittest.main()
