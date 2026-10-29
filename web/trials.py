"""Audio-guided trial recording over an attached dual-node session.

The recorder reuses each node's existing lossless ``LiveProvider`` recording
path. It never parses CSI, infers presence, or rewrites captured lines: it only
synchronizes an operator-facing phase plan, starts/stops both raw recordings,
and writes a sidecar with monotonic phase markers and checksums.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from web.source import LiveProvider

__all__ = [
    "DEFAULT_PHASES",
    "MAX_TRIAL_SECONDS",
    "PROTOCOL_ID",
    "Phase",
    "TrialRecorder",
    "idle_payload",
]

PROTOCOL_ID = "RFVISION-WEB-AUDIO-TRIAL-v1"
MAX_TRIAL_SECONDS = 115.0


@dataclass(frozen=True)
class Phase:
    phase_id: str
    label: str
    instruction: str
    seconds: float

    def as_dict(self) -> Dict[str, Any]:
        return {"id": self.phase_id, "label": self.label,
                "instruction": self.instruction,
                "seconds": float(self.seconds)}


DEFAULT_PHASES: tuple[Phase, ...] = (
    Phase("preparation", "Preparation",
          "Prepare the area. Remain clear of the RF path.", 10),
    Phase("empty-baseline", "Empty baseline",
          "Empty baseline. Leave the area now.", 20),
    Phase("enter", "Enter and settle",
          "Enter the area and move to the marked position.", 10),
    Phase("stand-still", "Stand still",
          "Stand still. Keep your position and posture.", 20),
    Phase("move", "Move naturally",
          "Move naturally within the marked area.", 20),
    Phase("exit", "Exit the area",
          "Exit the area now.", 10),
    Phase("post-exit", "Post-exit baseline",
          "Post-exit baseline. Remain outside the area.", 20),
)


def _utc(ts: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _normalise_phases(phases: Optional[Sequence[Any]]) -> List[Dict[str, Any]]:
    if phases is None:
        return [p.as_dict() for p in DEFAULT_PHASES]
    if not isinstance(phases, (list, tuple)) or not phases:
        raise ValueError("phases must be a non-empty list")
    out: List[Dict[str, Any]] = []
    seen = set()
    for raw in phases:
        if not isinstance(raw, dict):
            raise ValueError("each phase must be an object")
        phase_id = str(raw.get("id", "")).strip()
        label = str(raw.get("label", phase_id)).strip()
        instruction = str(raw.get("instruction", label)).strip()
        try:
            seconds = float(raw.get("seconds"))
        except (TypeError, ValueError) as exc:
            raise ValueError("phase seconds must be numeric") from exc
        if not phase_id or phase_id in seen:
            raise ValueError("phase ids must be present and unique")
        if not label or not instruction or len(instruction) > 240:
            raise ValueError("phase label/instruction invalid")
        if not 1.0 <= seconds <= 60.0:
            raise ValueError("each phase must be 1..60 seconds")
        seen.add(phase_id)
        out.append({"id": phase_id, "label": label,
                    "instruction": instruction, "seconds": seconds})
    total = sum(p["seconds"] for p in out)
    if total > MAX_TRIAL_SECONDS:
        raise ValueError(
            f"trial duration {total:g}s exceeds {MAX_TRIAL_SECONDS:g}s")
    return out


def idle_payload() -> Dict[str, Any]:
    return {
        "state": "IDLE", "active": False, "trial_id": None,
        "elapsed_s": 0.0, "remaining_s": None, "duration_s": None,
        "current_phase": None, "phases": [], "recordings": [],
        "metadata_path": None, "partial": False, "reason": None,
    }


class TrialRecorder:
    """One timed trial over both providers of a started dual session."""

    def __init__(self, session: Any, root: Optional[Path] = None,
                 monotonic=time.monotonic, wall_clock=time.time,
                 sleep=time.sleep, auto_finish: bool = True) -> None:
        self.session = session
        self.root = Path(root) if root is not None else (
            Path.cwd() / "research-data" / "web-trials")
        self._monotonic = monotonic
        self._wall = wall_clock
        self._sleep = sleep
        self._auto_finish = bool(auto_finish)
        self._lock = threading.Lock()
        self._state = "IDLE"
        self._trial_id: Optional[str] = None
        self._dir: Optional[Path] = None
        self._metadata_path: Optional[Path] = None
        self._start_mono: Optional[float] = None
        self._end_mono: Optional[float] = None
        self._start_wall: Optional[float] = None
        self._end_wall: Optional[float] = None
        self._phases: List[Dict[str, Any]] = []
        self._phase_index = 0
        self._recordings: List[Dict[str, Any]] = []
        self._nodes: List[Dict[str, Any]] = []
        self._reason: Optional[str] = None
        self._audio_enabled = False
        self._thread: Optional[threading.Thread] = None

    @property
    def active(self) -> bool:
        with self._lock:
            return self._state == "RUNNING"

    def start(self, phases: Optional[Sequence[Any]] = None,
              audio_enabled: bool = True) -> Dict[str, Any]:
        with self._lock:
            if self._state == "RUNNING":
                raise RuntimeError("trial already running")
            providers = getattr(self.session, "providers", None) or {}
            if not providers:
                raise RuntimeError("dual session has no providers")
            plan = _normalise_phases(phases)
            total = sum(p["seconds"] for p in plan)
            now_wall = float(self._wall())
            trial_id = "WT-" + time.strftime(
                "%Y%m%dT%H%M%SZ", time.gmtime(now_wall))
            self.root.mkdir(parents=True, exist_ok=True)
            base = trial_id
            suffix = 2
            while (self.root / trial_id).exists():
                trial_id = f"{base}-{suffix}"
                suffix += 1
            trial_dir = self.root / trial_id
            trial_dir.mkdir(parents=True, exist_ok=False)
            self._trial_id = trial_id
            self._dir = trial_dir
            self._metadata_path = trial_dir / "trial_meta.json"
            self._phases = [
                {**phase, "planned_start_s": start,
                 "planned_end_s": start + phase["seconds"],
                 "observed_start_s": (0.0 if idx == 0 else None)}
                for idx, phase in enumerate(plan)
                for start in [sum(p["seconds"] for p in plan[:idx])]
            ]
            self._phase_index = 0
            self._recordings = []
            self._nodes = self._capture_nodes(providers)
            self._reason = None
            self._audio_enabled = bool(audio_enabled)
            self._start_mono = float(self._monotonic())
            self._start_wall = now_wall
            self._end_mono = None
            self._end_wall = None
            started: List[Any] = []
            try:
                for nid, provider in providers.items():
                    target = trial_dir / f"{trial_id}_node-{nid.replace('esp32-', '')}_raw.bin"
                    provider.start_recording(
                        target,
                        max_seconds=min(total + 5.0,
                                        LiveProvider.REC_MAX_SECONDS))
                    started.append(provider)
                    self._recordings.append({
                        "node_id": nid, "path": str(target),
                        "bytes": 0, "sha256": None})
            except Exception:
                recorded = {r["node_id"]: r for r in self._recordings}
                for provider in started:
                    try:
                        info = provider.stop_recording()
                    except Exception:
                        info = None
                    nid = getattr(getattr(provider, "node", None),
                                  "node_id", None)
                    if info and nid and nid in recorded:
                        recorded[nid].update({
                            "path": info.get("path"),
                            "bytes": info.get("bytes"),
                            "sha256": info.get("sha256"),
                        })
                self._recordings = list(recorded.values())
                self._state = "START_FAILED"
                self._reason = "recording could not start on every node"
                self._write_metadata_locked()
                raise RuntimeError(self._reason)
            self._state = "RUNNING"
            self._write_metadata_locked()
            if self._auto_finish:
                self._thread = threading.Thread(
                    target=self._watch, daemon=True,
                    name=f"trial-watch-{trial_id}")
                self._thread.start()
            return self._status_locked()

    def stop(self, reason: str = "operator stopped the trial") -> Dict[str, Any]:
        with self._lock:
            if self._state != "RUNNING":
                return self._status_locked()
            return self._finalise_locked("ABORTED", reason)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            if self._state == "RUNNING":
                self._update_phase_locked()
            return self._status_locked()

    def _capture_nodes(self, providers: Dict[str, Any]) -> List[Dict[str, Any]]:
        stats: Dict[str, Any] = {}
        try:
            stats = self.session.session_stats().get("per_node", {})
        except Exception:
            pass
        nodes: List[Dict[str, Any]] = []
        for nid, provider in providers.items():
            node = getattr(provider, "node", None)
            stat = stats.get(nid, {}) if isinstance(stats, dict) else {}
            signal = stat.get("signal", {}) if isinstance(stat, dict) else {}
            stream = stat.get("stream", {}) if isinstance(stat, dict) else {}
            nodes.append({
                "node_id": nid,
                "board_mac": getattr(node, "board_mac", None),
                "by_path": getattr(node, "by_path", None),
                "port": getattr(provider, "port", None),
                "source_state": stat.get("source_state"),
                "valid": stream.get("valid"),
                "fresh": (not bool(stream.get("stale"))
                          if isinstance(stream, dict) else None),
                "bssid": signal.get("bssid"),
                "channel": signal.get("channel"),
            })
        return nodes

    def _elapsed_locked(self) -> float:
        if self._start_mono is None:
            return 0.0
        end = self._end_mono if self._end_mono is not None else float(
            self._monotonic())
        return max(0.0, end - self._start_mono)

    def _update_phase_locked(self) -> None:
        if not self._phases:
            return
        elapsed = self._elapsed_locked()
        idx = len(self._phases) - 1
        for pos, phase in enumerate(self._phases):
            if elapsed < phase["planned_end_s"]:
                idx = pos
                break
        if idx > self._phase_index:
            for pos in range(self._phase_index + 1, idx + 1):
                if self._phases[pos]["observed_start_s"] is None:
                    self._phases[pos]["observed_start_s"] = elapsed
            self._phase_index = idx
            self._write_metadata_locked()
        elif idx < self._phase_index:
            self._phase_index = idx

    def _watch(self) -> None:
        while True:
            with self._lock:
                if self._state != "RUNNING":
                    return
                self._update_phase_locked()
                total = (self._phases[-1]["planned_end_s"]
                         if self._phases else 0.0)
                if self._elapsed_locked() >= total:
                    self._finalise_locked(
                        "COMPLETE", "planned phase sequence elapsed")
                    return
            self._sleep(0.05)

    def _finalise_locked(self, state: str, reason: str) -> Dict[str, Any]:
        self._update_phase_locked()
        self._state = state
        self._reason = reason
        self._end_mono = float(self._monotonic())
        self._end_wall = float(self._wall())
        recorded = {r["node_id"]: r for r in self._recordings}
        providers = getattr(self.session, "providers", None) or {}
        for nid, provider in providers.items():
            try:
                info = provider.stop_recording()
            except Exception:
                info = None
            entry = recorded.setdefault(
                nid, {"node_id": nid, "path": None, "bytes": 0,
                      "sha256": None})
            if info:
                entry.update({"path": info.get("path"),
                              "bytes": info.get("bytes"),
                              "sha256": info.get("sha256")})
        self._recordings = list(recorded.values())
        self._write_metadata_locked()
        return self._status_locked()

    def _status_locked(self) -> Dict[str, Any]:
        if self._state == "IDLE":
            return idle_payload()
        elapsed = self._elapsed_locked()
        total = (self._phases[-1]["planned_end_s"]
                 if self._phases else 0.0)
        current = None
        if self._phases:
            phase = self._phases[self._phase_index]
            current = {
                **phase,
                "phase_elapsed_s": max(
                    0.0, elapsed - phase["planned_start_s"]),
                "phase_remaining_s": max(
                    0.0, phase["planned_end_s"] - elapsed),
            }
        return {
            "state": self._state,
            "active": self._state == "RUNNING",
            "trial_id": self._trial_id,
            "elapsed_s": round(elapsed, 3),
            "remaining_s": round(max(0.0, total - elapsed), 3),
            "duration_s": round(total, 3),
            "current_phase": current,
            "phases": [dict(p) for p in self._phases],
            "recordings": [dict(r) for r in self._recordings],
            "metadata_path": (str(self._metadata_path)
                              if self._metadata_path else None),
            "partial": self._state == "ABORTED",
            "reason": self._reason,
            "audio_guidance_requested": self._audio_enabled,
            "analysis_state": "NOT_RUN",
            "sensing_claim": "NONE",
        }

    def _metadata_locked(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "experiment_id": "RFVISION-WEB-TRIAL",
            "protocol_id": PROTOCOL_ID,
            "protocol_status": "DEFAULT_TEMPLATE_NOT_FROZEN",
            "trial_id": self._trial_id,
            "state": self._state,
            "started_utc": (_utc(self._start_wall)
                            if self._start_wall is not None else None),
            "ended_utc": (_utc(self._end_wall)
                          if self._end_wall is not None else None),
            "elapsed_mono_s": round(self._elapsed_locked(), 3),
            "planned_duration_s": (
                self._phases[-1]["planned_end_s"] if self._phases else None),
            "phase_markers": [dict(p) for p in self._phases],
            "nodes": [dict(n) for n in self._nodes],
            "recordings": [dict(r) for r in self._recordings],
            "audio_guidance_requested": self._audio_enabled,
            "partial": self._state == "ABORTED",
            "analysis_state": "NOT_RUN",
            "sensing_claim": "NONE",
            "reason": self._reason,
        }

    def _write_metadata_locked(self) -> None:
        if self._metadata_path is None:
            return
        tmp = self._metadata_path.with_suffix(".json.tmp")
        payload = self._metadata_locked()
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True),
                       encoding="utf-8")
        os.replace(tmp, self._metadata_path)
