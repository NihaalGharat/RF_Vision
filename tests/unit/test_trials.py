"""Unit tests for audio-guided trial recording (no hardware)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from web.trials import (
    DEFAULT_PHASES,
    MAX_TRIAL_SECONDS,
    TrialRecorder,
    idle_payload,
)


class FakeProvider:
    def __init__(self, nid: str) -> None:
        self.node = SimpleNamespace(
            node_id=nid, board_mac=f"mac-{nid}", by_path=f"path-{nid}")
        self.port = f"/dev/{nid}"
        self.path = None
        self.max_seconds = None
        self.active = False

    def start_recording(self, path, max_seconds):
        if self.active:
            raise RuntimeError("already recording")
        self.active = True
        self.path = Path(path)
        self.max_seconds = max_seconds
        self.path.write_text(f"raw-{self.node.node_id}\n", encoding="ascii")
        return str(self.path)

    def stop_recording(self):
        self.active = False
        if self.path is None:
            return None
        data = self.path.read_bytes()
        return {"path": str(self.path), "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}


class FakeSession:
    def __init__(self) -> None:
        self.providers = {
            "esp32-a": FakeProvider("esp32-a"),
            "esp32-b": FakeProvider("esp32-b"),
        }
        self.node_ids = tuple(self.providers)

    def session_stats(self):
        return {
            "per_node": {
                nid: {
                    "signal": {"bssid": "aa:bb:cc:dd:ee:ff",
                               "channel": 6},
                }
                for nid in self.providers
            },
        }


class Clock:
    def __init__(self) -> None:
        self.value = 1000.0

    def mono(self) -> float:
        return self.value

    def wall(self) -> float:
        return 1_800_000_000.0 + self.value


def _recorder(tmp_path, clock, auto_finish=False):
    return TrialRecorder(FakeSession(), root=tmp_path,
                         monotonic=clock.mono, wall_clock=clock.wall,
                         auto_finish=auto_finish)


def test_default_plan_is_110_seconds_and_phases_are_explicit():
    assert sum(p.seconds for p in DEFAULT_PHASES) == 110
    assert [p.phase_id for p in DEFAULT_PHASES] == [
        "preparation", "empty-baseline", "enter", "stand-still",
        "move", "exit", "post-exit",
    ]
    assert MAX_TRIAL_SECONDS == 115.0


def test_idle_payload_is_honest():
    payload = idle_payload()
    assert payload["state"] == "IDLE"
    assert payload["active"] is False
    assert payload["recordings"] == []


def test_start_records_both_nodes_and_stop_preserves_partial(tmp_path):
    clock = Clock()
    rec = _recorder(tmp_path, clock)
    started = rec.start(audio_enabled=True)
    assert started["state"] == "RUNNING"
    assert started["active"] is True
    assert started["duration_s"] == 110.0
    assert started["current_phase"]["id"] == "preparation"
    assert len(started["recordings"]) == 2
    assert rec.session.providers["esp32-a"].active is True
    assert rec.session.providers["esp32-b"].active is True
    assert rec.session.providers["esp32-a"].max_seconds == 115.0

    clock.value += 35.0
    live = rec.status()
    assert live["current_phase"]["id"] == "enter"
    assert live["current_phase"]["observed_start_s"] is not None
    assert live["elapsed_s"] == 35.0

    stopped = rec.stop(reason="operator abort")
    assert stopped["state"] == "ABORTED"
    assert stopped["partial"] is True
    assert stopped["reason"] == "operator abort"
    assert rec.session.providers["esp32-a"].active is False
    assert rec.session.providers["esp32-b"].active is False
    assert all(r["sha256"] for r in stopped["recordings"])
    assert all(r["bytes"] > 0 for r in stopped["recordings"])
    for recording in stopped["recordings"]:
        raw = Path(recording["path"]).read_bytes()
        assert recording["bytes"] == len(raw)
        assert recording["sha256"] == hashlib.sha256(raw).hexdigest()
    assert rec.stop()["state"] == "ABORTED"

    meta_path = Path(stopped["metadata_path"])
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["state"] == "ABORTED"
    assert meta["partial"] is True
    assert meta["analysis_state"] == "NOT_RUN"
    assert meta["sensing_claim"] == "NONE"
    assert meta["protocol_status"] == "DEFAULT_TEMPLATE_NOT_FROZEN"
    assert [n["node_id"] for n in meta["nodes"]] == ["esp32-a", "esp32-b"]
    assert len(meta["recordings"]) == 2
    assert any(m["observed_start_s"] is not None
               for m in meta["phase_markers"][1:])


def test_start_is_refused_while_running(tmp_path):
    rec = _recorder(tmp_path, Clock())
    rec.start()
    with pytest.raises(RuntimeError):
        rec.start()


def test_custom_plan_is_validated(tmp_path):
    rec = _recorder(tmp_path, Clock())
    with pytest.raises(ValueError):
        rec.start(phases=[{"id": "a", "label": "A",
                           "instruction": "Do A", "seconds": 30},
                          {"id": "b", "label": "B",
                           "instruction": "Do B", "seconds": 30},
                          {"id": "c", "label": "C",
                           "instruction": "Do C", "seconds": 30},
                          {"id": "d", "label": "D",
                           "instruction": "Do D", "seconds": 30}])
    with pytest.raises(ValueError):
        rec.start(phases=[{"id": "a", "label": "A",
                           "instruction": "Do A", "seconds": 0}])


def test_start_without_providers_is_refused(tmp_path):
    class Empty:
        providers = {}

        def session_stats(self):
            return {}

    rec = TrialRecorder(Empty(), root=tmp_path, auto_finish=False)
    with pytest.raises(RuntimeError):
        rec.start()


def test_start_failure_releases_started_writer_and_records_failure(tmp_path):
    class FailingProvider(FakeProvider):
        def start_recording(self, path, max_seconds):
            raise RuntimeError("synthetic writer start failure")

    class FailingSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.providers["esp32-b"] = FailingProvider("esp32-b")

    rec = TrialRecorder(FailingSession(), root=tmp_path, auto_finish=False)
    with pytest.raises(RuntimeError, match="could not start"):
        rec.start()
    assert rec.status()["state"] == "START_FAILED"
    assert rec.session.providers["esp32-a"].active is False
    meta = json.loads(
        Path(rec.status()["metadata_path"]).read_text(encoding="utf-8"))
    assert meta["state"] == "START_FAILED"
    assert [r["node_id"] for r in meta["recordings"]] == ["esp32-a"]


def test_watcher_completes_at_planned_monotonic_end(tmp_path):
    import time

    rec = TrialRecorder(FakeSession(), root=tmp_path, auto_finish=True)
    started = rec.start(phases=[{
        "id": "short", "label": "Short",
        "instruction": "Short phase", "seconds": 1}])
    assert started["state"] == "RUNNING"
    deadline = time.time() + 3.0
    while rec.active and time.time() < deadline:
        time.sleep(0.02)
    done = rec.status()
    assert done["state"] == "COMPLETE"
    assert done["reason"] == "planned phase sequence elapsed"
    assert done["partial"] is False


def test_server_trial_lifecycle_and_dual_stop_preserves(monkeypatch, tmp_path):
    import web.server as server
    from web import trials as trials_api

    class StubSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.stopped = False

        def stop(self):
            self.stopped = True

    def factory(session):
        return TrialRecorder(session, root=tmp_path, auto_finish=False)

    monkeypatch.setattr(trials_api, "TrialRecorder", factory)
    old_dual, old_trial = server.DUAL, server._TRIAL
    session = StubSession()
    try:
        server.DUAL = session
        server._TRIAL = None
        monkeypatch.setattr(
            server, "trial_readiness",
            lambda: {"rf_ready": True, "state": "RF_READY",
                     "reason": "test readiness"})
        started = server.trial_start({"audio_enabled": False})
        assert started["state"] == "RUNNING"
        assert started["audio_guidance_requested"] is False
        stopped = server.dual_stop()
        assert stopped["running"] is False
        assert session.stopped is True
        assert server._TRIAL.status()["state"] == "ABORTED"
        assert server.trial_status_payload()["partial"] is True
    finally:
        server.DUAL = old_dual
        server._TRIAL = old_trial


def test_server_trial_start_refuses_without_rf_ready(monkeypatch, tmp_path):
    import web.server as server

    old_dual, old_trial = server.DUAL, server._TRIAL
    session = FakeSession()
    try:
        server.DUAL = session
        server._TRIAL = None
        monkeypatch.setattr(
            server, "trial_readiness",
            lambda: {"rf_ready": False, "state": "NETWORK_MISMATCH",
                     "reason": "node BSSID mismatch"})
        with pytest.raises(RuntimeError, match="RF READY required"):
            server.trial_start({"audio_enabled": False})
        assert server._TRIAL is None
        assert not any(p.active for p in session.providers.values())
        assert not list(tmp_path.iterdir())
    finally:
        server.DUAL = old_dual
        server._TRIAL = old_trial
