"""Activity labels (movement-derived; no trained classifier yet).

RF Vision native module. Current activity output is DERIVED from the
movement probability (``sensing.motion``): ``MOVING`` when
``movement_prob >= 0.5``, else ``STATIC``. There is deliberately no trained
activity classifier in the foundation (upstream ``movement`` labels were
collected but never trained; csi-sensing activity models are
license-blocked with absent weights). A trained activity head is a
scheduled native work package -- until then every consumer must treat
these labels as heuristic. See
``docs/research/SCIENTIFIC_VALIDATION_STATUS.md``.
"""

from __future__ import annotations

__all__ = ["label_activity", "MOVING_THRESHOLD"]


#: Movement probability at/above which the link is labelled MOVING.
MOVING_THRESHOLD = 0.5


def label_activity(movement_prob: float,
                   threshold: float = MOVING_THRESHOLD) -> str:
    """Map a smoothed movement probability to MOVING/STATIC."""
    return "MOVING" if float(movement_prob) >= threshold else "STATIC"
