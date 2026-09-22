"""Unit tests for host-side two-node identity (csi.transport.nodes)."""

from __future__ import annotations

import os

import pytest

from csi.transport.nodes import (
    NODE_A,
    NODE_B,
    NODES,
    NodeIdentity,
    NodeIdentityError,
    all_nodes_resolved,
    node_for_device,
    resolve_device_node,
)


def _make_bypath(tmp_path, mapping):
    """Build a fake /dev/serial/by-path root.

    mapping: {symlink_name: target_dev_name}; targets are fake files.
    """
    root = tmp_path / "by-path"
    root.mkdir()
    devdir = tmp_path / "dev"
    devdir.mkdir()
    for link, dev in mapping.items():
        target = devdir / dev
        target.write_text("x")
        os.symlink(str(target), str(root / link))
    return str(root)


def test_node_table_separates_identity_from_experiment():
    assert NODE_A.node_id == "esp32-a"
    assert NODE_B.node_id == "esp32-b"
    assert NODE_A.board_mac == "b0:3f:d3:70:20:3c"
    assert NODE_B.board_mac == "04:b2:47:20:1a:dc"
    assert set(NODES) == {"esp32-a", "esp32-b"}
    for node in NODES.values():  # no RF/experiment fields on identity
        assert not hasattr(node, "bssid")
        assert not hasattr(node, "channel")
        assert not hasattr(node, "ssid")


def test_resolve_device_node_via_bypath(tmp_path):
    # Canonical home mapping: A on usb-0:5.4, B on usb-0:1.
    root = _make_bypath(tmp_path, {
        "pci-0000:00:14.0-usb-0:1:1.0-port0": "ttyUSB3",
        "pci-0000:00:14.0-usb-0:5.4:1.0-port0": "ttyUSB9",
    })
    assert resolve_device_node(NODE_A, by_path_root=root).endswith("ttyUSB9")
    assert resolve_device_node(NODE_B, by_path_root=root).endswith("ttyUSB3")


def test_resolve_missing_board_raises(tmp_path):
    root = _make_bypath(tmp_path, {
        "pci-0000:00:14.0-usb-0:5.4:1.0-port0": "ttyUSB9",
    })
    with pytest.raises(NodeIdentityError):
        resolve_device_node(NODE_B, by_path_root=root)


def test_resolve_unreadable_root_raises(tmp_path):
    with pytest.raises(NodeIdentityError):
        resolve_device_node(NODE_A,
                             by_path_root=str(tmp_path / "no-such-dir"))


def test_node_for_device_reverse_lookup(tmp_path):
    root = _make_bypath(tmp_path, {
        "pci-0000:00:14.0-usb-0:1:1.0-port0": "ttyUSB3",
        "pci-0000:00:14.0-usb-0:5.4:1.0-port0": "ttyUSB9",
    })
    dev_a = os.path.join(os.path.dirname(root), "dev", "ttyUSB9")
    assert node_for_device(dev_a, by_path_root=root) == NODE_A
    with pytest.raises(NodeIdentityError):
        node_for_device(os.path.join(os.path.dirname(root), "dev",
                                     "ttyUSB-missing"),
                        by_path_root=root)


def test_all_nodes_resolved_reports_every_gap(tmp_path):
    root = _make_bypath(tmp_path, {
        "pci-0000:00:14.0-usb-0:5.4:1.0-port0": "ttyUSB9",
    })
    with pytest.raises(NodeIdentityError) as exc:
        all_nodes_resolved(by_path_root=root)
    assert "esp32-b" in str(exc.value)


def test_ambiguous_bypath_raises(tmp_path):
    root = _make_bypath(tmp_path, {
        "x-usb-0:1-a-port0": "ttyUSB1",
        "y-usb-0:1-b-port0": "ttyUSB2",
    })
    with pytest.raises(NodeIdentityError):
        resolve_device_node(
            NodeIdentity("t", "usb-0:1", "00:00:00:00:00:00", "t"),
            by_path_root=root)
