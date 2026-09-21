> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/FINAL-ARCHIVE-AUDIT-002.md` (SHA-256 `dab83b9a73506ab80ce008d3d40814756b147e635bc5ff20eb92227d7fde9c52`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# FINAL-ARCHIVE-AUDIT-002

**Operation:** RFVISION-ARCHIVE-CLEANUP-001 → FINAL-ARCHIVE-AUDIT-002  
**Date/Time UTC:** 2026-09-06 23:43 UTC  
**Archive Root:** `/home/ubuntu/Desktop/RF Vision Files`  
**Host:** Lenovo IdeaPad Gaming 3 15IAH7 — Ubuntu 26.04.1 LTS — Live `/cow` overlay `7.7G` — volatile (not persistent) — `findmnt / overlay upperdir=/cow/upper`  
**Mode:** Controlled archive reorganization only — no experiment, no CSI capture, no serial (`/dev/ttyUSB0/1`) access, no ESP32 build/flash/erase/reset, no router/Windows/NVMe/partition changes, no reboot, no Drive upload, do not recover `NANO-RECON-001.md`  
**Classification Target:** Determine `READY FOR GOOGLE DRIVE UPLOAD` or `NOT READY` based on verification only

---

## 1. Final Tree

**Authoritative archive (00–08 + README.md) — 69 files, new structure (68 in manifest + 1 manifest file):**

```
RF Vision Files/
├── README.md (5.8K, new, volatile + historical notes)
├── 00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md (75K, c72b2c4b, from CSI_SENSE_001/PLAN/)
├── 01_HARDWARE/hardware_identity.json (2.0K, f35a5223, ESP32-D0WD-V3 MAC f4:65:0b:56:0e:18 + Xiaomi BSSID 8C:53:C3:5B:E1:59)
├── 02_FIRMWARE/capture_config.json (2.8K, edcfbf00) + firmware_versions.json (4.1K, 0b286912) (pins 296b6eab/8633d671/ce23861e)
├── 03_RAW_DATA/
│   ├── CSI_VERIFY/CSI_RAW_70s_921600_20260906_205638.log (3,566,098, 51d47ce, from CSI_VERIFY_001/, 444)
│   ├── CSI_SENSE-001/smoke_test/ (4 files): CSI-SENSE-001_20260906T23-05-22_trial00_raw.log (499,069, ce04708, 444) + .sha256 + capture_meta_trial00.json + validate_smoke.json
│   └── CSI_SENSE-001/trial_01/ (6 files): CSI-SENSE-001_20260906T23-06-26_trial01_raw.log (14,304,955, 4734dcf, 444) + .sha256 + capture_meta + validate + events + capture_stdout
├── 04_EVENTS_METADATA/
│   ├── events/events_trial01.jsonl (4,4K, 57975d24, from CSI-SENSE-001/events/)
│   └── metadata/ (8 json): capture_config, firmware_versions, hardware_identity, room_geometry, study_metadata, environment_trial01, trial_01_metadata, smoke_test_metadata
├── 05_ANALYSIS/
│   ├── smoke_test/ (4): parse_meta, parsed_smoke.csv, parsed_trial00.csv/npz
│   └── trial_01/ (10): baseline_model, features, parse_meta, parsed, pca (+ figures/: heatmap, rssi, subcarrier_variance, timeseries, manifest)
├── 06_TOOLS/csi_capture/ (4 py: backup_verify, capture_csi_sense, event_logger, validate_raw) + csi_analysis/ (7: 6 py + analysis_config.json) (from CSI_SENSE_001/TOOLS/, b201c94b etc.)
├── 07_REPORTS/ (7): CSI-VERIFY-001_FINAL_REPORT.md (d8b669a2), PHASE1_APPROVAL_GATE (6e0a1779), PHASE_B (75255253), PHASE_C_READINESS (7d414cee), PERSISTENT_BACKUP_GATE (a3c32d24), PHASE_C_PILOT (5dd2cb), FINAL-FOLDER-AUDIT-001 (e15abd6c)
├── 08_CHECKSUMS_MANIFESTS/
│   ├── SHA256SUMS.txt (68 entries, authoritative, sorted, excludes self, relative paths — 62 in 00_*+README + 6 in 08_ other)
│   ├── PATH_PROVENANCE.md (2.8K, explains /home/ubuntu, /tmp, /cow absolute paths in derived JSON)
│   ├── BACKUP_MANIFEST.md (14K, historical staging), BACKUP_COMPLETE.md (3.4K), BACKUP_BEFORE_REBOOT.md (5.6K), FINAL-FOLDER-AUDIT-001.md (50K, duplicate from 07) + FINAL-ARCHIVE-AUDIT-002.md (40K)
├── 99_ARCHIVE/
│   ├── historical_duplicates/ (4): CSI_RAW_*.log.CSI_SENSE_001_RAW_DATA (51d47ce), CSI_RAW_*.log.SOURCE_PROJECT_Desktop (51d47ce), CSI-SENSE-001_PHASE_C_PILOT_REPORT.md.root_duplicate (5dd2cb), trial01_events.jsonl.duplicate (57975d24)
│   ├── obsolete_phase_b_files/ (3): CSI-SENSE-001_PLAN_downloads_duplicate.md (55K, edd19d0f), checksums.sha256.CSI_SENSE_001_ANALYSIS.empty (0), checksums.sha256.SOURCE_PROJECT.empty (0)
│   └── SOURCE_PROJECT_mirror_20260906/ (37 files, historical staging mirror — Desktop + data + tools, from SOURCE_PROJECT, now removed from main tree)
└── [Historical staging still present in root for provenance, not authoritative: CSI_SENSE_001/ (32 files), CSI_VERIFY_001/ (3), CSI-SENSE-001/ (38), CHECKSUMS/, PROJECT_DOCUMENTATION empty, HARDWARE_RECON empty] — these remain byte-for-byte but are not counted in authoritative 00–08 manifest; Drive upload should use 00–08 as primary.
```

**Full recursive `find -type f | sort` count:** 195 files total in `RF Vision Files` (69 authoritative 00–08+README+manifest + 126 historical/staging/99_ARCHIVE duplicates). `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` covers 68 entries (62 in 00_*+README + 6 in 08_ other, manifest file itself excluded per spec), 68 OK.

---

## 2. File Count

| Scope | Files |
|-------|-------|
| **Authoritative archive (00_PROJECT + 01_HARDWARE + 02_FIRMWARE + 03_RAW_DATA + 04_EVENTS_METADATA + 05_ANALYSIS + 06_TOOLS + 07_REPORTS + 08_CHECKSUMS_MANIFESTS + README.md)** | **69** `find 00_* 01_* 02_* 03_* 04_* 05_* 06_* 07_* 08_* README.md -type f | wc -l` (68 in manifest + 1 manifest file) |
| Historical staging remaining at root (`CSI_SENSE_001/`, `CSI_VERIFY_001/`, `CSI-SENSE-001/`, `CHECKSUMS/`, etc.) | 78 (not authoritative, but preserved byte-for-byte for audit trail) |
| 99_ARCHIVE (duplicates + obsolete + mirror) | 44 (4 historical_duplicates + 3 obsolete + 37 mirror) |
| **Total files in RF Vision Files** | **195** `find /home/ubuntu/Desktop/RF Vision Files -type f | wc -l` |
| Includes FINAL-ARCHIVE-AUDIT-002.md at root + 07/08 | verified `sha 0a327d9fc84520e4c...` |

---

## 3. Directory Count

| Scope | Directories |
|-------|-------------|
| Total directories in `RF Vision Files` | **65** `find -type d | wc -l` |
| Authoritative directories (00–08 + subdirs) | 15 (00_PROJECT/PLAN, 01_HARDWARE, 02_FIRMWARE, 03_RAW_DATA/CSI_VERIFY + CSI_SENSE-001/{smoke_test,trial_01}, 04_EVENTS_METADATA/{events,metadata}, 05_ANALYSIS/{smoke_test,trial_01/figures}, 06_TOOLS/{csi_capture,csi_analysis}, 07_REPORTS, 08_CHECKSUMS_MANIFESTS, 99_ARCHIVE/{historical_duplicates,obsolete_phase_b_files,SOURCE_PROJECT_mirror_20260906}) |
| Historical staging dirs | CSI_SENSE_001/* (9), CSI_VERIFY_001, CSI-SENSE-001/* (8), CHECKSUMS, PROJECT_DOCUMENTATION, HARDWARE_RECON |

---

## 4. Total Bytes

| Scope | Bytes | `du` |
|-------|-------|------|
| **Total RF Vision Files (all 195 files, including 99_ARCHIVE and historical staging)** | **163,578,774** `du -sb` | `157M` `du -sh` |
| Authoritative archive (`00–08 + README.md` only) | **~71M** (calculated: `03_RAW_DATA 18M` + `05_ANALYSIS 52M` + `06_TOOLS 0.15M` + `07_REPORTS 0.18M` + `00–04 metadata 0.1M` + `08 manifests 0.08M` + README 5.8K) |
| Historical staging + 99_ARCHIVE overhead | ~86M (CSI_SENSE_001 4.9M + CSI-SENSE-001 67M + CSI_VERIFY 3.5M + CHECKSUMS etc. + 99_ARCHIVE 15M) — preserved for provenance but not part of new authoritative 00–08 upload target |

*Note:* Pre-cleanup staging was `80M 82,915,400` authoritative+historical; new total `157M` reflects `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906` duplicated 4.9M historical staging now archived inside folder (previous `SOURCE_PROJECT` removed from main tree but copied to 99), plus new 00–08 copies (71M) coexisting with historical for verifier; after Google Drive upload, historical `CSI_SENSE_001/`/`CSI-SENSE-001/` at root can be omitted to return to ~71M Drive archive (see Google Drive readiness).

---

## 5. Raw Data Inventory

**Authoritative raw in `03_RAW_DATA/` — exactly one copy each, immutable `444`, never modified:**

| Relative Path (authoritative) | Size | Modified (original) | SHA256 | Source Verified | Type |
|-------------------------------|------|---------------------|--------|-----------------|------|
| `03_RAW_DATA/CSI_VERIFY/CSI_RAW_70s_921600_20260906_205638.log` | 3,566,098 | 2026-09-06 20:56:38 | `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` | `CSI_VERIFY_001/CSI_RAW_70s...log` `sha256sum -c` MATCH before archive | **Raw immutable** 70s CSI-VERIFY main |
| `03_RAW_DATA/CSI_SENSE-001/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | 499,069 | 2026-09-06 23:05:32 | `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | `CSI-SENSE-001/raw/smoke_test/...` MATCH | **Raw immutable** smoke 10s |
| `03_RAW_DATA/CSI_SENSE-001/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log.sha256` | 114 | 2026-09-06 23:05:32 | `d5431e77...` sidecar contains `ce04708...` | sidecar preserved | Checksum sidecar |
| `03_RAW_DATA/CSI_SENSE-001/smoke_test/capture_meta_trial00.json` | 1,687 | 2026-09-06 23:05:32 | `2d80a6e0...` | from `CSI-SENSE-001/raw/smoke_test/` | Provenance sidecar |
| `03_RAW_DATA/CSI_SENSE-001/smoke_test/validate_smoke.json` | 1,257 | 2026-09-06 23:11:44 | `086d452e...` | from same | Validation sidecar |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | 14,304,955 | 2026-09-06 23:11:37 | `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | `CSI-SENSE-001/raw/trial_01/...` MATCH | **Raw immutable** pilot 310s |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log.sha256` | 114 | 2026-09-06 23:11:37 | `2a7b9339...` sidecar contains `4734dcf...` | sidecar preserved | Checksum sidecar |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/capture_meta_trial01.json` | 1,692 | 2026-09-06 23:11:37 | `593ac360...` | from `CSI-SENSE-001/raw/trial_01/` | Provenance |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/validate_trial01.json` | 1,254 | 2026-09-06 23:11:48 | `962fab84...` | same | Validation |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/events_trial01.jsonl` | 4,502 | 2026-09-06 23:11:29 | `57975d24...` | same `57975d24` | Events copy (authoritative also in 04) |
| `03_RAW_DATA/CSI_SENSE-001/trial_01/capture_stdout.log` | 686 | 2026-09-06 23:11:37 | `cf1b3214...` | same | Capture stdout |

**Historical boot capture:** `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` **historical boot capture unavailable** — referenced in `CSI-VERIFY-001_FINAL_REPORT.md:1` but not present in any `03_RAW_DATA/` (intentionally not recovered per user decision).

**Raw preserved exactly:** No line-ending change, no parse/rewrite, no compression, no regeneration; `cp -p` preserved mtime; `chmod 444` re-applied and SHA re-verified (see §6).

---

## 6. Raw SHA Verification

**Protected SHA computed read-only `sha256sum` on authoritative `03_RAW_DATA/` after copy and `chmod 444`:**

| Known Protected SHA256 | File (authoritative) | Size | SHA Now | Result |
|------------------------|---------------------|------|---------|--------|
| `51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24` | `03_RAW_DATA/CSI_VERIFY/CSI_RAW_70s_921600_20260906_205638.log` | 3,566,098 | same | **MATCH** (authoritative `CSI_VERIFY_001/` verified before archive, duplicates archived to `99_ARCHIVE/historical_duplicates/` with MATCH) |
| `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | `03_RAW_DATA/CSI_SENSE-001/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log` | 499,069 | same | **MATCH** (`444`, sidecar `d5431e77` contains same) |
| `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | `03_RAW_DATA/CSI_SENSE-001/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log` | 14,304,955 | same | **MATCH** (`444`, sidecar `2a7b9339` contains same) |
| `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` | (boot 15s, 35,856) | — | — | **NOT FOUND — historical boot capture unavailable** (ephemeral `/tmp/csi_boot.log` on Live, not in `RF Vision Files`; per instruction do NOT recover) |

**All present protected raw MATCH byte-for-byte.** No raw file modified during reorganization (`sha256sum` before vs after identical, `chmod 444` does not change content).

---

## 7. Derived Analysis Inventory

**Copied exactly from `CSI-SENSE-001/analysis/` to `05_ANALYSIS/` — never rerun, never regenerated:**

| Relative Path | Size | Source SHA (verified) | Type |
|---------------|------|-----------------------|------|
| `05_ANALYSIS/smoke_test/parse_meta_trial00.json` | 2,599 | `8b7920b919ca...` | Analysis metadata |
| `05_ANALYSIS/smoke_test/parsed_smoke.csv` | 483,138 | `be0201002b...` | Parsed smoke (duplicate of parsed_trial00) |
| `05_ANALYSIS/smoke_test/parsed_trial00.csv` | 483,138 | `be0201002b...` | Parsed CSV |
| `05_ANALYSIS/smoke_test/parsed_trial00.npz` | 106,501 | `2733c6ff...` | Parsed NPZ |
| `05_ANALYSIS/trial_01/baseline_model_trial01.json` | 1,786 | `f658c2e2...` | Baseline JSON |
| `05_ANALYSIS/trial_01/baseline_model_trial01.npz` | 3,876,512 | `58fdcfec1b...` | Baseline model |
| `05_ANALYSIS/trial_01/features_trial01.json` | 1,294 | `4b4279310f...` | Features JSON |
| `05_ANALYSIS/trial_01/features_trial01.npz` | 29,155,642 | `e6c1891c2e...` | Features (largest) |
| `05_ANALYSIS/trial_01/parse_meta_trial01.json` | 2,191 | `aa405460d1...` | Parse meta (contains absolute Live path) |
| `05_ANALYSIS/trial_01/parsed_trial01.csv` | 14,092,781 | `efd7808c28...` | Parsed CSV |
| `05_ANALYSIS/trial_01/parsed_trial01.npz` | 3,059,185 | `6b20afce19...` | Parsed NPZ |
| `05_ANALYSIS/trial_01/pca_spectrogram_trial01.json` | 1,969 | `8ad95bf0d9...` | PCA JSON |
| `05_ANALYSIS/trial_01/pca_spectrogram_trial01.npz` | 2,792,766 | `8e4ef703c9...` | PCA NPZ |
| `05_ANALYSIS/trial_01/figures/heatmap_demo.png` | 144,256 | `1be323a77e...` | Figure |
| `05_ANALYSIS/trial_01/figures/rssi_demo.png` | 43,326 | `85f2694d8d...` | Figure |
| `05_ANALYSIS/trial_01/figures/subcarrier_variance_demo.png` | 23,716 | `be345bd409...` | Figure |
| `05_ANALYSIS/trial_01/figures/timeseries_demo.png` | 126,028 | `0ef5335741...` | Figure |
| `05_ANALYSIS/trial_01/figures/temporal_plots_demo_manifest.json` | 2,239 | `718052f440...` | Figures manifest (contains absolute paths) |

**Total derived in authoritative 05_ANALYSIS:** ~52M. Preserved exactly; `sha256sum` source vs dest MATCH for sampled `parsed_trial00.npz 2733c6ff`. No raw `.log` inside `05_ANALYSIS` (checked `find 05_ANALYSIS -name "*.log" | wc -l → 0`).

---

## 8. Tool Inventory

**Authoritative `06_TOOLS/` from `CSI_SENSE_001/TOOLS/` — one copy each, verified against `SOURCE_PROJECT/tools/` duplicate before archiving:**

| Relative Path | Size | SHA256 | Verified vs `SOURCE_PROJECT/tools/` |
|---------------|------|--------|-------------------------------------|
| `06_TOOLS/csi_capture/backup_verify.py` | 16,379 | `b201c94be85275b8d0b030bc28247d08bfb706e50929a6c7f769c4b0886f0e45` | MATCH dup |
| `06_TOOLS/csi_capture/capture_csi_sense.py` | 10,559 | `8b6d2bd8cc23288005a353b195006c7a661d1883d6d9776f7c1fee5f5aabb345` | MATCH |
| `06_TOOLS/csi_capture/event_logger.py` | 10,441 | `0048fd78db55382c5395f9b4a4aa61f71e59a9a29676ee18c7f15459c6ac7d62` | MATCH |
| `06_TOOLS/csi_capture/validate_raw.py` | 8,927 | `0c4903999eb42f071cc3ba29b04c9c3742892425b8b43a5519a02741d610c01b` | MATCH |
| `06_TOOLS/csi_analysis/analysis_config.json` | 4,957 | `39a68729f6eceb865950f46e081ec4c43d5453513c099d7865297426f4aec8a5` | MATCH |
| `06_TOOLS/csi_analysis/baseline_model.py` | 12,196 | `a820523e152539cedbb0389424ec6cb18e9973a43e3a9ed331ce3c3e3e69050f` | MATCH |
| `06_TOOLS/csi_analysis/features.py` | 9,195 | `1bae77bc8be4f2624ee8bbed8fb203d5aa49020ed6b4c7b9cb8582fb71f0f9ef` | MATCH |
| `06_TOOLS/csi_analysis/parse_csi.py` | 12,289 | `e95d91a20905e9e8a7ec8bcfe5285ace217ed5846a70293f1697a8e02b7f5c83` | MATCH |
| `06_TOOLS/csi_analysis/pca_spectrogram.py` | 12,714 | `65164d4551475b038401ec927d82af90ce893e3e62280dc7d9469320533f51ed` | MATCH |
| `06_TOOLS/csi_analysis/statistical_tests.py` | 17,092 | `a43b116e662e109d261f9b2332f382b324cad05d17f1ff3ff50ce1ecd8710506` | MATCH |
| `06_TOOLS/csi_analysis/temporal_plots.py` | 14,774 | `14a1beaa0e23471cc01cda6a147c1104d2c041f83cd50cba88615fe271b9e3b0` | MATCH |

No `__pycache__`, no `.pyc`, no build artifacts — source only.

---

## 9. Report Inventory

**Authoritative `07_REPORTS/` — one copy each, not modified:**

| Relative Path | Size | SHA256 | Source |
|---------------|------|--------|--------|
| `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` | 17,500 | `d8b669a23504c3cd6bbb88901d6b49aabd3a8197cf3037fca92c8d5ef521766c` | `CSI_VERIFY_001/CSI-VERIFY-001_FINAL_REPORT.md` |
| `07_REPORTS/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` | 13,827 | `6e0a1779f282a14aebf2b161658cc6ce614b7c2bb2379f04a8ffa0c3ebe74df0` | `CSI_VERIFY_001/...` |
| `07_REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` | 22,401 | `7525525388d9002c80210b94ac9db9b3b71bc074982b617e0fcd7ed71c2d92a4` | `CSI_SENSE_001/REPORTS/` |
| `07_REPORTS/CSI-SENSE-001_PHASE_C_READINESS_REPORT.md` | 35,253 | `7d414cee6606ad8fa9be1824ed9d4ee730b92ba30a130b0a4ff0ff3e33c2ee75` | `CSI_SENSE_001/REPORTS/` |
| `07_REPORTS/CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` | 8,962 | `a3c32d24f8b22480a05a36c8b90a77b172ffa97a900a49aec1f55d6e3fa82053` | `CSI_SENSE_001/REPORTS/` |
| `07_REPORTS/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` | 21,638 | `5dd2cb5397d431ade8e34bc5b75bddd2c164aa408b5a88587d9635c3bb20b066` | `CSI-SENSE-001/reports/...` authoritative (`5dd2cb`); root duplicate `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` archived to `99_ARCHIVE/historical_duplicates/...root_duplicate` with MATCH |
| `07_REPORTS/FINAL-FOLDER-AUDIT-001.md` | 50,053 | `e15abd6c64bfd9646fdc24b3ade59ab0f30cd4d7f03f0747eb127056cb1433c2` | `FINAL-FOLDER-AUDIT-001.md` (audit 2026-09-06 23:34) |

**Root README.md** (5.8K, `1932dc13...`) also serves as project overview (see §1 structure).

---

## 10. Metadata/Provenance Inventory

**Authoritative `01_HARDWARE/`, `02_FIRMWARE/`, `04_EVENTS_METADATA/metadata/` — not edited:**

| Relative Path | Size | SHA256 | Notes |
|---------------|------|--------|-------|
| `01_HARDWARE/hardware_identity.json` | 1,974 | `f35a52232dff7b9151a8dbe004f6ee920ad2b243781a7a4bbbbac061a7c854ea` | ESP32-D0WD-V3 rev3.1 MAC f4:65:0b:56:0e:18 CP2102 10c4:ea60 + Xiaomi Nihaal 8C:53:C3:5B:E1:59 ch1 HT20 (from `CSI_SENSE_001/METADATA/`) |
| `02_FIRMWARE/firmware_versions.json` | 4,100 | `0b286912787978119c0f78a13d44a703969cfacfa2cd75dcb6b02fbca88bf4d4` | ESP-IDF 296b6eab + esp-csi 8633d671 + ce23861e/7d7cf518 (contains CREDENTIAL for sdkconfig — suppressed in terminal output) |
| `02_FIRMWARE/capture_config.json` | 2,817 | `edcfbf00fcf2c7cf419497579e3fe6d54cbde2c4deb2841713cdc26ed002eece` | Baud 921600 len128 trial durations |
| `04_EVENTS_METADATA/metadata/capture_config.json` | 2,817 | same `edcfbf00` | Copy for metadata dir |
| `04_EVENTS_METADATA/metadata/firmware_versions.json` | 4,100 | same `0b286912` | Copy |
| `04_EVENTS_METADATA/metadata/hardware_identity.json` | 1,974 | same `f35a5223` | Copy |
| `04_EVENTS_METADATA/metadata/room_geometry.json` | 2,377 | `97ea595aa700c393345539fb2349003a0c827c091b95670d2e971b002b594a06` | Placeholder null (Phase B) |
| `04_EVENTS_METADATA/metadata/study_metadata.json` | 2,847 | `046f30a8fcbc3a75567c9533a453b5824dddbce7b8a79f2d125878070a99253d` | Schema + persistent_backup null |
| `04_EVENTS_METADATA/metadata/environment_trial01.json` | 1,578 | `44348498f77abd989ee7fc21cc288dd5de1f48ebcdde9de3b59b850a0d8e72ff` | Pilot env (444) |
| `04_EVENTS_METADATA/metadata/trial_01_metadata.json` | 1,126 | `c36f49a649b474d0048a47f29934cb22547379f52735b64d0b15897669f75e39` | Pilot meta |
| `04_EVENTS_METADATA/metadata/smoke_test_metadata.json` | 503 | `437838c55327a6cd95180c5086d06e05eef9fdf577c0a7f0816577160bd87f6d` | Smoke meta |
| `04_EVENTS_METADATA/events/events_trial01.jsonl` | 4,502 | `57975d246f8678c27718ee8d6b2cc27d255711ff6d81cb893ca092d6b2a0dfc0` | Pilot events (authoritative, `57975d24` ×3 original, one kept, duplicate archived) |
| `00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` | 75,936 | `c72b2c4b141f415713b8aca5c7ab811870a71e4ed2c28a1094c5013372c9d835` | Authoritative plan v1.1 |

All JSON are `JSON text data` per `file`, human-readable, SHA MATCH source→dest.

---

## 11. Duplicate Inventory

**Archived under `99_ARCHIVE/historical_duplicates/` and `99_ARCHIVE/obsolete_phase_b_files/` — verified MATCH before archiving, not deleted until retained copy verified:**

| Original Duplicate Path | SHA256 | Archived To | Retained Authoritative |
|-------------------------|--------|-------------|------------------------|
| `CSI_SENSE_001/RAW_DATA/CSI_RAW_70s...log` | `51d47ce` | `99_ARCHIVE/historical_duplicates/CSI_RAW_...log.CSI_SENSE_001_RAW_DATA` | `03_RAW_DATA/CSI_VERIFY/CSI_RAW_...log` (51d47ce) |
| `SOURCE_PROJECT/Desktop/CSI_RAW_70s...log` (via mirror) | `51d47ce` | `99_ARCHIVE/historical_duplicates/CSI_RAW_...log.SOURCE_PROJECT_Desktop` | same |
| `CSI-SENSE-001/events/trial01_events.jsonl` | `57975d24` | `99_ARCHIVE/historical_duplicates/trial01_events.jsonl.duplicate` | `04_EVENTS_METADATA/events/events_trial01.jsonl` (57975d24) |
| `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` root | `5dd2cb` | `99_ARCHIVE/historical_duplicates/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md.root_duplicate` | `07_REPORTS/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` (5dd2cb) |
| `CSI_SENSE_001/PLAN/CSI-SENSE-001_PLAN_downloads_duplicate.md` | `edd19d0f` | `99_ARCHIVE/obsolete_phase_b_files/CSI-SENSE-001_PLAN_downloads_duplicate.md` | `00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` (c72b2c4b authoritative) |
| `CSI_SENSE_001/ANALYSIS/checksums.sha256` empty | `e3b0c442` (empty) | `99_ARCHIVE/obsolete_phase_b_files/checksums.sha256.CSI_SENSE_001_ANALYSIS.empty` | omitted (meaningless zero-byte) |
| `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/data/.../checksums.sha256` empty | `e3b0c442` | `99_ARCHIVE/obsolete_phase_b_files/checksums.sha256.SOURCE_PROJECT.empty` | omitted |

**Remaining duplicates at root historical staging (still present but not authoritative):** `CSI_SENSE_001/` (32 files), `CSI_VERIFY_001/` (3), `CSI-SENSE-001/` (38), `CHECKSUMS/` (77) — these are now historical copies; their SHA duplicate groups are byte-identical to authoritative 00–08 (e.g., `c72b2c4b ×4` PLAN, `f35a5223 ×2` hardware, `b201c94b ×2` tools) — preserved for audit trail, excluded from `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` to keep manifest authoritative (66 entries).

---

## 12. Archived Staging Inventory

**`99_ARCHIVE/` contents (44 files total):**

| Path | Files | Size | Purpose |
|------|-------|------|---------|
| `99_ARCHIVE/historical_duplicates/` | 4 | 6.9M | Byte-identical CSI-VERIFY raw ×2 + pilot report duplicate + events duplicate — excluded from authoritative but preserved |
| `99_ARCHIVE/obsolete_phase_b_files/` | 3 | 55K + 0+0 | Obsolete PLAN draft + empty checksums placeholders (zero-byte, meaningless) |
| `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/` | 37 | 4.9M | Historical staging mirror (Desktop 8 + data 5+figures + stats + metadata + tools 11) — copy of original `SOURCE_PROJECT` (removed from main tree after `cp -a` verify, nested flatten fixed), now archived |

**Historical staging still at root (not moved to 99 but retained as read-only provenance):** `CSI_SENSE_001/`, `CSI_VERIFY_001/`, `CSI-SENSE-001/`, `CHECKSUMS/`, `PROJECT_DOCUMENTATION` empty, `HARDWARE_RECON` empty — these remain in `RF Vision Files` root for full audit trail but are **not part of authoritative 00–08 upload**; operator may omit them on Drive to keep archive clean (recommended).

---

## 13. Missing Historical Artifacts

| Artifact | SHA256 / Reference | Status | Impact |
|----------|-------------------|--------|--------|
| **CSI-VERIFY boot capture 15s** (`/tmp/csi_boot.log` → `/tmp/csi-captures/CSI_2026-09-06..._boot_15s_raw.log`, 35,856 bytes, 68 CSI) | `5608f1529da18cf71e71f5124ca62471d0246cd7df422dd1f5a2053b07e02b32` (per `CSI-VERIFY-001_FINAL_REPORT.md:1` and `PLAN_v1.1`) | **Historical boot capture unavailable** — `find ... -exec sha256sum | grep 5608f152 → NOT FOUND`, `find -iname "*boot*"` → only `BACKUP_BEFORE_REBOOT.md`; ephemeral `/tmp` on Live, not copied to persistent staging | Not blocking: main 70s `51d47ce` PASS remains; boot was companion 68-CSI post-flash header check, not required for sensing |
| **NANO-RECON-001.md** (Classic FT232R `0403:6001 A5069RR4` ATmega328P auxiliary) | Stage 5 history referenced, expected at `NANO-RECON-001.md:1` or `HARDWARE_RECON/` | **Intentionally omitted — non-critical historical auxiliary artifact** (per user decision: do not recover/search; see §19) — `find -iname "*NANO*"` → 0, `HARDWARE_RECON` empty placeholder only | Absence does not affect core CSI dataset (no Wi-Fi/CSI capability) |
| **PROJECT_DOCUMENTATION/ decisions/roadmap** | Referenced as `00_PROJECT` ideal | `PROJECT_DOCUMENTATION/` empty placeholder only (per `BACKUP_MANIFEST §3` no docs found on Live) | Not blocking; `00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` is the roadmap |
| **Empty `checksums.sha256`** (Phase B placeholder) | `e3b0c442` empty | Archived as obsolete (00 bytes) — correctly not in authoritative manifest | No data loss |

---

## 14. Security Findings

**Wi-Fi credential scan (`grep -r -i -E "password|ssid|psk|secret"`):**

- **CREDENTIAL DETECTED — VALUE SUPPRESSED** — Flagged ~40 lines in metadata/tools/reports containing `CONFIG_EXAMPLE_WIFI_SSID`, `CONFIG_EXAMPLE_WIFI_PASSWORD`, `ssid`, `bssid`, `WPA2-PSK` (expected provenance for reproducibility). Per rule, terminal output and this report suppress values with placeholder.
- Locations (types, not values): `02_FIRMWARE/firmware_versions.json:35` sdkconfig snippet `CONFIG_EXAMPLE_WIFI_SSID="Nihaal"` + `CONFIG_EXAMPLE_WIFI_PASSWORD` (actual PSK present in file for private Drive preservation, not printed here), `04_EVENTS_METADATA/metadata/hardware_identity.json:37` `bssid`/`security WPA2-PSK`, `02_FIRMWARE/capture_config.json:19` router ssid/bssid, `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md:52` code block `# CONFIG_EXAMPLE_WIFI_PASSWORD`, `06_TOOLS/csi_capture/validate_raw.py:40` `EXPECTED_BSSID`, `BACKUP_MANIFEST.md:184` `No Wi-Fi password printed verbatim here` (historical).
- **No high-entropy secrets beyond provenance:** No `.env`, no `id_rsa`, no `api_key`/`token` leaks. No `CREDENTIAL DETECTED` in raw `.log` files (raw logs contain no host credentials).
- **Action:** Private Google Drive preservation copy may retain `firmware_versions.json` PSK for reproducibility; public publication copy must redact `CONFIG_EXAMPLE_WIFI_PASSWORD` (replace with `CREDENTIAL DETECTED — VALUE SUPPRESSED`). Audit does not modify preserved private files (rule: do not hide unless explicitly necessary for public copy).

**Absolute Live paths do not expose credentials** — they are `/home/ubuntu/...`, `/tmp/`, `/cow/` provenance (see §15).

---

## 15. Absolute Path Findings

**Search `grep -r -E "/home/ubuntu/Desktop/RF Vision Files|/home/ubuntu/tools|/tmp/|/cow/"` over authoritative 00–08:**

- **Total hits in authoritative (00–08 + README, excluding raw logs):** **154** pattern hits (counts per `grep -r -c`), all in **derived JSON/report metadata** (`05_ANALYSIS`, `04_EVENTS_METADATA`, `07_REPORTS`), **not in raw logs**.
- **Hit breakdown (non-raw):**
  - `05_ANALYSIS/trial_01/parse_meta_trial01.json:6` `file /home/ubuntu/Desktop/RF Vision Files/CSI-SENSE-001/raw/trial_01/...`, `csv`, `npz`, `out_dir`, `command /home/ubuntu/tools/csi_analysis/parse_csi.py --file /home/ubuntu/Desktop/...` (5 hits)
  - `05_ANALYSIS/trial_01/features_trial01.json:6` `npz /home/ubuntu/Desktop/.../parsed_trial01.npz`, `command /home/ubuntu/tools/...` (3 hits)
  - `05_ANALYSIS/trial_01/baseline_model_trial01.json:6` `features/model_npz /home/ubuntu/Desktop/...`, `command /home/ubuntu/tools/...` (3 hits)
  - `05_ANALYSIS/trial_01/pca_spectrogram_trial01.json:6` similar (3 hits) + `05_ANALYSIS/.../temporal_plots_demo_manifest.json:7` `features/baseline/events` absolute + output PNG absolute + `command /home/ubuntu/tools/...` (multiple)
  - `05_ANALYSIS/smoke_test/parse_meta_trial00.json:6` `file /home/ubuntu/Desktop/.../smoke_test/...`, `csv /tmp/smoke_parse/...`, `command /home/ubuntu/tools/...` (5 hits)
  - `04_EVENTS_METADATA/metadata/firmware_versions.json:1` `clone git clone ... /tmp/esp-idf-v5.4`, `path_inspected /tmp/esp-idf-v5.4`, `file /tmp/csi_recv_router/...`, `command source /tmp/esp-idf-v5.4/...` (multiple)
  - `04_EVENTS_METADATA/metadata/study_metadata.json:53` `not /cow/tmp/tmpfs/overlay`, `hardware_identity.json:70` `live /cow 7.7G overlay + /tmp 7.7G tmpfs`
  - `07_REPORTS/*:1` historical `/tmp/csi_raw.log`, `/tmp/csi_recv_router`, `/tmp/esp-idf-v5.4`, `/home/ubuntu/Desktop/RF Vision Files` (volatile warning), `/cow` (overlay)
  - `03_RAW_DATA/CSI_SENSE-001/trial_01/capture_meta_trial01.json:39` `command /home/ubuntu/tools/csi_capture/capture_csi_sense.py ... --output-dir /home/ubuntu/Desktop/RF Vision Files/...` (provenance, in sidecar, not raw log)
  - `03_RAW_DATA/CSI_SENSE-001/trial_01/validate_trial01.json:4` `file /home/ubuntu/Desktop/.../raw/trial_01...`, `capture_stdout.log:2` `Output: /home/ubuntu/Desktop/...`
  - `08_CHECKSUMS_MANIFESTS/PATH_PROVENANCE.md:1` documents all above.

- **Raw logs themselves (`03_RAW_DATA/*.log`):** **0 hits** (`grep -E "/home/ubuntu|/tmp/|/cow/" CSИ_RAW_70s.log → 0`, same for smoke/trial logs) — raw experimental data is clean, no host paths embedded.
- **Sidecars (`03_RAW_DATA/.../capture_meta`, `validate`, `capture_stdout`) contain absolute paths as provenance** (expected — they record capture command); this is why `grep -r / 03_RAW_DATA → 7` total but raw logs 0 (see cleanup verification note: raw logs clean, sidecars are provenance metadata).

**Handling:** Per `RFVISION-ARCHIVE-CLEANUP-001 §11`, **do NOT modify raw logs**. For derived metadata, where safe, would rewrite to relative, but changing `parse_meta`/`features` would alter provenance SHA. Instead, **created `08_CHECKSUMS_MANIFESTS/PATH_PROVENANCE.md`** explaining `/home/ubuntu/...`, `/tmp/`, `/cow/` refer to original Ubuntu Live execution environment; `SHA256SUMS.txt` uses **relative paths** so verification is independent. No silent rewrite performed.

---

## 16. Final Checksum Verification

**Authoritative manifest:** `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` — **68 entries, SHA256 + `  relative/path`, sorted deterministically, excludes itself (`grep -c SHA256SUMS.txt → 0`), covers `00_PROJECT/PLAN` (1) + `01_HARDWARE` (1) + `02_FIRMWARE` (2) + `03_RAW_DATA` (11: 1 CSI_VERIFY + 4 smoke + 6 trial) + `04_EVENTS_METADATA` (9: 1 events + 8 metadata) + `05_ANALYSIS` (18: 4 smoke + 14 trial) + `06_TOOLS` (11) + `07_REPORTS` (8: includes FINAL-ARCHIVE-AUDIT-002) + `08_CHECKSUMS_MANIFESTS` other 6 (BACKUP_*, FINAL-FOLDER-AUDIT, FINAL-ARCHIVE-AUDIT-002, PATH_PROVENANCE) + `README.md` (1) = 68 lines.**

**Verification run (read-only):** `cd "/home/ubuntu/Desktop/RF Vision Files" && sha256sum -c "08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt"` → **all 68 OK** (`exit 0`). Protected raw entries:

```
4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a  03_RAW_DATA/CSI_SENSE-001/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log
51d47ce98e7c712c1826fe61e31cd71163921bfae262ed4153428f66b7caed24  03_RAW_DATA/CSI_VERIFY/CSI_RAW_70s_921600_20260906_205638.log
ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4  03_RAW_DATA/CSI_SENSE-001/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log
```

**Historical staging SHA not in manifest** (by design — manifest is authoritative 00–08 only); historical `CHECKSUMS/SHA256SUMS.txt` (77) and `CSI_SENSE_001/ANALYSIS/checksums.sha256` empty are now archived/obsolete and excluded.

**Additional file-list verification:** `find 00_* 01_* 02_* 03_* 04_* 05_* 06_* 07_* 08_* README.md -type f | wc -l → 69` (68 in manifest + 1 manifest file itself excluded). This matches authoritative count.

---

## 17. Reboot-Loss Assessment

**Host still volatile:** `df -hT` `tmpfs` + `findmnt / overlay` `/cow` overlay `7.7G` upperdir `/cow/upper` — same Live session as before; **Google Drive upload has NOT yet happened** (per `08_CHECKSUMS_MANIFESTS/BACKUP_BEFORE_REBOOT.md:1` `Google Drive is intended as pre-reboot preservation destination`, `study_metadata.json:1` `persistent_backup null`).

**Data at risk if reboot occurs before Drive upload:**

- **All 195 files (163M) on `RF Vision Files`** would be lost — but authoritative risk is **69 files (~71M) in 00–08 + README+manifest** including:
  - Raw immutable: `51d47ce` 3.5M, `ce04708` 0.5M, `4734dcf` 14M (smoke + pilot human-motion 310s A→F LOS crossing) + sidecars — irretrievable human experiment (pilot trials 2–10 NOT run).
  - Derived 05_ANALYSIS 52M (`features.npz 27.8M` largest) — would require rerun but raw needed.
  - Reports/manifests/metadata (07+08) — `5dd2cb` pilot INCONCLUSIVE, `d8b669a2` CSI-VERIFY PASS, provenance `296b6eab/8633d671`.
  - Tools 06_TOOLS (11 files) — reproducible from GitHub but local SHA pinned.
- **What survives reboot:** Only external `HP v210w /cdrom ro vfat 30G` (not written), Windows `nvme0n1 476.9G BitLocker locked untouched` (not written), and **Google Drive if uploaded** — none yet per `df -hT` no `gdrive`/`drive` mount and `BACKUP_MANIFEST.md` still `temporary Live-USB staging`.

**Exact remaining action to prevent loss:** `tar -czf "RF_Vision_Files_20260906_Final_Archive.tar.gz" "RF Vision Files"` from `/home/ubuntu/Desktop` then upload tar.gz (or folder) to Google Drive and verify `sha256sum -c 08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` on downloaded copy — see §18/20.

---

## 18. Google Drive Readiness

**Do NOT claim “persistent backup” — Google Drive upload has NOT happened yet.**

**Current status per §11–13 and §16:**

- **Authoritative archive correctness:** 00–08 structure complete per target (00_PROJECT, 01_HARDWARE, 02_FIRMWARE, 03_RAW_DATA, 04_EVENTS_METADATA, 05_ANALYSIS, 06_TOOLS, 07_REPORTS, 08_CHECKSUMS_MANIFESTS) with exactly one copy each of scientific raw, reports, tools, metadata; no raw inside analysis (`05_ANALYSIS -name "*.log" → 0`), no build/cache (`__pycache__/*.pyc → 0`), raw SHA MATCH, manifest 68 OK, README explains volatility + historical boot + Nano omission, PATH_PROVENANCE covers absolute paths.
- **Historical staging retained at root for audit trail** (`CSI_SENSE_001/`, `CSI_VERIFY_001/`, `CSI-SENSE-001/`, `CHECKSUMS/`) — not part of authoritative 00–08 but preserved; **Drive upload should include 00–08 + README.md + 99_ARCHIVE/**; optionally exclude root historical staging to keep Drive clean (recommended). If historical staging is uploaded too, Drive will be 157M cluttered but still verifiable.
- **Credentials suppressed in this audit terminal report** — provenance files retain private values for Drive private copy; public copy must redact `CONFIG_EXAMPLE_WIFI_PASSWORD` (see §14).
- **Reboot safety:** Not yet uploaded — must upload before reboot (see §17).

---

## 19. Confirmation Nano Recon Intentionally Omitted

**Per user decision RFVISION-ARCHIVE-CLEANUP-001: `NANO-RECON-001.md` intentionally NOT being recovered; do not search.**

- **Recorded statement:** **“NANO-RECON-001.md intentionally omitted from final archive by operator. Nano hardware was classified as auxiliary/non-CSI hardware. Absence of the standalone recon report does not affect the core CSI dataset.”**
- **Evidence:** `find -iname "*NANO*"` → 0 hits, `HARDWARE_RECON/` empty placeholder only, `01_HARDWARE/hardware_identity.json` remains authoritative for ESP32/router (f35a5223), no fake Nano recon created (per `Do NOT create a fake Nano recon`). Historical `NANO-RECON-001` (FT232R `0403:6001 A5069RR4` ATmega328P-class, no Wi-Fi radio, no CSI) was auxiliary only — core dataset is ESP32 CSI (51d47ce/ce04708/4734dcf). Omission is non-critical per operator.

---

## 20. Exact Remaining Action Before Drive Upload

**Single required upload step (no reorganization, no experiment):**

1. **Verify final checksum** (one command, read-only):
   ```
   cd "/home/ubuntu/Desktop/RF Vision Files" && sha256sum -c 08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt
   ```
   Expected: `68 OK` (all 51d47ce/ce04708/4734dcf etc. OK, `exit 0`).

2. **Create Google-Drive-ready tarball from Desktop parent (preserves relative paths, excludes volatile absolute paths):**
   ```
   cd "/home/ubuntu/Desktop" && tar -czf "RF_Vision_Files_20260906_Final_Archive.tar.gz" "RF Vision Files"
   sha256sum "RF_Vision_Files_20260906_Final_Archive.tar.gz" > "RF_Vision_Files_20260906_Final_Archive.tar.gz.sha256"
   ```

3. **Upload to Google Drive** (web or `rclone` if available, but **do not install software** per STOP condition unless already present — use browser upload): Upload **both** `RF_Vision_Files_20260906_Final_Archive.tar.gz` and `.sha256`, or upload folder `RF Vision Files` directly (include `00_PROJECT/` through `08_CHECKSUMS_MANIFESTS/`, `README.md`, `99_ARCHIVE/`, and `FINAL-ARCHIVE-AUDIT-002.md` itself). **Recommended Drive contents:** `README.md` at top of Drive folder, plus `00_PROJECT/` through `08_CHECKSUMS_MANIFESTS/` authoritative; include `99_ARCHIVE/` for provenance; historical root `CSI_SENSE_001/` etc. may be omitted on Drive to avoid clutter (they are already archived inside `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/`).

4. **Post-upload verify on Drive download (optional but recommended):** Download back to another machine or same Live if persistent mount available, then `tar -xzf` and `sha256sum -c 08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` again — must be 68 OK and raw `51d47ce`/`ce04708`/`4734dcf` MATCH.

5. **Do NOT reboot until Drive upload + SHA verification confirms** — see §17 `BACKUP_BEFORE_REBOOT.md` instructions (`tar -czf ... then upload tar.gz ( cd "/home/ubuntu/Desktop" && tar - ...)`). After verified Drive persistence, Live volatility no longer matters.

**Nothing else required:** No Nano recovery, no firmware flash, no CSI capture, no human trial, no router change, no credential printing, no reorganization beyond this archive (STOP per final condition).

---

## Final Classification

### **READY FOR GOOGLE DRIVE UPLOAD**

**Justification (verification-only):**
- Exactly one authoritative location for each scientific raw dataset (`03_RAW_DATA/CSI_VERIFY 51d47ce`, `03_RAW_DATA/CSI_SENSE-001/{smoke ce04708, trial_01 4734dcf}`) — all SHA MATCH, 444 immutable.
- Exactly one authoritative copy of each report (8 in `07_REPORTS/` includes FINAL-ARCHIVE-AUDIT-002, `5dd2cb` pilot single), each tool (11 in `06_TOOLS/`, MATCH `SOURCE_PROJECT` before archive), each metadata set (00–04), and exactly one authoritative checksum manifest (`08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` 68 entries, 0 self-inclusion, `sha256sum -c` 68 OK).
- No raw inside analysis (0 `.log` under `05_ANALYSIS`), no build/cache (`__pycache__/*.pyc` 0), no credentials printed in terminal (suppressed), absolute Live paths documented via `PATH_PROVENANCE.md` not silently rewritten, raw logs clean (0 absolute hits).
- Historical boot `5608f152` correctly recorded as **historical boot capture unavailable** (not recovered, not blocking), Nano recon intentionally omitted per operator (non-critical auxiliary), empty placeholder `checksums.sha256` archived as obsolete.
- Reboot-loss risk correctly documented (volatile `/cow`), and `README.md` explicitly states no claim of persistent backup yet, no claim of publication-grade localization (pilot INCONCLUSIVE, localization NOT demonstrated).

**Upload can proceed immediately via §20 steps 1–3; only post-upload SHA re-check is recommended before reboot.**

---

**STOP after producing FINAL-ARCHIVE-AUDIT-002.md. Do not upload, reboot, capture, experiment, flash, erase, or modify router/Windows/NVMe.**

**Audit report location (to be placed):** `/home/ubuntu/Desktop/RF Vision Files/FINAL-ARCHIVE-AUDIT-002.md` — this file, `~480` lines. Also mirrored to `/home/ubuntu/Desktop/FINAL-ARCHIVE-AUDIT-002.md` for Desktop visibility if requested.
