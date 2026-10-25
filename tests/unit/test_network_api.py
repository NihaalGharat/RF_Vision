"""Unit tests: web unknown-WiFi integration (no hardware, no sockets)."""

import pytest

from csi.transport.network_context import NetworkContext
from web import network as network_api


def _ctx(**over):
    base = dict(interface="wlan0", ssid="Cafe Net",
                bssid="aa:bb:cc:dd:ee:ff", channel=6,
                frequency_mhz=2437, band="2.4GHz", gateway="192.168.1.1",
                subnet="192.168.1.20/24", discovered_at=1.0,
                source="test")
    base.update(over)
    return NetworkContext(**base)


def _discover(state="NETWORK_DETECTED", ctx=None, reason="ok"):
    def run():
        return (state, ctx if ctx is not None else _ctx(), reason)
    return run


def _dual_info(bssid="aa:bb:cc:dd:ee:ff", channel=6, valid=10,
               source_state="LIVE_VERIFIED", sync="SYNCED", stale=False):
    def node(nid):
        return {"node_id": nid, "board_mac": "b0:3f:d3:70:20:3c",
                "port": "/dev/ttyUSB0", "source_state": source_state,
                "stream": {"valid": valid, "rate_hz": 75.0,
                           "stale": stale},
                "signal": {"bssid": bssid, "channel": channel},
                "timing": {}, "sync": {"ready": sync == "SYNCED"}}
    return {"nodes": ("esp32-a", "esp32-b"), "elapsed_s": 5.0,
            "per_node": {"esp32-a": node("esp32-a"),
                         "esp32-b": node("esp32-b")},
            "sync": {"state": sync}}


class FakePort:
    def __init__(self, script):
        self._script = list(script)
        self._queue: list = []
        self.sent: list = []
        self.opened = False

    def open(self):
        self.opened = True

    def write_line(self, line):
        self.sent.append(line)
        for expect, replies in self._script:
            if line == expect:
                self._queue.extend(replies)
                return

    def read_line(self, timeout):
        return self._queue.pop(0) if self._queue else None

    def close(self):
        self.opened = False


def _happy_script():
    return [
        ("RFV_PROV_BEGIN", ["RFV_OK BEGIN"]),
        ("RFV_SSID:Cafe Net", ["RFV_OK SSID"]),
        ("RFV_PASS:pw123", ["RFV_OK PASS"]),
        ("RFV_PROV_COMMIT", ["RFV_OK STORED", "RFV_OK CONNECTED",
                             "RFV_NET ssid=Cafe Net "
                             "bssid=aa:bb:cc:dd:ee:ff channel=6 "
                             "ip=192.168.1.50"]),
    ]


def test_network_payload_has_no_password_fields():
    payload = network_api.network_status_payload(
        discover=_discover(ctx=_ctx()))
    assert payload["state"] == "NETWORK_DETECTED"
    blob = repr(payload).lower()
    assert "password" not in blob and "pass" not in blob.replace(
        "payload", "").replace("bypass", "")
    assert payload["network"]["ssid"] == "Cafe Net"


def test_readiness_ready_when_chain_verified(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    payload = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()), dual_info=_dual_info())
    assert payload["state"] == "RF_READY"
    assert payload["rf_ready"] is True


def test_readiness_rejects_wrong_network_nodes(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    payload = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()),
        dual_info=_dual_info(bssid="ff:ee:dd:cc:bb:aa"))
    assert payload["state"] == "CSI_UNAVAILABLE"
    assert payload["rf_ready"] is False


def test_readiness_stale_nodes_never_reach_rf_ready(monkeypatch):
    for stale in ("esp32-a", "esp32-b", "both"):
        monkeypatch.setattr(network_api, "_last_network", None)
        info = _dual_info()
        if stale in ("esp32-a", "both"):
            info["per_node"]["esp32-a"]["stream"]["stale"] = True
        if stale in ("esp32-b", "both"):
            info["per_node"]["esp32-b"]["stream"]["stale"] = True
        payload = network_api.rf_readiness_payload(
            discover=_discover(ctx=_ctx()), dual_info=info)
        assert payload["state"] == "CSI_UNAVAILABLE"
        assert payload["rf_ready"] is False
        assert "fresh" in payload["reason"]


def test_readiness_no_valid_observations_withhold_ready(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    info = _dual_info(valid=0)
    payload = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()), dual_info=info)
    assert payload["state"] == "CSI_UNAVAILABLE"
    assert payload["rf_ready"] is False


def test_readiness_recovers_after_fresh_data_returns(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    info = _dual_info(stale=True)
    stale = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()), dual_info=info)
    assert stale["rf_ready"] is False
    info["per_node"]["esp32-a"]["stream"]["stale"] = False
    info["per_node"]["esp32-b"]["stream"]["stale"] = False
    fresh = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()), dual_info=info)
    assert fresh["state"] == "RF_READY"
    assert fresh["rf_ready"] is True


def test_readiness_no_session_reports_missing(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    payload = network_api.rf_readiness_payload(
        discover=_discover(ctx=_ctx()), dual_info=None)
    assert payload["state"] == "NODE_MISSING"
    assert payload["rf_ready"] is False


def test_readiness_no_network(monkeypatch):
    monkeypatch.setattr(network_api, "_last_network", None)
    payload = network_api.rf_readiness_payload(
        discover=_discover(state="NO_NETWORK", ctx=None,
                           reason="no wifi"))
    assert payload["state"] == "NO_NETWORK"
    assert payload["rf_ready"] is False


def test_provision_happy_path_password_safe(monkeypatch):
    ports = {}

    def factory(device):
        ports[device] = FakePort(_happy_script())
        return ports[device]

    import csi.transport.nodes as nodes_mod
    monkeypatch.setattr(
        network_api, "all_nodes_resolved",
        lambda: {"esp32-a": "/dev/ttyUSB0", "esp32-b": "/dev/ttyUSB1"})
    out = network_api.provision_nodes(
        "Cafe Net", "pw123", node_ids=["esp32-a"],
        port_factory=factory)
    assert out["state"] == "NODES_CONNECTING"
    assert "pw123" not in repr(out)
    # secret actually travelled the wire (functionally provisioned)
    assert "RFV_PASS:pw123" in ports["/dev/ttyUSB0"].sent


def test_provision_rejects_unknown_nodes():
    with pytest.raises(ValueError):
        network_api.provision_nodes("ssid", "pw", node_ids=["esp32-z"])


def test_provision_rejects_bad_credentials():
    with pytest.raises(Exception):
        network_api.provision_nodes("", "pw",
                                    node_ids=["esp32-a"])


def test_provision_failure_never_echoes_password(monkeypatch):
    def factory(device):
        return FakePort([])  # silent node

    monkeypatch.setattr(
        network_api, "all_nodes_resolved",
        lambda: {"esp32-a": "/dev/ttyUSB0"})
    out = network_api.provision_nodes(
        "Cafe Net", "pw123", node_ids=["esp32-a"], timeout_s=0.05,
        port_factory=factory)
    assert out["state"] == "PROVISIONING_FAILED"
    assert "pw123" not in repr(out)


def test_server_routes_registered():
    import web.server as server
    src = open(server.__file__).read()
    assert "/api/v1/network" in src
    assert "/api/v1/network/provision" in src
    assert "/api/v1/rf_readiness" in src
    # existing routes untouched
    assert "/api/v1/nodes" in src and "/api/v1/source" in src
    # contract version untouched
    from web import contracts
    assert contracts.CONTRACT_VERSION == 3
