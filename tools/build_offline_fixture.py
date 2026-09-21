"""Build the offline UI fixture from the real CSI path (RFVISION-005).

Reads deterministic synthetic ``CSI_DATA`` lines (``tests/synthetic/
synth.py``, seed 7 — test plumbing, never evidence), parses each through
the REAL ``EspCsvAdapter`` + validators, derives amplitude via the REAL
``dsp/amplitude`` front-end, and writes ``web/fixtures/offline_demo.jsonl``
as ``sensing.snapshot`` envelopes labeled OFFLINE_FIXTURE with a manifest
sidecar (``offline_demo.manifest.json``: generator, seed, count, sha256).

Usage (repo root): ``python3 tools/build_offline_fixture.py``
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np  # noqa: E402

from csi.parser.esp_csv_adapter import EspCsvAdapter  # noqa: E402
from csi.validation.validators import validate_sample  # noqa: E402
from dsp.amplitude.amplitude import amplitude_valid  # noqa: E402
from tests.synthetic.synth import make_esp_csv_line  # noqa: E402
from web import contracts  # noqa: E402

SEED = 7
N_FRAMES = 120
FIXTURE = PROJECT_ROOT / "web" / "fixtures" / "offline_demo.jsonl"
MANIFEST = PROJECT_ROOT / "web" / "fixtures" / "offline_demo.manifest.json"


def main() -> int:
    """Generate the fixture; returns process exit code."""
    adapter = EspCsvAdapter()
    events = []
    for seq in range(1, N_FRAMES + 1):
        line = make_esp_csv_line(seq=seq, seed=SEED + seq,
                                 rssi=-50 + (seq % 7) - 3)
        try:
            sample = adapter.handle_line(line)
        except Exception as exc:  # PacketError subclasses
            raise RuntimeError(f"synthetic line {seq} rejected: {exc}") \
                from exc
        if sample is None:
            raise RuntimeError(f"synthetic line {seq} ignored by adapter")
        report = validate_sample(sample)
        if not report.ok:
            raise RuntimeError(f"synthetic sample {seq} invalid: "
                               f"{report.warnings}")
        amps = [float(v) for v in amplitude_valid(sample)]
        payload = contracts.sensing_snapshot_payload(
            presence="UNKNOWN", presence_prob=None,
            movement="UNKNOWN", movement_prob=None,
            position=None, position_m=None, confidence=None,
            rssi=float(sample.rssi), amplitudes=amps, phases=None,
            validated=False,
        )
        payload["source_state"] = "OFFLINE_FIXTURE"
        payload["fixture"] = {"generator": "tools/build_offline_fixture.py",
                              "seed": SEED, "frame": seq,
                              "adapter_stats": {
                                  "lines_seen": adapter.stats.lines_seen,
                                  "parsed": adapter.stats.parsed}}
        events.append(contracts.wrap_event("sensing.snapshot", payload,
                                           source="rfvision-fixture",
                                           seq=seq))
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    with open(FIXTURE, "w", encoding="utf-8") as fh:
        for event in events:
            fh.write(json.dumps(event) + "\n")
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    manifest = {"generator": "tools/build_offline_fixture.py", "seed": SEED,
                "frames": len(events), "created_utc": time.strftime(
                    "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sha256": digest,
                "label": "OFFLINE_FIXTURE — synthetic via real adapter; "
                         "never sensing evidence"}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n",
                        encoding="utf-8")
    print(f"wrote {FIXTURE} ({len(events)} frames, sha256={digest[:16]}…)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
