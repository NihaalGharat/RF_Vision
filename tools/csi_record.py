"""Headless raw-CSI recorder (stdlib + lazy pyserial).

Records timestamped ``CSI_DATA`` lines from the validated firmware to a CSV
session file WITHOUT parsing (parse later with :mod:`csi.parser`). Usage::

    python tools/csi_record.py --port /dev/ttyUSB0 --duration 60
    python tools/csi_record.py --list

The ``classify``/``session_name`` helpers are stdlib-only and unit-tested;
only ``open_port``/``main`` need pyserial.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from csi.capture.helpers import scrub_line
from csi.transport.serial_config import (
    BAUD_RATE, DEFAULT_PORT, READ_CHUNK_BYTES, RECONNECT_DELAY_S)


def classify_line(raw: str) -> Optional[str]:
    """Return ``'csi'`` for lines carrying CSI_DATA, else ``None``."""
    return "csi" if scrub_line(raw) is not None else None


def session_name(prefix: str = "session",
                 ts: Optional[float] = None) -> str:
    """Deterministic session filename stem (UTC, filesystem-safe)."""
    t = time.gmtime(ts if ts is not None else time.time())
    return f"{prefix}_{time.strftime('%Y%m%d_%H%M%S', t)}.csv"


def open_port(port: str, baud: int = BAUD_RATE):
    """Open the serial port (requires pyserial; lazy import)."""
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is required: pip install -r requirements-base.txt"
        ) from exc
    return serial.Serial(port, baud, timeout=1)


def main(argv=None) -> int:
    """CLI: record raw CSI lines with host timestamps."""
    parser = argparse.ArgumentParser(
        description="Record raw CSI_DATA lines (no parsing, no inference)")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=BAUD_RATE)
    parser.add_argument("--duration", type=float, default=0.0,
                        help="seconds to record (0 = until Ctrl+C)")
    parser.add_argument("--max-lines", type=int, default=0,
                        help="stop after N CSI lines (0 = unlimited)")
    parser.add_argument("--out", default=None,
                        help="output CSV path (default: ./<session>.csv)")
    parser.add_argument("--list", action="store_true",
                        help="list candidate ports and exit")
    args = parser.parse_args(argv)

    if args.list:
        from csi.capture.serial_receiver import find_serial_ports
        for p in find_serial_ports():
            print(p)
        return 0

    out_path = Path(args.out) if args.out else Path(session_name())
    ser = open_port(args.port, args.baud)
    print(f"recording {args.port} @ {args.baud} -> {out_path}")
    n = 0
    start = time.time()
    buffer = bytearray()
    try:
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("host_ts,line\n")
            while True:
                chunk = ser.read(READ_CHUNK_BYTES)
                if chunk:
                    buffer.extend(chunk)
                    while b"\n" in buffer:
                        raw, _, rest = buffer.partition(b"\n")
                        buffer = bytearray(rest)
                        text = raw.decode("utf-8", errors="replace")
                        payload = scrub_line(text)
                        if payload is None:
                            continue
                        fh.write(f"{time.time():.6f},{payload}\n")
                        n += 1
                        if args.max_lines and n >= args.max_lines:
                            raise StopIteration
                if args.duration and (time.time() - start) >= args.duration:
                    break
    except StopIteration:
        pass
    except KeyboardInterrupt:
        print()
    finally:
        ser.close()
    print(f"saved {n} CSI lines to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
