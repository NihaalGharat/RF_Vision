"""Unit tests for web/vision.py + contracts.vision_payload.

Hermetic: real VisionPipeline with stub per-node engines (no hardware,
no serial, no trained models). Time is injected via a manual clock.
"""

import threading
import time
from types import SimpleNamespace

import pytest

from web import contracts
from web.vision import VisionPipeline


def _stub_engine(presence="UNKNOWN", movement="UNKNOWN", prob=None,
                 score=None, display="UNKNOWN", last_update=None):
    state = SimpleNamespace(
        presence_label=presence, movement_label=movement,
        presence_probability=prob, movement_probability=None,
        last_update=last_update)
    snap_dict = {"presence_state": display,
                 "rf_evidence_confidence": score,
                 "confidence_calibration": "UNCALIBRATED",
                 "provenance": "RF-INFERRED" if prob is not None else "UNKNOWN",
                 "node_mode": "DUAL", "evidence_statement": None, "trail": []}
    return SimpleNamespace(
        _lock=threading.Lock(), state=state,
        _snap=snap_dict,  # same object the snapshot lambda reads
        showcase_snapshot=lambda **kw: dict(snap_dict),
        process_sample=lambda sample: None,
        reset_showcase=lambda: None,
    )


def _pipeline(now=1000.0):
    pipe = VisionPipeline.__new__(VisionPipeline)
    pipe._clock = lambda: now
    pipe._lock = threading.Lock()
    pipe.models = None
    pipe.model_name = "none (heuristic)"
    pipe.model_kind = "heuristic"
    pipe.engines = {}
    pipe._track = None
    pipe._track_seq = 0
    pipe._active_streak = 0
    pipe.started_at = now
    pipe.rx_operating_point = "ACCEPT_RX_ERRORS (engineering)"
    return pipe


def test_unknown_without_evidence():
    pipe = _pipeline()
    pipe.engines = {"esp32-a": _stub_engine(last_update=999.0),
                    "esp32-b": _stub_engine(last_update=999.0)}
    snap = pipe.snapshot()
    assert snap["evidence"] == "UNKNOWN"
    assert snap["tracks"] == []
    assert snap["xai"]["status"] == "XAI UNAVAILABLE"
    assert snap["spatial"] == {"level": "RF ACTIVITY", "zone": None,
                               "basis": snap["spatial"]["basis"]}
    assert snap["ml"]["model_status"] == "HEURISTIC_FALLBACK"
    contracts.vision_payload(available=True, vision=snap)


def test_possible_presence_and_track_creation():
    pipe = _pipeline()
    eng = _stub_engine(presence="PERSON", movement="MOVING", prob=0.8,
                       score=0.7, display="MOVING", last_update=999.5)
    pipe.engines = {"esp32-a": eng,
                    "esp32-b": _stub_engine(
                        presence="EMPTY", last_update=999.5)}
    first = pipe.snapshot()
    assert first["evidence"] == "POSSIBLE_PRESENCE"
    assert first["tracks"] == []  # streak 1: no manufacture yet
    second = pipe.snapshot()
    assert len(second["tracks"]) == 1
    assert second["tracks"][0]["id"] == "T1"
    assert second["tracks"][0]["provenance"] == "RF-INFERRED"
    contracts.vision_payload(available=True, vision=second)


def test_track_timeout():
    pipe = _pipeline()
    eng = _stub_engine(presence="PERSON", prob=0.8, score=0.7,
                       display="DETECTED", last_update=999.5)
    pipe.engines = {"esp32-a": eng,
                    "esp32-b": _stub_engine(presence="EMPTY",
                                            last_update=999.5)}
    pipe.snapshot()
    pipe.snapshot()
    assert len(pipe.snapshot()["tracks"]) == 1
    eng.state.presence_label = "EMPTY"
    eng._snap.update(presence_state="ABSENT",
                     rf_evidence_confidence=None)
    # Fresh samples (EMPTY) arriving after the track's last sighting:
    # evidence recovers to EMPTY while the track times out.
    eng.state.last_update = 1004.0
    pipe.engines["esp32-b"].state.last_update = 1004.0
    pipe._clock = lambda: 1006.0  # past TRACK_TIMEOUT_S, nodes fresh
    snap = pipe.snapshot()
    assert snap["tracks"] == []
    assert snap["evidence"] == "EMPTY"


def test_rf_activity_no_track():
    pipe = _pipeline()
    pipe.engines = {"esp32-a": _stub_engine(
        presence="EMPTY", movement="MOVING", last_update=999.5),
        "esp32-b": _stub_engine(presence="EMPTY", last_update=999.5)}
    snap = pipe.snapshot()
    assert snap["evidence"] == "RF_ACTIVITY"
    assert snap["tracks"] == []  # activity alone never manufactures
    assert snap["xai"]["status"] == "AVAILABLE"


def test_spatial_zone_never_localized():
    pipe = _pipeline()
    pipe.engines = {
        "esp32-a": _stub_engine(presence="PERSON", prob=0.9, score=0.85,
                                display="DETECTED", last_update=999.5),
        "esp32-b": _stub_engine(presence="PERSON", prob=0.6, score=0.5,
                                display="DETECTED", last_update=999.5)}
    pipe.snapshot()
    snap = pipe.snapshot()
    assert snap["spatial"]["level"] == "RF ESTIMATE"
    assert snap["spatial"]["zone"] == "NEAR-A"
    pipe.engines["esp32-b"]._snap["rf_evidence_confidence"] = 0.83
    snap2 = pipe.snapshot()
    assert snap2["spatial"]["zone"] == "BETWEEN"


def test_stale_nodes_degrade():
    pipe = _pipeline()
    pipe.engines = {"esp32-a": _stub_engine(presence="PERSON", prob=0.8,
                                            last_update=900.0),  # stale
                    "esp32-b": _stub_engine(presence="EMPTY",
                                            last_update=999.5)}
    snap = pipe.snapshot()
    assert snap["evidence"] == "EMPTY"  # stale node excluded, not trusted
    assert snap["spatial"]["level"] == "RF ACTIVITY"


def test_contract_rejects_localized_and_bad_tokens():
    with pytest.raises(contracts.ContractError):
        contracts.vision_payload(
            available=True,
            vision={"evidence": "POSSIBLE_PRESENCE",
                    "spatial": {"level": "LOCALIZED", "zone": None},
                    "xai": {"status": "AVAILABLE"}, "tracks": []})
    with pytest.raises(contracts.ContractError):
        contracts.vision_payload(
            available=True,
            vision={"evidence": "PERSON_AT_XYZ",
                    "spatial": {"level": "RF ACTIVITY", "zone": None},
                    "xai": {"status": "AVAILABLE"}, "tracks": []})
    ok = contracts.vision_payload(available=False, reason="no pipeline")
    assert ok == {"available": False, "vision": None,
                  "reason": "no pipeline"}
