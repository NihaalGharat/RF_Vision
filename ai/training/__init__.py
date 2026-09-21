"""Model implementations for RF Vision human sensing.

``baseline_model``
    Model A: scikit-learn candidates (KNN, Random Forest) with a uniform
    predict interface.
``neural_network``
    Model B: small PyTorch networks for presence classification and
    position regression (optional dependency).

Upstream source: ESP32-WiFi-CSI-Human-Sensing ``python/models/__init__.py``
(MIT, Sanaullah Shaheer). RF Vision change: absolute package imports.
"""

from ai.training.baseline_model import (
    BaselinePresenceModel,
    BaselinePositionModel,
    build_position_candidates,
    build_presence_candidates,
    load_sklearn_model,
    save_sklearn_model,
)

__all__ = [
    "BaselinePresenceModel",
    "BaselinePositionModel",
    "build_position_candidates",
    "build_presence_candidates",
    "load_sklearn_model",
    "save_sklearn_model",
]
