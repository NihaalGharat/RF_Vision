"""Heuristic STATIC/MOVING detector from temporal CSI activity.

Moved verbatim from ``sensing/inference_engine.py`` (upstream:
ESP32-WiFi-CSI-Human-Sensing ``python/inference.py``, MIT) so that
``sensing.motion`` is the canonical owner. ``inference_engine`` re-exports
it for backward compatibility.

Uses the ``move_rel_activity`` feature (mean relative amplitude change
over the window): a person walking changes the channel much faster
than a static room. One noisy sample never flips the state because
the probability is exponentially smoothed over consecutive windows.
The threshold comes from config, or from ``calibrate.py`` (empty-room
baseline + margin) when auto-calibration is enabled.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

LOG = logging.getLogger("wifi_sensing.motion")

__all__ = ["MovementDetector"]


class MovementDetector:
    """Heuristic STATIC/MOVING detector from temporal CSI activity."""

    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.alpha = float(cfg.get("movement", {}).get("smoothing_alpha", 0.5))
        self.threshold = float(cfg.get("movement_threshold", 0.12))
        self.auto_cal = bool(cfg.get("movement", {}).get(
            "auto_threshold_from_calibration", True))
        self._prob = None

    def update_threshold_from_calibration(self, cal_file) -> None:
        """Adopt the empty-room baseline measured by calibrate.py, if any."""
        try:
            cal = json.loads(Path(cal_file).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        baseline = float(cal.get("empty_activity", 0.0))
        if baseline > 0:
            self.threshold = baseline * 1.5
            LOG.info("movement threshold %.4f from calibration "
                     "(empty baseline %.4f)", self.threshold, baseline)

    def update(self, features: np.ndarray, names: list) -> float:
        """Feed one feature vector; return smoothed P(movement) in [0, 1]."""
        try:
            idx = names.index("move_rel_activity")
            activity = float(features[idx])
        except (ValueError, IndexError):
            activity = 0.0
        scale = max(self.threshold, 1e-6)
        raw = 1.0 / (1.0 + float(np.exp(-(activity - self.threshold)
                                        / (0.5 * scale))))
        self._prob = raw if self._prob is None \
            else self.alpha * raw + (1.0 - self.alpha) * self._prob
        return self._prob
