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
    """

    def __init__(self, window: int = 64) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._pairs: Deque[float] = deque(maxlen=window)

    def observe(self, device_ts: float, host_ts: float) -> float:
        """Add one observation; return the current offset estimate."""
        self._pairs.append(float(host_ts) - float(device_ts))
        return self.offset

    @property
    def offset(self) -> Optional[float]:
        """Median offset, or ``None`` before the first observation."""
        if not self._pairs:
            return None
        return float(statistics.median(self._pairs))

    def device_to_host(self, device_ts: float) -> Optional[float]:
        """Map a device timestamp into host time (``None`` if uncalibrated)."""
        if self.offset is None:
            return None
        return float(device_ts) + self.offset

    def reset(self) -> None:
        """Forget all observations (clock discipline changed)."""
        self._pairs.clear()
