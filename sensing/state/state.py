"""Tracking state snapshot (GUI-facing).

Moved verbatim from ``sensing/inference_engine.py`` (upstream:
ESP32-WiFi-CSI-Human-Sensing ``python/inference.py``, MIT) so that
``sensing.state`` is the canonical owner of the cross-thread state object.
``inference_engine`` re-exports it for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

__all__ = ["SystemState"]


@dataclass
class SystemState:
    """Thread-safe view of the current tracking state (GUI-facing)."""

    connection: str = "OFFLINE"          # ONLINE / OFFLINE
    presence_label: str = "UNKNOWN"      # PERSON / EMPTY / UNKNOWN
    presence_probability: Optional[float] = None
    movement_label: str = "UNKNOWN"      # MOVING / STATIC / UNKNOWN
    movement_probability: Optional[float] = None
    position_raw: Optional[float] = None
    position_filtered: Optional[float] = None
    confidence: Optional[float] = None
    csi_rate: float = 0.0
    latency_ms: float = 0.0
    packets: int = 0
    malformed: int = 0
    model_name: str = "none (heuristic)"
    last_update: float = 0.0
