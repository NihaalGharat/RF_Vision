"""Phase 3 — approximate spatial RF evidence layer (spatial.js + pernode hold).

Runs the REAL JS modules through a Node driver (no mocks, no reimplementation).
Node resolution: $RFVISION_NODE_BIN, PATH, ~/.local/bin/node. Skipped with an
explained reason when no runtime exists — never silently passed.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = Path(__file__).with_name("spatial_evidence_driver.mjs")


def _node_bin():
    for cand in (
        os.environ.get("RFVISION_NODE_BIN"),
        shutil.which("node"),
        str(Path.home() / ".local" / "bin" / "node"),
        str(Path.home() / ".local" / "node-p3" / "bin" / "node"),
    ):
        if cand and Path(cand).exists():
            return cand
    return None


NODE = _node_bin()
needs_node = pytest.mark.skipif(
    NODE is None, reason="no Node.js runtime (RFVISION_NODE_BIN/PATH)"
)


def run_scenarios(scenarios):
    proc = subprocess.run(
        [NODE, str(DRIVER), str(REPO)],
        input=json.dumps(scenarios),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"driver failed: {proc.stderr[:2000]}"
    out = json.loads(proc.stdout)
    assert len(out) == len(scenarios)
    for r in out:
        assert "error" not in r, f"scenario {r.get('id')}: {r['error']}"
    return {r["id"]: r.get("result") for r in out}


def rep(n, v):
    return [float(v)] * n


@needs_node
def test_spatial_determinism_and_dominance():
    res = run_scenarios([
        {"id": "a1", "op": "zoneEvidence", "dA": 0.6, "dB": 0.2},
        {"id": "a2", "op": "zoneEvidence", "dA": 0.6, "dB": 0.2},
        {"id": "b", "op": "zoneEvidence", "dA": 0.15, "dB": 0.65},
        {"id": "bal", "op": "zoneEvidence", "dA": 0.4, "dB": 0.4},
        {"id": "quiet", "op": "zoneEvidence", "dA": 0, "dB": 0},
    ])
    assert res["a1"] == res["a2"]  # deterministic
    assert res["a1"]["leader"] == "nearA"
    assert res["b"]["leader"] == "nearB"
    assert res["bal"]["leader"] == "between"  # balanced response
    assert res["quiet"]["leader"] is None
    assert res["quiet"]["zones"] == {"nearA": 0, "nearB": 0, "between": 0}
    for r in res.values():
        for v in r["zones"].values():
            # JSON may round-trip integral floats as int — accept both.
            assert isinstance(v, (int, float)) and 0.0 <= v <= 1.0  # finite + bounded


@needs_node
def test_spatial_rejects_nonfinite_inputs():
    nan, inf = {"$num": "NaN"}, {"$num": "Infinity"}
    res = run_scenarios([
        {"id": "nan", "op": "zoneEvidence", "dA": nan, "dB": 0.3},
        {"id": "neg", "op": "zoneEvidence", "dA": -5, "dB": 0.3},
        {"id": "huge", "op": "zoneEvidence", "dA": inf, "dB": inf},
    ])
    # NaN/negative/non-finite sanitized to 0 — single-sided evidence or quiet,
    # still bounded; Infinity on both sides is rejected, not fabricated.
    assert res["nan"]["leader"] == "nearB"
    assert res["neg"]["leader"] == "nearB"
    assert res["huge"]["leader"] is None
    assert res["huge"]["zones"] == {"nearA": 0, "nearB": 0, "between": 0}


@needs_node
def test_frame_shape_no_metres_no_xyz():
    res = run_scenarios([
        {"id": "f", "op": "frameShape", "obs": {
            "dA": 0.5, "dB": 0.2, "freshA": True, "freshB": True, "now": 1}},
    ])
    f = res["f"]
    assert f["mode"] == "APPROXIMATE"
    assert f["frame"] == "APPROX_NORMALIZED"
    assert f["hasXYZ"] is False
    assert f["hasMetres"] is False
    assert f["hasProb"] is False
    assert set(f["keys"]) == {
        "mode", "coordinateFrame", "evidenceTier", "zones", "leader",
        "uncertainty", "sourceNodes", "timestamp", "stale"}


@needs_node
def test_tier_transitions():
    held_a = [{"dA": 0.6, "dB": 0.2, "freshA": True, "freshB": True, "now": i}
              for i in range(5)]
    flip = [{"dA": 0.6 if i % 2 == 0 else 0.2,
             "dB": 0.2 if i % 2 == 0 else 0.6,
             "freshA": True, "freshB": True, "now": i} for i in range(6)]
    res = run_scenarios([
        {"id": "held", "op": "fieldSeq", "seq": held_a},
        {"id": "flip", "op": "fieldSeq", "seq": flip},
        {"id": "one", "op": "fieldSeq", "seq": [
            {"dA": 0.6, "dB": None, "freshA": True, "freshB": False, "now": 0}]},
        {"id": "none", "op": "fieldSeq", "seq": [
            {"dA": None, "dB": None, "freshA": False, "freshB": False, "now": 0}]},
        {"id": "stale", "op": "fieldSeq", "seq": held_a[:3] + [
            {"dA": 0.6, "dB": 0.2, "freshA": True, "freshB": False, "now": 9}]},
    ])
    assert res["held"]["field"]["evidenceTier"] == "RF_ESTIMATE"
    assert res["held"]["field"]["leader"] == "nearA"
    assert res["held"]["hold"] is True
    # Ambiguous alternating direction never promotes.
    assert res["flip"]["field"]["evidenceTier"] == "RF_ACTIVITY"
    assert res["flip"]["hold"] is False
    # Single node: activity only, no fabricated differential.
    assert res["one"]["field"]["evidenceTier"] == "RF_ACTIVITY"
    assert res["one"]["field"]["zones"] == {"nearA": 0, "nearB": 0, "between": 0}
    assert res["one"]["field"]["sourceNodes"] == ["A"]
    # No nodes: no field.
    assert res["none"]["field"]["evidenceTier"] == "NO_LIVE"
    # Freshness loss downgrades a held estimate.
    assert res["stale"]["field"]["evidenceTier"] == "RF_ACTIVITY"
    assert res["stale"]["field"]["stale"] is True
    assert res["stale"]["hold"] is False


@needs_node
def test_summaries_honest_wording():
    res2 = run_scenarios([
        {"id": "s1", "op": "summary", "obs": {
            "dA": 0.6, "dB": 0.55, "freshA": True, "freshB": True, "now": 0}},
        {"id": "s2", "op": "summary", "obs": {
            "dA": None, "dB": None, "freshA": False, "freshB": False, "now": 0}},
    ])
    assert "NO LOCATION CLAIM" in res2["s1"]["summary"]
    assert res2["s1"]["tier"] == "RF_ACTIVITY"
    assert res2["s2"]["summary"] == "NO LIVE RF DATA"


@needs_node
def test_hold_freezes_baseline_but_drift_adapts():
    base = rep(62, 10.0)
    res = run_scenarios([
        {"id": "freeze", "op": "holdFreezes",
         "amps": rep(62, 14.0), "baseline": base},
    ])
    assert res["freeze"]["baselineFrozen"] is True
    assert res["freeze"]["baselineMoved"] is True
    assert res["freeze"]["disturbFinite"] is True


@needs_node
def test_persistent_event_survives_drift_adapts():
    # Persistent one-sided step: evidence must still be observable after 60
    # frames (held baseline), tier promoted to RF_ESTIMATE.
    res = run_scenarios([
        {"id": "event", "op": "holdBaseline",
         "baseA": rep(62, 10.0), "baseB": rep(62, 10.0),
         "eventA": [10.0 + (i % 62) * 0.1 + 4.0 for i in range(62)],
         "eventB": rep(62, 10.0), "frames": 60},
        # Common-mode slow drift: never holds, baseline keeps adapting.
        {"id": "drift", "op": "holdBaseline",
         "baseA": rep(62, 10.0), "baseB": rep(62, 10.0),
         "eventA": rep(62, 10.5), "eventB": rep(62, 10.5), "frames": 60},
    ])
    ev = res["event"]
    assert ev["everHold"] is True
    assert ev["finalTier"] == "RF_ESTIMATE"
    first = ev["means"][0][0]
    last = ev["means"][-1][0]
    assert last > 0.5 * first, (first, last)  # not absorbed
    dr = res["drift"]
    assert dr["everHold"] is False  # drift never freezes the baseline
