"""Filtering utilities (canonical entry point).

Front-end over :mod:`dsp.preprocessing`: Hampel spike rejection (always
available, numpy only) plus Butterworth low-pass design/apply helpers
(require scipy, same as the streaming filter in ``Preprocessor``). No
duplicate implementations -- the streaming state machine stays in
``Preprocessor``; these are the batch/testable forms.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

from dsp.preprocessing.preprocessing import hampel_filter

__all__ = ["design_lowpass", "apply_lowpass", "hampel_filter"]


def design_lowpass(cutoff_hz: float, rate_hz: float,
                   order: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """Design a digital Butterworth low-pass; return ``(b, a)``."""
    try:
        from scipy.signal import butter
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "design_lowpass requires scipy; pip install scipy") from exc
    if not 0 < cutoff_hz < rate_hz / 2:
        raise ValueError("cutoff must be within (0, Nyquist)")
    wn = min(cutoff_hz / (0.5 * rate_hz), 0.99)
    return butter(order, wn, btype="low")


def apply_lowpass(matrix: np.ndarray, cutoff_hz: float, rate_hz: float,
                  order: int = 4) -> np.ndarray:
    """Zero-phase-ish batch low-pass along the time axis (rows = samples).

    Uses forward filtering (``lfilter``); the real-time equivalent with
    filter state lives in ``Preprocessor``.
    """
    try:
        from scipy.signal import lfilter
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "apply_lowpass requires scipy; pip install scipy") from exc
    b, a = design_lowpass(cutoff_hz, rate_hz, order)
    out = lfilter(b, a, np.asarray(matrix, dtype=np.float64), axis=0)
    return np.asarray(out)
