"""Unit tests: RF readiness chain evaluation (pure logic, no I/O)."""

from csi.transport.rf_readiness import (
    NodeCheck,
    RF_STATES,
    evaluate_rf_readiness,
)


def _good_node(node_id="esp32-a"):
    return NodeCheck(node_id=node_id, identity_ok=True, reachable=True,
                     csi_available=True, bssid_match=True,
                     channel_match=True, source_verified=True)


def test_states_vocabulary_complete():
    for required in ("NO_NETWORK", "NETWORK_DETECTED",
                     "NETWORK_UNSUPPORTED", "CREDENTIAL_REQUIRED",
                     "PROVISIONING", "PROVISIONING_FAILED",
                     "NODES_CONNECTING", "NODE_MISSING", "NODE_UNREACHABLE",
                     "CLIENT_ISOLATION", "CSI_UNAVAILABLE", "SYNC_UNHEALTHY",
                     "NETWORK_CHANGED", "RF_READY"):
        assert required in RF_STATES


def test_full_dual_chain_reports_rf_ready():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED",
        nodes_expected=2, nodes=[_good_node("esp32-a"),
                                 _good_node("esp32-b")],
        sync_state="SYNCED")
    assert res.state == "RF_READY"
    assert res.rf_ready is True
    assert res.degraded is False


def test_association_alone_never_rf_ready():
    # Nodes reachable but no CSI: must NOT be ready.
    nodes = [NodeCheck(node_id="esp32-a", identity_ok=True, reachable=True),
             NodeCheck(node_id="esp32-b", identity_ok=True, reachable=True)]
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2, nodes=nodes,
        sync_state="SYNCED")
    assert res.state == "CSI_UNAVAILABLE"
    assert res.rf_ready is False


def test_unsupported_network_blocks_everything():
    res = evaluate_rf_readiness(
        network_state="NETWORK_UNSUPPORTED",
        network_reason="band 5GHz unsupported",
        nodes_expected=2, nodes=[_good_node("esp32-a"),
                                 _good_node("esp32-b")],
        sync_state="SYNCED")
    assert res.state == "NETWORK_UNSUPPORTED"
    assert res.rf_ready is False


def test_no_network_blocks():
    res = evaluate_rf_readiness(network_state="NO_NETWORK",
                                network_reason="no active wifi")
    assert res.state == "NO_NETWORK"
    assert res.rf_ready is False


def test_provisioning_states_reported_not_skipped():
    for stage in ("CREDENTIAL_REQUIRED", "PROVISIONING",
                  "PROVISIONING_FAILED"):
        res = evaluate_rf_readiness(
            network_state="NETWORK_DETECTED", provisioning_state=stage)
        assert res.state == stage
        assert res.rf_ready is False


def test_missing_node_never_substituted():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2,
        nodes=[_good_node("esp32-a")], sync_state="SYNCED")
    assert res.state == "NODE_MISSING"
    assert res.rf_ready is False


def test_wrong_identity_rejected():
    nodes = [_good_node("esp32-a"),
             NodeCheck(node_id="esp32-b", reachable=True)]  # identity bad
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2, nodes=nodes,
        sync_state="SYNCED")
    assert res.state == "NODE_UNREACHABLE"
    assert "identity" in res.reason
    assert res.rf_ready is False


def test_wrong_network_csi_rejected():
    nodes = [_good_node("esp32-a"),
             NodeCheck(node_id="esp32-b", identity_ok=True, reachable=True,
                       csi_available=True, bssid_match=False,
                       channel_match=True, source_verified=True)]
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2, nodes=nodes,
        sync_state="SYNCED")
    assert res.state == "CSI_UNAVAILABLE"
    assert "mismatch" in res.reason
    assert res.rf_ready is False


def test_unhealthy_sync_withholds_ready():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2,
        nodes=[_good_node("esp32-a"), _good_node("esp32-b")],
        sync_state="SYNCING")
    assert res.state == "SYNC_UNHEALTHY"
    assert res.rf_ready is False


def test_single_healthy_node_of_pair_is_degraded_not_ready():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2,
        nodes=[_good_node("esp32-a")],
        sync_state="UNSYNCED")
    # Only one node resolved of two expected -> NODE_MISSING grade first.
    assert res.rf_ready is False
    assert res.state in ("NODE_MISSING", "SINGLE-DEGRADED")


def test_single_node_mode_ready_without_sync():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=1,
        nodes=[_good_node("esp32-a")], sync_state="UNSYNCED")
    assert res.state == "RF_READY"
    assert res.rf_ready is True


def test_network_change_forces_reverification():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2,
        nodes=[_good_node("esp32-a"), _good_node("esp32-b")],
        sync_state="SYNCED", network_changed_flag=True)
    assert res.state == "NETWORK_CHANGED"
    assert res.rf_ready is False


def test_isolation_surfaced_not_firmware_blame():
    res = evaluate_rf_readiness(
        network_state="NETWORK_DETECTED", nodes_expected=2,
        nodes=[_good_node("esp32-a"), _good_node("esp32-b")],
        sync_state="SYNCED", isolation_suspected=True)
    assert res.state == "CLIENT_ISOLATION"
    assert "firmware failure" in res.reason
    assert res.rf_ready is False
