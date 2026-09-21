"""Integration: receiver line handling + raw writer + heuristic engine.

No hardware: ``SerialReceiver._handle_line`` is driven directly with
synthetic ``#CSI`` lines, and ``InferenceEngine`` runs model-free
(heuristic fallback) plus stub-model checks. Verifies the single-fire fix
(one callback + one row per packet) and the live loop's plumbing.
"""

import tempfile
import time
import unittest
from pathlib import Path

import numpy as np

from csi.capture.serial_receiver import RawSessionWriter, SerialReceiver
from csi.parser.csi_parser import parse_line
from sensing.inference_engine import InferenceEngine, LoadedModels
from tests.synthetic.synth import make_json_line


class TestReceiverHandling(unittest.TestCase):
    def _receiver(self, **kw):
        got = []
        tmp = tempfile.TemporaryDirectory()
        record = Path(tmp.name) / "rec.csv" if kw.get("record") else None
        rx = SerialReceiver(port="loop://", baud=921600,
                            callback=got.append, record_path=record)
        rx._tmp = tmp  # keep alive for the test duration
        return rx, got

    def test_single_fire_per_packet(self):
        rx, got = self._receiver(record=True)
        line = make_json_line(seed=4)
        rx._handle_line(line)
        rx._handle_line(line)
        self.assertEqual(len(got), 2)  # exactly one callback per packet
        self.assertEqual(rx.packets, 2)
        rx._writer.close()
        rows = Path(rx._record_path).read_text().splitlines()
        self.assertEqual(len(rows), 3)  # header + 2 rows (no duplication)

    def test_malformed_counted(self):
        rx, got = self._receiver()
        rx._handle_line("#CSI {broken json")
        self.assertEqual(rx.malformed, 1)
        self.assertEqual(got, [])

    def test_status_lines_ignored(self):
        rx, got = self._receiver()
        rx._handle_line("#STAT uptime=5")
        rx._handle_line("")
        self.assertEqual(rx.packets, 0)


class TestHeuristicEngine(unittest.TestCase):
    def test_live_loop_plumbing(self):
        cfg = {"movement": {"smoothing_alpha": 0.5},
               "movement_threshold": 0.12,
               "presence": {"smoothing_alpha": 0.6},
               "presence_threshold": 0.5,
               "csi": {}, "features": {}, "sample_rate": 60,
               "smoothing_factor": 0.35, "room_width": 5.0}
        engine = InferenceEngine(cfg, None)
        for i in range(90):
            s = parse_line(make_json_line(seed=i).split("#CSI ", 1)[1],
                           1700000000.0 + i / 60.0)
            engine.process_sample(s)
            engine.update_link_status(True, 60.0, i + 1, 0)
        snap = engine.snapshot_for_plot()
        self.assertEqual(len(snap["amplitudes"]), 90)
        self.assertIn(engine.state.presence_label, ("PERSON", "EMPTY"))
        self.assertIn(engine.state.movement_label, ("MOVING", "STATIC"))
        self.assertEqual(engine.state.connection, "ONLINE")
        self.assertGreater(engine.state.packets, 0)


class TestModelBackedEngine(unittest.TestCase):
    def _engine(self, presence, position=None, scaler=None):
        cfg = {"movement": {"smoothing_alpha": 0.5},
               "movement_threshold": 0.12,
               "presence": {"smoothing_alpha": 0.6},
               "presence_threshold": 0.5,
               "csi": {}, "features": {}, "sample_rate": 60,
               "smoothing_factor": 0.35, "room_width": 5.0}
        models = LoadedModels(presence=presence, position=position,
                              scaler=scaler, feature_names=[], manifest={})
        return InferenceEngine(cfg, models)

    def _pump(self, engine, n=80):
        for i in range(n):
            s = parse_line(make_json_line(seed=i).split("#CSI ", 1)[1],
                           1700000000.0 + i / 60.0)
            engine.process_sample(s)
        return engine.state

    def test_sklearn_stub_models(self):
        class Presence:
            kind = "sklearn"
            def predict(self, x):
                assert x.ndim == 1 and len(x) == 180
                return 0.9

        class Position:
            kind = "sklearn"
            def predict(self, x):
                assert x.ndim == 1 and len(x) == 180
                return 0.42

        state = self._pump(self._engine(Presence(), Position()))
        self.assertEqual(state.presence_label, "PERSON")
        self.assertAlmostEqual(state.position_raw, 0.42)
        self.assertAlmostEqual(state.position_filtered, 0.42)

    def test_torch_stub_models_use_scaler(self):
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler().fit(np.random.default_rng(0).normal(
            size=(50, 180)))

        class TorchPresence:
            kind = "torch"
            def predict(self, x):
                assert x.ndim == 1 and len(x) == 180
                return 0.9

        class TorchPosition:
            kind = "torch"
            def predict(self, x):
                assert x.ndim == 1 and len(x) == 180
                return 0.7

        state = self._pump(
            self._engine(TorchPresence(), TorchPosition(), scaler))
        self.assertEqual(state.presence_label, "PERSON")
        self.assertAlmostEqual(state.position_raw, 0.7)


if __name__ == "__main__":
    unittest.main()
