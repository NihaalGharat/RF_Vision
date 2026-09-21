"""Serial transport constants for the validated acquisition path.

Single source of truth for the USB-serial link between the ESP32
(``csi_recv_router`` firmware) and the Ubuntu host. Values mirror the
firmware ``sdkconfig.defaults`` (921600 8N1) and the validated experiment
(``/dev/ttyUSB0``). Import these instead of hardcoding baud rates or port
name patterns in capture code.
"""

from __future__ import annotations

#: Baud rate pinned by the firmware build (sdkconfig.defaults).
BAUD_RATE = 921600
#: Byte format: 8 data bits, no parity, 1 stop bit.
BYTE_FORMAT = "8N1"
#: Validated device node during the reference experiment.
DEFAULT_PORT = "/dev/ttyUSB0"
#: Port-name substrings accepted during auto-detection (Linux/macOS/Windows).
PORT_PATTERNS = ("usbmodem", "usbserial", "ttyusb", "ttyacm", "cu.usb")
#: Ping trigger used by csi_recv_router: 10 ms interval, 1-byte payload.
PING_INTERVAL_MS = 10
PING_PAYLOAD_BYTES = 1
#: Reconnect backoff after a serial I/O error (seconds).
RECONNECT_DELAY_S = 2.0
#: Link considered offline after this silence (seconds).
OFFLINE_AFTER_S = 3.0
#: Chunk size for background serial reads (bytes).
READ_CHUNK_BYTES = 4096
