# RFVISION-008 — DATA CONSOLIDATION REPORT

- Operation: RFVISION-008-FINAL-DATA-CONSOLIDATION (DATA/REPOSITORY ORGANIZATION only)
- Date (UTC): 2026-09-21 · No hardware/firmware/experiment changes.
- Freeze: `main`, clean tree, HEAD `3f72ae4`.

## 1. Old research-data location

`~/RFVision-Research-Data/` — 115 files, 131,158,780 B,
pre-move inventoried with per-file SHA-256 (`/tmp` working inventory, deleted
after use). Structure: `legacy-csi-verify-001/`, `legacy-csi-sense-001/`
(`raw/`, `derived/`, `superseded-phaseB-ANALYSIS/`, `tools-reference/`,
`manifests/`, `reference-docs/`, `MANIFEST.md`), `rfvision-003/`.

## 2. New research-data location

`~/Desktop/RF Vision/research-data/` — canonical, inside the
project; Git-ignored except `MANIFEST.md` + `README.md` (negations;
dir-contents ignore pattern because git cannot re-include under an excluded
parent). Old location retained as a dormant second copy (no active dependency).

```
research-data/
├── MANIFEST.md · README.md   (tracked)
├── legacy-csi-verify-001/    (R1)
├── legacy-csi-sense-001/     (R2/R3 raw, derived, superseded, tools-ref, manifests, reference-docs)
└── rfvision-003/             (003 capture)
```

## 3. Files consolidated

115 files copied with `copytree` + `copy2` (structure, bytes, modes preserved).
No renames, no transforms, no parsing/rewriting of raw CSI.

## 4. Total size

131,158,780 B across 115 content files (top-level MANIFEST/README excluded
from the count). Post-copy byte total matches pre-move inventory exactly.

## 5. Checksum verification

115/115 files BYTE-IDENTICAL to pre-move SHA-256 (full-tree recompute, not
filenames). Per-file table (path, size, SHA, experiment, source, original):
`research-data/MANIFEST.md`. Legacy `.sha256` sidecars carried over untouched.

## 6. R1/R2/R3 verification

| Dataset | SHA-256 | Size | Status |
|---|---|---|---|
| R1 VERIFY-70s | `51d47ce9…caed24` | 3,566,098 | verified, `444` |
| R2 trial_01 | `4734dcf5…7b8a40a` | 14,304,955 | verified, `444` |
| R3 smoke | `ce047085…46e37ca4` | 499,069 | verified, `444` |
| 003 capture | `c64e5a00…f352df` (baseline recorded pre-move) | 57,081,856 | verified unchanged, `444` |

Raw captures made read-only after verification; no transformations.

## 7. Git exclusion verification

- `git status --short` shows only intended docs (no `.log/.npz/.csv/.bin` bulk).
- `git check-ignore -v` confirms representative raw/derived/binary files ignored
  via `.gitignore: research-data/*`; `MANIFEST.md`/`README.md` confirmed trackable.
- Tracked bulk: only the allowlisted `docs/reference/example_csi.csv` fixture
  (unchanged). Staged for commit: `.gitignore`, root `README.md`,
  `research-data/{MANIFEST.md,README.md}`, provenance addendum, this report — docs only.

## 8. Legacy Downloads verification

Before deletion, all 62 legacy files content-verified (SHA-256, not filenames):
49 byte-identical in repo/research-data + 13 transformed-into-repo (both SHAs in
`LEGACY-MIGRATION-PROVENANCE.md`). R1/R2/R3 explicitly confirmed in both legacy
and project copies. Zero unique-uncovered files.

## 9. Files removed

`~/Downloads/RF Vision Files-20260921T163602Z-1-001`
(62 verified files) deleted after §§5/8/12/13 passed. Only unrelated `.deb`
installers remain in `~/Downloads/` (untouched — out of scope).

## 10. Files retained

- In git: 238 + 6 new ≈ 244 tracked (this op adds 6: `.gitignore` mod, READMEs,
  MANIFEST, provenance mod, this report).
- Canonical data: 115 files in `research-data/`.
- Dormant backup: 115 files in `~/RFVision-Research-Data/` (see §11).

## 11. Independent-backup status

PRESENT — `~/RFVision-Research-Data/` retained with identical bytes as the
second copy outside the project (same disk; best achievable independence —
no off-disk copy exists). This satisfied the §10 safety condition, permitting
Downloads retirement. Project has no active dependency on it.

## 12. Credential scan

- Git-tracked + pending files: 0 password-value hits; 0 hits across API-key,
  bearer, private-key, SSH, password-assignment patterns (REDACTED/methodology
  contexts excluded by design; values never printed).
- `research-data/` (ignored, never enters history) retains original bytes in 2
  files (`superseded` README + backup manifest mirrors — paths only, documented
  here per §11 allowance); byte-identical preservation required no modification.
  Wi-Fi rotation still recommended (006 audit).

## 13. Tests

`python3 -m pytest tests/ -q` after consolidation + deletions: **107 passed**
(baseline unchanged; data move touched no code).

## 14. Git commit

- H1 `docs: consolidate research data under RF Vision` (scope per §7-staging):
  `PENDING_H1`.
- H2 `docs: record RFVISION-008 commit hash in consolidation report`
  (this file with H1 filled): `PENDING_H2` (repo 002-pattern).
- Verify: `git log --oneline -3`; tree clean at close; no remote (user-deferred).

## 15. Final directory structure

```
~/Desktop/RF Vision/
├── ai/ csi/ dsp/ sensing/ localization/ realtime/ web/ unity/ firmware/
├── tests/ config/ experiments/ research/ tools/ visualization/ docs/
├── research-data/        ← canonical data (Git-ignored except MANIFEST/README)
├── README.md · LICENSE · requirements-*.txt · ...
└── .git/                 ← ONLY authoritative repo
```

No active dependency on `~/RFVision-Research-Data` (dormant backup) or on
`~/Downloads/...` (retired). Remaining gaps (003R, boot capture, geometry,
rotation, GitHub, loose `/tmp` scripts) carry over from RFVISION-007 §15.

END OF RFVISION-008 REPORT.
