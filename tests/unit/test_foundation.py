"""Unit tests: event envelope, capture helpers, config, XAI, tools."""

import unittest

import numpy as np

from ai.xai.xai import Explanation, permutation_importance, rf_importance
from csi.capture.helpers import RateMeter, WaitTimer, scrub_line, stamp_line
from csi.transport.serial_config import BAUD_RATE, DEFAULT_PORT
from config.settings import (
    PROJECT_ROOT,
    deep_merge,
    get_nested,
    load_config,
    resolve_path,
)
from realtime.protocol.event_envelope import (
    EVENT_TYPES,
    EventError,
    make_event,
    parse_event,
)
from tools.csi_record import classify_line, session_name


class TestEnvelope(unittest.TestCase):
    def test_roundtrip(self):
        ev = make_event("sensing.snapshot", {"presence": "PERSON"},
                        source="test", ts=1700000000.0, seq=3)
        import json
        back = parse_event(json.dumps(ev))
        self.assertEqual(back["payload"]["presence"], "PERSON")
        self.assertEqual(back["seq"], 3)

    def test_bad_type(self):
        with self.assertRaises(EventError):
            make_event("nope.event", {})

    def test_missing_field(self):
        with self.assertRaises(EventError):
            parse_event('{"type": "system.log"}')

    def test_schema_mismatch(self):
        with self.assertRaises(EventError):
            parse_event('{"schema": 999, "type": "system.log", "ts": 1, '
                        '"source": "x", "seq": 0, "payload": {}}')

    def test_known_types(self):
        self.assertIn("xai.explanation", EVENT_TYPES)


class TestHelpers(unittest.TestCase):
    def test_scrub(self):
        line = "I (123) wifi: CSI_DATA,1,2,3"
        self.assertEqual(scrub_line(line), "CSI_DATA,1,2,3")
        self.assertIsNone(scrub_line("I (123) wifi: hello"))
        self.assertIsNone(scrub_line(""))

    def test_stamp(self):
        out = stamp_line("CSI_DATA,1", ts=1700000000.0)
        self.assertTrue(out.endswith(",1700000000.000000"))

    def test_rate_meter(self):
        m = RateMeter(window_seconds=10.0)
        for i in range(5):
            rate = m.tick(ts=1000.0 + i)
        self.assertAlmostEqual(rate, 5 / 4)
        self.assertEqual(m.count, 5)

    def test_wait_timer_zero(self):
        t = WaitTimer(0.0)
        self.assertEqual(t.wait(now=100.0), 0.0)
        with self.assertRaises(ValueError):
            WaitTimer(-1.0)

    def test_serial_constants(self):
        self.assertEqual(BAUD_RATE, 921600)
        self.assertEqual(DEFAULT_PORT, "/dev/ttyUSB0")


class TestConfig(unittest.TestCase):
    def test_deep_merge(self):
        import copy
        from config.settings import DEFAULTS
        merged = deep_merge(copy.deepcopy(DEFAULTS), {"baud_rate": 115200})
        self.assertEqual(merged["baud_rate"], 115200)
        self.assertEqual(merged["sample_rate"], 60)

    def test_default_yaml_loads(self):
        cfg = load_config()
        self.assertEqual(cfg["baud_rate"], 921600)
        self.assertTrue(cfg["csi"]["trim_first_word_invalid"])
        self.assertEqual(get_nested(cfg, "train.seed"), 42)

    def test_resolve_path(self):
        p = resolve_path({"log_dir": "logs"}, "log_dir")
        self.assertEqual(p.parent, PROJECT_ROOT)


class TestXai(unittest.TestCase):
    def test_rf_importance(self):
        class FakeRF:
            feature_importances_ = np.array([0.5, 0.3, 0.2])
        ex = rf_importance(FakeRF(), ["a", "b", "c"])
        self.assertAlmostEqual(sum(ex.values()), 1.0)
        self.assertEqual(ex.top(1)[0][0], "a")
        payload = ex.as_payload()
        self.assertEqual(payload["method"], "rf_impurity")

    def test_permutation(self):
        ex = permutation_importance(lambda x: float(x[0] * 2.0 + x[1]),
                                    np.array([1.0, 5.0]), ["f0", "f1"],
                                    n_repeats=3, seed=0)
        self.assertEqual(ex.method, "permutation")
        self.assertEqual(set(ex.keys()), {"f0", "f1"})
        self.assertTrue(all(v >= 0.0 for v in ex.values()))
        self.assertEqual(len(ex.top(2)), 2)
        payload = ex.as_payload()
        self.assertIn("scores", payload)


class TestTools(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify_line("CSI_DATA,1,2"), "csi")
        self.assertIsNone(classify_line("hello"))

    def test_session_name(self):
        name = session_name(ts=1700000000.0)
        self.assertTrue(name.startswith("session_"))
        self.assertTrue(name.endswith(".csv"))


if __name__ == "__main__":
    unittest.main()
