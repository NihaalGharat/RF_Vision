# RFVISION-006 — LEGACY INVENTORY (Phase 1 audit)

- Operation: RFVISION-006-LEGACY-CONSOLIDATION, ANALYSIS phase
- Date (UTC): 2026-09-21
- Legacy source (absolute): `~/Downloads/RF Vision Files-20260921T163602Z-1-001`
- Canonical inner root: `~/Downloads/RF Vision Files-20260921T163602Z-1-001/RF Vision Files`
- Current authoritative repo: `~/Desktop/RF Vision` (NOT modified in this phase)
- Audit workspace: `/tmp/rfvision-legacy-audit/` (outside both projects)
- Method: read-only inspection. No deletions, no copies into the current repo in this phase.
- git binary: NOT available in this environment (`git: command not found`); current `.git/` directory exists but history could not be traversed via CLI. `.git/HEAD`, `index`, `logs` inspected by file read only.

## 1. Source verification

| Item | Value |
|---|---|
| Legacy path exists | YES (both outer wrapper and inner `RF Vision Files/`) |
| Legacy total size | 162 MB (`du -sh`) |
| Legacy total files | 232 (`find -type f \| wc -l`) |
| Legacy directory count | 73 (`find -type d \| wc -l`) |
| Current repo size | 6.1 MB (`du -sh`, includes `.git/`) |
| Current tracked-ish files (excl `.git`, `__pycache__`, `.pytest_cache`) | 202 |
| Legacy `.git` presence | NONE (`find -maxdepth 4 -name .git` → no hits) |
| Legacy archives (`.zip/.tar*/.7z/.rar`) | NONE |
| Legacy timestamps (content) | 2026-09-06 (all inner files: plan, reports, captures, metadata) |
| Legacy timestamps (wrapper) | 2026-09-21 22:07 (extraction of the `...-20260921T163602Z-1-001` bundle) |
| File-type breakdown (by extension, case-insensitive) | `json` 68, `md` 53, `py` 40, `png` 20, `npz` 13, `log` 11, `sha256` 7, `csv` 6, `jsonl` 5, `txt` 3, plus 4 suffixed historical-duplicate markers (`.SOURCE_PROJECT_Desktop`, `.CSI_SENSE_001_RAW_DATA`, `.root_duplicate`, `.duplicate`, `.empty`, `.csi_sense_001_raw_data`) |
| Raw data present | YES — 3 unique raw captures (see §3), each with sidecars |
| Screenshots/images | 20× `.png` (analysis figures only; no setup/room photos — `room_geometry_photo_*.jpg` absent, tape/photo protocol unfulfilled) |
| Datasets/logs/installers/binaries/temp | `.npz/.csv/.log` only; NO installers, NO binaries, NO ESP-IDF toolchain, NO `.pyc/__pycache__`, NO firmware `.bin` files (only SHA-256 pins) |

## 2. Structural overview (inner root)

```
RF Vision Files/
├── 00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md      # canonical plan
├── 01_HARDWARE/hardware_identity.json               # canonical HW identity
├── 02_FIRMWARE/{firmware_versions,capture_config}.json
├── 03_RAW_DATA/CSI_VERIFY/ + CSI_SENSE-001/{trial_01,smoke_test}/
├── 04_EVENTS_METADATA/{events,metadata}/
├── 05_ANALYSIS/{trial_01,smoke_test}/
├── 06_TOOLS/{csi_capture (4 py), csi_analysis (7 py + json)}   # canonical tools
├── 07_REPORTS/ (8 md)                               # canonical reports
├── 08_CHECKSUMS_MANIFESTS/ (SHA256SUMS + manifests + audits + provenance)
├── BACKUP_MANIFEST.md / BACKUP_COMPLETE.md / BACKUP_BEFORE_REBOOT.md (root copies)
├── CSI-SENSE-001_PHASE_C_PILOT_REPORT.md (root copy)
├── FINAL-FOLDER-AUDIT-001.md / FINAL-ARCHIVE-AUDIT-002.md (root copies)
├── README.md                                        # archive-level README (volatile-Live warning)
├── CHECKSUMS/SHA256SUMS.txt
├── CSI_VERIFY_001/  (2 reports + 1 raw log copy)
├── CSI_SENSE_001/   (PLAN/REPORTS/TOOLS/METADATA/RAW_DATA/ANALYSIS mirror, older naming)
├── CSI-SENSE-001/   (BACKUP_BEFORE_REBOOT + analysis/checksums/events/metadata/raw/reports — pilot-era layout)
├── CSI-SENSE-001/   (same, hyphen variant — pilot-era layout)
├── 04_EVENTS_METADATA / 03_RAW_DATA / 05_ANALYSIS (canonical splits of the same content)
├── SOURCE_PROJECT/{Desktop (8), data/CSI-SENSE-001, tools}     # pre-archive mirror
├── 99_ARCHIVE/historical_duplicates/ (4) + obsolete_phase_b_files/ (3) + SOURCE_PROJECT_mirror_20260906/ (full mirror)
```

Critical dedup finding (byte-identical SHA-256 over full file bytes):

- 232 files → **78 unique content hashes**.
- **227 of 232 files sit in 73 duplicate groups** (i.e. the archive is ~3–7 mirrors of the same ~78 payloads under different directory names).
- Largest duplicated payloads: `features_trial01.npz` 29,155,642 B ×2; `CSI-SENSE-001_..._trial01_raw.log` 14,304,955 B ×2; `parsed_trial01.csv` 14,092,781 B ×2; `CSI_RAW_70s...log` 3,566,098 B ×7; plus `.npz/.png/.csv/.json/.md/.py` mirrors ×2–4.
- Consequence: migration must deduplicate to ONE canonical copy per hash; the remaining ~150 files are VERIFIED DUPLICATES (DELETE-class after verification, never migrated individually).

## 3. Immutable raw captures (unique content)

| # | Canonical path (`03_RAW_DATA/...`) | SHA-256 (full) | Size | Copies in archive | Provenance |
|---|---|---|---|---|---|
| R1 | `03_RAW_DATA/CSI_VERIFY/CSI_RAW_70s_921600_20260906_205638.log` | `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` | 3,566,098 B | 7 (CSI_VERIFY_001/, CSI_SENSE_001/RAW_DATA/, SOURCE_PROJECT/Desktop/, 03_RAW_DATA/, 99_ARCHIVE ×3) | CSI-VERIFY-001 PASS: 7,152 valid vectors / 70 s, ~102 Hz wall / 141 Hz chip, `len 128` → 64 subcarriers, ch 1, 0 missing seq |
| R2 | `03_RAW_DATA/CSI_SENSE-001/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | 14,304,955 B | 2 (03_RAW_DATA + CSI-SENSE-001/raw) | CSI-SENSE-001 pilot trial_01 A→F, 310.98 s, 2026-09-06T23:06:26Z; verdict PILOT INCONCLUSIVE (N=1) |
| R3 | `03_RAW_DATA/CSI_SENSE-001/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | 499,069 B | 2 (03_RAW_DATA + CSI-SENSE-001/raw) | 10.09 s smoke test immediately pre-pilot |
| — | Boot 15 s capture `5608f152...` (68 CSI, 35,856 B, cited in VERIFY report) | `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` | 35,856 B | **0 — ABSENT** | HISTORICAL GAP: ephemeral `/tmp/csi_boot.log` on Live USB, never staged; recorded as unavailable |

Each raw log ships sidecars in the canonical layout: `capture_meta_*.json`, `validate_*.json`, `.sha256`, `events_trial01.jsonl` (trial_01), `capture_stdout.log` (trial_01). Permissions noted `444` read-only in README (not re-verified here; no writes performed).

## 4. Item inventory (deduplicated — one row per UNIQUE content)

Allowed actions: KEEP / MIGRATE / ARCHIVE / DUPLICATE / OBSOLETE / DELETE / UNDECIDED.
`Current equivalent` refers to `~/Desktop/RF Vision` (baseline for §6 matrix).

### 4A. Project planning

| PATH (canonical) | TYPE | SIZE | PURPOSE | DATE/VERSION | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|---|
| `00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` (+ mirrors in `CSI_SENSE_001/PLAN/`, `SOURCE_PROJECT/Desktop/`, `99_ARCHIVE/...`, hash `c72b2c4b` 753 lines) | md plan | ~plan 753 L | Full A–F protocol, gates, validity criteria, backup rule §5.5, walking-speed-as-covariate | 2026-09-06 v1.1 | HIGH — only executed human-protocol definition; current `experiments/protocols/BASELINE_PROTOCOL.md` is a 23-line template with NO A–F detail | none (template only) | MIGRATE (as historical protocol reference, redacted if needed) |
| `CSI_SENSE_001/ANALYSIS/PROTOCOL.md` + `SOURCE_PROJECT/data/.../PROTOCOL.md` (hash `d2ea217b`) | md protocol | small | Phase-B-era protocol note | 2026-09-06 | MEDIUM — superseded by v1.1 plan | `experiments/protocols/BASELINE_PROTOCOL.md` (template) | ARCHIVE (reference only) |
| `CSI_SENSE_001/ANALYSIS/README.md` + `SOURCE_PROJECT/.../README.md` (hash `b204b10d`) | md readme | small | Phase-B data-readme | 2026-09-06 | LOW | `research/datasets/README.md`, `experiments/*/README.md` | ARCHIVE |

### 4B. Hardware

| PATH | TYPE | SIZE | PURPOSE | DATE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|---|
| `01_HARDWARE/hardware_identity.json` (hash `f35a5223`, mirrors in `04_EVENTS_METADATA/metadata/`, `CSI_SENSE_001/METADATA/`, `SOURCE_PROJECT/.../metadata/`) | json provenance | 1,974 B | Exact pre-Ubuntu identities: ESP32-D0WD-V3 rev3.1 MAC `f4:65:0b:56:0e:18`, 4 MB `0x68:0x4016 dio40m`, CP2102 `10c4:ea60 /dev/ttyUSB0` 921600, Xiaomi 4C/R4CM `Nihaal 8C:53:C3:5B:E1:59` ch1 2412 HT20, Lenovo IdeaPad Gaming 3 15IAH7 BIOS `JMCN48WW` Ubuntu 26.04.1 Live `/cow`, Intel AX201, NVMe untouched | 2026-09-06 | HIGH — lost-detail recovery (BIOS rev, flash IDs, bridge by-id, gateway, signal −39 dBm, Live volatility) | `docs/hardware/BASELINE.md` (same pins, less detail) + `RFVISION-003` §2 (bridge-only re-verification) | MIGRATE (redacted: keep BSSID/MAC for reproducibility per README policy; strip password-adjacent `nmcli --show-secrets` wording to a provenance note) |

### 4C. Firmware / capture config

| PATH | TYPE | SIZE | PURPOSE | DATE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|---|
| `02_FIRMWARE/firmware_versions.json` (hash `0b286912`, + mirrors) | json provenance | 4,100 B | ESP-IDF v5.4.4 `296b6eab...`, esp-csi `8633d671...`, `csi_recv_router` app_main pins, build SHAs `ce23861e`/`7d7cf518`, flash cmd, rates 102/141 Hz | 2026-09-06 | HIGH — pins MATCH current `BASELINE.md`; build/flash transcript is unique | `docs/hardware/BASELINE.md` + `firmware/esp32/csi_recv_router/` (verbatim source) | MIGRATE (SANITIZED: `sdkconfig.defaults` line contains **Wi-Fi password plaintext** — MUST redact before migration; see §7) |
| `02_FIRMWARE/capture_config.json` (hash `edcfbf00`, + mirrors) | json config | 2,817 B | Baud 921600, `CONFIG_SEND_FREQUENCY 100`, A–F durations (90/12/60/35/12/90, total 310), validity gates (missing ≤1 %, malformed ≤0.5 %, no gap >500 ms, ch1 ≥99 %), backup rule, tool map | 2026-09-06 | HIGH — only machine-readable trial gate definition | `config/default.yaml` + `experiments/metadata/EXPERIMENT_METADATA_SCHEMA.md` (generic schema, no A–F values) | MIGRATE (values as historical reference; do NOT overwrite current defaults) |

### 4D. CSI raw + sidecars (evidence — NEVER bulk-commit to git)

| PATH | TYPE | SIZE | PURPOSE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|
| `03_RAW_DATA/CSI_VERIFY/*.log` (R1 + 6 dup copies) | log raw | 3.57 MB | VERIFY PASS evidence | HIGH (only PASS capture) | NONE in repo (correct — raw lives outside git; `~/RFVision-Research-Data/rfvision-003/` holds only the anomalous 57 MB FAIL capture `c64e5a00...`) | MIGRATE-EXTERNAL (copy ONE canonical R1 to `~/RFVision-Research-Data/legacy-csi-verify-001/` + manifest; NEVER into git) |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/*` (raw R2 + `capture_meta_trial01.json` + `capture_stdout.log` + `events_trial01.jsonl` + `validate_trial01.json` + `.sha256`) | log/json/jsonl | 14.3 MB + KB sidecars | Pilot N=1 evidence chain | HIGH (INCONCLUSIVE is still evidence; validates parser + gates) | NONE | MIGRATE-EXTERNAL (raw) + MIGRATE (sidecar *metadata* as docs reference, small JSONs only) |
| `03_RAW_DATA/CSI_SENSE-001/smoke_test/*` (raw R3 + `capture_meta_trial00.json` + `validate_smoke.json` + `.sha256`) | log/json | 0.5 MB + KB | Smoke-test evidence | MEDIUM-HIGH | NONE | MIGRATE-EXTERNAL (raw) + MIGRATE (sidecar metadata) |
| `04_EVENTS_METADATA/events/events_trial01.jsonl` (+ `CSI-SENSE-001/events/trial01_events.jsonl` dup, `99_ARCHIVE/...trial01_events.jsonl.duplicate`) | jsonl events | KB | A→F pilot event timeline (walk_start/walk_end etc.) | HIGH — ground-truth sidecar | `experiments/metadata/EXPERIMENT_METADATA_SCHEMA.md` (schema only, no data) | MIGRATE (metadata doc) |
| `04_EVENTS_METADATA/metadata/{capture_config,firmware_versions,hardware_identity,room_geometry,study_metadata,trial_01_metadata,smoke_test_metadata,environment_trial01}.json` | json metadata | KB each | Study/geometry/env/trial descriptors | HIGH (with caveats: `room_geometry.json` is a NULL placeholder — documents an UNFULFILLED measurement, still valuable as gap record; `environment_trial01.json` has UNKNOWNs + one measured height ~0.55 m) | schema only | MIGRATE (selected JSONs as historical evidence docs) |

### 4E. Derived analysis (reproducible, NOT raw)

| PATH | TYPE | SIZE | PURPOSE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|
| `05_ANALYSIS/trial_01/{parsed_trial01.csv (14.1 MB), parsed_trial01.npz (3.1 MB), features_trial01.npz (29.2 MB)+.json, baseline_model_trial01.npz (3.9 MB)+.json, pca_spectrogram_trial01.npz (2.8 MB)+.json, parse_meta_trial01.json, figures/*.png + manifest}` (+ full `CSI-SENSE-001/analysis/` mirror) | csv/npz/json/png | ~55 MB per copy ×2 | Parser outputs, amplitude/phase features, baseline μ/σ/cov, PCA+STFT, demo figures | MEDIUM — proves toolchain ran on real data; fully reproducible from raw + tools; large | NONE (current `dsp/`, `ai/` have no pilot-derived artifacts; `research/datasets/README.md` forbids bulk raw/derived in git) | ARCHIVE-EXTERNAL (ONE copy to research-data `legacy-.../derived/` + manifest; migrate ONLY small JSON metas + figure manifest reference into docs; NEVER bulk `.npz/.csv` into git) |
| `05_ANALYSIS/smoke_test/{parsed_smoke.csv, parsed_trial00.csv (0.48 MB ×2 names), parsed_trial00.npz (0.1 MB), parse_meta_trial00.json}` (+ mirror) | csv/npz/json | ~1 MB | Smoke-test parse outputs | LOW-MEDIUM | NONE | ARCHIVE-EXTERNAL (same rule) |
| `CSI_SENSE_001/ANALYSIS/{stats (pca/statistical_tests ×3–4), figures (heatmap/rssi/variance/timeseries + manifest)}` + `SOURCE_PROJECT/data/...` + `99_ARCHIVE/...` mirrors | json/npz/png | ~1 MB unique | Phase-B-era derived stats/figs (older naming) | LOW — superseded by `05_ANALYSIS` trial_01 set | NONE | ARCHIVE (reference only; deduplicate) |

### 4F. Software tools (11 unique Python files, mirrored ×4)

| PATH (canonical `06_TOOLS/`) | TYPE | SIZE | PURPOSE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|
| `csi_capture/capture_csi_sense.py` (264 L) | py capture | ~8 KB | pyserial 921600 `read(4096)→wb`, A–F timed capture | MEDIUM — experiment harness; overlaps `tools/csi_record.py` (108 L, binary-safe recorder) + `csi/capture/serial_receiver.py` | `tools/csi_record.py`, `csi/capture/serial_receiver.py`, `csi/capture/helpers.py` | REFERENCE ONLY (do NOT duplicate; adapt ideas — e.g. timed-phase capture — only via new work item) |
| `csi_capture/event_logger.py` (262 L) | py events | ~8 KB | wall_clock_ns + chip_seq sync 100 ms sidecar logger | MEDIUM — overlaps `realtime/protocol/event_envelope.py` conceptually | `realtime/protocol/event_envelope.py` | REFERENCE ONLY |
| `csi_capture/validate_raw.py` (227 L) | py validation | ~7 KB | Post-capture gates (missing/malformed/channel/BSSID/len) | MEDIUM-HIGH — validity thresholds match `capture_config.json`; complements `csi/validation/validators.py` (50 L generic) | `csi/validation/validators.py` | ADAPT candidate (port thresholds as test vectors / docs, not blind copy) |
| `csi_capture/backup_verify.py` (373 L) | py backup gate | ~12 KB | Persistent-backup enforcement (refuses `/cow/tmp/tmpfs/overlay`, write-test SHA round-trip, ≥5 GB) | MEDIUM — operational safety tooling with NO current equivalent | NONE | MIGRATE-as-reference (docs note + optional future `tools/` item; NOT active code now) |
| `csi_analysis/parse_csi.py` (304 L, regex `CSI_PATTERN` 24-group + `re.finditer` glued handling) | py parser | ~12 KB | Validated against real captures (14 malformed 0.195 % glued fragments) | HIGH as technique reference — BUT wire-format incompatible with current `CsiSample` JSON model; current `csi/parser/esp_csv_adapter.py` already bridges `CSI_DATA` CSV via `csv` module (25-col incl. smoothing/not_sounding) | `csi/parser/esp_csv_adapter.py` + `csi/parser/csi_parser.py` | REFERENCE ONLY (document glued-fragment technique; do NOT replace adapter; add regression test only if gap proven) |
| `csi_analysis/features.py` (230 L) | py DSP | ~7 KB | amp `sqrt(I²+Q²)`, phase `atan2` detrended | LOW-MEDIUM — overlaps `dsp/preprocessing` + `dsp/features` (Human-Sensing-derived, tested) | `dsp/preprocessing/preprocessing.py`, `dsp/features/feature_extraction.py` | REJECT (current tested chain wins; keep as citation) |
| `csi_analysis/baseline_model.py` (288 L) | py stats | ~9 KB | μ/σ/cov deviation + walking covariate | MEDIUM — no current equivalent (current `ai/training/baseline_model.py` is an ML baseline, different concept) | NONE (name collision, different concept) | REFERENCE ONLY |
| `csi_analysis/pca_spectrogram.py` (321 L) | py stats | ~10 KB | PCA on baseline + STFT 2 s 90 % overlap | MEDIUM — no current equivalent | NONE | REFERENCE ONLY |
| `csi_analysis/statistical_tests.py` (376 L) | py stats | ~12 KB | Q1–Q6 distribution-dependent FDR effect-size | MEDIUM-HIGH — only significance-testing method in either tree | NONE | REFERENCE ONLY (candidate for future `experiments/analysis/` work) |
| `csi_analysis/temporal_plots.py` (335 L) | py viz | ~10 KB | A/C/D/F overlay + events + speed plots | LOW-MEDIUM — overlaps `visualization/` conceptually | `visualization/dashboard/`, `visualization/rf/` | REFERENCE ONLY |
| `csi_analysis/analysis_config.json` (hash `39a68729`) | json config | KB | Parser/feature/PCA/plot params | LOW-MEDIUM | `config/default.yaml` | ARCHIVE (cite params in provenance) |
| Mirrors: `CSI_SENSE_001/TOOLS/`, `SOURCE_PROJECT/tools/`, `99_ARCHIVE/.../tools/` (same 11 files, hashes `a820523e…` etc. identical) | py/json | same | Pre-archive copies | — | — | DUPLICATE (migrate once from `06_TOOLS/` only) |

### 4G. Reports / audits / manifests

| PATH | TYPE | SIZE | PURPOSE | RELEVANCE | CURRENT EQUIVALENT | ACTION |
|---|---|---|---|---|---|---|
| `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` (265 L, `d8b669a2`) + `CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` (224 L, `6e0a1779`) | md evidence | 17.5 KB + 13.8 KB | PASS verdict + phase-1 gate (pins, rates, BSSID, boot-gap note) | HIGH — foundational evidence current repo cites but does not contain | `docs/research/SCIENTIFIC_VALIDATION_STATUS.md` (policy), `RFVISION-003` (contrasting FAIL) | MIGRATE (SANITIZED: contains password line — redact) |
| `07_REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` (266 L, `75255253`) | md | 22.4 KB | Host-tooling PASS (parser validated, no human experiment) | MEDIUM-HIGH | NONE | MIGRATE |
| `07_REPORTS/CSI-SENSE-001_PHASE_C_READINESS_REPORT.md` (315 L, `7d414cee`) | md | 35.3 KB | READY WITH REQUIRED ACTIONS (geometry/env/backup prerequisites) | HIGH — prerequisite logic current protocol template lacks | `experiments/protocols/BASELINE_PROTOCOL.md` (template) | MIGRATE |
| `07_REPORTS/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` (324 L) + root + `CSI-SENSE-001/reports/` copies | md | 21.6 KB | PILOT INCONCLUSIVE N=1 (valid data, no sensing claim) | HIGH — negative/inconclusive result, scientifically valuable | NONE | MIGRATE |
| `07_REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` (196 L, `a3c32d24`) | md | 9.0 KB | Backup-gate enforcement record | MEDIUM | NONE | MIGRATE (with backup tooling reference) |
| `07_REPORTS/FINAL-FOLDER-AUDIT-001.md` (497 L) + `FINAL-ARCHIVE-AUDIT-002.md` (396 L) (+ root + `08_CHECKSUMS_MANIFESTS/` + `CHECKSUMS/` copies) | md audits | 51.1 KB + 39.8 KB | Folder/archive self-audits (volatile-Live warnings, dup accounting, boot-gap, Nano note) | MEDIUM-HIGH as provenance of the archive itself | `docs/research/RFVISION-REPO-FOUNDATION-001-ANALYSIS-ARCHIVE.md` (different scope) | MIGRATE (ONE canonical copy each; rest DUPLICATE) |
| `08_CHECKSUMS_MANIFESTS/{SHA256SUMS.txt (7,775 B), BACKUP_MANIFEST.md (13,840 B), BACKUP_COMPLETE.md (3,394 B), BACKUP_BEFORE_REBOOT.md (5,668 B), PATH_PROVENANCE.md (2,814 B)}` + `CHECKSUMS/SHA256SUMS.txt (9,537 B)` + root copies | md/txt manifests | KBs | Checksums, staging manifest, path-provenance (`/home/ubuntu` Live paths), reboot warnings | HIGH (checksums) / MEDIUM (staging narrative) | NONE (current `research/datasets/README.md` policy only) | MIGRATE (SHA256SUMS excerpt + PATH_PROVENANCE note; staging narrative condensed into migration provenance, not verbatim bulk) |
| `README.md` (47 L) | md index | 5,853 B | Archive index + status + volatility + Nano + checksum instructions | MEDIUM — good summary style; Live-Google-Drive narrative is stale post-transition | `README.md` (current) | ARCHIVE (cite, do NOT replace current README) |
| `CSI-SENSE-001/BACKUP_BEFORE_REBOOT.md` + `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` (pilot-era layout copies) | md | KBs | Era-specific copies | LOW (dup of canonical) | — | DUPLICATE |

### 4H. Archive / obsolete (explicitly non-authoritative by legacy authors)

| PATH | TYPE | SIZE | PURPOSE | ACTION |
|---|---|---|---|---|
| `99_ARCHIVE/historical_duplicates/{CSI_RAW...log.CSI_SENSE_001_RAW_DATA, .SOURCE_PROJECT_Desktop, PHASE_C_PILOT_REPORT.md.root_duplicate, trial01_events.jsonl.duplicate}` | log/md/jsonl dup markers | 3.6 MB + KBs | Intentionally quarantined duplicates | OBSOLETE/DELETE-class (verified duplicates; no migration) |
| `99_ARCHIVE/obsolete_phase_b_files/{checksums.sha256.*.empty (0 B ×2), CSI-SENSE-001_PLAN_downloads_duplicate.md}` | empty/md | 0 B + KB | Empty placeholder checksums + Downloads-duplicate plan | OBSOLETE/DELETE-class |
| `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/{Desktop, data, tools}` | mirror | ~tens of MB | Full pre-archive mirror (hashes identical to canonical) | DUPLICATE (do not migrate; record hash equality) |
| `SOURCE_PROJECT/{Desktop, data, tools}` | mirror | ~tens of MB | Same as above (one generation newer) | DUPLICATE (do not migrate; record hash equality) |
| `CSI_VERIFY_001/`, `CSI_SENSE_001/` (older underscore naming) | mirror | ~tens of MB | Superseded layout generation | DUPLICATE/SUPERSEDED (canonical is `00–08` + hyphen `CSI-SENSE-001/` pilot set) |

## 5. Deep content analysis (categories A–H summary)

- **A. Planning:** ONE executable plan (v1.1, 753 L) + Phase-B protocol note. Current repo has only a 23-line unexecuted template. Gap is real; plan is the single most valuable document migration.
- **B. Hardware:** Exact identities + Live-volatility record + untouched-NVMe attestation. Current `BASELINE.md` preserves pins but drops BIOS/flash-ID/bridge-by-id/gateway/signal/Live details. Recoverable without re-measurement.
- **C. Firmware:** Pins match current baseline exactly (IDF `296b6eab`, CSI `8633d671`, app `ce23861e`, bootloader `7d7cf518`); build/flash transcript + `CONFIG_SEND_FREQUENCY 100` + 102/141 Hz observed rates are unique. No `.c/.bin` sources in legacy (current firmware directory is the authority — DO NOT import anything over it).
- **D. CSI:** 3 raw captures + full sidecar chain + 2 audit reports. No CSI schemas beyond the `parse_csi.py` header comment + `FIELD_NAMES`; no separate schema doc. Current `csi/formats/WIRE_FORMATS.md` + adapter cover the format going forward.
- **E. Experiments:** ONE A→F pilot (N=1, INCONCLUSIVE) + smoke test. Room geometry UNMEASURED (placeholder), environment partially UNKNOWN, trials 2–10 never run, localization/ML/3D never performed. Value is methodological (protocol + gates + negative result), not a result to claim.
- **F. Software:** 11 Python tools, original (no third-party headers found), experiment-specific. Current stack is Human-Sensing-derived + native adapter; overlap is partial and legacy is NOT a drop-in replacement.
- **G. Research:** NO papers, NO literature reviews, NO citations, NO publication drafts in legacy. (Current `docs/background/`, `docs/third_party/bib/` cover background; no gap.)
- **H. Documentation:** 8 reports + plan + manifests + README + metadata JSONs. NO setup/troubleshooting guides beyond backup/reboot notes; NO diagrams (only generated heatmap/timeseries PNGs); NO RuView/Unity/three.js material (binary-grep hits were false positives on `.npz/.png` bytes; zero textual matches).

## 6. Security / credentials (values SUPPRESSED — see §7 of matrix doc for handling)

- CONFIRMED: Wi-Fi password (WPA2-PSK) printed VERBATIM in `02_FIRMWARE/firmware_versions.json` (`sdkconfig.defaults` string) and in `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` (×2 lines: config quote + `nmcli --show-secrets` transcript line). Propagated via mirrors to `04_EVENTS_METADATA/metadata/firmware_versions.json`, both audit reports, manifests. Total `password`-case-insensitive hits: 74 across 24 files (includes benign `nmcli --show-secrets` provenance discussion — still credential-adjacent).
- NOT secrets: router BSSID/MAC, ESP32 MAC, gateway IP, SSID `Nihaal` — retained deliberately for reproducibility (README §Security states this policy); treat as operational PII, keep in redacted migration (BSSID/MAC stay, password never migrates).
- NOT found: API keys, tokens (hits are English `token` in code + `api.macvendors.com`), private/SSH keys, `.pem/.key` files — none.
- Current repo: grep for the password value and `EXAMPLE_WIFI_PASSWORD` → ZERO hits. Must stay that way.

## 7. License / provenance

- Legacy contains NO `LICENSE` file, NO per-file SPDX/copyright headers in the 11 Python tools (scanned `.py/.md/.txt/.c/.h/.ino` for `license|copyright|SPDX|MIT|Apache|GPL` — only hits are prose mentions of `LICENSE`/license in reports/protocols, no third-party code blocks).
- Assessment: legacy tools read as ORIGINAL project code (no vendored upstream identified; firmware PYTHON pins reference official Espressif repos by URL+commit but no code copied into legacy).
- Consequence: NOTHING in legacy needs a `THIRD_PARTY_NOTICES.md` entry. If any tool is later adapted, attribute as `RF Vision legacy (CSI-SENSE-001, 2026-09-06, pre-Ubuntu archive)` with original path + hash, under the project MIT license — no external obligations found.

## 8. Action rollup (unique-content basis, 78 hashes)

| Action | Meaning | Approx. unique items |
|---|---|---|
| MIGRATE (docs/metadata, sanitized) | Plan, HW identity, firmware/config pins (redacted), trial/env/study/geometry metadata, events, validate/capture sidecar JSONs, 7 reports/audits, checksum/provenance excerpts | ~20 |
| MIGRATE-EXTERNAL (raw + derived bulk, outside git) | R1/R2/R3 raw logs (ONE copy each) + derived `.npz/.csv` sets + figures (ONE copy) to `~/RFVision-Research-Data/legacy-*/` with manifests | ~15 payload hashes (large) |
| REFERENCE ONLY / ADAPT-candidate | 11 Python tools (techniques, thresholds, gates) — no direct copy into active tree | 11 |
| ARCHIVE (condensed citation) | README, Phase-B protocol/readme, analysis_config, staging narratives | ~6 |
| DUPLICATE / SUPERSEDED / OBSOLETE / DELETE-class | All mirror copies, `99_ARCHIVE` quarantine, empty checksums, root dup copies | ~150 files (verified by hash) |
| UNDECIDED | NONE (every unique item classified above; nothing left ambiguous) |

 multiplied file counts differ from unique counts because of the ×2–×7 mirroring — §2 dedup table is authoritative for cleanup.

## 9. Verification notes for this inventory

- Hashes R1/R2/R3 recomputed locally in this phase (`python3 hashlib.sha256`) and match sidecar `.sha256` filenames/content and `SHA256SUMS.txt` entries (`51d47ce…`, `4734dcf…`, `ce04708…` prefixes).
- Duplicate groups computed by full-byte SHA-256 over all 232 files (78 unique).
- No writes were made to either the legacy source or the current repo during inventory. All outputs are in `/tmp/rfvision-legacy-audit/`.
- `git` CLI unavailable — current-repo history statements rely on in-repo report files (`RFVISION-FOUNDATION-IMPLEMENTATION-REPORT.md`, `RFVISION-003`, `RFVISION-004/005`) rather than `git log`.
