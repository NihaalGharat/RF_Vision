"""Explainable-AI foundation (interfaces + model-agnostic importances).

RF Vision native. No upstream XAI code exists (verified: none of the four
audited repositories implements XAI), so this module defines the starting
interface plus the two attributions available with zero new methodology:

* RandomForest impurity importances mapped back onto RF Vision feature
  names (``rf_importance``) -- descriptive, NOT causal;
* a permutation-importance skeleton that works with any
  ``predict(1-D vector)`` wrapper (``permutation_importance``).

SHAP/LIME/attention explanations are scheduled work. Every explanation
payload carries ``method`` + ``caveats`` and must be reported with the
status in ``docs/research/SCIENTIFIC_VALIDATION_STATUS.md``: feature
importance is not validated as a physical RF explanation.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

__all__ = ["Explanation", "rf_importance", "permutation_importance"]


class Explanation(dict):
    """Attribution payload: feature name -> score, plus method metadata."""

    def __init__(self, scores: Dict[str, float], method: str,
                 caveats: str = "") -> None:
        super().__init__(scores)
        self.method = method
        self.caveats = caveats

    def top(self, k: int = 10) -> List[tuple]:
        """Top-k (feature, score) pairs by absolute score."""
        return sorted(self.items(), key=lambda kv: abs(kv[1]),
                      reverse=True)[:max(k, 0)]

    def as_payload(self) -> dict:
        """JSON-serializable payload for the ``xai.explanation`` event."""
        return {"method": self.method, "caveats": self.caveats,
                "scores": dict(self)}


def rf_importance(rf_model, feature_names: Sequence[str]) -> Explanation:
    """Impurity importances from a fitted RandomForest (descriptive only)."""
    importances = getattr(rf_model, "feature_importances_", None)
    if importances is None:
        raise ValueError("model exposes no feature_importances_")
    importances = np.asarray(importances, dtype=float)
    if len(importances) != len(feature_names):
        raise ValueError(
            f"{len(importances)} importances vs {len(feature_names)} names")
    total = importances.sum()
    scores = {name: float(v / total) if total > 0 else 0.0
              for name, v in zip(feature_names, importances)}
    return Explanation(
        scores, method="rf_impurity",
        caveats="Impurity importance is descriptive (split utility), not a "
                "validated physical explanation of RF propagation.")


def permutation_importance(predict: Callable[[np.ndarray], float],
                           baseline_vector: np.ndarray,
                           feature_names: Sequence[str],
                           baseline_score: Optional[float] = None,
                           n_repeats: int = 5,
                           seed: int = 42) -> Explanation:
    """Permutation importance around one reference vector.

    Each feature (or the full vector slice for grouped names -- caller
    decides granularity) is shuffled across ``n_repeats`` seeded copies;
    importance = mean absolute change in the model output. Model-agnostic;
    works with any ``predict(1-D) -> float`` wrapper (KNN/RF/MLP uniform
    interface).
    """
    rng = np.random.default_rng(seed)
    x0 = np.asarray(baseline_vector, dtype=float).reshape(-1)
    if len(x0) != len(feature_names):
        raise ValueError(
            f"{len(x0)} values vs {len(feature_names)} names")
    y0 = float(predict(x0)) if baseline_score is None else float(baseline_score)
    scores: Dict[str, float] = {}
    for i, name in enumerate(feature_names):
        deltas = []
        for _ in range(max(n_repeats, 1)):
            xp = x0.copy()
            xp[i] = float(rng.permutation(x0)[i])
            deltas.append(abs(float(predict(xp)) - y0))
        scores[name] = float(np.mean(deltas))
    return Explanation(
        scores, method="permutation",
        caveats="Local to the reference vector; permutation breaks feature "
                "correlations, so scores are comparative, not causal.")
