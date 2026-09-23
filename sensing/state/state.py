"""Tracking state snapshot (GUI-facing).

Moved verbatim from ``sensing/inference_engine.py`` (upstream:
ESP32-WiFi-CSI-Human-Sensing ``python/inference.py``, MIT) so that
``sensing.state`` is the canonical owner of the cross-thread state object.
``inference_engine`` re-exports it for backward compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

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
    # -- P1 showcase layer (additive; all default to "no inference") ----
    # presence_state: ABSENT / DETECTED / MOVING / STATIONARY /
    #   LOW_CONFIDENCE / EXITING / UNKNOWN (owner: sensing/state/persistence).
    presence_state: str = "UNKNOWN"
    # rf_evidence_confidence: product score in [0, 1], ALWAYS uncalibrated
    # (owner: sensing/confidence). None = no score (never zero-as-unknown).
    rf_evidence_confidence: Optional[float] = None
    confidence_calibration: str = "UNCALIBRATED"
    # provenance: UNKNOWN (no inference) / TRANSPORT (signal only) /
    #   RF-INFERRED (heuristic/model output, never a measurement).
    provenance: str = "UNKNOWN"
    # node_mode: UNKNOWN / SINGLE / DUAL / SINGLE-DEGRADED.
    node_mode: str = "UNKNOWN"
    # evidence_statement: canned factual sentence for the current state
    # (owner: ai/xai.factual_evidence_statement) or None.
    evidence_statement: Optional[str] = None
    # trail: recent RF-inferred 1-D positions in [0, 1] (oldest first),
    # for the 1-D trajectory view. Empty = none available.
    trail: List[float] = field(default_factory=list)
    # xai_status: NOT AVAILABLE until a validated explanation exists.
    xai_status: str = "NOT AVAILABLE"
