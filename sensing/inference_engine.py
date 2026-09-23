"""Real-time inference: model loading + streaming detection pipeline.

* :func:`load_models` loads the artifacts written by ``train.py`` (model
  manifest + scaler + feature configuration) once at startup. Training
  never runs at inference time.
* :class:`MovementDetector` — heuristic STATIC/MOVING from temporal CSI
  activity, exponentially smoothed.
* :class:`InferenceEngine` — full pipeline:
  CSI sample -> preprocessing -> windowed features -> presence
  classifier -> position model -> position filter -> :class:`SystemState`
  (a locked snapshot the GUI can poll safely).
"""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Optional

import numpy as np
from sklearn.preprocessing import StandardScaler

from csi.parser.csi_parser import CsiSample
from sensing.state.state import SystemState
from sensing.motion.motion import MovementDetector
from sensing.presence.presence import PresenceSmoother
from sensing.activity.activity import label_activity
from sensing.confidence.confidence import (
    CALIBRATION_LABEL,
    aggregate_evidence,
)
from sensing.state.persistence import PresencePersistence

# Backward-compatible re-exports (canonical homes: sensing.state,
# sensing.motion). ``from sensing.inference_engine import SystemState``
# keeps working.
__all__ = [
    "SystemState",
    "MovementDetector",
    "LoadedModels",
    "load_models",
    "apply_scaler",
    "InferenceEngine",
]

LOG = logging.getLogger("wifi_sensing.inference")


@dataclass
class LoadedModels:
    """Everything inference needs from the training stage."""

    presence: object                 # .predict(features) -> P(person)
    position: Optional[object]       # .predict(features) -> [0, 1] or None
    scaler: Optional[StandardScaler] # shared feature scaler (fit on train)
    feature_names: list
    manifest: dict

    @property
    def position_available(self) -> bool:
        return self.position is not None


def load_models(models_dir: Path, cfg: dict) -> Optional[LoadedModels]:
    """Load the best models from ``models_dir``; ``None`` when absent."""
    manifest_path = models_dir / "model_manifest.json"
    if not manifest_path.exists():
        LOG.warning("no model manifest at %s - run train.py first",
                    manifest_path)
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    feature_names = manifest.get("feature_names") or []
    scaler = None
    scaler_file = manifest.get("scaler")
    if scaler_file:
        scaler_path = models_dir / scaler_file
        if scaler_path.exists():
            import joblib
            scaler = joblib.load(scaler_path)

    from ai.training.baseline_model import BaselinePositionModel, \
        BaselinePresenceModel

    def _load_presence():
        entry = manifest.get("presence")
        if not entry:
            return None
        path = models_dir / entry["file"]
        if entry.get("type") == "torch":
            from ai.training import neural_network as nn_mod
            return nn_mod.TorchPresenceModel(
                nn_mod.load_torch_model("presence", len(feature_names),
                                        str(path), cfg),
                name=entry.get("name", "presence"))
        from ai.training import baseline_model as bl_mod
        return BaselinePresenceModel(
            bl_mod.load_sklearn_model(str(path)),
            name=entry.get("name", "presence"))

    def _load_position():
        entry = manifest.get("position")
        if not entry:
            return None
        path = models_dir / entry["file"]
        if entry.get("type") == "torch":
            from ai.training import neural_network as nn_mod
            return nn_mod.TorchPositionModel(
                nn_mod.load_torch_model("position", len(feature_names),
                                        str(path), cfg),
                name=entry.get("name", "position"))
        from ai.training import baseline_model as bl_mod
        return BaselinePositionModel(
            bl_mod.load_sklearn_model(str(path)),
            name=entry.get("name", "position"))

    presence = _load_presence()
    position = _load_position()
    if presence is None:
        LOG.warning("manifest contains no usable presence model")
        return None
    LOG.info("models loaded: presence=%s%s",
             getattr(presence, "name", "?"),
             f", position={getattr(position, 'name', '?')}"
             if position is not None else " (no position model)")
    return LoadedModels(presence=presence, position=position, scaler=scaler,
                        feature_names=feature_names, manifest=manifest)


def apply_scaler(scaler: Optional[StandardScaler], features: np.ndarray) -> np.ndarray:
    """Scale features for models that expect scaled input (torch models).

    sklearn candidates embed their own scaler in the pipeline; applying the
    shared scaler again would be wrong there, so callers only use this for
    torch models (``kind == "torch"``).
    """
    x = np.asarray(features, dtype=np.float64).reshape(1, -1)
    if scaler is None:
        return x
    return scaler.transform(x)


class InferenceEngine:
    """Full real-time pipeline: CSI sample -> presence/movement/position.

    Thread model: :meth:`process_sample` is called from the serial
    receiver thread; the GUI polls the locked :attr:`state` snapshot and
    :meth:`snapshot_for_plot` from its own timer.
    """

    def __init__(self, cfg: dict, models: Optional[LoadedModels]) -> None:
        from dsp.features.feature_extraction import (
            FeatureConfig, FeatureExtractor)
        from localization.tracking.position_filter import (
            PositionFilter, PositionFilterConfig)
        from dsp.preprocessing.preprocessing import (
            PreprocessConfig, Preprocessor)

        self.cfg = cfg
        self.models = models
        self.preproc_cfg = PreprocessConfig.from_config(cfg)
        self.preprocessor = Preprocessor(self.preproc_cfg)
        self.extractor = FeatureExtractor(
            FeatureConfig.from_config(cfg), self.preproc_cfg)
        self.feature_names = self.extractor.feature_names()
        self.position_filter = PositionFilter(
            PositionFilterConfig.from_config(cfg))
        self.presence = PresenceSmoother(
            alpha=float(cfg.get("presence", {}).get("smoothing_alpha", 0.6)),
            threshold=float(cfg.get("presence_threshold", 0.5)))
        self.movement = MovementDetector(cfg)
        if self.movement.auto_cal:
            cal_file = cfg.get("movement", {}).get("calibration_file")
            if cal_file:
                self.movement.update_threshold_from_calibration(cal_file)
        if models is not None:
            self.model_name = getattr(models.presence, "name", "model")
        else:
            self.model_name = "none (heuristic fallback)"

        self.latency_ms = 0.0
        self._lock = threading.Lock()
        self._amplitude_history: Deque[np.ndarray] = deque(maxlen=300)
        self._rssi_history: Deque[float] = deque(maxlen=300)
        self._position_history: Deque[Optional[float]] = deque(maxlen=200)
        self._persistence = PresencePersistence()
        self.state = SystemState(model_name=self.model_name)

    # ------------------------------------------------------------------
    def process_sample(self, sample: CsiSample) -> None:
        """Consume one raw CSI sample (called from the serial thread)."""
        t0 = time.perf_counter()
        amp = self.preprocessor.process(sample)
        if amp is None:
            return
        self._amplitude_history.append(amp.copy())
        self._rssi_history.append(float(sample.rssi))
        fv = self.extractor.update(amp, sample.rssi, sample.ts_local)
        if fv is None:
            return

        movement_prob = self.movement.update(fv.values, fv.names)

        if self.models is not None:
            # All model wrappers take a 1-D feature vector. Torch models need
            # the shared scaler applied first (sklearn wrappers scale
            # internally, so the shared scaler must NOT be applied to them).
            flat = fv.values.reshape(-1)
            if getattr(self.models.presence, "kind", "") == "torch":
                flat = apply_scaler(self.models.scaler, flat).reshape(-1)
            presence_prob = float(self.models.presence.predict(flat))
        else:
            # Honest fallback when no model is trained yet: motion implies
            # a person. Clearly reported as "heuristic" in the UI.
            presence_prob = min(max(movement_prob, 0.0), 1.0)
        smoothed_presence, presence_label = self.presence.update(presence_prob)

        person = presence_label == "PERSON"
        position_raw: Optional[float] = None
        position_filtered: Optional[float] = None
        if person and self.models is not None \
                and self.models.position_available:
            flat = fv.values.reshape(-1)
            if getattr(self.models.position, "kind", "") == "torch":
                flat = apply_scaler(self.models.scaler, flat).reshape(-1)
            position_raw = float(self.models.position.predict(flat))
            position_filtered = self.position_filter.filter(
                position_raw, fv.timestamp)
        if not person:
            self.position_filter.reset()

        latency = (time.perf_counter() - t0) * 1000.0
        self.latency_ms = (0.9 * self.latency_ms + 0.1 * latency
                           if self.latency_ms else latency)

        with self._lock:
            self._position_history.append(position_filtered)
            self.state.last_update = time.time()
            self.state.presence_label = presence_label
            self.state.presence_probability = smoothed_presence
            self.state.movement_label = label_activity(movement_prob)
            self.state.movement_probability = movement_prob
            self.state.position_raw = position_raw
            self.state.position_filtered = position_filtered
            self.state.confidence = smoothed_presence if person else None
            self.state.latency_ms = self.latency_ms
            # -- P1 showcase layer (additive; inference math above untouched)
            score, _contributors = aggregate_evidence(
                presence_prob=smoothed_presence,
                movement_prob=movement_prob)
            state_name, shown = self._persistence.update(
                presence_label=presence_label,
                movement_label=self.state.movement_label,
                confidence=score)
            self.state.presence_state = state_name
            self.state.rf_evidence_confidence = shown
            self.state.confidence_calibration = CALIBRATION_LABEL
            self.state.provenance = "RF-INFERRED"
            self.state.trail = self._trail_locked()
            try:
                from ai.xai.xai import factual_evidence_statement
                self.state.evidence_statement = factual_evidence_statement(
                    state_name, self.state.movement_label)
            except Exception:
                self.state.evidence_statement = None

    # ------------------------------------------------------------------
    def update_link_status(self, online: bool, rate: float, packets: int,
                           malformed: int) -> None:
        """Refresh link-level stats (from the serial receiver thread)."""
        with self._lock:
            self.state.connection = "ONLINE" if online else "OFFLINE"
            self.state.csi_rate = rate
            self.state.packets = packets
            self.state.malformed = malformed

    def _trail_locked(self, limit: int = 60) -> list:
        """Recent non-None filtered 1-D positions, oldest first (need lock)."""
        vals = [v for v in self._position_history if v is not None]
        return [float(v) for v in vals[-max(limit, 1):]]

    def reset_showcase(self) -> None:
        """Forget showcase/persistence state (new live session)."""
        with self._lock:
            self._persistence.reset()
            self._position_history.clear()
            self.state.presence_label = "UNKNOWN"
            self.state.presence_probability = None
            self.state.movement_label = "UNKNOWN"
            self.state.movement_probability = None
            self.state.position_raw = None
            self.state.position_filtered = None
            self.state.confidence = None
            self.state.presence_state = "UNKNOWN"
            self.state.rf_evidence_confidence = None
            self.state.provenance = "UNKNOWN"
            self.state.node_mode = "UNKNOWN"
            self.state.evidence_statement = None
            self.state.trail = []

    def showcase_snapshot(self, *, node_mode: str = "SINGLE",
                          nodes_available: int = 1, nodes_total: int = 1,
                          data_quality_ok: bool = True,
                          stale: bool = False,
                          derate: float = 1.0) -> dict:
        """P1 showcase payload: additive contract-v3 fields (JSON-safe).

        Recomputes the evidence score with the caller's session context
        (node topology, quality, staleness, degrade derate) WITHOUT
        advancing persistence — time advances only in ``process_sample``.
        Safe to call per broadcast frame (~10 Hz) from any thread.
        """
        from ai.xai.xai import factual_evidence_statement
        with self._lock:
            presence_label = self.state.presence_label
            movement_label = self.state.movement_label
            presence_prob = self.state.presence_probability
            movement_prob = self.state.movement_probability
            persisted_state, _ = self._persistence.current()
            trail = self._trail_locked()
            score, _contributors = aggregate_evidence(
                presence_prob=presence_prob, movement_prob=movement_prob,
                nodes_available=nodes_available, nodes_total=nodes_total,
                data_quality_ok=data_quality_ok, stale=stale, derate=derate)
            if stale or presence_prob is None:
                # Frozen last-known: show, don't score.
                display_state = (persisted_state
                                 if persisted_state != "UNKNOWN"
                                 else "UNKNOWN")
                shown = None
            else:
                display_state, shown = self._persistence.preview(
                    presence_label=presence_label,
                    movement_label=movement_label, confidence=score)
        try:
            statement = factual_evidence_statement(
                display_state, movement_label)
        except ValueError:
            statement = None
        return {
            "presence_state": display_state,
            "rf_evidence_confidence": shown,
            "confidence_calibration": CALIBRATION_LABEL,
            "provenance": ("RF-INFERRED" if presence_prob is not None
                           else "UNKNOWN"),
            "node_mode": node_mode,
            "evidence_statement": statement,
            "trail": trail,
        }

    # ------------------------------------------------------------------
    def snapshot_for_plot(self) -> dict:
        """Copy of debug-plot histories (GUI thread)."""
        with self._lock:
            return {
                "amplitudes": list(self._amplitude_history),
                "rssi": list(self._rssi_history),
                "positions": list(self._position_history),
            }



def main(argv=None) -> int:
    """CLI: headless real-time inference (no GUI)."""
    import argparse

    from config.settings import load_config, resolve_path, setup_logging
    from csi.capture.serial_receiver import SerialReceiver

    parser = argparse.ArgumentParser(
        description="Run real-time presence/movement/position inference "
                    "from the ESP32 CSI stream (headless)")
    parser.add_argument("--port", default=None,
                        help="serial port (default: config value)")
    parser.add_argument("--baud", type=int, default=None)
    parser.add_argument("--models-dir", default=None,
                        help="directory with trained models "
                             "(default: config value)")
    parser.add_argument("--config", default=None, help="config.yaml path")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    cfg["log_level"] = "DEBUG" if args.debug else cfg.get("log_level", "INFO")
    setup_logging(cfg)

    models_dir = Path(args.models_dir) if args.models_dir \
        else resolve_path(cfg, "model_path")
    models = load_models(models_dir, cfg)
    if models is None:
        print("WARNING: no trained models found - presence/movement run in "
              "heuristic mode and position is unavailable.\n"
              "Train models with: python dataset_collector.py && python "
              "train.py\n")

    engine = InferenceEngine(cfg, models)

    def on_sample(sample: CsiSample) -> None:
        engine.process_sample(sample)

    port = args.port or cfg.get("serial_port", "auto")
    baud = args.baud or int(cfg.get("baud_rate", 921600))
    receiver = SerialReceiver(port, baud, callback=on_sample)
    receiver.start()

    print("Real-time CSI inference (Ctrl+C to stop)")
    print("-" * 64)
    try:
        while True:
            time.sleep(0.5)
            engine.update_link_status(
                receiver.is_online, receiver.packet_rate,
                receiver.packets, receiver.malformed)
            s = engine.state
            pos = (f"{s.position_filtered:.2f}"
                   if s.position_filtered is not None else "  --")
            raw = (f"{s.position_raw:.2f}"
                   if s.position_raw is not None else "--")
            conf = (f"{s.confidence * 100:5.1f}%"
                    if s.confidence is not None else "  -- ")
            print(f"\r[{s.connection:7s}] {s.presence_label:6s} "
                  f"P={s.presence_probability if s.presence_probability is not None else 0:.2f} "
                  f"{s.movement_label:6s} pos={pos} (raw {raw}) "
                  f"conf={conf} csi={s.csi_rate:5.1f}/s "
                  f"lat={s.latency_ms:4.1f}ms ",
                  end="", flush=True)
    except KeyboardInterrupt:
        print("\nstopped")
    finally:
        receiver.stop()
        receiver.join(timeout=5.0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
