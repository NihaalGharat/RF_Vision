# RFVISION-006 — LEGACY CONSOLIDATION REPORT

> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Migrated 2026-09-21 · See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

- Operation: RFVISION-006-LEGACY-CONSOLIDATION (ANALYSIS → approved MIGRATION → VERIFICATION → CLEANUP)
- Approval: `APPROVED — MIGRATE LEGACY RF VISION MATERIAL` (user, 2026-09-21)
- Authoritative repo (only): `~/Desktop/RF Vision` — foundation untouched, change purely additive.

## 1. Legacy source

- Path: `~/Downloads/RF Vision Files-20260921T163602Z-1-001` (canonical inner `RF Vision Files/`)
- Size: 162 MB · Files: 232 · Dirs: 73 · No `.git` · No archives
- Types: `json` 68, `md` 53, `py` 40, `png` 20, `npz` 13, `log` 11, `sha256` 7, `csv` 6, `jsonl` 5, `txt` 3 (+ historical-dup markers)
- Content dates: 2026-09-06 (Ubuntu Live era) · Wrapper extracted 2026-09-21
- Full audit: `/tmp/rfvision-legacy-audit/LEGACY_INVENTORY.md` (analysis phase, outside git)

## 2. Legacy inventory summary

232 files collapse to **78 unique content hashes** — the archive is 3–7 mirrors of
the same payloads (`00–08` canonical layout + `CSI-SENSE-001/` + `CSI_SENSE_001/`
+ `SOURCE_PROJECT/` + `99_ARCHIVE/` mirrors). 227 files sit in 73 duplicate
groups. Three unique raw captures (R1 VERIFY-70s PASS; R2 pilot trial_01
INCONCLUSIVE N=1; R3 smoke), full sidecar chains, 11 Python tools, 8 reports +
plan v1.1, metadata/evidence JSONs, derived `.npz/.csv/.png` sets. No RuView /
Unity / papers / installers / binaries / firmware `.bin` (pins only). Boot
15 s capture `5608f152…` cited but ABSENT (Live `/tmp` gap — unrecoverable).

## 3. Current-vs-legacy comparison

Matrix: `/tmp/rfvision-legacy-audit/CURRENT_VS_LEGACY_MATRIX.md`. Headlines:
firmware pins AGREE (IDF `296b6eab`, CSI `8633d671`, app `ce23861e`) — legacy
corroborates `docs/hardware/BASELINE.md`, nothing changed. Current parser/DSP/
test chain wins over legacy tools (REFERENCE ONLY, no replacement). Legacy plan
v1.1, HW detail, gate thresholds, and PASS/pilot reports fill real gaps. Legacy
PASS (R1) and current RFVISION-003 FAIL coexist (different captures/dates).
Zero RuView material in legacy — RFVISION-004 stays controlling.

## 4. Important recovered information

- Exact HW identities: ESP32-D0WD-V3 rev3.1 MAC `f4:65:0b:56:0e:18`, flash
  `0x68:0x4016 dio40m`, CP2102 by-id, Xiaomi 4C/R4CM `Nihaal 8C:53:C3:5B:E1:59`
  ch1/2412/HT20, Lenovo 82S9 BIOS `JMCN48WW`, Live `/cow` volatility, NVMe untouched.
- Build/flash transcript (723 K app / 26 K bootloader, 102/141 Hz observed).
- A–F gate thresholds (missing ≤1 %, malformed ≤0.5 %, gap >500 ms, ch1 ≥99 %).
- Trial/env/study metadata incl. NULL/UNKNOWN gap records (geometry unmeasured —
  preserved as gap, not invented). Single measured height ~0.55 m (ESP32).
- VERIFY PASS + INCONCLUSIVE N=1 pilot (negative result preserved as evidence).

## 5. Migrated material

- **Into git (32 files, ~420 KB, all new — zero tracked files modified):**
  `docs/research/legacy/` (plan, 2 VERIFY, 4 phase, 2 audits, metadata ×5,
  evidence ×5, derived-meta ×6, TOOL-REFERENCE.md, LEGACY-CLEANUP-MANIFEST.md),
  `docs/hardware/legacy/` (identity, firmware REDACTED, capture config),
  `docs/security/LEGACY_CREDENTIAL_AUDIT.md` (REDACTED),
  `docs/research/LEGACY-MIGRATION-PROVENANCE.md`, this report.
- **External, outside git (59 files, 74,058,859 B, byte-identical, raw read-only
  `444`):** `~/RFVision-Research-Data/legacy-csi-verify-001/` (R1),
  `~/RFVision-Research-Data/legacy-csi-sense-001/` (`raw/`, `derived/`,
  `superseded-phaseB-ANALYSIS/`, `tools-reference/`, `manifests/`,
  `reference-docs/`, `MANIFEST.md` + per-file `.sha256`).
- **Not migrated as code:** all 11 legacy tools (technique notes only).

## 6. Historical material retained

- Legacy source retains 62 canonical files (README + `00_PROJECT/`–`07_REPORTS/`,
  ~73 MB) as the source archive.
- External store retains full derived bulk + Phase-B superseded set + tool
  reference + manifests (reproducible without polluting git).

## 7. Duplicates

150+ mirror files verified byte-identical (full SHA-256, 73 groups) across
`SOURCE_PROJECT/`, `99_ARCHIVE/...mirror`, `CSI_VERIFY_001/`, `CSI_SENSE_001/`,
`CSI-SENSE-001/` pilot layout, root copies, `08_CHECKSUMS_MANIFESTS/` copies.
Migrated once from canonical paths; rest classified VERIFIED DUPLICATE.

## 8. Obsolete material

`99_ARCHIVE/historical_duplicates/` (quarantined dups), `obsolete_phase_b_files/`
(2× 0-byte checksums + superseded plan copy `edd19d0f`, preserved externally
first), Phase-B-era stats/figs (superseded by `05_ANALYSIS`, preserved
externally), stale Live-USB/Google-Drive staging narrative (condensed, not copied).

## 9. Deleted/moved material

- **Deleted: 0 files** (no destructive deletion anywhere).
- **Moved (safe-move): 170 files** from the legacy source to
  `~/Downloads/RF Vision Legacy Cleanup/` (D-class duplicates + E-class obsolete,
  each SHA-verified pre-move). Manifest:
  `docs/research/legacy/LEGACY-CLEANUP-MANIFEST.md` (+ identical copy in the
  quarantine dir). Quarantine may be deleted by the user at will — nothing in it
  is unique.
- Legacy end state: 62 canonical files (see §6); current repo is the ONE authority.

## 10. Credential findings

Wi-Fi password plaintext in `firmware_versions.json` + VERIFY report (×2) +
folder audit (×1) + mirrors — **4 occurrences redacted** (`REDACTED`), values
never reproduced. BSSID/MAC/SSID retained (reproducibility IDs). No API
keys/tokens/private/SSH keys found. Current repo verified clean (0 hits).
Full audit: `docs/security/LEGACY_CREDENTIAL_AUDIT.md`. Recommendation: rotate
the Wi-Fi password.

## 11. License findings

No third-party code/headers in legacy (scan of all `.py/.md/.txt/.c/.h/.ino`
for license/copyright/SPDX/MIT/Apache/GPL — prose mentions only). No
`THIRD_PARTY_NOTICES.md` change required (verified unmodified). Legacy tools
treated as original project code under MIT; future adaptations attribute
`RF Vision legacy (CSI-SENSE-001, 2026-09-06, pre-Ubuntu archive)`.

## 12. Checksum verification

- 28/28 in-repo files match migration records (post-redaction SHAs; 11
  transformed incl. 10 MD headers + 4 redactions + 1 wording change, 17
  byte-identical).
- 59/59 external files match (byte-identical; R1 `51d47ce…`, R2 `4734dcf…`,
  R3 `ce04708…` confirmed).
- 170/170 moved files SHA-matched pre-move (6 initially-unmatched small files
  preserved externally first, then moved).
- Transformed files never claimed byte-identical (original + new SHAs in
  `LEGACY-MIGRATION-PROVENANCE.md`).

## 13. Test results

`python3 -m pytest tests/ -q` from repo root: **107 passed in 2.72 s**
(baseline grown from the 68-test foundation through RFVISION-003/004/005; green
before and after — migration is docs-only, no code touched).

## 14. Final project structure (new paths only)

```
docs/research/legacy/{plan+8 reports, metadata/, evidence/, derived-meta/, TOOL-REFERENCE.md, LEGACY-CLEANUP-MANIFEST.md}
docs/research/{LEGACY-MIGRATION-PROVENANCE.md, RFVISION-006-LEGACY-CONSOLIDATION-REPORT.md (this file)}
docs/hardware/legacy/{hardware_identity, firmware_versions.REDACTED, capture_config}.json
docs/security/LEGACY_CREDENTIAL_AUDIT.md
```

No parallel legacy structure, no `.git` copied, no `__pycache__`/installer/binary
pollution, no raw bytes in git (`.log/.npz/.csv` absent — `.gitignore`-consistent).

## 15. Git commit

- Migration commit (H1): `docs: consolidate legacy RF Vision project material`
  (all §5 in-repo files + provenance + credential audit + cleanup manifest).
- Record commit (H2): `docs: record RFVISION-006 commit hash in consolidation report`
  (this file with H1 filled in) — follows the repo's 002 pattern
  (RFVISION-003 §16, foundation §21).
- H1: `FILL_H1` · H2: `FILL_H2` (filled immediately post-commit; see `git log --oneline -3`).
- Remote: none (local-only; GitHub policy remains user-deferred per RFVISION-003 §18).

## 16. Unresolved items

1. Boot 15 s capture `5608f152…` permanently unavailable (ephemeral Live `/tmp`).
2. Room geometry never measured (placeholder retained as gap record).
3. Trials 2–10 never run; pilot N=1 INCONCLUSIVE — no sensing claim possible.
4. RFVISION-003 live-CSI FAIL stands (needs physical-access 003R remediation).
5. Quarantine-dir deletion decision left to the user.
6. `git` CLI lives at `~/.local/gitroot/usr/bin/git` (not on default `PATH`).

## 17. Next actions (proposals, NOT started)

1. RFVISION-003R re-capture with physical access (cable/port/firmware read-only checks).
2. Future `experiments/analysis/` work may adapt legacy Q1–Q6 stats / baseline /
   PCA-STFT / `validate_raw` thresholds — each needs its own work item + tests.
3. Rotate Wi-Fi password (see §10).
4. GitHub remote creation remains user-deferred.

END OF RFVISION-006 REPORT.
