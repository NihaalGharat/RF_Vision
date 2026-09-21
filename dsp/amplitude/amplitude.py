"""Amplitude utilities (canonical entry point for CSI amplitude).

Thin, tested front-end over :mod:`csi.parser.csi_parser`: amplitude in
:math:`|I + jQ|` on the full buffer or restricted to the valid-subcarrier
mask. All heavier logic (first-word trimming, Hampel, smoothing) stays in
:mod:`dsp.preprocessing`; this module exists so downstream code
(``signal.features``, ``sensing.*``, ``ai.*``) imports amplitude from one
stable place.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from csi.parser.csi_parser import (
    VALID_SUBCARRIERS_20MHZ,
    CsiSample,
    amplitude,
    raw_to_complex,
    valid_amplitude,
)

__all__ = [
    "VALID_SUBCARRIERS_20MHZ",
    "amplitude_full",
    "amplitude_valid",
    "complex_slots",
]


def complex_slots(sample: CsiSample) -> np.ndarray:
    """Complex I/Q slots for the sample (first-word trim applied)."""
    return raw_to_complex(sample.csi, sample.first_word_invalid)


def amplitude_full(sample: CsiSample) -> np.ndarray:
    """Amplitude for every packed complex slot in the raw buffer."""
    return amplitude(sample)


def amplitude_valid(
    sample: CsiSample,
    valid_subcarriers: Sequence[int] = VALID_SUBCARRIERS_20MHZ,
) -> np.ndarray:
    """Amplitude restricted to the valid subcarrier indices."""
    return valid_amplitude(sample, valid_subcarriers)
