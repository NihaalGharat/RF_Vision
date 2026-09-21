"""Phase utilities (experiment-gated).

Raw ESP32 phase carries a per-packet offset and clock drift, so phase is
NOT part of the default pipeline (amplitude-only, see
:mod:`dsp.preprocessing`). This module exposes the sanitizer
(:func:`~signal.preprocessing.preprocessing.clean_phase`, unwrap +
linear-detrended) for controlled experiments only. Any use of phase
features must pass the validation gate in
``docs/research/SCIENTIFIC_VALIDATION_STATUS.md`` before its results are
reported.

Upstream source of ``clean_phase``: ESP32-WiFi-CSI-Human-Sensing
``python/preprocessing.py`` (MIT). RF Vision change: re-exported here as
the canonical phase entry point; implementation stays in one place.
"""

from __future__ import annotations

import numpy as np

from dsp.preprocessing.preprocessing import clean_phase

#: Phase pipeline status. ``False`` = amplitude-only default; experiments
#: must explicitly enable and validate phase before reporting results.
PHASE_ENABLED_BY_DEFAULT = False

__all__ = ["PHASE_ENABLED_BY_DEFAULT", "sanitize_phase"]


def sanitize_phase(phase_matrix: np.ndarray) -> np.ndarray:
    """Unwrap + detrend a (n_samples, n_subcarriers) phase matrix."""
    return clean_phase(np.asarray(phase_matrix, dtype=np.float64))
