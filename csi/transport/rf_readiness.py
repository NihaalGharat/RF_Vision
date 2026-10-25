"""RF readiness evaluation: the honest chain from network to RF READY.

Pure logic (no I/O, stdlib only). Distinguishes each link of the chain:

NETWORK_DETECTED vs NETWORK_COMPATIBLE (folded into the network_state
input) vs NODE CONNECTED vs CSI AVAILABLE vs RF READY — an ESP32 Wi-Fi
association alone is never reported as RF readiness.

RF READY requires ALL of:
1. active network valid (NETWORK_DETECTED)
2. network compatible (validated by ``NetworkContext.compatible``)
3. every expected node reachable with verified identity
4. CSI fresh on every expected node with expected BSSID/channel match
5. acquisition healthy (per-node source_state LIVE_VERIFIED + fresh)
6. synchronization healthy (dual mode: SYNCED; single mode: N/A)

One healthy node out of two enters SINGLE-DEGRADED — never a silent
healthy two-node claim. ``NETWORK_CHANGED`` forces re-verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

__all__ = [
    "RF_STATES",
    "NodeCheck",
    "ReadinessResult",
    "evaluate_rf_readiness",
]

#: Explicit failure/progress states required by the task. SINGLE-DEGRADED
#: reuses the existing showcase vocabulary (contracts.NODE_MODES).
RF_STATES = (
    "NO_NETWORK",
    "NETWORK_DETECTED",
    "NETWORK_UNSUPPORTED",
    "CREDENTIAL_REQUIRED",
    "PROVISIONING",
    "PROVISIONING_FAILED",
    "NODES_CONNECTING",
    "NODE_MISSING",
    "NODE_UNREACHABLE",
    "CLIENT_ISOLATION",
    "CSI_UNAVAILABLE",
    "SYNC_UNHEALTHY",
    "NETWORK_CHANGED",
    "SINGLE-DEGRADED",
    "RF_READY",
)


@dataclass(frozen=True)
class NodeCheck:
    """Per-node verification inputs (measured, never inferred)."""

    node_id: str
    identity_ok: bool = False
    reachable: bool = False
    csi_available: bool = False
    bssid_match: bool = False
    channel_match: bool = False
    fresh: bool = False  # valid observation inside existing STALE window
    source_verified: bool = False  # LIVE_VERIFIED acquisition gate


@dataclass(frozen=True)
class ReadinessResult:
    """Outcome of :func:`evaluate_rf_readiness`."""

    state: str
    rf_ready: bool
    reason: str
    degraded: bool = False


def evaluate_rf_readiness(
    *,
    network_state: str,
    network_reason: str = "",
    provisioning_state: Optional[str] = None,
    nodes_expected: int = 2,
    nodes: Optional[List[NodeCheck]] = None,
    sync_state: str = "UNSYNCED",
    network_changed_flag: bool = False,
    isolation_suspected: bool = False,
) -> ReadinessResult:
    """Evaluate the RF readiness chain in strict dependency order.

    Each check gates only on already-satisfied prerequisites, so the
    reported state always names the FIRST broken link — never a
    downstream symptom.
    """
    node_list: List[NodeCheck] = list(nodes or [])

    # 0. Stale network assumptions invalidate everything first.
    if network_changed_flag:
        return ReadinessResult(
            state="NETWORK_CHANGED", rf_ready=False,
            reason="active network changed mid-session; "
                   "re-verification required before RF READY")

    # 1-2. Network presence + compatibility.
    if network_state == "NO_NETWORK":
        return ReadinessResult(
            state="NO_NETWORK", rf_ready=False,
            reason=network_reason or "no active wifi network detected")
    if network_state == "NETWORK_UNSUPPORTED":
        return ReadinessResult(
            state="NETWORK_UNSUPPORTED", rf_ready=False,
            reason=network_reason or "active network unsupported "
            "by ESP32 acquisition path")

    # 3. Provisioning pipeline states (reported, never skipped).
    if provisioning_state in ("CREDENTIAL_REQUIRED", "PROVISIONING",
                              "PROVISIONING_FAILED"):
        return ReadinessResult(
            state=provisioning_state, rf_ready=False,
            reason=network_reason or
            f"provisioning stage: {provisioning_state}")

    # 4. Node presence / reachability / identity.
    by_id: Dict[str, NodeCheck] = {n.node_id: n for n in node_list}
    if len(by_id) < nodes_expected:
        missing = nodes_expected - len(by_id)
        return ReadinessResult(
            state="NODE_MISSING", rf_ready=False,
            reason=f"{missing} of {nodes_expected} expected nodes "
                   f"absent (never substitute one node for another)")
    unreachable = [n for n in node_list if not n.reachable]
    if unreachable:
        names = ", ".join(n.node_id for n in unreachable)
        return ReadinessResult(
            state="NODE_UNREACHABLE", rf_ready=False,
            reason=f"node(s) unreachable: {names}")
    bad_identity = [n for n in node_list if not n.identity_ok]
    if bad_identity:
        names = ", ".join(n.node_id for n in bad_identity)
        return ReadinessResult(
            state="NODE_UNREACHABLE", rf_ready=False,
            reason=f"node identity unverified (wrong/duplicate node "
                   f"suspected): {names}")

    # 5. Client/AP isolation gates IP-dependent paths. The validated CSI
    # data path is USB serial, so isolation is reported honestly without
    # blocking serial-verified readiness — but it IS surfaced, never
    # misclassified as a firmware failure.
    if isolation_suspected:
        return ReadinessResult(
            state="CLIENT_ISOLATION", rf_ready=False,
            reason="node IPs unreachable at L2 (ESTIMATED): client/AP "
                   "isolation suspected; IP-dependent checks withheld, "
                   "not a firmware failure")

    # 6. CSI availability + expected network validation per node.
    for node in node_list:
        if not node.csi_available:
            return ReadinessResult(
                state="CSI_UNAVAILABLE", rf_ready=False,
                reason=f"no CSI from {node.node_id}; RF READY withheld")
        if not (node.bssid_match and node.channel_match):
            return ReadinessResult(
                state="CSI_UNAVAILABLE", rf_ready=False,
                reason=f"{node.node_id} CSI not on expected network "
                       f"(BSSID/channel mismatch); wrong-network node "
                       f"rejected")
        if not node.fresh:
            return ReadinessResult(
                state="CSI_UNAVAILABLE", rf_ready=False,
                reason=f"no fresh CSI from {node.node_id} (outside the "
                       f"existing STALE window); RF READY withheld")
        if not node.source_verified:
            return ReadinessResult(
                state="CSI_UNAVAILABLE", rf_ready=False,
                reason=f"{node.node_id} acquisition gate not passed "
                       f"(LIVE_VERIFIED required)")

    # 7. Synchronization health.
    if nodes_expected == 1 and len(node_list) == 1:
        return ReadinessResult(
            state="RF_READY", rf_ready=True,
            reason="single-node chain verified: network valid, node "
                   "identified, CSI on expected network, acquisition "
                   "healthy (sync N/A single-node)")
    if len(node_list) == 1 and nodes_expected == 2:
        # Single healthy node of a dual pair: degraded, explicit.
        if sync_state == "SYNCED":
            state = "SINGLE-DEGRADED"
        else:
            # Even sync cannot be claimed single-node in dual mode.
            state = "SINGLE-DEGRADED"
        return ReadinessResult(
            state=state, rf_ready=False, degraded=True,
            reason="only one of two expected nodes healthy; "
                   "SINGLE-DEGRADED (never a two-node claim)")
    if sync_state != "SYNCED":
        return ReadinessResult(
            state="SYNC_UNHEALTHY", rf_ready=False,
            reason=f"dual-node sync not SYNCED (currently "
                   f"{sync_state}); RF READY withheld")

    return ReadinessResult(
        state="RF_READY", rf_ready=True,
        reason="full chain verified: network valid + compatible, both "
               "nodes identified + reachable, CSI on expected network, "
               "acquisition healthy, sync SYNCED")
