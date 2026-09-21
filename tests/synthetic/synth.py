"""Deterministic synthetic CSI generators (stdlib only, no numpy).

Test plumbing, never signal truth: generates well-formed ``CSI_DATA``
(25-column, classic) lines and ``#CSI {JSON}`` lines with a seeded PRNG so
unit/integration tests are hermetic. Synthetic data must NEVER be quoted
as sensing evidence (see ``docs/research/SCIENTIFIC_VALIDATION_STATUS.md``).
"""

from __future__ import annotations

import json
import random
from typing import List

__all__ = ["make_iq", "make_esp_csv_line", "make_json_line"]


def make_iq(n_slots: int = 64, seed: int = 0) -> List[int]:
    """Deterministic int8 I/Q payload (2 ints per slot)."""
    rng = random.Random(seed)
    return [rng.randint(-60, 60) for _ in range(2 * n_slots)]


def make_esp_csv_line(seq: int = 1, n_slots: int = 64, seed: int = 0,
                      rssi: int = -50, channel: int = 6,
                      first_word_invalid: int = 0) -> str:
    """One well-formed classic ``CSI_DATA`` line (len matches payload)."""
    iq = make_iq(n_slots, seed)
    payload = "[" + ",".join(str(v) for v in iq) + "]"
    cols = ["CSI_DATA", str(seq), "AABBCCDDEEFF", str(rssi), "0", "1", "0",
            "0", "0", "0", "0", "0", "0", "0", "-90", "0", str(channel), "0",
            "123456789", "0", "100", "0", str(len(iq)),
            str(first_word_invalid), f'"{payload}"']
    return ",".join(cols)


def make_json_line(seq: int = 1, n_slots: int = 64, seed: int = 0,
                   rssi: int = -50) -> str:
    """One well-formed ``#CSI {JSON}`` line for the JSON parser path."""
    obj = {"timestamp": 123456789, "seq": seq, "rssi": rssi, "channel": 6,
           "secondary_channel": 0, "sig_mode": 1, "mcs": 0, "cwb": 0,
           "rate": 0, "aggregation": 0, "stbc": 0, "fec_coding": 0,
           "sgi": 0, "noise_floor": -90, "ampdu_cnt": 0, "sig_len": 100,
           "rx_state": 0, "ant": 0, "timestamp_wifi": 123456789,
           "mac": "AABBCCDDEEFF", "first_word_invalid": 0,
           "csi_len": 2 * n_slots, "csi": make_iq(n_slots, seed)}
    return "#CSI " + json.dumps(obj)
