# RFVISION-007 — FINAL PROJECT CONSOLIDATION REPORT

- Operation: RFVISION-007-FINAL-PROJECT-CONSOLIDATION (PROJECT/DATA CLEANUP only)
- Date (UTC): 2026-09-21
- Freeze state at start: `main`, clean tree, HEAD `06fb23d`; no reinit, no second repo.

## 1. Final project root

`~/Desktop/RF Vision` — the one authoritative RF Vision Git repository.

## 2. Final Git root

`git rev-parse --show-toplevel` → `~/Desktop/RF Vision`
(`git` via `~/.local/gitroot/usr/bin/git`, not on default `PATH`).
Log tail at freeze: `06fb23d / ac09bd7 / 8f8c7ea / 106f16c / 779e306`.

## 3. Active project structure

Modular, no legacy trees in root, no duplicate firmware/CSI/DSP trees, no
upstream copies, no nested `.git`. Package layout with one `__init__.py` per
package (36 empty markers — intentional, not duplicates):

```
ai/ (26) · csi/ (23) · dsp/ (23) · sensing/ (20) · localization/ (22)
realtime/ (13) · web/ (36) · unity/ (2: integration/, project/)
firmware/ (12: acquisition/, esp32/, protocols/, traffic_gen_reference/)
tests/ (36) · config/ (5) · experiments/ (5) · research/ (3)
tools/ (5) · visualization/ (9) · docs/ (70+) · logs/ (ignored)
```

Full concise tree: `docs/research/RFVISION-007-FINAL-TREE.txt`.
233 tracked files at freeze → 238 after this commit (3 analysis-phase docs +
this report + final tree). Only bulk-adjacent tracked file remains
`docs/reference/example_csi.csv` (small fixture, explicitly allowlisted in
`.gitignore`); no `.log/.npz/.bin/caches/secrets/installers` tracked.
`.gitignore` covers `*.log, *.csv (minus fixture), *.pkl/*.pt/*.pth`,
firmware build outputs, Unity generated dirs, secrets, caches.

## 4. Material consolidated

Priority order kept (§3): validated foundation → 004 RuView architecture →
005 UI → 006 legacy material → historical evidence. Present and verified:
source code, firmware, CSI modules, DSP, sensing/localization/AI-XAI
foundations, realtime server, web UI, Unity integration contract, tests,
config, research protocols, architecture + hardware docs (incl.
`docs/hardware/BASELINE.md`), `SCIENTIFIC_VALIDATION_STATUS.md`,
`THIRD_PARTY_NOTICES.md`, RuView provenance (`RUVIEW_IMPLEMENTATION_PROVENANCE.md`,
`RUVIEW_REUSE_AND_LICENSE_AUDIT.md`, `SOURCE_PROVENANCE.md`),
`LEGACY-MIGRATION-PROVENANCE.md`, historical reports under
`docs/research/legacy/`, `LEGACY_CREDENTIAL_AUDIT.md`.
Nothing overwritten with legacy copies; no obsolete architecture reintroduced.
New in this operation: `docs/research/legacy/analysis-phase/` (see §8).

## 5. Historical material preserved

- In git (36 files): `docs/research/legacy/` — plan v1.1, 8 phase/verify/audit
  reports, metadata ×5, evidence ×5, derived-meta ×6, `TOOL-REFERENCE.md`,
  `LEGACY-CLEANUP-MANIFEST.md`, `analysis-phase/` (inventory, matrix, plan);
  `docs/hardware/legacy/` (identity, firmware REDACTED, capture config).
- Outside git, byte-identical (59 files, 74,058,859 B): see §6.

## 6. External research-data inventory

`~/RFVision-Research-Data/` — 115 files, raw read-only (`444`):

| Location | Files | Content |
|---|---|---|
| `legacy-csi-verify-001/` | 2 | R1 VERIFY-70s raw log + `.sha256` |
| `legacy-csi-sense-001/raw/` | 6 | R2 trial_01 + R3 smoke logs, `capture_stdout.log`, sidecars |
| `legacy-csi-sense-001/derived/` | 36 | parsed CSV/NPZ, parse-meta, features, baseline, PCA, figures + sidecars |
| `legacy-csi-sense-001/superseded-phaseB-ANALYSIS/` | 26 | Phase-B superseded set + sidecars |
| `legacy-csi-sense-001/tools-reference/` | 22 | 11 legacy tools + sidecars (reference only) |
| `legacy-csi-sense-001/manifests/` | 15 | backup/path/SHA manifests, 5 unique-small + sidecars |
| `legacy-csi-sense-001/reference-docs/` | 6 | archive + phaseB READMEs, protocol + sidecars |
| `legacy-csi-sense-001/MANIFEST.md` | 1 | 59-entry external manifest |
| `rfvision-003/` | 1 | `csi_raw_60s.bin` (003-phase capture, untouched by this op) |

Every preserved dataset has SHA-256 sidecar + provenance (source path,
experiment ref) via `MANIFEST.md` + `LEGACY-MIGRATION-PROVENANCE.md`.
R1 `51d47ce9…caed24` / R2 `4734dcf5…27b8a40a` / R3 `ce047085…3646e37ca4`
re-verified this operation — match, unmodified, still outside git.

## 7. Duplicate files removed

- In-repo SHA-256 scan (233 tracked files): exactly 1 group — 36 empty
  `__init__.py` package markers (hash `e3b0c44…`). Intentional Python
  packaging; 0 actionable duplicates; 0 files removed from the repo.
- Quarantine (`~/Downloads/RF Vision Legacy Cleanup/`): all 170 content files
  re-verified non-unique this operation — 137 byte-identical to repo/research-data
  content; 25 pre-header originals of in-repo transformed docs (header strip ⇒
  match); 2 pre-redaction firmware JSONs (password→REDACTED ⇒ match); 3
  `hardware_identity.json` mirror variants differing only in one
  provenance-wording value (`router.security` suffix; no credential value);
  1 `PLAN.md` twin byte-identical to canonical v1.1; 2 superseded-plan copies
  byte-identical to external unique-small preservation. 170/170 non-unique ⇒
  **quarantine directory DELETED** (+ its manifest copy; manifest retained in
  repo at `docs/research/legacy/LEGACY-CLEANUP-MANIFEST.md`). Method:
  full-SHA recompute + normalization, not filename matching.
- Legacy Downloads (62 files): every file content-covered — 19 byte-identical
  in repo, 13 transformed-into-repo (provenance records both SHAs), 30
  byte-identical external. Classification: all DUPLICATE-class
  (content preserved under A/B with provenance). **Retained untouched** as a
  cold second copy (it still holds the only other copy of R1/R2/R3 raw bytes);
  status: verified redundant, no longer required. Nothing unique deleted.

## 8. Temporary files removed

- `/tmp/rfvision-legacy-audit/` (204 KB, 11 files: inventory, matrix, plan,
  scripts, machine records): the 3 analysis-phase reports had no in-repo copy,
  so they were preserved byte-identical (0 credential hits) at
  `docs/research/legacy/analysis-phase/` FIRST (machine records' content lives
  on in `LEGACY-MIGRATION-PROVENANCE.md` + manifests). Then deleted.
- `/tmp/ruview-audit/` (172 MB: upstream RuView tarball + extracted tree):
  third-party upstream material, intentionally never in-repo (§11); required
  outputs (004 audit report + third-party provenance docs) confirmed in-repo.
  Deleted.
- Out of scope, left untouched: loose `/tmp/rfvision_*.py`, `/tmp/cdp_probe.py`
  (unique working scripts, not in repo, not in §7's named list), `/tmp/*.png`
  screenshots, `rfvision005_server.log/.pid` — user decision.

## 9. Legacy Downloads cleanup

Source `~/Downloads/.../RF Vision Files-20260921T163602Z-1-001` now holds only
the 62 canonical files (`README` + `00_PROJECT/`–`07_REPORTS/`). Verified
62/62 preserved elsewhere (§7) before any deletion elsewhere; deletion applied
only to quarantine/tmp. End state: downloads dir retained as cold copy,
no longer required — project does not depend on it.

## 10. Credential scan

Full-repo scan this operation: Wi-Fi password value, AWS keys, generic API-key
patterns, bearer tokens, private-key blocks, SSH keys, password assignments —
**0 hits** (36 `REDACTED`/methodology contexts excluded by design; values never
printed). Sanitized legacy files remain sanitized. External byte-identical
archives retain original bytes by design (documented in the credential audit);
rotation of the Wi-Fi password still recommended.

## 11. License/provenance status

No third-party code/headers in legacy material (006 finding stands);
`THIRD_PARTY_NOTICES.md` unmodified. RuView provenance chain intact (§4).
Legacy provenance chain intact + extended (`analysis-phase/`). No upstream
repository copies introduced. No `THIRD_PARTY_NOTICES.md` change required.

## 12. SHA verification

- R1/R2/R3 external: match (see §6).
- Legacy-source coverage: 62/62 files (19 exact-repo + 13 transformed-repo +
  30 exact-external).
- Quarantine pre-deletion: 170/170 non-unique (see §7).
- In-repo bulk check: only the allowlisted fixture; no raw bytes in git.
- Analysis-phase copies: byte-identical (3/3).

## 13. Test result

`python3 -m pytest tests/ -q` after all deletions: **107 passed in 2.72s** —
baseline unchanged (count and result identical before/after; cleanup touched no
code, only docs-additive + external deletions).

## 14. Final Git commit

One focused commit: `chore: finalize RF Vision project consolidation`
(files: `docs/research/legacy/analysis-phase/` ×3,
`docs/research/RFVISION-007-FINAL-PROJECT-CONSOLIDATION-REPORT.md`,
`docs/research/RFVISION-007-FINAL-TREE.txt`). Staged: docs only — no raw CSI,
NPZ/CSV bulk, caches, secrets, installers, upstream repos. Hash: see operation
delivery (`git log --oneline -1`); tree clean at close.

## 15. Remaining project gaps

1. RFVISION-003 live-CSI FAIL stands — needs physical-access 003R remediation.
2. Boot 15 s capture permanently absent; room geometry unmeasured (gap records kept).
3. Pilot N=1 INCONCLUSIVE — no sensing claim; trials 2–10 never run.
4. Wi-Fi password rotation still recommended (§10).
5. GitHub remote creation still user-deferred.
6. Raw evidence now relies on research-data + legacy-downloads cold copies
   (quarantine gone by design — no working-copy redundancy left in Downloads).
7. Loose `/tmp` working scripts/screenshots left for the user (§8).
8. Future analysis adaptations (Q1–Q6 stats, thresholds) each need their own
   work item + tests. No new phase started.

END OF RFVISION-007 REPORT.
