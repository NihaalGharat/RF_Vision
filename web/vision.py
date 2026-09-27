"""RF Vision pipeline: deterministic evidence + ML + tracks + spatial + XAI.

Composition layer over the validated stack — new code here, no validated
module is modified:

* per-node :class:`sensing.inference_engine.InferenceEngine` instances fed
  through the existing ``sample_observer`` seam of ``LiveProvider``
  (acquisition, sync, gates, contracts untouched);
* windows/features come from the existing
  ``dsp.features.FeatureExtractor`` inside each engine (Gate 3 = reuse);
* presence/activity/confidence/persistence come from the existing
  ``sensing/*`` modules (Gate 2 = reuse);
* the sklearn presence model (Gate 4) is loaded through the existing
  ``load_models`` path; without artifacts the engines run their honest
  heuristic fallback and the payload says so.

Aggregation in this module is deliberately conservative:

* evidence: ``EMPTY`` / ``RF_ACTIVITY`` / ``POSSIBLE_PRESENCE`` /
  ``UNKNOWN`` — never a person claim, never identity;
* tracks: at most one anonymous temporary track, created only from
  sustained ``POSSIBLE_PRESENCE``, dropped on timeout (Gate 5);
* spatial: ``RF ESTIMATE`` zone from the node evidence differential, or
  ``RF ACTIVITY`` with no zone on degraded input; ``LOCALIZED`` is never
  emitted (no spatial calibration exists) (Gate 6);
* XAI: factual sentences from pipeline facts, else ``XAI UNAVAILABLE``
  (Gate 8).

All state here is ENGINEERING/DEMONSTRATION, never controlled research
evidence. ``snapshot()`` is side-effect-free (no persistence advance) so
it is safe to call from a polling HTTP handler at any rate.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

__all__ = [
    "EVIDENCE_STATES",
    "SPATIAL_LEVELS",
    "TRACK_TIMEOUT_S",
    "STALE_AFTER_S",
    "VisionPipeline",
]

#: Deterministic aggregate evidence states (vision-scoped; the per-node
#: P1 product states in sensing/state/persistence.py are untouched).
EVIDENCE_STATES = (
    "EMPTY",
    "RF_ACTIVITY",
    "POSSIBLE_PRESENCE",
    "UNKNOWN",
)

#: Spatial honesty levels. LOCALIZED is listed as the top of the
#: hierarchy but this module never emits it (no calibration).
SPATIAL_LEVELS = (
    "LOCALIZED",
    "RF ESTIMATE",
    "RF ACTIVITY",
)

#: Seconds without POSSIBLE_PRESENCE before the anonymous track drops.
TRACK_TIMEOUT_S = 5.0

#: Seconds without an engine update before that node reads stale.
STALE_AFTER_S = 3.0

#: Max |score_a - score_b| still read as BETWEEN (presentation band on
#: uncalibrated scores — selects the zone label, never a position).
ZONE_DEAD_BAND = 0.15

#: Consecutive POSSIBLE_PRESENCE snapshots before a track is created
#: (conservative creation: never manufacture a person).
TRACK_CREATE_STREAK = 2


class VisionPipeline:
    """Dual-node vision aggregation over per-node inference engines."""

    def __init__(self, node_ids: tuple = ("esp32-a", "esp32-b"),
                 models_dir: Optional[Path] = None,
                 clock: Optional[Callable[[], float]] = None) -> None:
        from config.settings import load_config, resolve_path
        from sensing.inference_engine import InferenceEngine, load_models

        self._clock = clock or time.time
        self._lock = threading.Lock()
        cfg = load_config()
        # Engineering operating point (vision-local; research default
        # untouched): accept firmware rx_state!=0 frames. Measured
        # 2026-09-27 on live dual traffic: rx_state==1 amplitudes match
        # rx_state==0 (20.41+-1.39 vs 20.30+-0.88, n=2991/10); the strict
        # drop starves live windows (4548 samples -> 0 rows on node A).
        # Outliers remain handled by the Hampel + EMA chain. Collection
        # for training uses the same point (--accept-rx-errors).
        cfg = dict(cfg)
        cfg["csi"] = dict(cfg.get("csi", {}))
        cfg["csi"]["drop_rx_state_errors"] = False
        self.rx_operating_point = "ACCEPT_RX_ERRORS (engineering)"
        models = None
        resolved = (Path(models_dir) if models_dir is not None
                    else Path(resolve_path(cfg, "model_path")))
        try:
            models = load_models(resolved, cfg)
        except Exception:
            models = None
        self.models = models
        self.model_name = (getattr(models.presence, "name", "model")
                           if models is not None else "none (heuristic)")
        self.model_kind = ("sklearn" if models is not None else "heuristic")
        self.engines: Dict[str, Any] = {
            nid: InferenceEngine(cfg, models) for nid in node_ids
        }
        self._track: Optional[Dict[str, Any]] = None
        self._track_seq = 0
        self._active_streak = 0
        self.started_at = self._clock()

    # -- sample seam ---------------------------------------------------
    def observer(self, node_id: str) -> Callable[[Any], None]:
        """``sample_observer`` callable for one node's provider.

        Exceptions are swallowed by the provider seam already; the guard
        here keeps a vision failure from ever breaking capture.
        """
        engine = self.engines.get(node_id)

        def _observe(sample: Any) -> None:
            try:
                if engine is not None:
                    engine.process_sample(sample)
            except Exception:
                pass

        return _observe

    def reset(self) -> None:
        """Forget runtime state (session stop)."""
        with self._lock:
            for engine in self.engines.values():
                try:
                    engine.reset_showcase()
                except Exception:
                    pass
            self._track = None
            self._active_streak = 0

    # -- aggregation ---------------------------------------------------
    def _node_view(self, node_id: str, engine: Any,
                   now: float) -> Dict[str, Any]:
        """One node's evidence view (no persistence advance)."""
        try:
            snap = engine.showcase_snapshot(
                node_mode="DUAL", nodes_available=2, nodes_total=2,
                data_quality_ok=True, stale=False, derate=1.0)
        except Exception:
            snap = {"presence_state": "UNKNOWN",
                    "rf_evidence_confidence": None,
                    "confidence_calibration": "UNCALIBRATED",
                    "provenance": "UNKNOWN", "node_mode": "DUAL",
                    "evidence_statement": None, "trail": []}
        try:
            with engine._lock:  # same-thread read pattern as engine itself
                presence_label = engine.state.presence_label
                movement_label = engine.state.movement_label
                presence_prob = engine.state.presence_probability
                movement_prob = engine.state.movement_probability
                last_update = engine.state.last_update
        except Exception:
            presence_label, movement_label = "UNKNOWN", "UNKNOWN"
            presence_prob, movement_prob, last_update = None, None, None
        stale = (last_update is None
                 or (now - float(last_update)) > STALE_AFTER_S)
        score = snap.get("rf_evidence_confidence")
        # Data-quality telemetry for diagnosis + XAI (read-only counters).
        try:
            preproc = engine.preprocessor.stats.as_dict()
            preproc = {k: (dict(v) if isinstance(v, dict) else v)
                       for k, v in preproc.items()}
        except Exception:
            preproc = None
        try:
            buffered = int(len(engine.extractor._amp_buf))
        except Exception:
            buffered = None
        return {
            "node_id": node_id,
            "stale": bool(stale),
            "presence_label": (presence_label or "UNKNOWN"),
            "movement_label": (movement_label or "UNKNOWN"),
            "presence_prob": (float(presence_prob)
                              if presence_prob is not None else None),
            "movement_prob": (float(movement_prob)
                              if movement_prob is not None else None),
            "evidence_score": (float(score) if score is not None else None),
            "display_state": snap.get("presence_state", "UNKNOWN"),
            "preproc": preproc,
            "window_buffered": buffered,
        }

    def _aggregate(self, views: List[Dict[str, Any]]) -> str:
        fresh = [v for v in views if not v["stale"]]
        if not fresh:
            return "UNKNOWN"
        if any(v["presence_label"] == "PERSON" for v in fresh):
            return "POSSIBLE_PRESENCE"
        if any(v["movement_label"] == "MOVING" for v in fresh):
            return "RF_ACTIVITY"
        if all(v["presence_label"] == "EMPTY" for v in fresh):
            return "EMPTY"
        return "UNKNOWN"

    def _update_track(self, evidence: str, now: float) -> List[Dict[str, Any]]:
        """Anonymous temporary track (at most one; evidence-gated)."""
        if evidence == "POSSIBLE_PRESENCE":
            self._active_streak += 1
        else:
            self._active_streak = 0
        if (self._track is None
                and self._active_streak >= TRACK_CREATE_STREAK):
            self._track_seq += 1
            self._track = {
                "id": f"T{self._track_seq}",
                "state": "POSSIBLE_PRESENCE",
                "first_seen": now,
                "last_seen": now,
                "provenance": "RF-INFERRED",
            }
        elif self._track is not None:
            if evidence == "POSSIBLE_PRESENCE":
                self._track["last_seen"] = now
                self._track["state"] = "POSSIBLE_PRESENCE"
            elif now - float(self._track["last_seen"]) > TRACK_TIMEOUT_S:
                self._track = None
                self._active_streak = 0
        return [dict(self._track)] if self._track is not None else []

    def _spatial(self, views: List[Dict[str, Any]],
                 evidence: str) -> Dict[str, Any]:
        """Two-node zone estimate (honest degraded forms, never LOCALIZED)."""
        fresh = [v for v in views if not v["stale"]]
        if len(fresh) < 2 or evidence not in ("POSSIBLE_PRESENCE",
                                              "RF_ACTIVITY"):
            return {"level": "RF ACTIVITY", "zone": None,
                    "basis": ("single-node/degraded input: activity only, "
                              "no zone estimated")}
        scores = {v["node_id"]: v["evidence_score"] for v in fresh}
        if any(s is None for s in scores.values()):
            return {"level": "RF ACTIVITY", "zone": None,
                    "basis": "insufficient scored evidence for a zone"}
        ids = sorted(scores)
        diff = float(scores[ids[0]] - scores[ids[1]])
        if abs(diff) <= ZONE_DEAD_BAND:
            zone: Optional[str] = "BETWEEN"
        else:
            winner = ids[0] if diff > 0 else ids[1]
            zone = ("NEAR-A" if winner == "esp32-a"
                    else "NEAR-B" if winner == "esp32-b"
                    else f"NEAR-{winner}")
        return {"level": "RF ESTIMATE", "zone": zone,
                "basis": ("node evidence differential "
                          f"({ids[0]}={scores[ids[0]]:.2f}, "
                          f"{ids[1]}={scores[ids[1]]:.2f}); uncalibrated, "
                          "no metres, no position")}

    def _xai(self, evidence: str, views: List[Dict[str, Any]],
             tracks: List[Dict[str, Any]],
             spatial: Dict[str, Any]) -> Dict[str, Any]:
        """Evidence-based explanation, else XAI UNAVAILABLE."""
        if evidence in ("UNKNOWN", "EMPTY"):
            return {"status": "XAI UNAVAILABLE",
                    "statement": None}
        fresh = [v for v in views if not v["stale"]]
        agreed = [v["node_id"] for v in fresh
                  if v["presence_label"] == "PERSON"
                  or v["movement_label"] == "MOVING"]
        moving = [v["node_id"] for v in fresh
                  if v["movement_label"] == "MOVING"]
        parts = [f"aggregate evidence is {evidence}"]
        if agreed:
            parts.append(
                f"{len(agreed)}/{len(fresh)} node(s) show RF change "
                f"({', '.join(sorted(set(agreed)))})")
        if moving:
            parts.append(f"temporal movement on {', '.join(sorted(set(moving)))}")
        if self.model_kind == "sklearn":
            parts.append(f"engineering presence model "
                         f"({self.model_name}) concurs within its "
                         f"uncalibrated operating range")
        else:
            parts.append("no trained model attached; deterministic "
                         "heuristic evidence only")
        if tracks:
            parts.append(f"anonymous track {tracks[0]['id']} held from "
                         f"sustained evidence")
        if spatial.get("zone"):
            parts.append(f"zone {spatial['zone']} ({spatial['level']}) "
                         f"from node differential")
        return {"status": "AVAILABLE",
                "statement": "RF evidence increased because "
                             + "; ".join(parts) + "."}

    def snapshot(self) -> Dict[str, Any]:
        """Full vision state (JSON-safe; side-effect-free except tracks)."""
        now = self._clock()
        with self._lock:
            views = [self._node_view(nid, eng, now)
                     for nid, eng in self.engines.items()]
            evidence = self._aggregate(views)
            tracks = self._update_track(evidence, now)
            spatial = self._spatial(views, evidence)
            xai = self._xai(evidence, views, tracks, spatial)
            ml = {
                "model_name": self.model_name,
                "model_kind": self.model_kind,
                "model_status": ("ACTIVE" if self.model_kind == "sklearn"
                                 else "HEURISTIC_FALLBACK"),
                "confidence_label": "MODEL CONFIDENCE (UNCALIBRATED)",
                "classification": "engineering",
            }
            return {
                "available": True,
                "ts": now,
                "evidence": evidence,
                "nodes": views,
                "ml": ml,
                "tracks": tracks,
                "spatial": spatial,
                "xai": xai,
                "provenance": "ENGINEERING_UNCONTROLLED",
                "calibration": "UNCALIBRATED",
                "rx_operating_point": self.rx_operating_point,
            }
