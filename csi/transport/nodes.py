"""Host-side two-node identity map (two-node sensing foundation).

Deterministic node identity WITHOUT firmware changes and WITHOUT fragile
``/dev/ttyUSBn`` numbering:

* primary key: stable USB by-path (``/dev/serial/by-path/*-<path>-port0``),
  which is fixed by the USB topology while the boards stay plugged in;
* verified key: ESP32 STA MAC, confirmed with ``esptool chip_id`` immediately
  before flashing / at validation time and recorded here.

USB serial numbers are NOT used (both CP2102 bridges report ``0001``).
``/dev/ttyUSBn`` names are NEVER identity — they are resolved from the
by-path at session start and may differ across boots.

Experiment/RF configuration (AP BSSID, channel, capture parameters) is
deliberately NOT part of this module — see ``LiveProvider`` parameters and
``config/default.yaml``. This module answers only "which physical board is
this stream from".
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

__all__ = [
    "NodeIdentity",
    "NODE_A",
    "NODE_B",
    "NODES",
    "BY_PATH_ROOT",
    "NodeIdentityError",
    "resolve_device_node",
    "node_for_device",
    "all_nodes_resolved",
]


class NodeIdentityError(RuntimeError):
    """Raised when a node cannot be resolved to a live device node."""


#: Root exposing stable USB topology symlinks (Linux).
BY_PATH_ROOT = "/dev/serial/by-path"


@dataclass(frozen=True)
class NodeIdentity:
    """Physical identity of one CSI receiver node."""

    node_id: str
    by_path: str
    board_mac: str
    description: str


#: Validated single-node receiver (RFVISION-003 golden baseline).
#: Home-AP validation 2026-09-22 measured board A on usb-0:5.4.
NODE_A = NodeIdentity(
    node_id="esp32-a",
    by_path="usb-0:5.4",
    board_mac="b0:3f:d3:70:20:3c",
    description="validated ESP32-D0WD-V3 rev3.1 receiver (csi_recv_router)",
)

#: Second receiver (silicon-identical; flashed + validated in this phase).
#: Home-AP validation 2026-09-22 measured board B on usb-0:1.
NODE_B = NodeIdentity(
    node_id="esp32-b",
    by_path="usb-0:1",
    board_mac="04:b2:47:20:1a:dc",
    description="second ESP32-D0WD-V3 rev3.1 receiver (csi_recv_router)",
)

NODES: Dict[str, NodeIdentity] = {
    NODE_A.node_id: NODE_A,
    NODE_B.node_id: NODE_B,
}


def resolve_device_node(node: NodeIdentity,
                        by_path_root: str = BY_PATH_ROOT) -> str:
    """Resolve a node to its current ``/dev`` device node via USB by-path.

    Returns e.g. ``/dev/ttyUSB1``. Raises :class:`NodeIdentityError` when
    the by-path symlink is absent (board unplugged or moved to another
    USB port — replug to the recorded port, do not guess ``ttyUSBn``).
    """
    try:
        entries = sorted(os.listdir(by_path_root))
    except OSError as exc:
        raise NodeIdentityError(
            f"by-path root {by_path_root} unreadable: {exc}") from exc
    matches = [e for e in entries if node.by_path in e]
    if not matches:
        raise NodeIdentityError(
            f"node {node.node_id}: no device for by-path {node.by_path!r} "
            f"(board unplugged or moved USB port?)")
    if len(matches) > 1:
        raise NodeIdentityError(
            f"node {node.node_id}: ambiguous by-path {node.by_path!r}: "
            f"{matches}")
    return os.path.join("/dev", os.readlink(
        os.path.join(by_path_root, matches[0])).split("/")[-1])


def node_for_device(device: str,
                    by_path_root: str = BY_PATH_ROOT) -> NodeIdentity:
    """Reverse lookup: which node owns an open ``/dev`` device node."""
    real = os.path.realpath(device)
    try:
        entries = sorted(os.listdir(by_path_root))
    except OSError as exc:
        raise NodeIdentityError(
            f"by_path root {by_path_root} unreadable: {exc}") from exc
    for name in entries:
        if os.path.realpath(os.path.join(by_path_root, name)) == real:
            for node in NODES.values():
                if node.by_path in name:
                    return node
    raise NodeIdentityError(
        f"device {device} does not match any known node by-path")


def all_nodes_resolved(
        by_path_root: str = BY_PATH_ROOT) -> Dict[str, str]:
    """Resolve every known node; returns ``{node_id: device}``.

    Raises :class:`NodeIdentityError` listing every unresolvable node so a
    dual session never starts half-identified.
    """
    resolved: Dict[str, str] = {}
    missing: List[str] = []
    for node in NODES.values():
        try:
            resolved[node.node_id] = resolve_device_node(
                node, by_path_root=by_path_root)
        except NodeIdentityError:
            missing.append(f"{node.node_id} (by-path {node.by_path})")
    if missing:
        raise NodeIdentityError(
            "unresolved nodes: " + "; ".join(missing))
    return resolved
