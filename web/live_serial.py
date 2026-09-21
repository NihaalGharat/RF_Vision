"""Raw serial line source for the live CSI path (RFVISION-009).

Stdlib + POSIX ``termios`` only — deliberately NOT pyserial: opening a
port via termios never touches modem-control lines, so merely opening
``/dev/ttyUSB0`` cannot reset the already-validated receiver (no flash,
no erase, no reset in this operation).

Binary-safe: bytes are accumulated and split on LF; each line is
decoded as ASCII with replacement characters so a corrupt byte can
never kill the stream. Every raw line stays observable — recording is
lossless when enabled and malformed input is counted by the caller,
never silently dropped.
"""

from __future__ import annotations

import os
import select
import time
from typing import Iterator, List, Optional, Union

__all__ = [
    "DEFAULT_PORT",
    "DEFAULT_BAUD",
    "LiveSerialError",
    "SerialLineSource",
    "FakeLineSource",
]

#: Validated receiver attachment (RFVISION-003R-C2).
DEFAULT_PORT = "/dev/ttyUSB0"
DEFAULT_BAUD = 921600

#: A line longer than this without a newline is an overlong fragment
#: (corruption), not data — drop it and count it.
MAX_LINE_BYTES = 65536


class LiveSerialError(RuntimeError):
    """Raised when the serial transport cannot be opened or dies."""


class SerialLineSource:
    """One-shot raw line reader for a POSIX serial port.

    Open once per session (``open()``), iterate lines, ``close()``.
    ``bytes_read`` counts every byte received (throughput accounting).
    ``overlong_dropped`` counts corruption fragments discarded by the
    length guard.
    """

    def __init__(self, port: str = DEFAULT_PORT, baud: int = DEFAULT_BAUD,
                 read_timeout_s: float = 0.5) -> None:
        self.port = str(port)
        self.baud = int(baud)
        self.read_timeout_s = float(read_timeout_s)
        self._fd: Optional[int] = None
        self.bytes_read = 0
        self.overlong_dropped = 0
        self.opened_at: Optional[float] = None

    # -- lifecycle ---------------------------------------------------
    def open(self) -> "SerialLineSource":
        """Open the port in raw 8N1 mode (raises LiveSerialError)."""
        if self._fd is not None:
            return self
        try:
            import termios
            import tty
        except ImportError as exc:  # non-POSIX host
            raise LiveSerialError(
                f"serial live source needs POSIX termios: {exc}") from exc
        try:
            fd = os.open(self.port, os.O_RDONLY | os.O_NOCTTY
                         | os.O_NONBLOCK)
        except OSError as exc:
            raise LiveSerialError(
                f"cannot open {self.port}: {exc.strerror or exc}") from exc
        try:
            attrs = termios.tcgetattr(fd)
            attrs[0] = attrs[1] = attrs[3] = 0  # iflag/oflag/lflag: raw
            attrs[2] = (termios.CLOCAL | termios.CREAD | termios.CS8)
            try:
                speed = getattr(termios, f"B{self.baud}")
            except AttributeError:
                raise LiveSerialError(
                    f"baud {self.baud} unsupported by termios on this host")
            attrs[4] = attrs[5] = speed  # ispeed/ospeed
            attrs[6][termios.VMIN] = 0
            attrs[6][termios.VTIME] = 0
            termios.tcsetattr(fd, termios.TCSANOW, attrs)
            tty.setraw(fd)  # ensure no line processing lingers
            # Re-assert raw baud after setraw (setraw may touch speeds).
            attrs = termios.tcgetattr(fd)
            attrs[4] = attrs[5] = speed
            termios.tcsetattr(fd, termios.TCSANOW, attrs)
        except (termios.error, OSError) as exc:
            os.close(fd)
            raise LiveSerialError(
                f"cannot configure {self.port} @ {self.baud}: {exc}") from exc
        self._fd = fd
        self.opened_at = time.time()
        return self

    def close(self) -> None:
        """Release the port (idempotent)."""
        fd, self._fd = self._fd, None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass

    @property
    def is_open(self) -> bool:
        """True while the port is held."""
        return self._fd is not None

    # -- reading -------------------------------------------------------
    def iter_lines(self) -> Iterator[str]:
        """Yield decoded lines until closed or the transport dies.

        Raises LiveSerialError on transport failure. A closed source
        simply ends iteration (clean session stop).
        """
        if self._fd is None:
            raise LiveSerialError("serial source is not open")
        buf = bytearray()
        fd = self._fd
        while self._fd is not None:
            try:
                ready, _, _ = select.select([fd], [], [], self.read_timeout_s)
            except (OSError, ValueError) as exc:
                raise LiveSerialError(f"serial select failed: {exc}") from exc
            if not ready:
                continue  # timeout: lets the caller re-check stop flags
            try:
                chunk = os.read(fd, 4096)
            except OSError as exc:
                raise LiveSerialError(f"serial read failed: {exc}") from exc
            if not chunk:
                raise LiveSerialError("serial transport closed (EOF)")
            self.bytes_read += len(chunk)
            buf += chunk
            while True:
                nl = buf.find(b"\n")
                if nl < 0:
                    if len(buf) > MAX_LINE_BYTES:
                        self.overlong_dropped += 1
                        del buf[:]
                    break
                raw = bytes(buf[:nl + 1])
                del buf[:nl + 1]
                yield raw.decode("ascii", errors="replace")


class FakeLineSource:
    """In-memory line source for tests (no hardware).

    ``lines`` are str or bytes; ``raise_after`` injects a transport
    failure after that many yielded lines (disconnect simulation);
    ``pace_s`` sleeps between lines (rate-realistic session tests) —
    either a fixed seconds value or a callable ``(index) -> seconds``
    (e.g. an instant burst followed by a paced stream).
    """

    def __init__(self, lines: List[Union[str, bytes]],
                 raise_after: Optional[int] = None,
                 raise_message: str = "injected transport failure",
                 pace_s: float = 0.0) -> None:
        self._lines = list(lines)
        self._raise_after = raise_after
        self._raise_message = raise_message
        self._pace_s = pace_s
        self._open = False
        self.bytes_read = 0
        self.overlong_dropped = 0
        self.opened_at: Optional[float] = None
        self.closed = False

    def open(self) -> "FakeLineSource":
        self._open = True
        self.opened_at = time.time()
        return self

    def close(self) -> None:
        self._open = False
        self.closed = True

    @property
    def is_open(self) -> bool:
        return self._open

    def iter_lines(self) -> Iterator[str]:
        if not self._open:
            raise LiveSerialError("fake source is not open")
        for idx, line in enumerate(self._lines):
            if (self._raise_after is not None
                    and idx >= self._raise_after):
                raise LiveSerialError(self._raise_message)
            pace = self._pace_s(idx) if callable(self._pace_s) else self._pace_s
            if pace > 0:
                time.sleep(pace)
            if isinstance(line, bytes):
                self.bytes_read += len(line)
                yield line.decode("ascii", errors="replace")
            else:
                self.bytes_read += len(line.encode("ascii", errors="replace"))
                yield line
