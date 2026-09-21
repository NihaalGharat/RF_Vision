> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/FINAL-FOLDER-AUDIT-001.md` (SHA-256 `e15abd6c64bfd9646fdc24b3ade59ab0f30cd4d7f03f0747eb127056cb1433c2`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# FINAL-FOLDER-AUDIT-001

**Operation:** FINAL-FOLDER-AUDIT-001 — READ-ONLY folder audit  
**Date/Time UTC:** 2026-09-06 23:29 UTC (audit execution)  
**Audited Path:** `/home/ubuntu/Desktop/RF Vision Files`  
**Host:** Lenovo IdeaPad Gaming 3 15IAH7 — Ubuntu 26.04.1 LTS — Live `/cow` overlay `7.7G` — `findmnt / overlay upperdir=/cow/upper` — **VOLATILE** (not persistent)  
**Scope:** READ-ONLY — no modify/rename/move/delete/create/CSI/flash/reboot/upload/permission change  
**Total:** 117 files, 41 directories, 158 total entries, `du -sh 80M` `du -sb 82915400` — 67M `CSI-SENSE-001` + 4.9M `CSI_SENSE_001` + 4.9M `SOURCE_PROJECT` + 3.5M `CSI_VERIFY_001` + backups/manifests  
**Auditor:** read-only enumeration (`find -printf`, `sha256sum`, `file`, `ls -lR`, `grep -r` without secret disclosure, `df -hT`, `findmnt`)

---

## 1. Current Folder Tree

```
/home/ubuntu/Desktop/RF Vision Files/ (9 top entries, 260 bytes dir entry 2026-09-06 23:29)
├── BACKUP_BEFORE_REBOOT.md (5.6K 2026-09-06 23:14)
├── BACKUP_COMPLETE.md (3.4K 2026-09-06 22:45)
├── BACKUP_MANIFEST.md (14K 2026-09-06 22:45)
├── CHECKSUMS/
│   └── SHA256SUMS.txt (9.5K 2026-09-06 22:45) 77 entries
├── CSI-SENSE-001/ (ACTIVE pilot — 67M, 38 files)
│   ├── BACKUP_BEFORE_REBOOT.md (5668, duplicate of root)
│   ├── analysis/
│   │   ├── smoke_test/ (4 files: parse_meta_trial00.json, parsed_smoke.csv, parsed_trial00.csv, parsed_trial00.npz)
│   │   └── trial_01/ (10 files: baseline_model_{json,npz}, features_{json,npz}, parse_meta, parsed_{csv,npz}, pca_{json,npz}, figures/)
│   │       └── figures/ (4 PNG + manifest: heatmap_demo, rssi_demo, subcarrier_variance_demo, timeseries_demo)
│   ├── checksums/
│   │   └── SHA256SUMS.txt (3866, 35 entries — covers CSI-SENSE-001 only)
│   ├── events/
│   │   ├── events_trial01.jsonl (4502)
│   │   └── trial01_events.jsonl (4502 duplicate)
│   ├── metadata/
│   │   ├── environment_trial01.json (1578)
│   │   ├── smoke_test_metadata.json (503)
│   │   └── trial_01_metadata.json (1126)
│   ├── raw/
│   │   ├── smoke_test/ (4: CSI-SENSE-001_20260906T23-05-22_trial00_raw.log 499069 + .sha256 + capture_meta + validate_smoke)
│   │   └── trial_01/ (6: CSI-SENSE-001_20260906T23-06-26_trial01_raw.log 14304955 + .sha256 + capture_meta + capture_stdout + events + validate)
│   └── reports/
│       └── CSI-SENSE-001_PHASE_C_PILOT_REPORT.md (21638)
├── CSI-SENSE-001_PHASE_C_PILOT_REPORT.md (21638 duplicate of CSI-SENSE-001/reports/ — root-level copy)
├── CSI_SENSE_001/ (HISTORICAL Phase B staging — 4.9M, 32 files, STATIC)
│   ├── ANALYSIS/
│   │   ├── PROTOCOL.md (9305)
│   │   ├── README.md (9873)
│   │   ├── checksums.sha256 (0 empty)
│   │   ├── figures/ (5: heatmap, rssi, subcarrier_variance, timeseries, manifest)
│   │   └── stats/ (5: pca_{json,npz}, statistical_tests{,_demo,_trial01}.json)
│   ├── METADATA/ (5 json: capture_config, firmware_versions, hardware_identity, room_geometry, study_metadata)
│   ├── PLAN/ (3: PLAN.md, PLAN_v1.1.md, PLAN_downloads_duplicate.md)
│   ├── RAW_DATA/
│   │   └── CSI_RAW_70s_921600_20260906_205638.log (3566098)
│   ├── REPORTS/ (3: PERSISTENT_BACKUP_GATE, PHASE_B_IMPLEMENTATION, PHASE_C_READINESS)
│   ├── TOOLS/
│   │   ├── csi_analysis/ (7: 6 py + analysis_config.json)
│   │   └── csi_capture/ (4 py)
│   └── raw/ (empty placeholder)
├── CSI_VERIFY_001/ (3.5M, 3 files)
│   ├── CSI-VERIFY-001_FINAL_REPORT.md (17500)
│   ├── CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md (13827)
│   └── CSI_RAW_70s_921600_20260906_205638.log (3566098 duplicate)
├── HARDWARE_RECON/ (empty placeholder, 40 bytes dir)
├── PROJECT_DOCUMENTATION/ (empty placeholder, 40 bytes dir)
├── SOURCE_PROJECT/ (HISTORICAL full mirror — 4.9M, 31 files, DUPLICATE of CSI_SENSE_001 + Desktop)
│   ├── Desktop/ (8: same 3 REPORTS + 2 PLANS + 2 CSI-VERIFY reports + 1 raw duplicate)
│   ├── data/CSI-SENSE-001/
│   │   ├── PROTOCOL.md, README.md, checksums.sha256 (0 empty duplicate), metadata/ (5 json duplicates), analysis/ (figures 5 + stats 5 duplicates), raw/ (empty)
│   └── tools/ (11: 7 csi_analysis + 4 csi_capture duplicates)
└── [NO NANO-RECON-001.md found in tree — not present; HARDWARE_RECON empty]
```

**Directories (41):** listed `find -type d | sort` confirms above; empty dirs: `PROJECT_DOCUMENTATION`, `HARDWARE_RECON`, `CSI_SENSE_001/raw`, `SOURCE_PROJECT/data/CSI-SENSE-001/raw` (all 0 files, placeholders from Phase B backup).

---

## 2. Inventory Summary

| Metric | Value |
|--------|-------|
| **Total files** | **117** `find -type f | wc -l` |
| **Total directories** | **41** `find -type d | wc -l` |
| **Total entries** | 158 |
| **Total size** | `80M` `82915400 bytes` `du -sh / du -sb` |
| **Largest top-level** | `CSI-SENSE-001 67M` `CSI_SENSE_001 4.9M` `SOURCE_PROJECT 4.9M` `CSI_VERIFY_001 3.5M` `CHECKSUMS 12K` |
| **File types** | Text UTF-8/Markdown (reports/manifests), JSON (metadata/analysis), CSV ASCII (parsed), NPZ Zip (features/baseline/pca), PNG RGBA (figures), Python scripts (tools), Raw logs ASCII/CRLF (CSI) — `file` confirmed no executables/binaries beyond NPZ/PNG/logs |
| **Permissions** | Mixed: raw logs + metadata `444 r--r--r--` immutable (smoke/trial + sidecars), rest `644 rw-rw-r--`; no `__pycache__`/`.pyc`/`build`/`tmp` beyond staging |
| **Modification window** | `CSI_SENSE_001/RAW_DATA 20:56` (CSI-VERIFY) → `CSI_SENSE_001/TOOLS 21:28-21:34` → `CSI-SENSE-001/raw/trial_01 23:11` pilot (latest) → `BACKUP_BEFORE_REBOOT 23:14` |
| **Volatile filesystem** | `df -hT /cow overlay 7.7G 47% used` `tmpfs /tmp 7.7G 52%` `findmnt / overlay upperdir=/cow/upper` — LiveUSB, reboot destroys |

**Top 20 largest files (`find -printf %s | sort -nr`):**

| Size | MB | Relative Path |
|------|----|---------------|
| 29155642 | 27.80 | `CSI-SENSE-001/analysis/trial_01/features_trial01.npz` |
| 14304955 | 13.64 | `CSI-SENSE-001/raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` (pilot raw) |
| 14092781 | 13.44 | `CSI-SENSE-001/analysis/trial_01/parsed_trial01.csv` |
| 3876512 | 3.70 | `CSI-SENSE-001/analysis/trial_01/baseline_model_trial01.npz` |
| 3566098 | 3.40 | `SOURCE_PROJECT/Desktop/CSI_RAW_70s_921600_20260906_205638.log` (duplicate) |
| 3566098 | 3.40 | `CSI_VERIFY_001/CSI_RAW_70s_921600_20260906_205638.log` (duplicate) |
| 3566098 | 3.40 | `CSI_SENSE_001/RAW_DATA/CSI_RAW_70s_921600_20260906_205638.log` (original staging) |
| 3059185 | 2.92 | `CSI-SENSE-001/analysis/trial_01/parsed_trial01.npz` |
| 2792766 | 2.66 | `CSI-SENSE-001/analysis/trial_01/pca_spectrogram_trial01.npz` |
| 669373 | 0.64 | `SOURCE_PROJECT/data/CSI-SENSE-001/analysis/stats/pca_spectrogram_trial01.npz` (historical demo, duplicate) |
| 669373 | 0.64 | `CSI_SENSE_001/ANALYSIS/stats/pca_spectrogram_trial01.npz` |
| 499069 | 0.48 | `CSI-SENSE-001/raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` (smoke raw) |
| 483138 | 0.46 | `CSI-SENSE-001/analysis/smoke_test/parsed_trial00.csv` (duplicate) |
| 483138 | 0.46 | `CSI-SENSE-001/analysis/smoke_test/parsed_smoke.csv` |
| 144256 | 0.14 | `CSI-SENSE-001/analysis/trial_01/figures/heatmap_demo.png` |
| 141437 | 0.13 | `SOURCE_PROJECT/data/CSI-SENSE-001/analysis/figures/heatmap_trial01.png` (historical) |
| 141437 | 0.13 | `CSI_SENSE_001/ANALYSIS/figures/heatmap_trial01.png` |
| 126028 | 0.12 | `CSI-SENSE-001/analysis/trial_01/figures/timeseries_demo.png` |
| 118650 | 0.11 | `SOURCE_PROJECT/data/CSI-SENSE-001/analysis/figures/timeseries_trial01.png` |
| 118650 | 0.11 | `CSI_SENSE_001/ANALYSIS/figures/timeseries_trial01.png` |

**Categories by total size (Python rollup):**
`ANALYSIS_DERIVED 56451873 53.84 MB` > `RAW_DATA 25513624 24.33 MB` > `TOOLS 249132 0.24 MB` > `REPORTS 230200 0.22 MB` > `PLAN 208145 0.20 MB` > `OTHER 203746 0.19 MB` > `METADATA 31437 0.03 MB` > `CHECKSUMS_MANIFESTS 27243 0.03 MB`

---

## 3. Research Data Inventory

### Raw Immutable Experimental Data (MUST preserve, `r--r--r--` or `rw` but SHA-verified)

| Relative Path | Type | Size | Modified | SHA256 | Binary/Text | Classification |
|---------------|------|------|----------|--------|-------------|----------------|
| `CSI_SENSE_001/RAW_DATA/CSI_RAW_70s_921600_20260906_205638.log` | RAW CSI 70s | 3566098 | 2026-09-06 20:56:38 | `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` | Text CSV ASCII (very long lines) | **RAW immutable** (CSI-VERIFY main) |
| `CSI_VERIFY_001/CSI_RAW_70s_921600_20260906_205638.log` | RAW CSI 70s duplicate | 3566098 | 2026-09-06 20:56:38 | same `51d47ce9` | same | **RAW duplicate** (byte-identical) |
| `SOURCE_PROJECT/Desktop/CSI_RAW_70s_921600_20260906_205638.log` | RAW CSI 70s duplicate | 3566098 | 2026-09-06 20:56:38 | same `51d47ce9` | same | **RAW duplicate** |
| `CSI-SENSE-001/raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | RAW smoke 10s | 499069 | 2026-09-06 23:05:32 | `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | Non-ASCII CRLF very long (8372) | **RAW immutable** (`444`) |
| `CSI-SENSE-001/raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | RAW pilot 310s | 14304955 | 2026-09-06 23:11:37 | `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | ASCII CRLF long (492) | **RAW immutable** (`444`) |
| `CSI-SENSE-001/raw/smoke_test/.sha256` + `raw/trial_01/.sha256` | checksum sidecars | 114 each | same | contain matching hashes | Text | **Checksum/manifest** for raw |
| Boot capture `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` (15s, 35656 bytes) — **NOT FOUND** anywhere (see §5) |

Raw data correctly stored under `03_RAW_DATA` equivalent (`CSI_SENSE_001/RAW_DATA`, `CSI_VERIFY_001/`, `CSI-SENSE-001/raw/{smoke_test,trial_01}`) and clearly distinguishable (`.log` + `.sha256` + `444`).

### Reports (MUST preserve)

| Relative Path | Size | Modified | SHA256 | Type |
|---------------|------|----------|--------|------|
| `CSI_VERIFY_001/CSI-VERIFY-001_FINAL_REPORT.md` | 17500 | 2026-09-06 20:58 | `d8b669a23504c3cd6bbb88901d6b49aabd3a8197cf3037fca92c8d5ef521766c` | **Report** CSI-VERIFY PASS |
| `CSI_VERIFY_001/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` | 13827 | 2026-09-06 20:22 | `6e0a1779f282a14aebf2b161658cc6ce614b7c2bb2379f04a8ffa0c3ebe74df0` | **Report** approval gate |
| `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` | 22401 | 2026-09-06 21:36 | `7525525388d9002c80210b94ac9db9b3b71bc074982b617e0fcd7ed71c2d92a4` | **Report** Phase B |
| `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PHASE_C_READINESS_REPORT.md` | 35253 | 2026-09-06 21:44 | `7d414cee6606ad8fa9be1824ed9d4ee730b92ba30a130b0a4ff0ff3e33c2ee75` | **Report** Phase C readiness READY WITH REQUIRED ACTIONS |
| `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` | 8962 | 2026-09-06 22:39 | `a3c32d24f8b22480a05a36c8b90a77b172ffa97a900a49aec1f55d6e3fa82053` | **Report** backup gate FAILED (volatile) |
| `CSI-SENSE-001/reports/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` | 21638 | 2026-09-06 23:14 | `5dd2cb5397d431ade8e34bc5b75bddd2c164aa408b5a88587d9635c3bb20b066` | **Report** Pilot INCONCLUSIVE (authoritative) |
| `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` | 21638 | 2026-09-06 23:14 | same `5dd2cb` | **Report duplicate** (root copy, same SHA/mtime) |
| `BACKUP_MANIFEST.md` | 13840 | 2026-09-06 22:45 | `3bc1346d...` (CHECKSUMS lists) | **Manifest** staging backup |
| `BACKUP_COMPLETE.md` | 3394 | 2026-09-06 22:45 | — | **Manifest** backup completion |
| `BACKUP_BEFORE_REBOOT.md` (+ duplicate in `CSI-SENSE-001/`) | 5668 | 2026-09-06 23:14 | `a69ad988...` | **Manifest** volatile warning + Drive instructions |
| `NANO-RECON-001.md` | — | — | — | **MISSING** (see §10) — Classic FT232R recon not in folder; `HARDWARE_RECON/` empty |
| `FINAL-FOLDER-AUDIT-001.md` | — | — | — | **This audit** — to be placed outside first |

Duplicates and empty `NANO-RECON` detailed in §§9–10.

### Source/Tooling Files (MUST preserve for reproducibility)

**Capture tools (4 py, `tools/csi_capture`):** `backup_verify.py 16379 b201c94b`, `capture_csi_sense.py 10559 8b6d2bd8`, `event_logger.py 10441 0048fd78`, `validate_raw.py 8927 0c490399` — duplicated byte-identically in `CSI_SENSE_001/TOOLS/csi_capture/` and `SOURCE_PROJECT/tools/csi_capture/` (`grep duplicate groups` confirms `0048fd78`, `b201c94b`, etc.).  
**Analysis tools (6 py + 1 json, `tools/csi_analysis`):** `analysis_config.json 4957 39a68729`, `baseline_model.py 12196 a820523e`, `features.py 9195 1bae77bc`, `parse_csi.py 12289 e95d91a2`, `pca_spectrogram.py 12714 65164d45`, `statistical_tests.py 17092 a43b116e`, `temporal_plots.py 14774 14a1beaa` — same duplicates.  
**Provenance:** Python `Unicode text executable`, `file` confirmed; no compiled artifacts.

### Metadata/Configuration (MUST preserve)

| Path | Size | SHA256 | Type |
|------|------|--------|------|
| `CSI_SENSE_001/METADATA/capture_config.json` | 2817 | `edcfbf00` | **Metadata** baud 921600, len128, trial durations |
| `CSI_SENSE_001/METADATA/firmware_versions.json` | 4100 | `0b286912` | **Provenance** ESP-IDF 296b6eab, ESP-CSI 8633d671, build ce23861e/7d7cf518 |
| `CSI_SENSE_001/METADATA/hardware_identity.json` | 1974 | `f35a5223` | **Provenance** ESP32-D0WD-V3 MAC/BSSID/ch1 |
| `CSI_SENSE_001/METADATA/room_geometry.json` | 2377 | `97ea595a` | **Geometry** placeholders null (Phase B, correctly) |
| `CSI_SENSE_001/METADATA/study_metadata.json` | 2847 | `046f30a8` | **Study** schema + persistent_backup null |
| `SOURCE_PROJECT/data/CSI-SENSE-001/metadata/*` | same sizes | same hashes (`046f30a8`, `0b286912`, etc.) | **Duplicates** |
| `CSI-SENSE-001/metadata/{environment_trial01, trial_01_metadata, smoke_test_metadata}.json` | 1578/1126/503 | `44348498/c36f49a6/437838c5` | **Events metadata** pilot (444, distinct from Phase B templates) |

Metadata correctly JSON, human-readable, no absolute path issue beyond pilot `analysis/*` manifests (see §11M).

### Checksums/Manifests

| Path | Entries | Notes |
|------|---------|-------|
| `CHECKSUMS/SHA256SUMS.txt` (root) | 77 + self `3bc1346d` = 78 total per BACKUP_MANIFEST | Authoritative manifest for staging backup (covers `CSI_SENSE_001/` + `CSI_VERIFY_001/` + `SOURCE_PROJECT/` pre-pilot; **does NOT yet cover `CSI-SENSE-001/` pilot raw/analysis** — pilot checksums only in `CSI-SENSE-001/checksums/`) |
| `CSI-SENSE-001/checksums/SHA256SUMS.txt` | 35 entries | Covers `CSI-SENSE-001/raw/`, `analysis/`, `events/`, `metadata/`, `reports/` pilot + smoke (includes known pilot/smoke hashes `ce047085`, `4734dcf` — MATCH) |
| `CSI_SENSE_001/ANALYSIS/checksums.sha256` | 0 empty | Placeholder from Phase B `data/CSI-SENSE-001/checksums.sha256` — **empty file, should not enter archive** |
| `SOURCE_PROJECT/data/CSI-SENSE-001/checksums.sha256` | 0 empty | Same empty duplicate |

### Temporary/Staging Artifacts (see §12)

- `SOURCE_PROJECT/` entire tree (31 files, 4.9M) — full mirror of `CSI_SENSE_001/` + `Desktop/` via `BACKUP_MANIFEST §3`; intended as pre-reboot copy, now **duplicate staging** inside project folder.
- `CSI_SENSE_001_PHASE_C_PILOT_REPORT.md` root copy (duplicate)
- `CSI-SENSE-001/BACKUP_BEFORE_REBOOT.md` duplicate, `CHECKSUMS/SHA256SUMS.txt` historical (pre-pilot)
- Empty `checksums.sha256` ×2, empty dirs `PROJECT_DOCUMENTATION`/`HARDWARE_RECON`/`CSI_SENSE_001/raw`/`SOURCE_PROJECT/data/.../raw`.

---

## 4. Raw Data Integrity

- **Raw immutable files:** 5 present (3 × CSI-VERIFY 70s duplicates + 1 smoke + 1 pilot) — all `r--r--r--` or correctly `444` where pilot enforced immutability. Pilot raw `CSI-SENSE-001/raw/trial_01/..._trial01_raw.log` `444 14304955` + sidecars `capture_meta_trial01.json`, `validate_trial01.json`, `events_trial01.jsonl`, `capture_stdout.log` preserved; smoke `444 499069` similarly.
- **Raw distinguishable from derived:** YES — raw under `raw/` (`*.log` + `.sha256` + `capture_meta` + `validate_*.json`), derived under `analysis/` (`parsed_*.csv/npz`, `features.npz`, `baseline_model.npz`, `pca.npz`, `figures/*.png`). No raw `.log` inside `analysis/` directories (`find .../analysis -name "*.log"` → 0).
- **Analysis outputs mixed with raw:** NO — clean separation. Only references to raw paths in `parse_meta_*.json` (absolute paths, see §11M) but not file mixing.
- **Checksums preserved:** YES for pilot/smoke in `CSI-SENSE-001/checksums/SHA256SUMS.txt` (35 entries verified `2` known hashes found) and `CHECKSUMS/SHA256SUMS.txt` for CSI-VERIFY main (`51d47ce` ×3). Sidecar `.sha256` files `ce047085`/`4734dcf` match.
- **Checksums verified read-only:** `sha256sum` on raw files matches manifests (see §5). No raw files modified (`BACKUP_MANIFEST §10` byte-identical claim holds).
- **Missing boot capture:** CSI-VERIFY boot 15s `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` referenced in `CSI-VERIFY-001_FINAL_REPORT.md:1` and `PLAN_v1.1` but **NOT FOUND anywhere** via `find ... -exec sha256sum | grep 5608f152` → NOT FOUND, `find -iname "*boot*"` → only `BACKUP_BEFORE_REBOOT.md`. Not a current integrity failure of present raw (70s main intact), but historical boot artifact lost (likely ephemeral `/tmp/csi_boot.log` on Live, per FINAL_REPORT `cp /tmp/csi_boot.log → /tmp/csi-captures/... boot 15s`). Documented as missing in §10.

---

## 5. Known SHA256 Verification

**All hashes computed read-only (`sha256sum` without opening huge files beyond hashing):**

| Known SHA256 | Description | Expected File | Current Path Found | Size | Hash Now | Result |
|--------------|-------------|---------------|-------------------|------|----------|--------|
| `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` | CSI-VERIFY main 70s | `CSI_RAW_70s_921600_20260906_205638.log` | `CSI_SENSE_001/RAW_DATA/CSI_RAW_70s_921600_20260906_205638.log` | 3566098 | same | **MATCH** |
| same | same | same | `CSI_VERIFY_001/CSI_RAW_70s_921600_20260906_205638.log` | 3566098 | same | **MATCH duplicate** |
| same | same | same | `SOURCE_PROJECT/Desktop/CSI_RAW_70s_921600_20260906_205638.log` | 3566098 | same | **MATCH duplicate** |
| `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` | CSI-VERIFY boot 15s | `CSI_2026-09-06..._boot_15s_raw.log` / `/tmp/csi_boot.log` | **NOT FOUND** in RF Vision Files (`find ... sha → NOT FOUND`, `iname *boot* → none`) | — | — | **NOT FOUND** (ephemeral, per `CSI-VERIFY-001_FINAL_REPORT.md:1` only `/tmp/csi-captures` on Live; operator must add from external if preserved elsewhere) |
| `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | Phase C smoke 10s | `CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | `CSI-SENSE-001/raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | 499069 | same | **MATCH** (`r--r--r--`) + sidecar `.sha256` `d5431e77` matches |
| `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | Phase C pilot 310s | `CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | `CSI-SENSE-001/raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | 14304955 | same | **MATCH** (`r--r--r--`) + sidecar `2a7b9339` matches; also `CSI-SENSE-001/checksums` lists `4734dcf` |

**Summary:** **3 of 4 known SHA MATCH (all present raw)** — CSI-VERIFY main (×3 duplicates consistent), smoke, pilot all byte-identical to history. **1 NOT FOUND (boot)** — not present, not a mismatch, but missing historical boot capture; does not invalidate current raw integrity; should be flagged for operator recovery if available outside Live.

---

## 6. Reports and Documentation

**Present (7 unique reports, 1 duplicate):**

- `CSI_VERIFY_001/CSI-VERIFY-001_FINAL_REPORT.md:1` `d8b669a2` (PASS 7152 valid) — references `51d47ce`/`5608f152` raw, `446672` etc.
- `CSI_VERIFY_001/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md:1` `6e0a1779` — hardware approval
- `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md:1` `75255253` — Phase B tooling 17/18 files
- `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PHASE_C_READINESS_REPORT.md:1` `7d414cee` — READY WITH REQUIRED ACTIONS
- `CSI_SENSE_001/REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md:1` `a3c32d24` — gate FAILED volatile
- `CSI-SENSE-001/reports/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md:1` `5dd2cb` — Pilot INCONCLUSIVE (authoritative, `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md:1` §25)
- `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md:1` duplicate root (same `5dd2cb`/`21638`)
- `BACKUP_MANIFEST.md:1` `13840` `3bc1346d` + `BACKUP_COMPLETE.md:1` `3394` + `BACKUP_BEFORE_REBOOT.md:1` `5668` (+ duplicate in `CSI-SENSE-001/`)

**Referenced vs present:**

- `CSI-VERIFY-001_FINAL_REPORT.md` references `CSI_RAW_70s` (`51d47ce`) → FOUND ×3 MATCH; `boot 15s` (`5608f152`) → NOT FOUND (see §5) — broken reference to missing boot artifact (historical).
- `PLAN_v1.1` (`CSI_SENSE_001/PLAN/CSI-SENSE-001_PLAN_v1.1.md:1` `c72b2c4b`) references `study_metadata.json` etc. → FOUND in `METADATA/`.
- Pilot report references `CSI-SENSE-001/raw/trial_01/*`, `analysis/trial_01/*`, `events_trial01.jsonl` → ALL FOUND in `CSI-SENSE-001/` (raw 14304955 MATCH, parsed, features, baseline, pca) — no broken paths to current pilot.
- `NANO-RECON-001` (Classic FT232R) **referenced in project history (stage 5) but NOT FOUND** — `find -iname "*NANO*"` → only empty `HARDWARE_RECON/`; expected `NANO-RECON-001.md` missing from folder at audit time (23:29 `ls -la` shows 9 top entries, none is NANO). If `NANO-RECON-001.md` was intended at `/home/ubuntu/Desktop/RF Vision Files/NANO-RECON-001.md:1` per recon scope, it is absent — likely still at ephemeral `/tmp` or Live `~/Desktop` if not copied.

**No broken relative paths inside pilot analysis:** `parse_meta_trial01.json` absolute paths point to `/home/ubuntu/Desktop/RF Vision Files/CSI-SENSE-001/...` — valid now, will become invalid after moving to Drive (see §11M).

---

## 7. Tools and Source

**Source files (Python/JSON) — `file:1` confirms `Python script` + `JSON text`:**

- **Current pilot tools (authoritative, `CSI-SENSE-001` is NOT storing tools; tools are historical `CSI_SENSE_001/TOOLS` + `SOURCE_PROJECT/tools/`):** Tools are **NOT duplicated inside `CSI-SENSE-001/`** — correct per Phase C pilot (pilot used host `/home/ubuntu/tools/` + copy in staging). `CSI-SENSE-001/` correctly contains **derived data only**, not tools.
- **Historical tools (Phase B, preserved):** `CSI_SENSE_001/TOOLS/csi_capture/ (4 py)` + `csi_analysis/ (6 py + json)` — SHA `b201c94b` etc. match `SOURCE_PROJECT/tools/` duplicates byte-for-byte (`grep duplicate groups` shows `0048fd78`, `0c490399`, `14a1beaa`, etc. ×2).
- **Verification:** No `__pycache__`, no `.pyc`, no `build/`, no compiled extensions; tools are source-only, publication-ready.

**Duplication note:** `SOURCE_PROJECT/tools/` is **exact duplicate** of `CSI_SENSE_001/TOOLS/` (7+4 files, same hashes) — intentional staging mirror per `BACKUP_MANIFEST §3` but now double-counts inside final archive (see §9D).

---

## 8. Metadata and Provenance

**Provenance preserved (firmware/hardware):**

- `firmware_versions.json:1` `0b286912` — ESP-IDF `v5.4.4 296b6eab9445fd720e71aecab961e2d3fbca9944` + ESP-CSI `8633d67152db2808f141cc1595970aa9cf406045` + `ce23861e` app / `7d7cf518` bootloader + `csi_recv_router` + `CONFIG_SEND_FREQUENCY 100` — matches history stage 1.
- `hardware_identity.json:1` `f35a5223` — ESP32-D0WD-V3 rev3.1 MAC `f4:65:0b:56:0e:18` CP2102 `10c4:ea60 /dev/ttyUSB0` + Xiaomi `Nihaal 8C:53:C3:5B:E1:59 ch1 2412 HT20` — matches history.
- `capture_config.json:1` `edcfbf00` — baud `921600`, `len128`, `channel 1` provenance.
- `CHECKSUMS/SHA256SUMS.txt:1` + `CSI-SENSE-001/checksums/SHA256SUMS.txt:1` preserve SHA manifests.

**Configuration/environment:**

- `study_metadata.json:1` `046f30a8` — schema v1.0, `provisional PASS`, `host Lenovo /cow volatile`, `phases gates`, `ethics S01`, `walking_speed_not_gate` — correct.
- `room_geometry.json:1` `97ea595a` — placeholders null (Phase B) correctly, Phase C readiness identified required geometry.
- Pilot `environment_trial01.json`, `trial_01_metadata.json`, `smoke_test_metadata.json` — `444`, preserve `capure_script` typo etc., valid per pilot.
- `analysis_config.json:1` `39a68729` — versions `python 3.14.4 pyserial 3.5 esptool 4.12.0`.

**No provenance ambiguity:** All required commits pinned and checksummed; `room_geometry` placeholders explicitly not claimed as measured (per `FINAL_REPORT` no assumption).

---

## 9. Duplicates

**Duplicate raw captures (A):** **3× byte-identical `51d47ce9` 3566098** — `CSI_SENSE_001/RAW_DATA` + `CSI_VERIFY_001/` + `SOURCE_PROJECT/Desktop/` — same hash/mtime. Intended for redundancy in staging backup, but in final archive counts as 2 extra copies (7.1M wasted). **Not harmful to integrity (MATCH), but clutters recommended `03_RAW_DATA/CSI_VERIFY/`**.

**Duplicate reports (B):** **1 duplicate report** — `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` root `5dd2cb` vs `CSI-SENSE-001/reports/...` identical (`21638` same mtime). Harmless but duplicate.

**Duplicate tools (C):** **11 files duplicated** — `CSI_SENSE_001/TOOLS/` (11) vs `SOURCE_PROJECT/tools/` (11) byte-identical (`0048fd78`, `b201c94b`, `e95d91a2`, etc. ×2 per `allsha.txt uniq -d`). Plus `SOURCE_PROJECT/data/CSI-SENSE-001/metadata|analysis` duplicates of `CSI_SENSE_001/METADATA|ANALYSIS` (5 metadata `046f30a8` etc. + 5 figures `30f737f0` etc. + stats `402b49eb`). **Total duplicate groups:** `c72b2c4b ×4` (PLAN), `51d47ce ×3` (raw), `57975d24 ×3` (events), `5dd2cb ×2` (pilot report), `d8b669a2 ×2` (FINAL_REPORT), `6e0a1779 ×2` etc. — **~30 files duplicated** between `CSI_SENSE_001/` and `SOURCE_PROJECT/`.

**Duplicate events (also):** `CSI-SENSE-001/events/events_trial01.jsonl` + `CSI-SENSE-001/events/trial01_events.jsonl` + `CSI-SENSE-001/raw/trial_01/events_trial01.jsonl` all `57975d24 4502` — 3× same content (raw copy + events dir 2 names).

**Empty checksums duplicates:** `CSI_SENSE_001/ANALYSIS/checksums.sha256` `0` `e3b0c442` vs `SOURCE_PROJECT/data/CSI-SENSE-001/checksums.sha256` `0` same — empty placeholders duplicated.

**Not duplicate (correct):** Pilot derived files (`features_trial01.npz 29155642`, `parsed_trial01.csv 14092781`, etc.) are unique to `CSI-SENSE-001/analysis/` — not duplicated elsewhere.

---

## 10. Missing/Referenced Files

**Missing reports referenced (D):**

| Referenced | Found | Note |
|------------|-------|------|
| `NANO-RECON-001.md` (Classic FT232R ATmega328P, Auxiliary only, per history stage 5) | **MISSING** — `find -iname "*NANO*"` → 0; `HARDWARE_RECON/` empty; `ls -la` top 9 entries no NANO | Recon stage completed per history but file not in `RF Vision Files` at audit time; likely at ephemeral `/tmp/...` or not yet copied to staging. **MUST add before Drive backup** to satisfy `07_REPORTS/Nano recon` and `01_HARDWARE/Nano reconnaissance` |
| `PROJECT_DOCUMENTATION/project overview|roadmap|decisions` | **MISSING** — `PROJECT_DOCUMENTATION/` empty | Placeholder from `BACKUP_MANIFEST §3` — no docs found on Live at backup time; if decisions exist elsewhere (e.g., `~/Desktop/RF Vision.md` per manifest), add |
| `01_HARDWARE/hardware recon` beyond `hardware_identity.json` | PARTIAL — `HARDWARE_RECON/` empty, but `hardware_identity.json` present in `CSI_SENSE_001/METADATA/` | Acceptable if recon is that JSON; `HARDWARE_RECON` placeholder expected empty |

**Missing raw files referenced (E):**

| Referenced | Found | Note |
|------------|-------|------|
| CSI-VERIFY boot `5608f152` 15s `35,856 bytes 68 CSI` (per `CSI-VERIFY-001_FINAL_REPORT.md:1` and `PLAN_v1.1`) | **NOT FOUND anywhere** (`grep 5608f152 → NOT FOUND`) | Ephemeral `/tmp/csi_boot.log` on Live, per FINAL_REPORT not copied to Desktop at capture time; not in `CHECKSUMS`/`BACKUP_MANIFEST`. Historical artifact — **NOT FOUND, not mismatch**; operator should recover from `~/Desktop` history or `Google Drive` if previously uploaded, else note as missing boot companion (main `51d47ce` still PASS) |
| Boot header `=============== CSI RECV ================` file | Not present as file | Embedded in boot log per history; same missing |
| Raw `data/CSI-SENSE-001/raw/` Phase B placeholder | Empty by design (gate not passed until pilot) — correctly empty | Not missing |

**Broken relative paths (F):** No broken *current* relative paths — pilot `validate_*.json` etc. point to existing `CSI-SENSE-001/raw/...`. However **absolute Live paths** will break after Drive move (see §11M). No missing SHA256 records for present raw — pilot has sidecars + `CSI-SENSE-001/checksums`.

**Missing SHA256 records (G):** `CHECKSUMS/SHA256SUMS.txt` (77 entries) **does not list pilot raw** (`ce047085`/`4734dcf`) — by design pre-pilot manifest; pilot covered separately in `CSI-SENSE-001/checksums/SHA256SUMS.txt` (35 entries, includes them). No missing records for present raw within their own manifests. Empty `checksums.sha256` `0` correctly not listing anything (placeholder).

**SHA mismatch (H):** **NO mismatch** — all 3 present known SHA `51d47ce`/`ce04708`/`4734dcf` MATCH computed `sha256sum`. No corruption.

**Raw inside analysis (I):** PASS — `find .../analysis -name "*.log"` → 0. Only path strings in JSON manifests reference raw, not file mixing.

**Analysis mixed with immutable raw (J):** PASS — raw `CSI-SENSE-001/raw/` contains only raw logs/sidecars; analysis `CSI-SENSE-001/analysis/` contains only derived `csv/npz/json/png` (correct). `CSI_SENSE_001/ANALYSIS/stats/` similarly only derived.

**Inconsistent naming (N):** `CSI_SENSE_001` (underscore, caps `ANALYSIS`/`METADATA`/`PLAN`) vs `CSI-SENSE-001` (hyphen, lowercase `analysis`/`metadata`/`reports`) vs `CSI_VERIFY_001` (underscore) vs `SOURCE_PROJECT` (underscore) — **inconsistent** (see §14).

**Version/provenance ambiguity (O):** NO — pinned commits clear (`296b6eab`/`8633d671`).

**Contradiction with history (P):** `HARDWARE_RECON empty` contradicts history expectation of Nano recon file — flagged; `PROJECT_DOCUMENTATION empty` okay per manifest; `CHECKSUMS 77` pre-pilot vs `67M CSI-SENSE-001` post-pilot correctly separate but needs consolidation.

---

## 11. Secrets/Credentials

**Never printing actual secrets — per audit rule `credential/secret detected — DO NOT expose in report`.**

**Pattern hits (`grep -r -i -E "password|ssid|psk|..."`):** `grep` flagged ~40 lines containing terms `SSID`, `BSSID`, `WPA`, `password`, `PSK`, `CONFIG_EXAMPLE_WIFI_SSID`, `CONFIG_EXAMPLE_WIFI_PASSWORD` in **reports** (`PILOT_REPORT.md:38`, `BACKUP_MANIFEST.md:184`, etc.) and **metadata/tools** (`capture_config.json:18`, `hardware_identity.json:36`, `firmware_versions.json:35`, `validate_raw.py:40`). These are **expected reproductions** for provenance (router identity `Nihaal`/`8C:53:C3:5B:E1:59`, `WPA2-PSK`, sdkconfig defaults). **No raw credential exposure beyond intended provenance.**

**Specific handling:**

- `BACKUP_MANIFEST.md:184` explicitly states `No Wi-Fi password / PSK is printed verbatim here` — PASS.
- Reports retain `BSSID 8C:53:C3:5B:E1:59` (not secret, MAC) — okay to disclose per history.
- `firmware_versions.json:35` contains `CONFIG_EXAMPLE_WIFI_SSID="Nihaal"` and `CONFIG_EXAMPLE_WIFI_PASSWORD` placeholder — **credential/secret detected — DO NOT expose in report** (actual password string not printed here; audit suppresses with `sed`).
- No files contain high-entropy `api_key`/`token` beyond local provenance.

**Verdict:** **Credential/secret detected — DO NOT expose in report** — audit output suppresses with placeholder as required; folder contains only expected router provenance, no inadvertent `.env`/`id_rsa`/`token` leaks. **Before Drive upload, verify `firmware_versions.json` sdkconfig snippet and `CSI-VERIFY-001_FINAL_REPORT.md:52` code block do not contain literal PSK if sharing publicly** — currently contains literal string per `firmware_versions.json:1` line  `CONFIG_EXAMPLE_WIFI_PASSWORD="REDACTED"` (detected via `grep password`) — **operator must redact PSK in public publication copy** but preservation copy for Drive is okay if Drive is private; audit does not print it here.

---

## 12. Temporary/Disposable Files

**Should NOT enter research archive (99_ARCHIVE candidate):**

| Path | Reason |
|------|--------|
| `SOURCE_PROJECT/` entire tree (31 files, 4.9M) | **Temporary staging mirror** — byte-identical mirror of `CSI_SENSE_001/` + `Desktop/` created 2026-09-06 22:45 by `BACKUP_MANIFEST` as “Source files were COPIED, not moved”; now duplicate inside final folder (7× tools, 5 metadata, 5 figures, 3 reports, 1 raw). **Disposable for final archive — keep outside or `99_ARCHIVE/`** |
| `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` root copy (21638) | Duplicate of `CSI-SENSE-001/reports/...` — staging artifact |
| `CSI-SENSE-001/BACKUP_BEFORE_REBOOT.md` + `BACKUP_BEFORE_REBOOT.md` root (5668 ×2) | Pre-reboot staging warning — **useful to keep one copy in `08_CHECKSUMS_MANIFESTS`** but duplicate not needed |
| `CHECKSUMS/SHA256SUMS.txt` (9.5K 77 entries) | **Historical pre-pilot manifest** — superceded by `CSI-SENSE-001/checksums/SHA256SUMS.txt` for pilot; consolidated manifest needed (see §14) |
| `CSI_SENSE_001/ANALYSIS/checksums.sha256` (0 empty) + `SOURCE_PROJECT/data/CSI-SENSE-001/checksums.sha256` (0 empty) | **Empty placeholders** — `empty` `file` → `e3b0c442`; should not enter archive |
| `CSI_SENSE_001/raw/` empty + `SOURCE_PROJECT/data/CSI-SENSE-001/raw/` empty | Empty placeholders — not needed |
| `PROJECT_DOCUMENTATION/` empty + `HARDWARE_RECON/` empty | Placeholders — keep dirs or remove; not harmful but empty |
| `CSI_SENSE_001/PLAN/CSI-SENSE-001_PLAN_downloads_duplicate.md` (56273 `edd19d0f`) | Smaller draft duplicate of `PLAN_v1.1` (`c72b2c4b`) — keep only `PLAN_v1.1.md` authoritative |
| No `__pycache__`, no `.pyc`, no `.tmp`, no `.build` | PASS — no cache/build artifacts |

**Total temporary bulk:** ~5M `SOURCE_PROJECT` + duplicate raw 7.1M extra copies + empty files — ~12M recoverable if de-duplicated.

---

## 13. Current vs Recommended Structure

**Ideal target (proposed logical, DO NOT reorganize now):**

```
00_PROJECT/  ├── overview/roadmap/decisions
01_HARDWARE/ ├── hardware recon + ESP32 identity + router + Nano recon
02_FIRMWARE/ ├── provenance ESP-IDF/ESP-CSI/config
03_RAW_DATA/ ├── CSI_VERIFY/ CSI_SENSE/{smoke,pilot}/ IMMUTABLE/
04_EVENTS_METADATA/ ├── events + study/room/env
05_ANALYSIS/ ├── parsed/features/baseline/PCA/spectrogram/stats
06_TOOLS/    ├── capture/validation/backup/parsing/analysis
07_REPORTS/  ├── verification/Phase B/C readiness/pilot/Nano
08_CHECKSUMS_MANIFESTS/ ├── SHA256 + backup manifests + integrity
99_ARCHIVE/  └── temporary
```

**Current mapping:**

| Ideal | Current Location(s) | Coverage | Gap |
|-------|---------------------|----------|-----|
| `00_PROJECT` | `PROJECT_DOCUMENTATION/` empty + `CSI_SENSE_001/PLAN/` (3) + `SOURCE_PROJECT/Desktop/PLAN*.md` | PLAN.md present `c72b2c4b` but no `00_PROJECT/` dir; decisions/roadmap not as separate docs | Create `00_PROJECT/` and move `PLAN_v1.1` as roadmap |
| `01_HARDWARE` | `CSI_SENSE_001/METADATA/hardware_identity.json` (`f35a5223`) + `HARDWARE_RECON/` empty + `NANO-RECON` missing | ESP32/router identity covered, but `HARDWARE_RECON` empty and `NANO-RECON-001.md` absent | Need `01_HARDWARE/NANO-RECON-001.md` etc. |
| `02_FIRMWARE` | `CSI_SENSE_001/METADATA/firmware_versions.json` + `capture_config.json` + `CSI_SENSE_001/TOOLS/csi_capture` | Full provenance `296b6eab`/`8633d671`/`ce23861e` present | Need `02_FIRMWARE/` dir to consolidate |
| `03_RAW_DATA` | `CSI_VERIFY_001/CSI_RAW...log` + `CSI_SENSE_001/RAW_DATA/` + `CSI-SENSE-001/raw/{smoke_test,trial_01}` | **GOOD** — raw correctly separated, immutable `444` | Remove duplicate `SOURCE_PROJECT/Desktop/CSI_RAW...` |
| `04_EVENTS_METADATA` | `CSI-SENSE-001/events/` + `metadata/` + `CSI_SENSE_001/METADATA/` (room_geometry etc.) + `SOURCE_PROJECT/data/.../metadata` | Events duplicated `×3 57975d24`, metadata duplicated `×2` | Consolidate to single `04_EVENTS_METADATA/` |
| `05_ANALYSIS` | `CSI-SENSE-001/analysis/{smoke_test,trial_01}` + `CSI_SENSE_001/ANALYSIS/{figures,stats}` + `SOURCE_PROJECT/data/.../analysis` | Derived correctly separated, but duplicated historical demo analysis in `CSI_SENSE_001/ANALYSIS` vs new `CSI-SENSE-001/analysis` | Merge/choose authoritative |
| `06_TOOLS` | `CSI_SENSE_001/TOOLS/csi_capture|analysis` + `SOURCE_PROJECT/tools/` | Tools duplicated ×2 | Keep single `06_TOOLS/` |
| `07_REPORTS` | `CSI_VERIFY_001/*FINAL*`, `CSI_SENSE_001/REPORTS/*`, `CSI-SENSE-001/reports/*`, `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` root | All reports present except NANO | Add `07_REPORTS/NANO-RECON-001.md`, consolidate pilot report single location |
| `08_CHECKSUMS_MANIFESTS` | `CHECKSUMS/SHA256SUMS.txt` (77) + `CSI-SENSE-001/checksums/SHA256SUMS.txt` (35) + `BACKUP_MANIFEST.md` + `BACKUP_COMPLETE.md` + `BACKUP_BEFORE_REBOOT.md` + empty `checksums.sha256` | Manifests present but split pre/post-pilot; empty placeholders | Create single consolidated `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` covering **117 files** + backup manifests |
| `99_ARCHIVE` | Not present — temporary artifacts scattered (`SOURCE_PROJECT`, empty dirs, duplicate report) | No archive dir | Create `99_ARCHIVE/` for disposable |

**Overall assessment:** Structure is **functional but fragmented** — raw/analysis separation **good** (no raw in analysis §4I), reports preserved, provenance intact, but historical `CSI_SENSE_001/` + `SOURCE_PROJECT/` duplicate staging + naming inconsistency (`_` vs `-`) prevents `READY` for publication archive. **Not organized well enough for direct Drive publication without cleanup** (see §14–15).

---

## 14. Required Reorganization

**Classify each change (no file moves executed in this audit — recommendations only):**

### MUST DO BEFORE DRIVE BACKUP

- **[MUST] Recover/add `NANO-RECON-001.md`** — Classic FT232R `0403:6001 A5069RR4 ftdi_sio /dev/ttyUSB1` recon (Auxiliary only) per history stage 5 is **missing** from `RF Vision Files` (`HARDWARE_RECON empty`). If file exists at `/tmp/NANO-RECON-001.md` or `~/Desktop` or external, copy to `01_HARDWARE/NANO-RECON-001.md` (or current `HARDWARE_RECON/NANO-RECON-001.md` then reorganize). Without it, Drive backup lacks stage 5 deliverable.
- **[MUST] Consolidate checksums to single authoritative manifest covering 117 files** — Current `CHECKSUMS/SHA256SUMS.txt` (77 pre-pilot) does NOT cover `CSI-SENSE-001/` pilot. Generate new `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` (or `CHECKSUMS/SHA256SUMS.txt` updated) by `find . -type f -exec sha256sum {} \; | sort` over **entire** `RF Vision Files` excluding the manifest itself. Keep `CSI-SENSE-001/checksums/SHA256SUMS.txt` as subset or deprecate. Without consolidated hash, Drive integrity unverifiable.
- **[MUST] Note volatile warning in any Drive README** — `BACKUP_BEFORE_REBOOT.md` already states `volatile overlay /cow` + `Google Drive is intended as pre-reboot preservation` — MUST retain one copy at root of Drive upload with `NOT persistent` disclaimer. Do not delete both `BACKUP_BEFORE_REBOOT.md`.

### SHOULD DO BEFORE DRIVE BACKUP

- **[SHOULD] De-duplicate raw 3× → 1× in `03_RAW_DATA/CSI_VERIFY/`** — Keep one authoritative `CSI_VERIFY_001/CSI_RAW...log` (`51d47ce`) under `03_RAW_DATA/CSI_VERIFY/` (or keep `CSI_VERIFY_001/` as is) and **remove/move** the two extra copies (`CSI_SENSE_001/RAW_DATA/` duplicate, `SOURCE_PROJECT/Desktop/` duplicate) to `99_ARCHIVE/` or delete from Drive copy to save 7.1M and avoid publication confusion. Raw SHA remains same; verify after dedup.
- **[SHOULD] Remove/Archive `SOURCE_PROJECT/` entire duplicate (31 files, 4.9M)** — This is staging mirror (`BACKUP_MANIFEST §3` “Source files were COPIED”) now duplicating `CSI_SENSE_001/` exactly. **DO NOT upload `SOURCE_PROJECT/` as separate tree to Drive** — either delete from Drive staging or move to `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/` if audit trail needed. Saves 4.9M and removes `duplicate tools/metadata` confusion.
- **[SHOULD] Remove single duplicate report `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` root** — Keep only `CSI-SENSE-001/reports/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` (`5dd2cb`) as authoritative; root copy is staging convenience.
- **[SHOULD] Remove empty `checksums.sha256` ×2 (0 bytes `e3b0c442`)** — placeholders from Phase B `data/CSI-SENSE-001/checksums.sha256`; not needed in archive (empty).
- **[SHOULD] Keep authoritative `PLAN_v1.1.md` only** — `CSI_SENSE_001/PLAN/CSI-SENSE-001_PLAN_downloads_duplicate.md` (`edd19d0f 56273`) is smaller draft; keep `PLAN_v1.1.md` (`c72b2c4b 75936`) as authoritative, move draft to `99_ARCHIVE/` or delete from Drive.
- **[SHOULD] Fix absolute paths in pilot manifests or add README note** — `CSI-SENSE-001/analysis/trial_01/{parse_meta,features,baseline,pca,temporal_plots}_*.json` contain hard ` /home/ubuntu/Desktop/RF Vision Files/...:1` and `/home/ubuntu/tools/...:1` (grep `absolute path patterns` shows 20+ lines). **Will become invalid after moving to Drive** (different base). SHOULD either rewrite as relative `./raw/...` before Drive or include `README: absolute paths refer to Live session` disclaimer. Not data loss, but usability.
- **[SHOULD] Create `00_PROJECT/01_HARDWARE/...` logical dirs per §13 target instead of scattered `CSI_SENSE_001` / `CSI-SENSE-001` / `CSI_VERIFY_001`** — For publication archive, reorganize to ideal structure (move `CSI_VERIFY_001/` → `03_RAW_DATA/CSI_VERIFY/` + `07_REPORTS/`, etc.). **Can be post-upload reorganization** but recommended before to avoid Drive clutter. Keep at least one `README.md` at Drive root mapping old→new.
- **[SHOULD] Normalize naming `CSI_SENSE_001` vs `CSI-SENSE-001` vs `CSI_VERIFY_001`** — Choose `CSI-SENSE-001` (hyphen, pilot authoritative) or `CSI_SENSE_001` consistently; current mix is confusing. Rename to consistent scheme in Drive reorganized copy (e.g., all hyphen).

### CAN DO LATER (post-Drive, not blocking)

- [CAN] Remove empty placeholder dirs `PROJECT_DOCUMENTATION`/`HARDWARE_RECON`/`CSI_SENSE_001/raw`/`SOURCE_PROJECT/data/.../raw` or keep as `99_ARCHIVE`.
- [CAN] Move `BACKUP_MANIFEST.md`/`BACKUP_COMPLETE.md` to `08_CHECKSUMS_MANIFESTS/` with checksums (they are currently at root).
- [CAN] Generate consolidated file list `FILELIST.txt` (`find -printf "%P\t%s\t%m\t%TY-..." | sort`) for Drive archive index.
- [CAN] Add `FINAL-FOLDER-AUDIT-001.md` to `07_REPORTS/` or `08_CHECKSUMS_MANIFESTS/` after this audit (currently to be placed outside first).

### DO NOT TOUCH

- **[DO NOT TOUCH] Raw immutable experimental data** — `CSI-SENSE-001/raw/{smoke_test,trial_01}/*.log` (`ce047085` 499069, `4734dcf` 14304955) and sidecars (`capture_meta`, `validate`, `.sha256`) `444` — **never modify/rename/move without preserving SHA**; they are human experiment data `PILOT INCONCLUSIVE` must remain byte-identical.
- **[DO NOT TOUCH] CSI-VERIFY main raw 70s `51d47ce`** — 3 copies currently MATCH; if de-duplicating, keep one byte-identical, verify SHA after.
- **[DO NOT TOUCH] Firmware/hardware provenance JSON** — `hardware_identity.json`, `firmware_versions.json`, `capture_config.json` — do not edit (contain `296b6eab`/`8633d671`).
- **[DO NOT TOUCH] Analysis derived files** — `parsed_trial01.csv 14092781`, `features.npz 29155642`, `baseline_model.npz`, `pca.npz` etc. in `CSI-SENSE-001/analysis/` — do not re-run/replace; they are results of pilot INCONCLUSIVE, keep as is.
- **[DO NOT TOUCH] Validated pilot report `5dd2cb` and verification FINAL `d8b669a2`** — never edit after preservation.

---

## 15. Google Drive Backup Readiness

### **READY WITH CLEANUP**

**Explanation:**

- **Functional readiness:** All **critical raw immutable data** (`51d47ce` main CSI-VERIFY, `ce047085` smoke, `4734dcf` pilot) **MATCH SHA** and are present with sidecars (`444`), all **Phase B tooling** (11 files) and **metadata provenance** (`296b6eab`/`8633d671`/MAC `f4:65:0b:56:0e:18` BSSID `8C:53:C3:5B:E1:59`) present, all **authoritative reports** (CSI-VERIFY PASS, Phase B, Phase C readiness, Pilot INCONCLUSIVE `5dd2cb`) preserved, pilot analysis derived correctly separated, no raw-in-analysis mixing, no cache artifacts, volatile warning documented.

- **Not READY (without cleanup):** **Missing `NANO-RECON-001.md`** (stage 5) not in folder — Drive backup would lack Nano auxiliary recon deliverable; **non-consolidated checksums** (`CHECKSUMS 77` pre-pilot + `CSI-SENSE-001/checksums 35` pilot) require single authoritative manifest for 117 files to verify Drive integrity; **duplicate bulk** (`SOURCE_PROJECT` 4.9M + 2× extra raw 7.1M + root pilot report duplicate + empty `checksums.sha256`) will clutter publication archive and inflate Drive upload ~12M; **absolute Live paths** in pilot JSON manifests will break after Drive move without README note; **naming inconsistency** (`CSI_SENSE_001` vs `CSI-SENSE-001`) confuses logical organization per §13.

- **NOT READY would require** missing critical raw, SHA mismatch, or absent pilot report — none of which apply (all MATCH). Therefore **READY** if operator **adds Nano recon** (MUST), **generates consolidated SHA256 manifest** (MUST), and **performs §14 SHOULD cleanup** (de-duplicate/source-project/archive) before or immediately after Drive upload with clear mapping. If operator uploads current folder as-is **without Nano and with duplicate SOURCE_PROJECT**, integrity remains (raw MATCH) but organization is **NOT publication-ready** — would need post-upload reorganization and second checksum pass.

**Minimal MUST before upload:** `NANO-RECON-001.md` added + consolidated `SHA256SUMS.txt` for 117 files (plus retaining `BACKUP_BEFORE_REBOOT.md` volatile disclaimer). **Recommended SHOULD before upload** (`SOURCE_PROJECT` archived/removed, extra raw removed, pilot root duplicate removed, empty checksums removed) yields clean 65–70M Drive archive instead of 80M cluttered.

---

## 16. Reboot Safety

**Explicitly: What data would be lost if the Live session reboots before Google Drive backup:**

- **ALL data in `/home/ubuntu/Desktop/RF Vision Files` (117 files, 80M, 82915400 bytes)** is currently on **volatile Live-USB storage** (`/cow` overlay `7.7G` `overlay upperdir=/cow/upper` + `/tmp` tmpfs `7.7G` per `df -hT` / `findmnt / overlay`): **`findmnt` shows `TARGET / SOURCE /cow FSTYPE overlay OPTIONS rw...upperdir=/cow/upper`** — reboot destroys `/cow/upper` unless persisted to Drive/USB. This includes:
  - **Raw immutable experimental data:** CSI-VERIFY main `51d47ce` 70s 3.5M, **pilot raw `4734dcf` 310s 14M** (`CSI-SENSE-001/raw/trial_01/...`), **smoke `ce047085` 10s 499K** — **human experiment pilot (A→F, PILOT INCONCLUSIVE) would be irretrievably lost** (no persistent copy; `/home/ubuntu/data/CSI-SENSE-001/raw` empty, `nvme0n1` BitLocker locked untouched per `hardware_identity.json:1`, `/cdrom` `HP v210w` `ro` `vfat 30G` not written).
  - **All derived analysis:** `CSI-SENSE-001/analysis/trial_01/` `features.npz 27.8M`, `parsed_trial01.csv 13.4M`, `baseline_model.npz`, `pca.npz`, `figures/*.png` 53.8M total — lost.
  - **All reports/manifests/metadata:** `CSI-VERIFY-001_FINAL_REPORT.md:1` `d8b669a2`, `PHASE_B`/`PHASE_C` reports, `PILOT_REPORT.md:1` `5dd2cb` INCONCLUSIVE, `BACKUP_MANIFEST.md`, `CHECKSUMS/SHA256SUMS.txt` (77+35), `firmware_versions.json` `296b6eab`/`8633d671`, `hardware_identity.json` `f4:65:0b:56:0e:18` — lost.
  - **Tools duplication not lost** (source remains at `/home/ubuntu/tools/` + `/home/ubuntu/data/` on Live, but also volatile `Live` — same loss) — **pilot raw is unique to this `RF Vision Files` staging**.
  - **Ephemeral sources already lost if not in `RF Vision Files`:** CSI-VERIFY boot `5608f152` already NOT FOUND (likely only `/tmp/csi_boot.log`); if `NANO-RECON-001.md` remains only at `/tmp` or `~/Desktop`, reboot loses it too.
- **What survives reboot:** **Nothing on `RF Vision Files` path** — only if already uploaded to **Google Drive** (intended destination per `BACKUP_BEFORE_REBOOT.md:1` `tar -czf RF_Vision_Files...`) or external `HP v210w 30G /cdrom ro` (currently `ro`, not written) or Windows `nvme0n1` `476.9G BitLocker` (untouched, locked) would survive — but audit shows **no persistent Drive upload yet** (`study_metadata.json:1` `persistent_backup null` per `PHASE_C_READINESS_REPORT`, `BACKUP_MANIFEST` still `temporary Live-USB staging`). **No Google Drive mount observed in `df -hT`** (no `drive`/`gdrive`/`rclone` memt).
- **Therefore:** **Reboot before Drive backup = total loss of PHASE C pilot (smoke + trial_01 raw 15M), derived analysis 53M, and all staging reports — would require re-running human experiment (Trials 2–10 not run) and rebuilding analysis, but current pilot raw is unique human-motion capture (A→F LOS crossing) not repeatable without new subject.**

**Safety action:** **DO NOT reboot** until `Google Drive upload of entire `/home/ubuntu/Desktop/RF Vision Files` (or `tar -czf "RF_Vision_Files_20260906_2315_UTC.tar.gz" "RF Vision Files"` then upload) **sha-verified** (consolidated manifest MATCH). Keep `BACKUP_BEFORE_REBOOT.md` instructions visible.

---

## Appendix — Commands Executed (read-only)

```
find /home/ubuntu/Desktop/RF Vision Files -type d -print | sort
find -type f -printf "%P\t%y\t%s\t%TY-%Tm-%Td %TH:%TM:%TS\t%p" | sort
du -sh /du -sb /du -sh /*
find -type f -printf "%s %p" | sort -nr | head -20
find -type f -print0 | xargs -0 file | sort
sha256sum <each known raw> and find -name "*.log" -exec sha256sum | sort
find -type f -exec sha256sum {} \; | sort > /tmp/allsha.txt; awk uniq -c; duplicate groups
cat CHECKSUMS/SHA256SUMS.txt / CSI-SENSE-001/checksums/SHA256SUMS.txt
ls -la / ls -laR PROJECT_DOCUMENTATION HARDWARE_RECON
grep -r -i -E "password|ssid|psk|secret" | sed "credential/secret detected — DO NOT expose in report"
grep -r -E "/home/ubuntu|/tmp/|/cow/" | cut -c1-200
df -hT / findmnt -T
grep -r "csi_raw|5608f152|51d47ce" etc. (all read-only)
```

**No files modified, renamed, moved, deleted, created, flashed, or rebooted — read-only audit STOP.**

---

**Report written outside first:** `/tmp/FINAL-FOLDER-AUDIT-001.md` (this file, 270+ lines) — contents provided in terminal; to preserve in project folder copy to `/home/ubuntu/Desktop/RF Vision Files/FINAL-FOLDER-AUDIT-001.md:1` **after** audit review (copy, not move, verify SHA after).  
**STOP after audit. Do not reorganize. Do not upload. Do not reboot. Do not experiment.**
