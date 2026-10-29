"""P0 — dual-session operator status projection.

Runs the REAL frontend sources.js through a Node driver. The legacy
/api/v1/stream/status contract remains the single-source fallback; the dual
projection is derived only from the authoritative /api/v1/nodes payload.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = Path(__file__).with_name("status_projection_driver.mjs")


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
    return {r["id"]: r for r in out}


def node(state="LIVE_VERIFIED", valid=100, connection="SYNCED"):
    return {
        "source_state": state,
        "valid": valid,
        "connection": connection,
    }


def nodes_payload(*entries, sync="SYNCED"):
    return {
        "available": True,
        "sync_state": sync,
        "session": {"nodes": ["A", "B"]},
        "nodes": list(entries),
    }


@needs_node
def test_healthy_dual_is_visible_as_dual_not_off():
    res = run_scenarios([{
        "id": "healthy",
        "mode": "off",
        "nodes": nodes_payload(node(), node(), sync="SYNCED"),
    }])["healthy"]
    assert res["fallback"] == "OFF"
    assert res["projection"]["state"] == "SYNCED"
    assert res["operatorLabel"] == "DUAL LIVE / SYNCED"


@needs_node
def test_starting_dual_is_pending_not_verified():
    res = run_scenarios([{
        "id": "starting",
        "mode": "off",
        "nodes": nodes_payload(sync="UNSYNCED"),
    }])["starting"]
    assert res["projection"]["state"] == "STARTING"
    assert res["operatorLabel"] == "DUAL STARTING"


@needs_node
def test_degraded_dual_is_not_reported_live():
    res = run_scenarios([{
        "id": "degraded",
        "mode": "off",
        "nodes": nodes_payload(
            node(connection="DEGRADED"),
            node(state="DISCONNECTED", valid=0, connection="DISCONNECTED"),
        ),
    }])["degraded"]
    assert res["projection"]["state"] in ("DEGRADED", "STALE")
    assert res["operatorLabel"] in ("DUAL DEGRADED", "DUAL STALE")
    assert "LIVE" not in res["operatorLabel"]


@needs_node
def test_stale_dual_is_not_reported_live():
    res = run_scenarios([{
        "id": "stale",
        "mode": "off",
        "nodes": nodes_payload(
            node(state="STALE", valid=100, connection="DEGRADED"),
            node(),
        ),
    }])["stale"]
    assert res["projection"]["state"] == "STALE"
    assert res["operatorLabel"] == "DUAL STALE"


@needs_node
def test_dual_stopped_falls_back_to_legacy_off():
    res = run_scenarios([{
        "id": "stopped",
        "mode": "off",
        "nodes": {"available": False, "nodes": [], "sync_state": "UNSYNCED"},
    }])["stopped"]
    assert res["projection"] is None
    assert res["operatorLabel"] == "OFF"


@needs_node
def test_single_source_live_is_unchanged():
    res = run_scenarios([{
        "id": "single",
        "mode": "live",
        "nodes": {"available": False, "nodes": [], "sync_state": "UNSYNCED"},
    }])["single"]
    assert res["projection"] is None
    assert res["operatorLabel"] == "LIVE"


@needs_node
def test_no_session_stays_off():
    res = run_scenarios([{
        "id": "none",
        "mode": "off",
        "nodes": None,
    }])["none"]
    assert res["projection"] is None
    assert res["operatorLabel"] == "OFF"


@needs_node
def test_network_match_requires_bssid_and_channel_provenance():
    res = run_scenarios([
        {"id": "match", "op": "networkMatch",
         "network": {"bssid": "AA:BB:CC:DD:EE:FF", "channel": 11},
         "node": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11}},
        {"id": "wrong_bssid", "op": "networkMatch",
         "network": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11},
         "node": {"bssid": "11:22:33:44:55:66", "channel": 11}},
        {"id": "wrong_channel", "op": "networkMatch",
         "network": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11},
         "node": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 1}},
        {"id": "missing_bssid", "op": "networkMatch",
         "network": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11},
         "node": {"channel": 11}},
        {"id": "missing_channel", "op": "networkMatch",
         "network": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11},
         "node": {"bssid": "aa:bb:cc:dd:ee:ff"}},
        {"id": "missing_target", "op": "networkMatch",
         "network": {"ssid": "VCET Lab"}, "node": {"bssid": "aa:bb:cc:dd:ee:ff", "channel": 11}},
    ])
    assert res["match"]["state"] == "MATCH"
    assert res["wrong_bssid"]["state"] == "MISMATCH"
    assert res["wrong_channel"]["state"] == "MISMATCH"
    assert res["missing_bssid"]["state"] == "UNKNOWN"
    assert res["missing_channel"]["state"] == "UNKNOWN"
    assert res["missing_target"]["state"] == "UNKNOWN"
