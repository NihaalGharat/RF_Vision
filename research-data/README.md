# research-data/ — canonical RF Vision research data (RFVISION-008)

> "Raw and large derived research datasets are intentionally excluded
> from Git history."

This directory holds the project's preserved CSI captures and derived
research datasets. **Only this `README.md` and `MANIFEST.md` are tracked
in Git** (see `.gitignore`: `research-data/` ignored with two negations).
Everything else here is local working data, not history.

## Layout

```
research-data/
├── MANIFEST.md                  ← tracked: every file (path, size, SHA-256, provenance)
├── README.md                    ← tracked: this file
├── legacy-csi-verify-001/       ← R1: CSI-VERIFY-001 70 s PASS capture (2026-09-06)
├── legacy-csi-sense-001/
│   ├── raw/                     ← R2 trial_01 + R3 smoke captures (+ stdout sidecar)
│   ├── derived/                 ← parsed CSV/NPZ, features, baseline, PCA, figures
│   ├── superseded-phaseB-ANALYSIS/ ← Phase-B superseded set (audit trail)
│   ├── tools-reference/         ← 11 legacy tools, REFERENCE ONLY
│   ├── manifests/               ← backup/path/checksum manifests + unique-small
│   ├── reference-docs/          ← archive + phase-B READMEs, protocol
│   └── MANIFEST.md              ← RFVISION-006 59-entry manifest (historical record)
└── rfvision-003/                ← 003 golden-test capture (FAIL context, unchanged)
```

Codebook: R1 = VERIFY-70s PASS · R2 = trial_01 pilot (INCONCLUSIVE N=1) ·
R3 = smoke trial_00 · 003 = RFVISION-003 capture.

## How manifests work

- `MANIFEST.md` lists every content file with size + SHA-256 + experiment /
  provenance + source + original (`~/RFVision-Research-Data/`) location.
- Each dataset file ships with a `.sha256` sidecar (from RFVISION-006).
- Raw captures are read-only (`444`) — never edit, parse in place, or rewrite.

## How SHA verification works

```bash
cd research-data
sha256sum -c legacy-csi-verify-001/CSI_RAW_70s_921600_20260906_205638.log.sha256
sha256sum -c legacy-csi-sense-001/raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log.sha256
sha256sum -c legacy-csi-sense-001/raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log.sha256
# or verify the full tree against MANIFEST.md:
python3 - <<'EOF'
import hashlib, re
from pathlib import Path
root = Path('.')
rows = [l for l in (root/'MANIFEST.md').read_text().splitlines() if l.startswith('| `')]
assert rows, "no manifest rows"
bad = []
for r in rows:
    m = re.match(r"\| `(.+?)` \| (\d+) \| `([0-9a-f]{64})`", r)
    rel, size, sha = m.groups()
    p = root/rel
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if h != sha or p.stat().st_size != int(size): bad.append(rel)
print(f"{len(rows)-len(bad)}/{len(rows)} OK" + (f" BAD: {bad}" if bad else ""))
EOF
```

## How to reproduce analysis from raw data

1. Read the capture sidecars first: `evidence/capture_meta_*.json`,
   `validate_*.json` in `docs/research/legacy/evidence/` (in-git metadata).
2. Study design + gate thresholds: `docs/research/legacy/CSI-SENSE-001_PLAN_v1.1.md`,
   `CSI-VERIFY-001_FINAL_REPORT.md`.
3. Legacy technique reference (do NOT import as active code):
   `docs/research/legacy/TOOL-REFERENCE.md` + `research-data/legacy-csi-sense-001/tools-reference/`.
4. Parse raw logs with the current validated chain (`csi/`, `dsp/`) — never
   overwrite the read-only originals; write outputs outside `research-data/`
   or under a new ignored scratch dir.
5. Current scientific status (what is/isn't validated):
   `docs/research/SCIENTIFIC_VALIDATION_STATUS.md`.

## Redundant copy

`~/RFVision-Research-Data/` is retained as a dormant second copy of the same
bytes (no active dependency — the project reads only this directory). It is
the independent backup that allowed the legacy Downloads archive to be retired.
