"""Timestamp synchronization helpers (RF Vision native, stdlib only).

Single-node foundation plus the multi-node design hook. Today every sample
carries two clocks (``ts_esp32_us`` from the firmware, ``ts_local`` from
the host); this module estimates the offset between them robustly (median
of paired observations) so future multi-receiver fusion has one common
time base. True multi-node sync (NTP/PTP discipline, drift tracking) is a
scheduled native work package -- see ``realtime/protocol/``.
"""

from __future__ import annotations

import statistics
from collections import deque
from typing import Deque, Optional

__all__ = ["ClockOffsetEstimator"]


class ClockOffsetEstimator:
    """Robust host-minus-device clock offset estimator.

    Feed ``(device_ts, host_ts)`` pairs in identical units; the offset is
    the median of ``host - device`` over a sliding window, which rejects
    scheduling outliers without any model of drift.

    Two-node extension (additive): :attr:`jitter` (median absolute
    deviation of the window) quantifies offset stability, and
    :attr:`drift_per_sample` (least-squares slope of offset versus
    observation index) exposes clock drift trend. Neither changes the
    offset estimate itself.
    """

    def __init__(self, window: int = 64) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._pairs: Deque[float] = deque(maxlen=window)
        self._n = 0

    def observe(self, device_ts: float, host_ts: float) -> float:
        """Add one observation; return the current offset estimate."""
        self._pairs.append(float(host_ts) - float(device_ts))
        self._n += 1
        return self.offset

    @property
    def n(self) -> int:
        """Total observations seen (window may hold fewer)."""
        return self._n

    @property
    def offset(self) -> Optional[float]:
        """Median offset, or ``None`` before the first observation."""
        if not self._pairs:
            return None
        return float(statistics.median(self._pairs))

    @property
    def jitter(self) -> Optional[float]:
        """Median absolute deviation of the window (same units as offset).

        ``None`` with fewer than 2 observations. Robust to outliers, so a
        small jitter means the offset estimate is stable.
        """
        if len(self._pairs) < 2:
            return None
        med = statistics.median(self._pairs)
        return float(statistics.median([abs(v - med) for v in self._pairs]))

    @property
    def drift_per_sample(self) -> Optional[float]:
        """Least-squares slope of offset vs observation index in-window.

        ``None`` with fewer than 2 observations. Near-zero means the two
        clocks run at the same rate; a sustained non-zero slope is drift.
        """
        n = len(self._pairs)
        if n < 2:
            return None
        vals = list(self._pairs)
        mean_x = (n - 1) / 2.0
        mean_y = sum(vals) / n
        sxx = sum((i - mean_x) ** 2 for i in range(n))
        if sxx == 0:
            return 0.0
        sxy = sum((i - mean_x) * (v - mean_y)
                  for i, v in enumerate(vals))
        return float(sxy / sxx)

    def stable(self, max_jitter: float, min_n: int = 8) -> bool:
        """True when the estimate rests on enough stable observations."""
        if self._n < min_n:
            return False
        jit = self.jitter
        return jit is not None and jit <= max_jitter

    def device_to_host(self, device_ts: float) -> Optional[float]:
        """Map a device timestamp into host time (``None`` if uncalibrated)."""
        if self.offset is None:
            return None
        return float(device_ts) + self.offset

    def reset(self) -> None:
        """Forget all observations (clock discipline changed)."""
        self._pairs.clear()
        self._n = 0
