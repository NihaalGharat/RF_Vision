"""Unit tests: serial provisioning exchange + credential non-exposure.

Fake serial only — no hardware, no ports opened.
"""

import pytest

from csi.transport.provisioning import (
    Credentials,
    CredentialsError,
    ProvisioningError,
    ProvisioningSession,
    parse_response,
    parse_status_line,
    redact,
)

SECRET = "s3cr3t-p@ss w0rd"


class FakeSerial:
    """Scripted node: maps received lines to canned response lines."""

    def __init__(self, script):
        self.script = list(script)
        self.sent: list = []
        self._queue: list = []

    def write_line(self, line):
        self.sent.append(line)
        for expect, replies in self.script:
            if line == expect:
                self._queue.extend(replies)
                return
        self._queue.append("RFV_ERR unknown-command")

    def read_line(self, timeout):
        if self._queue:
            return self._queue.pop(0)
        return None


def _happy_script():
    return [
        ("RFV_PROV_BEGIN", ["RFV_OK BEGIN"]),
        ("RFV_SSID:Cafe Net", ["RFV_OK SSID"]),
        (f"RFV_PASS:{SECRET}", ["RFV_OK PASS"]),
        ("RFV_PROV_COMMIT", ["RFV_OK STORED", "RFV_OK CONNECTED",
                             "RFV_NET ssid=Cafe Net "
                             "bssid=aa:bb:cc:dd:ee:ff channel=6 "
                             "ip=192.168.1.50"]),
    ]


def test_happy_path_provisions_node():
    serial = FakeSerial(_happy_script())
    session = ProvisioningSession(["esp32-a"])
    creds = Credentials("Cafe Net", SECRET)
    try:
        res = session.provision_node(
            "esp32-a", creds, serial.write_line, serial.read_line)
    finally:
        creds.clear()
    assert res.state == "PROVISIONED"
    assert res.status["bssid"] == "aa:bb:cc:dd:ee:ff"
    assert res.status["channel"] == "6"
    assert res.status["ip"] == "192.168.1.50"
    assert SECRET not in res.reason


def test_credential_validation_rejects_bad_input():
    with pytest.raises(CredentialsError):
        Credentials("", SECRET)
    with pytest.raises(CredentialsError):
        Credentials("x" * 33, SECRET)
    with pytest.raises(CredentialsError):
        Credentials("ok", "p" * 65)
    with pytest.raises(CredentialsError):
        Credentials("has\nnewline", SECRET)


def test_repr_never_exposes_password():
    creds = Credentials("Cafe Net", SECRET)
    assert SECRET not in repr(creds)
    assert SECRET not in str(creds)
    creds.clear()


def test_node_rejection_surfaces_without_secret():
    serial = FakeSerial([("RFV_PROV_BEGIN", ["RFV_ERR bad-state"])])
    session = ProvisioningSession(["esp32-a"])
    creds = Credentials("Cafe Net", SECRET)
    try:
        res = session.provision_node(
            "esp32-a", creds, serial.write_line, serial.read_line)
    finally:
        creds.clear()
    assert res.state == "PROVISIONING_FAILED"
    assert SECRET not in res.reason


def test_silent_node_times_out_without_secret():
    serial = FakeSerial([])
    # override: node never answers anything
    serial._queue = []
    serial.script = []
    session = ProvisioningSession(["esp32-a"])
    creds = Credentials("Cafe Net", SECRET)
    try:
        res = session.provision_node(
            "esp32-a", creds, serial.write_line, serial.read_line,
            timeout_s=0.05)
    finally:
        creds.clear()
    assert res.state == "PROVISIONING_FAILED"
    assert SECRET not in res.reason


def test_interleaved_csi_lines_skipped_not_fatal():
    script = [
        ("RFV_PROV_BEGIN", ["CSI_DATA,1,aa,1,2,3", "RFV_OK BEGIN"]),
        ("RFV_SSID:Cafe Net", ["RFV_OK SSID"]),
        (f"RFV_PASS:{SECRET}", ["RFV_OK PASS"]),
        ("RFV_PROV_COMMIT", ["RFV_OK STORED",
                             "RFV_NET ssid=Cafe Net "
                             "bssid=aa:bb:cc:dd:ee:ff channel=6 "
                             "ip=192.168.1.50"]),
    ]
    serial = FakeSerial(script)
    session = ProvisioningSession(["esp32-a"])
    creds = Credentials("Cafe Net", SECRET)
    try:
        res = session.provision_node(
            "esp32-a", creds, serial.write_line, serial.read_line)
    finally:
        creds.clear()
    assert res.state == "PROVISIONED"


def test_parse_status_line_requires_all_fields():
    with pytest.raises(ValueError):
        parse_status_line("RFV_NET ssid=x bssid=y")  # missing channel/ip
    with pytest.raises(ValueError):
        parse_response("CSI_DATA,1,2,3")  # not a prov response
    with pytest.raises(ProvisioningError):
        parse_response("RFV_ERR nope")


def test_redact_strips_secrets():
    creds = Credentials("Cafe Net", SECRET)
    dirty = f"write [{SECRET}] failed on port"
    clean = redact(dirty, [creds.ssid, *creds.secrets()])
    assert SECRET not in clean
    assert "***" in clean
    creds.clear()


def test_empty_node_list_rejected():
    with pytest.raises(CredentialsError):
        ProvisioningSession([])


class FloodedSerial(FakeSerial):
    """Node whose first BEGIN reply is lost to CSI interleaving.

    Emits CSI junk slower than real time so the 3 s retransmit
    triggers, then answers cleanly (quiet window engaged).
    """

    def __init__(self, script, junk_before_ok=80):
        super().__init__(script)
        self._junk_before_ok = junk_before_ok

    def read_line(self, timeout):
        import time as _time
        if self._junk_before_ok > 0:
            self._junk_before_ok -= 1
            _time.sleep(0.05)
            return "CSI_DATA,1,aa:bb:cc:dd:ee:ff,-50,1,1"
        return super().read_line(timeout)


def test_lost_begin_reply_recovered_by_retransmit():
    serial = FloodedSerial(_happy_script())
    session = ProvisioningSession(["esp32-a"])
    creds = Credentials("Cafe Net", SECRET)
    try:
        res = session.provision_node(
            "esp32-a", creds, serial.write_line, serial.read_line,
            timeout_s=30.0)
    finally:
        creds.clear()
    assert res.state == "PROVISIONED"
    assert serial.sent.count("RFV_PROV_BEGIN") >= 2
    assert SECRET not in res.reason
