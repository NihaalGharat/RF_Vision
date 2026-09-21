"""Realtime serial stream: threaded CSI capture for the live pipeline.

Canonical implementation: :mod:`csi.capture.serial_receiver`. Re-exported
here so the realtime layer has a stable import path.
"""

from csi.capture.serial_receiver import (
    RawSessionWriter,
    SerialReceiver,
    find_serial_ports,
)

__all__ = ["RawSessionWriter", "SerialReceiver", "find_serial_ports"]
