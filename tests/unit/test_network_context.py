"""Unit tests: laptop active-WiFi discovery and network context.

All OS interaction uses an injected fake runner — no nmcli/iw/ip calls,
no hardware, fully offline.
"""

from csi.transport.network_context import (
    check_client_isolation,
    discover_active_network,
    network_changed,
    NetworkContext,
)


def _runner(outputs):
    def run(argv, timeout):
        key = " ".join(argv)
        for prefix, text in outputs.items():
            if key.startswith(prefix):
                return text
        return ""
    return run


def _home_outputs(freq="2412 MHz", chan="1"):
    return {
        "nmcli -t -f DEVICE,TYPE,STATE": (
            "wlp0s20f3:wifi:connected:Nihaal\n"
            "lo:loopback:unmanaged:--\n"),
        "nmcli -t -f IN-USE,SSID": (
            f"*\\:escaped:other:ssid:AA\\:BB\\:CC\\:DD\\:EE\\:FF:6:2437 MHz:"
            f"80:WPA2\n"
            f"*:Nihaal:8C\\:53\\:C3\\:5B\\:E1\\:59:{chan}:{freq}:90:WPA2\n"),
        "ip route show default":
            "default via 192.168.31.1 dev wlp0s20f3 proto dhcp metric 600\n",
        "ip -o -f inet addr show":
            "2: wlp0s20f3    inet 192.168.31.10/24 brd 192.168.31.255 "
            "scope global dynamic noprefixroute wlp0s20f3\n",
    }


def test_detects_home_2g_network():
    state, ctx, reason = discover_active_network(
        runner=_runner(_home_outputs()))
    assert state == "NETWORK_DETECTED"
    assert ctx is not None
    assert ctx.ssid == "Nihaal"
    assert ctx.bssid == "8c:53:c3:5b:e1:59"
    assert ctx.frequency_mhz == 2412
    assert ctx.band == "2.4GHz"
    assert ctx.channel == 1
    assert ctx.gateway == "192.168.31.1"
    assert ctx.subnet == "192.168.31.10/24"
    assert "2.4" in reason


def test_5ghz_network_unsupported_with_reason():
    state, ctx, reason = discover_active_network(
        runner=_runner(_home_outputs(freq="5180 MHz", chan="36")))
    assert state == "NETWORK_UNSUPPORTED"
    assert ctx is not None
    assert ctx.band == "5GHz"
    assert "2.4" in reason  # names the compatible band honestly


def test_no_active_wifi_reports_no_network():
    run = _runner({"nmcli -t -f DEVICE,TYPE,STATE":
                   "wlp0s20f3:wifi:disconnected:--\n"})
    state, ctx, reason = discover_active_network(runner=run)
    assert state == "NO_NETWORK"
    assert ctx is None
    assert reason


def test_missing_tools_report_no_network_never_guess():
    state, ctx, reason = discover_active_network(runner=_runner({}))
    assert state == "NO_NETWORK"
    assert ctx is None


def test_ssid_with_embedded_colon_parses():
    outputs = {
        "nmcli -t -f DEVICE,TYPE,STATE":
            "wlan0:wifi:connected:office\\:net\n",
        "nmcli -t -f IN-USE,SSID":
            "*:office\\:net:11\\:22\\:33\\:44\\:55\\:66:6:2437 MHz:70:WPA2\n",
        "ip route show default": "",
        "ip -o -f inet addr show": "",
    }
    state, ctx, _ = discover_active_network(runner=_runner(outputs))
    assert state == "NETWORK_DETECTED"
    assert ctx is not None
    assert ctx.ssid == "office:net"


def test_iw_fallback_when_nmcli_detail_missing():
    outputs = {
        "nmcli -t -f DEVICE,TYPE,STATE": "wlan0:wifi:connected:Fallback\n",
        "nmcli -t -f IN-USE,SSID": "",
        "iw dev wlan0 link": ("Connected to aa:bb:cc:dd:ee:ff "
                              "(on wlan0)\n\tSSID: Fallback\n"
                              "\tfreq: 2462\n"),
        "ip route show default": "",
        "ip -o -f inet addr show": "",
    }
    state, ctx, _ = discover_active_network(runner=_runner(outputs))
    assert state == "NETWORK_DETECTED"
    assert ctx is not None
    assert ctx.ssid == "Fallback"
    assert ctx.channel == 11


def test_network_changed_detects_ssid_bssid_channel():
    _, old, _ = discover_active_network(runner=_runner(_home_outputs()))
    assert old is not None
    same = NetworkContext(**{**old.__dict__})
    changed, _ = network_changed(old, same)
    assert changed is False
    moved = NetworkContext(
        **{**old.__dict__, "bssid": "aa:bb:cc:dd:ee:ff"})
    changed, reason = network_changed(old, moved)
    assert changed is True
    assert "bssid" in reason
    changed, _ = network_changed(old, None)
    assert changed is True


def test_isolation_no_ips_not_applicable():
    suspected, detail = check_client_isolation([], runner=_runner({}))
    assert suspected is False
    assert "serial" in detail


def test_isolation_suspected_when_all_neighbours_failed():
    run = _runner({"ip neigh show":
                   "192.168.31.50 dev wlp0s20f3 lladdr aa:bb:cc:dd:ee:ff "
                   "FAILED\n"})
    suspected, detail = check_client_isolation(["192.168.31.50"],
                                               runner=run)
    assert suspected is True
    assert "ESTIMATED" in detail


def test_isolation_clear_when_neighbour_live():
    run = _runner({"ip neigh show":
                   "192.168.31.50 dev wlp0s20f3 lladdr aa:bb:cc:dd:ee:ff "
                   "REACHABLE\n"})
    suspected, _ = check_client_isolation(["192.168.31.50"], runner=run)
    assert suspected is False


def test_no_password_ever_in_context():
    _, ctx, _ = discover_active_network(runner=_runner(_home_outputs()))
    assert ctx is not None
    blob = repr(ctx.__dict__)
    assert "password" not in blob.lower().replace("'", "")
