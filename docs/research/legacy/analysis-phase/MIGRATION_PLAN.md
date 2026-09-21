# RFVISION-006 — MIGRATION PLAN (proposal — NO changes made yet)

- Status: PROPOSAL ONLY. The current repo (`~/Desktop/RF Vision`) has NOT been modified. The legacy source has NOT been deleted or moved.
- Approval gate: do NOT execute §6–§9 until the user replies with the exact phrase `APPROVED — MIGRATE LEGACY RF VISION MATERIAL`.
- Conventions: `LEGACY:` = `~/Downloads/RF Vision Files-20260921T163602Z-1-001/RF Vision Files/...`; `CUR:` = `~/Desktop/RF Vision/...`; `EXT:` = `~/RFVision-Research-Data/...` (outside git).
- Sanitization rule: every migrated JSON/MD is passed through a redaction pass that replaces the Wi-Fi password value with `REDACTED` and rewrites `nmcli --show-secrets` transcript lines to provenance notes. BSSID/MAC/SSID/gateway stay (reproducibility IDs, per legacy README §Security). Redaction is recorded in provenance (original SHA vs new SHA — never claimed byte-identical).
- Size rule: NOTHING larger than ~200 KB goes into git. Raw `.log` (MBs) and derived `.npz/.csv` (MBs) go to `EXT:` with manifests only in git.

## A. MUST MIGRATE (loss would damage provenance or block future CSI-SENSE work)

| # | Legacy source (canonical, dedup: migrate ONE copy) | Destination | WHY (one line) | Sanitization / transform |
|---|---|---|---|---|
| A1 | `LEGACY:00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` (`c72b2c4b`) | `CUR:docs/research/legacy/CSI-SENSE-001_PLAN_v1.1.md` | Only executable A–F protocol; template has no detail | Redact if password present (verify at migration); prepend provenance header (source path + SHA + date + HISTORICAL / PRE-UBUNTU label) |
| A2 | `LEGACY:01_HARDWARE/hardware_identity.json` (`f35a5223`) | `CUR:docs/hardware/legacy/CSI-SENSE-001_hardware_identity.json` | Exact pre-transition identities unrecoverable otherwise | Rewrite `security: "WPA2-PSK (from nmcli --show-secrets)"` → `"WPA2-PSK (method on file, value not migrated)"`; keep BSSID/MAC |
| A3 | `LEGACY:02_FIRMWARE/firmware_versions.json` (`0b286912`) | `CUR:docs/hardware/legacy/CSI-SENSE-001_firmware_versions.REDACTED.json` | Build/flash transcript corroborates baseline pins | Replace password value with `REDACTED`; record original SHA in provenance |
| A4 | `LEGACY:02_FIRMWARE/capture_config.json` (`edcfbf00`) | `CUR:docs/hardware/legacy/CSI-SENSE-001_capture_config.json` | Only machine-readable gate definition | None needed (no password in this file — re-verify at migration) |
| A5 | `LEGACY:04_EVENTS_METADATA/metadata/study_metadata.json`, `environment_trial01.json`, `trial_01_metadata.json` (`CSI-SENSE-001/metadata/` copies: `smoke_test_metadata.json`), `room_geometry.json` (NULL placeholder) | `CUR:docs/research/legacy/metadata/` (same basenames) | Study/env/trial descriptors + gap record (UNKNOWNs/NULLs prevent false claims) | None (no passwords found in these; re-verify) |
| A6 | `LEGACY:03_RAW_DATA/CSI_SENSE-001/trial_01/{capture_meta_trial01.json, validate_trial01.json, events_trial01.jsonl}` + `LEGACY:03_RAW_DATA/CSI_SENSE-001/smoke_test/{capture_meta_trial00.json, validate_smoke.json}` + `LEGACY:04_EVENTS_METADATA/events/events_trial01.jsonl` | `CUR:docs/research/legacy/evidence/` (same basenames) | Ground-truth + validation sidecars needed to interpret R2/R3 | None (re-verify); dedup `events_trial01.jsonl` (two identical copies → one) |
| A7 | `LEGACY:07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` (`d8b669a2`), `CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` (`6e0a1779`) | `CUR:docs/research/legacy/` (same basenames) | PASS evidence the current tree cites but lacks | Redact 2 password lines → `CONFIG_EXAMPLE_WIFI_PASSWORD="REDACTED"` + `(connection details verified via nmcli — values not reproduced)` |
| A8 | `LEGACY:07_REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md`, `CSI-SENSE-001_PHASE_C_READINESS_REPORT.md`, `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md`, `CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` | `CUR:docs/research/legacy/` (same basenames) | Phase-B/C/pilot/gate record incl. INCONCLUSIVE verdict | Redact if needed (scan at migration); keep verdict labels verbatim |
| A9 | `LEGACY:07_REPORTS/FINAL-FOLDER-AUDIT-001.md`, `FINAL-ARCHIVE-AUDIT-002.md` (one copy each) | `CUR:docs/research/legacy/` (same basenames) | Provenance of the archive itself | Redact password-adjacent lines if present |
| A10 | Raw R1/R2/R3 (ONE copy each, see hashes below) | `EXT:legacy-csi-verify-001/CSI_RAW_70s_921600_20260906_205638.log` (R1); `EXT:legacy-csi-sense-001/raw/trial_01/...` (R2 + sidecars); `EXT:legacy-csi-sense-001/raw/smoke_test/...` (R3 + sidecars) | Immutable evidence; unique in project family | Byte-identical copy (`cp`, then `sha256sum -c`); `chmod a-w`; manifest records source/dest/SHA/size |
| A11 | Small derived metas: `LEGACY:05_ANALYSIS/trial_01/{parse_meta_trial01.json, features_trial01.json, baseline_model_trial01.json, pca_spectrogram_trial01.json, figures/temporal_plots_demo_manifest.json}` + `smoke_test/parse_meta_trial00.json` | `CUR:docs/research/legacy/derived-meta/` | Proves toolchain ran; KB-scale; interprets derived payloads without their MBs | None |
| A12 | Manifest excerpts: hashes of every migrated item + `LEGACY:08_CHECKSUMS_MANIFESTS/PATH_PROVENANCE.md` note | `CUR:docs/research/LEGACY-MIGRATION-PROVENANCE.md` (new, per §17–18 of the operation) + `CUR:docs/security/LEGACY_CREDENTIAL_AUDIT.md` (new, REDACTED) + `CUR:docs/research/RFVISION-006-LEGACY-CONSOLIDATION-REPORT.md` (final report) | Provenance + credential audit + operation report are REQUIRED deliverables | Password values never appear; original SHAs listed for auditability |

Raw hashes (authoritative): R1 `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` (3,566,098 B); R2 `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` (14,304,955 B); R3 `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` (499,069 B).

## B. SHOULD MIGRATE (valuable reference; docs-only, no active code)

| # | Legacy source | Destination | WHY |
|---|---|---|---|
| B1 | `LEGACY:06_TOOLS/csi_capture/backup_verify.py` + `LEGACY:07_REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` (already A8) | Design note in `CUR:docs/research/legacy/TOOL-REFERENCE.md` (new, short) + keep script OUTSIDE git at `EXT:legacy-csi-sense-001/tools-reference/` (one copy of all 11 tools) | Unique safety-gate design; future `tools/` work can adapt it without inheriting untested code |
| B2 | `LEGACY:06_TOOLS/csi_analysis/{statistical_tests.py, baseline_model.py, pca_spectrogram.py}` + `analysis_config.json` | Same `TOOL-REFERENCE.md` (method summaries: Q1–Q6 FDR, μ/σ/cov + walk covariate, PCA+STFT 2 s/90 %, params) + scripts to `EXT:` reference dir | No current counterparts; only significance-testing/statistical-baseline methods in the family |
| B3 | `LEGACY:06_TOOLS/csi_analysis/parse_csi.py` (glued `re.finditer` technique) + `csi_capture/validate_raw.py` (thresholds) | `TOOL-REFERENCE.md` (technique note + threshold table) + scripts to `EXT:` | Documents validated technique; thresholds are ADAPT-candidates for future test vectors |
| B4 | `LEGACY:08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` (full) + `LEGACY:BACKUP_MANIFEST.md` | Full files to `EXT:legacy-csi-sense-001/manifests/`; condensed summary into `LEGACY-MIGRATION-PROVENANCE.md` | Preserves checksum discipline without bulk-importing stale Live-staging narrative |
| B5 | `LEGACY:CSI_SENSE_001/ANALYSIS/PROTOCOL.md`, `README.md` (Phase-B era), `LEGACY:README.md` (archive index) | Cited (not copied) in final report §4/§6; full text to `EXT:` reference dir | Superseded but citable; keeps git diff focused |

## C. HISTORICAL ARCHIVE (keep OUTSIDE git, referenced by manifest)

- ONE external copy of the derived bulk: `LEGACY:05_ANALYSIS/trial_01/{parsed_trial01.csv, parsed_trial01.npz, features_trial01.npz, baseline_model_trial01.npz, pca_spectrogram_trial01.npz, figures/*.png}` + `smoke_test/{parsed_smoke.csv, parsed_trial00.csv, parsed_trial00.npz}` → `EXT:legacy-csi-sense-001/derived/` (deduplicate the `CSI-SENSE-001/analysis/` mirror — same bytes, do not copy twice).
- ONE external copy of the full 11-tool reference set from `LEGACY:06_TOOLS/` → `EXT:legacy-csi-sense-001/tools-reference/` (other three mirrors not copied).
- Manifest (`EXT:legacy-csi-sense-001/MANIFEST.md` + per-file `.sha256`) records source path, destination, SHA-256, size, provenance for every external file.
- Rationale: reproducible but large; `research/datasets/README.md` forbids bulk in git; external preservation satisfies the scientific-evidence rule without polluting history.

## D. DUPLICATE (do not migrate; verification record only)

- All of: `LEGACY:SOURCE_PROJECT/` (full mirror), `LEGACY:99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/`, `LEGACY:CSI_VERIFY_001/`, `LEGACY:CSI_SENSE_001/`, `LEGACY:CSI-SENSE-001/` pilot-era layout where byte-identical to canonical, `LEGACY:03/04/05` mirrors of each other, root copies (`BACKUP_MANIFEST.md`, `BACKUP_COMPLETE.md`, `BACKUP_BEFORE_REBOOT.md`, pilot report, both audits), `08_CHECKSUMS_MANIFESTS/` copies of reports, `CHECKSUMS/SHA256SUMS.txt` (older generation).
- Verification: full-byte SHA-256 equality already computed (73 duplicate groups, 227 files). Migration provenance will list one representative hash per group; cleanup manifest will mark the rest VERIFIED DUPLICATE.

## E. OBSOLETE (do not migrate)

- `LEGACY:99_ARCHIVE/historical_duplicates/` (4 quarantined dups) — superseded by canonical copies.
- `LEGACY:99_ARCHIVE/obsolete_phase_b_files/` (2× 0-byte `checksums.sha256.*.empty` + Downloads-duplicate plan `edd19d0f…`) — empty placeholders + superseded plan copy.
- `LEGACY:CSI_SENSE_001/ANALYSIS/` Phase-B-era stats/figs where superseded by `05_ANALYSIS/trial_01/` (keep ONE external reference copy per §C only if a hash differs; identical hashes → duplicate).
- Stale Live-USB narrative (`/cow` overlay capacity notes, Google-Drive-upload-before-reboot instructions, `/home/ubuntu` execution paths) — facts condensed into provenance; instructions not migrated.

## F. DELETE (proposed cleanup-class after verified migration — EXECUTE ONLY post-approval + post-verification)

- From the OLD Downloads folder ONLY, and ONLY via safe-move to `~/Downloads/RF Vision Legacy Cleanup/` first (no destructive `rm -rf` on the whole tree):
  1. All D-class VERIFIED DUPLICATES (after manifest confirms each hash migrated or intentionally dropped).
  2. All E-class OBSOLETE (empty checksums, quarantined dups).
  3. Staging narratives already condensed (root `BACKUP_COMPLETE.md`, `BACKUP_MANIFEST.md` copies — originals preserved in `08_CHECKSUMS_MANIFESTS/` + external manifests dir).
- NEVER delete pre-verification: R1/R2/R3 (until external copies checksum-verified), unique reports/plan/metadata (until git copies verified), anything UNDECIDED (none remain, but rule stands).

## 5. Security handling (credential audit → `docs/security/LEGACY_CREDENTIAL_AUDIT.md`, REDACTED)

- Findings to record (no values): (1) Wi-Fi password plaintext in `02_FIRMWARE/firmware_versions.json` `sdkconfig.defaults` + mirrors; (2) same password in `CSI-VERIFY-001_FINAL_REPORT.md` ×2 lines + audit-report mirrors; (3) `nmcli --show-secrets` methodology mentions (credential-adjacent, no additional values); (4) BSSID/MAC/SSID/gateway retained by policy (not secrets); (5) NO API keys/tokens/private/SSH keys found; (6) current repo verified CLEAN (0 hits for password value / `EXAMPLE_WIFI_PASSWORD`; `sdkconfig.defaults` contains no SSID/password).
- Recommendations: rotate the Wi-Fi password (it lived in a Live-USB archive staged for cloud upload); treat the legacy archive as credential-bearing until cleaned; never commit the value (enforced by redaction pass + pre-commit grep in validation).
- License handling: no third-party content found in legacy → NO `THIRD_PARTY_NOTICES.md` change. If `validate_raw.py` thresholds are ever adapted, attribute as RF Vision legacy (path + hash) under project MIT.

## 6. Migration execution (AFTER approval only)

1. Create `CUR:docs/research/legacy/`, `CUR:docs/hardware/legacy/`, `CUR:docs/research/legacy/{metadata,evidence,derived-meta}/`, `CUR:docs/security/` (as needed).
2. For each A-item: copy ONE canonical source → destination, apply redaction pass, prepend provenance header (legacy path + legacy SHA + migration date + HISTORICAL / PRE-UBUNTU tag where host-specific).
3. For A10/C: `mkdir -p EXT:legacy-csi-{verify-001,sense-001}/{raw,derived,tools-reference,manifests}`; byte-identical `cp`; `sha256sum -c`; `chmod a-w` raw; write `MANIFEST.md` + per-file `.sha256`.
4. Write `CUR:docs/research/LEGACY-MIGRATION-PROVENANCE.md` (every artifact: legacy source, legacy SHA, destination, action, reason, date; transformed files list original + new SHA).
5. Write `CUR:docs/security/LEGACY_CREDENTIAL_AUDIT.md` (REDACTED) and `CUR:docs/research/RFVISION-006-LEGACY-CONSOLIDATION-REPORT.md` (16 sections per operation §25).
6. Validate (§7), then cleanup (§8), then single commit (§9).

## 7. Validation (must all pass before cleanup/commit)

1. `ls`/`sha256sum -c` every migrated file (git + external); transformed files show new SHA ≠ original SHA (expected — redaction).
2. Grep migrated tree for password value + `EXAMPLE_WIFI_PASSWORD` + `BEGIN .*PRIVATE KEY` → 0 hits.
3. `python3 -m pytest tests/ -q` from `CUR:` → green (baseline: foundation 68 tests; re-confirm count at migration time).
4. `git status --short` / `git diff --stat` review (requires git binary — currently MISSING in this env; migration must be executed where `git` exists, or install user-space git first as done in the foundation operation).
5. Documentation link check (new `legacy/` paths referenced from report + provenance resolve).
6. Project-tree check (no parallel legacy structure; no `.git` copied; no `__pycache__`/installer/binary pollution).
7. License check (`THIRD_PARTY_NOTICES.md` unchanged is correct; confirm).

## 8. Cleanup preview (post-verification only)

- Safe-move D+F classes to `~/Downloads/RF Vision Legacy Cleanup/`; write `LEGACY-CLEANUP-MANIFEST.md` (moved file, reason, destination, verification status).
- Old Downloads folder end state: only unique historical material with no active-project home (expected: essentially nothing beyond already-mirrored content, OR the folder retained as-is if the user prefers — decision at cleanup time, never automatic).
- Current repo remains the ONE authority throughout.

## 9. Git (post-verification only)

- Commit inside `CUR:` only. Message: `docs: consolidate legacy RF Vision project material` (or code-descriptive variant if an ADAPT is approved — none proposed now).
- Exclude: credentials, raw/derived bulk, caches, `EXT:` paths, legacy `.git` (none exists), installers/binaries.
- Record commit hash in the final report. No push without explicit instruction (remote policy follows RFVISION-003 §18 — user-deferred).

## 10. STOP — awaiting approval

ANALYSIS COMPLETE. Deliverables in `/tmp/rfvision-legacy-audit/`: `LEGACY_INVENTORY.md`, `CURRENT_VS_LEGACY_MATRIX.md`, this `MIGRATION_PLAN.md` (+ `all_legacy_files.txt`, `all_current_files.txt` working lists).

Required approval phrase: `APPROVED — MIGRATE LEGACY RF VISION MATERIAL`

No modification has been made to `~/Desktop/RF Vision` or to the legacy source. Do not proceed to §6–§9 without approval.
