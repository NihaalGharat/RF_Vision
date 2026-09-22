"""Adapter: Espressif ``CSI_DATA`` serial lines -> :class:`CsiSample`.

The validated acquisition firmware (``firmware/esp32/csi_recv_router``)
emits 25-column ``CSI_DATA,...`` text lines, while the RF Vision parsing and
signal chain consumes :class:`~csi.parser.csi_parser.CsiSample` (the
``#CSI {JSON}`` field model). This adapter bridges the two WITHOUT touching
the proven firmware: it parses one ``CSI_DATA`` line, validates the payload
length, and builds the identical sample object the rest of the pipeline
uses. Malformed lines are counted, never fatal.

Classic-ESP32 (legacy) column layout (25 columns)::

    CSI_DATA,seq,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,
    not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,
    channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,
    len,first_word_invalid,"[I0,R0,I1,R1,...]"

Notes:
  * I/Q order on the wire is (imag, real) pairs; the payload array is passed
    through untouched and interpreted downstream by
    :func:`~csi.parser.csi_parser.raw_to_complex`.
  * The 15-column C5/C6 variant is NOT accepted (different ``rx_ctrl``
    layout); such lines are rejected with ``column_count`` so a future
    adapter can be added explicitly instead of silently mis-parsing.
"""

from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np

from csi.parser.csi_parser import CsiSample, PacketError

#: Exact column count of the classic-ESP32 CSI_DATA line.
CSI_DATA_COLUMNS = 25


@dataclass
class AdapterStats:
    """Counters for the adapter (surfaced in logs / debug view)."""

    lines_seen: int = 0
    parsed: int = 0
    rejected_total: int = 0
    rejection_reasons: Dict[str, int] = field(default_factory=dict)

    def reject(self, reason: str) -> None:
        self.rejected_total += 1
        self.rejection_reasons[reason] = self.rejection_reasons.get(reason, 0) + 1

    def as_dict(self) -> dict:
        out = dict(self.__dict__)
        out["rejection_reasons"] = dict(self.rejection_reasons)
        return out


def parse_esp_csv_line(line: str, local_ts: Optional[float] = None,
                       ts_host_ns: Optional[int] = None) -> CsiSample:
    """Parse one ``CSI_DATA,...`` line into a :class:`CsiSample`.

    Raises :class:`PacketError` on any structural problem (wrong tag,
    wrong column count, non-integer fields, payload length mismatch,
    out-of-range I/Q values).
    ``ts_host_ns`` should be stamped at serial ingress; when omitted it is
    stamped here (still host-side, slightly later).
    """
    text = line.strip()
    if not text:
        raise PacketError("empty line")
    try:
        cols = next(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise PacketError(f"CSV split failed: {exc}") from exc
    if not cols or cols[0] != "CSI_DATA":
        raise PacketError(f"not a CSI_DATA line: {cols[0] if cols else ''!r}")
    if len(cols) != CSI_DATA_COLUMNS:
        raise PacketError(
            f"column count {len(cols)} != {CSI_DATA_COLUMNS} "
            "(C5/C6 15-column variant is not supported by this adapter)")

    try:
        seq = int(cols[1])
        mac = str(cols[2])
        rssi = int(cols[3])
        rate = int(cols[4])
        sig_mode = int(cols[5])
        mcs = int(cols[6])
        bandwidth = int(cols[7])
        smoothing = int(cols[8])  # noqa: F841 (parsed for completeness)
        not_sounding = int(cols[9])  # noqa: F841 (parsed for completeness)
        aggregation = int(cols[10])
        stbc = int(cols[11])
        fec_coding = int(cols[12])
        sgi = int(cols[13])
        noise_floor = int(cols[14])
        ampdu_cnt = int(cols[15])
        channel = int(cols[16])
        secondary_channel = int(cols[17])
        local_timestamp = int(cols[18])
        ant = int(cols[19])
        sig_len = int(cols[20])
        rx_state = int(cols[21])
        payload_len = int(cols[22])
        first_word_invalid = int(cols[23])
    except ValueError as exc:
        raise PacketError(f"non-integer header field: {exc}") from exc

    try:
        payload = json.loads(cols[24])
    except json.JSONDecodeError as exc:
        raise PacketError(f"payload is not a JSON array: {exc}") from exc
    if not isinstance(payload, list) or not payload:
        raise PacketError("payload must be a non-empty array")
    if len(payload) != payload_len:
        raise PacketError(
            f"payload length mismatch: header len={payload_len}, "
            f"got {len(payload)}")
    for value in payload:
        if isinstance(value, bool) or not isinstance(value, int):
            raise PacketError(f"non-integer payload value: {value!r}")
        if not -128 <= value <= 127:
            raise PacketError(f"payload value out of int8 range: {value}")

    return CsiSample(
        ts_esp32_us=local_timestamp,
        ts_local=float(local_ts if local_ts is not None else time.time()),
        ts_host_ns=(int(ts_host_ns) if ts_host_ns is not None
                    else time.monotonic_ns()),
        seq=seq,
        rssi=rssi,
        channel=channel,
        secondary_channel=secondary_channel,
        sig_mode=sig_mode,
        mcs=mcs,
        cwb=bandwidth,
        rate=rate,
        aggregation=aggregation,
        stbc=stbc,
        fec_coding=fec_coding,
        sgi=sgi,
        noise_floor=noise_floor,
        ampdu_cnt=ampdu_cnt,
        sig_len=sig_len,
        rx_state=rx_state,
        ant=ant,
        ts_wifi_us=local_timestamp,
        mac=mac,
        first_word_invalid=bool(first_word_invalid),
        csi=np.asarray(payload, dtype=np.int8),
    )


class EspCsvAdapter:
    """Stateful adapter wrapper that counts parsed/rejected lines."""

    def __init__(self) -> None:
        self.stats = AdapterStats()

    def handle_line(self, line: str,
                    local_ts: Optional[float] = None,
                    ts_host_ns: Optional[int] = None) -> Optional[CsiSample]:
        """Parse one line; ``None`` for blanks/non-CSI lines.

        Raises :class:`PacketError` for structurally invalid CSI_DATA lines
        (counted in stats before re-raising).
        """
        text = line.strip()
        if not text or not text.startswith("CSI_DATA"):
            return None
        self.stats.lines_seen += 1
        try:
            sample = parse_esp_csv_line(text, local_ts, ts_host_ns)
        except PacketError:
            self.stats.reject("malformed")
            raise
        self.stats.parsed += 1
        return sample
