"""Validation helpers for parsed CSI samples.

Parsing (:mod:`csi.parser`) guarantees structure; this module checks
*plausibility* against the documented ESP32 ranges so that out-of-range
metadata is caught before it reaches features, datasets, or models.
Nothing here mutates the sample.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from csi.parser.csi_parser import CsiSample

#: Documented plausibility ranges (inclusive). Violations produce warnings,
#: not rejections -- the raw stream is authoritative.
RSSI_MIN, RSSI_MAX = -110, 30
CHANNEL_24GHZ_MIN, CHANNEL_24GHZ_MAX = 1, 14
VALID_SIG_MODES = (0, 1, 3)
VALID_CWB = (0, 1)


@dataclass
class ValidationReport:
    """Outcome of validating one sample."""

    ok: bool
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> Dict[str, object]:
        return {"ok": self.ok, "warnings": list(self.warnings)}


def validate_sample(sample: CsiSample) -> ValidationReport:
    """Check a sample's metadata plausibility; return a report."""
    warnings: List[str] = []
    if not RSSI_MIN <= sample.rssi <= RSSI_MAX:
        warnings.append(f"rssi {sample.rssi} dBm outside [{RSSI_MIN}, {RSSI_MAX}]")
    if not CHANNEL_24GHZ_MIN <= sample.channel <= CHANNEL_24GHZ_MAX:
        warnings.append(f"channel {sample.channel} outside 2.4 GHz band")
    if sample.sig_mode not in VALID_SIG_MODES:
        warnings.append(f"sig_mode {sample.sig_mode} not in {VALID_SIG_MODES}")
    if sample.cwb not in VALID_CWB:
        warnings.append(f"cwb {sample.cwb} not in {VALID_CWB}")
    if sample.n_subcarriers < 8:
        warnings.append(f"only {sample.n_subcarriers} subcarrier slots")
    if sample.seq < 0:
        warnings.append(f"negative sequence {sample.seq}")
    return ValidationReport(ok=not warnings, warnings=warnings)
