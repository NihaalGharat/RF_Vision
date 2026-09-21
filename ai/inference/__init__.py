"""Model-loading API for the inference stage.

Canonical loader lives in :mod:`sensing.inference_engine` (it defines the
``LoadedModels`` contract the engine consumes); this package re-exports it
so ``ai.inference`` is the documented import path for training/evaluation
consumers. No duplicate implementation.
"""

from sensing.inference_engine import LoadedModels, apply_scaler, load_models

__all__ = ["LoadedModels", "apply_scaler", "load_models"]
