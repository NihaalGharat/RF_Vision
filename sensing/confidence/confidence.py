"""RF Evidence Confidence aggregator (P1 showcase foundation).

Product-state communication, NOT science. Combines already-computed
inference outputs (presence/motion evidence, node availability, data
quality) into ONE honestly-labelled product score in [0, 1].

Hard rules (binding):

* The score is ALWAYS labelled ``UNCALIBRATED`` — it is a smoothed,
  weighted evidence summary, never a probability, confidence interval,
  or validated detection confidence.
* No new detection thresholds live here. Detection mathematics in
  ``sensing/presence``, ``sensing/motion`` and ``sensing/activity`` are
  consumed as-is; this module only weights their outputs.
* Weights below are product policy (transparent, listed in
  ``contributors``), not calibrated science. Changing them changes UI
  emphasis, never a scientific claim.

Stdlib only — no numpy — so the web console can use it without dragging
the DSP stack into the transport layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

__all__ = [
    "CALIBRATION_LABEL",
    "DEGRADE_DERATE",
    "aggregate_evidence",
]

#: Mandatory label attached to every score this module produces.
CALIBRATION_LABEL = "UNCALIBRATED"

#: Confidence derate applied when the session runs degraded (a node down
#: in a dual attachment). Product policy required by the P1 directive
#: ("reduce RF Evidence Confidence" on node failure) — documented here,
#: not a measurement. Applied by the caller (``web/server.py``), which
#: knows the node topology; the engine does not.
DEGRADE_DERATE = 0.75

#: Relative weights of the evidence legs. Fixed, transparent, uncalibrated.
_W_PRESENCE = 0.6
_W_MOVEMENT = 0.4


def _clamp01(value: float) -> float:
    return min(max(float(value), 0.0), 1.0)


def aggregate_evidence(
    *,
    presence_prob: Optional[float],
    movement_prob: Optional[float],
    nodes_available: int = 1,
    nodes_total: int = 1,
    data_quality_ok: bool = True,
    stale: bool = False,
    derate: float = 1.0,
) -> Tuple[Optional[float], Dict[str, Any]]:
    """Combine existing evidence legs into an uncalibrated score.

    Returns ``(score, contributors)`` where ``score`` is ``None`` when no
    evidence exists yet (no inference outputs) or the input is stale —
    callers must render ``None`` as "no confidence", never as zero
    confidence. ``contributors`` records every leg so the UI (and tests)
    can show exactly what went into the number.
    """
    contributors: Dict[str, Any] = {
        "calibration": CALIBRATION_LABEL,
        "weights": {"presence": _W_PRESENCE, "movement": _W_MOVEMENT},
        "nodes_available": int(nodes_available),
        "nodes_total": int(nodes_total),
        "data_quality_ok": bool(data_quality_ok),
        "stale": bool(stale),
        "derate": float(derate),
    }
    if stale:
        contributors["reason"] = "stale input: last-known state shown, no score"
        return None, contributors
    if presence_prob is None:
        contributors["reason"] = "no inference output yet"
        return None, contributors

    base = (_W_PRESENCE * _clamp01(presence_prob)
            + _W_MOVEMENT * _clamp01(movement_prob if movement_prob is not None else 0.0))
    node_factor = (_clamp01(nodes_available / max(nodes_total, 1))
                   if nodes_total > 0 else 0.0)
    quality_factor = 1.0 if data_quality_ok else 0.5
    score = _clamp01(base * node_factor * quality_factor * _clamp01(derate))
    contributors.update({
        "presence_prob": float(presence_prob),
        "movement_prob": (float(movement_prob)
                          if movement_prob is not None else None),
        "base": base,
        "node_factor": node_factor,
        "quality_factor": quality_factor,
    })
    return score, contributors
