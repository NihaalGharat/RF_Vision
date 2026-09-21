"""Presence decision: smoothed PERSON/EMPTY from per-window probabilities.

RF Vision native module. Encapsulates the exponential-smoothing +
threshold logic previously inline in ``InferenceEngine.process_sample``
(identical math): the raw per-window presence probability (model output
or, with no models trained, the movement probability as an honest
heuristic fallback) is smoothed with ``presence.smoothing_alpha`` and
compared against ``presence_threshold``.
"""

from __future__ import annotations

from typing import Optional, Tuple

__all__ = ["PresenceSmoother", "decide_presence"]


def decide_presence(smoothed_prob: float, threshold: float = 0.5) -> str:
    """Map a smoothed presence probability to a PERSON/EMPTY label."""
    return "PERSON" if smoothed_prob >= threshold else "EMPTY"


class PresenceSmoother:
    """Exponential smoother + thresholder for presence probabilities."""

    def __init__(self, alpha: float = 0.6, threshold: float = 0.5) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = float(alpha)
        self.threshold = float(threshold)
        self._prob: Optional[float] = None

    def reset(self) -> None:
        """Forget the smoothing state (stream restarted)."""
        self._prob = None

    def update(self, raw_prob: float) -> Tuple[float, str]:
        """Feed one per-window probability; return ``(smoothed, label)``."""
        raw = min(max(float(raw_prob), 0.0), 1.0)
        if self._prob is None:
            self._prob = raw
        else:
            self._prob = self.alpha * raw + (1.0 - self.alpha) * self._prob
        return self._prob, decide_presence(self._prob, self.threshold)

    @property
    def smoothed(self) -> Optional[float]:
        """Current smoothed probability (``None`` before the first update)."""
        return self._prob
