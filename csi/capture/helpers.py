"""Host-side serial helpers (stdlib only).

Clean re-implementations of the bring-up idioms from Steven M. Hernandez's
ESP32-CSI-Tool ``python_utils/`` (MIT, 2020 -- see THIRD_PARTY_NOTICES.md):
``read_stdin.py`` (line scrubbing), ``wait_timer.py`` (throttling),
``serial_append_time.py`` (host timestamping), ``serial_measure_rate.py``
(rate measurement). No code copied; behaviour re-implemented against the
RF Vision ``CSI_DATA`` / ``#CSI`` line model.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Deque, Optional


def scrub_line(line: str) -> Optional[str]:
    """Return the first ``CSI_DATA`` payload in a raw console line.

    ESP-IDF monitors interleave log lines (``I (123) ...``) with CSI lines;
    this scans for the ``CSI_DATA`` marker and returns the substring from
    it, or ``None`` when the line carries no CSI data. Blank input yields
    ``None``.
    """
    if not line:
        return None
    idx = line.find("CSI_DATA")
    if idx < 0:
        return None
    return line[idx:].strip() or None


def stamp_line(line: str, ts: Optional[float] = None) -> str:
    """Append a host Unix timestamp column to a CSI line.

    Mirrors the ``serial_append_time.py`` pattern: ``<line>,<host_ts>`` with
    six decimals. Used when the firmware timestamp is unavailable or wraps.
    """
    host_ts = ts if ts is not None else time.time()
    return f"{line.rstrip()},{host_ts:.6f}"


class WaitTimer:
    """Throttle loop iterations to a minimum period (``wait_timer.py``)."""

    def __init__(self, period_seconds: float) -> None:
        if period_seconds < 0:
            raise ValueError("period must be >= 0")
        self.period = float(period_seconds)
        self._next: float = 0.0

    def wait(self, now: Optional[float] = None) -> float:
        """Sleep until the next tick; return seconds actually slept."""
        t = now if now is not None else time.time()
        if self._next <= t:
            self._next = t + self.period
            return 0.0
        delay = self._next - t
        time.sleep(delay)
        self._next += self.period
        return delay


class RateMeter:
    """Rolling packet-rate estimate (``serial_measure_rate.py`` pattern)."""

    def __init__(self, window_seconds: float = 10.0) -> None:
        if window_seconds <= 0:
            raise ValueError("window must be > 0")
        self.window = float(window_seconds)
        self._stamps: Deque[float] = deque()

    def tick(self, ts: Optional[float] = None) -> float:
        """Record a packet arrival; return the current rate (packets/s)."""
        now = ts if ts is not None else time.time()
        self._stamps.append(now)
        cutoff = now - self.window
        while self._stamps and self._stamps[0] < cutoff:
            self._stamps.popleft()
        span = now - self._stamps[0] if len(self._stamps) > 1 else 0.0
        if span <= 0.0:
            return float(len(self._stamps))
        return len(self._stamps) / span

    @property
    def count(self) -> int:
        """Packets currently inside the window."""
        return len(self._stamps)
