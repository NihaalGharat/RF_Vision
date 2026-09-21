> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` (SHA-256 `7525525388d9002c80210b94ac9db9b3b71bc074982b617e0fcd7ed71c2d92a4`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-SENSE-001 — PHASE B IMPLEMENTATION REPORT (Host-Side Tooling Only)

**Study:** CSI-SENSE-001 — Does Human Presence/Movement Produce a Measurable CSI Response?  
**Phase:** B — HOST-SIDE TOOLING ONLY (PLANNING v1.1 → IMPLEMENT PHASE B)  
**Date:** 2026-09-06 21:35 UTC  
**Host:** Lenovo IdeaPad Gaming 3 15IAH7 82S9 — Ubuntu 26.04.1 LTS — Kernel 7.0.0-30 — Live /cow overlay  
**Plan:** `~/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (753 lines, SHA `c72b2c4b`, supersedes v1.0)  
**Approval:** `CSI-SENSE-001 — APPROVED for Phase B` (separate Phase C approval not yet granted)  
**Result:** **PHASE B COMPLETE — host-side software validated, no hardware/RF/human data changes, STOP before Phase C.**

---

## 1. Implementation Summary

Phase B implemented **all** host-side tooling defined in `PLAN_v1.1 §14` while strictly observing HARD SAFETY / SCOPE BOUNDARY: no ESP32 flash/erase/firmware rebuild, no Xiaomi router change, no Windows/BIOS/partition/nvme0n1 change, no human experiment, no Phase C.

Tooling supports future controlled experiment (A→F 310s, 10 trials) while remaining fully usable without conducting it — verified via dry-runs, synthetic fixtures, and analysis of existing `CSI-VERIFY-001` raw capture.

- **Proven CSI format reused:** `CSI_DATA` CSV at 921600 baud, `len=128` (64 subcarriers I/Q), fields `seq,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,len,first_word,data"[I,Q,...]"` (app_main.c `ets_printf`), glued fragments handled via `re.finditer` (proven 14 glued in 7166 records).
- **Raw integrity:** raw preserved immutable, never modified; parsed/derived separate; SHA-256 checksums; malformed/truncated detection; `chmod a-w` after capture.
- **Backup gate §5.5:** distinguishes persistent vs `/cow`, `/tmp`, `tmpfs`, `overlay`, volatile — verifies actual destination via `df -hT`/`findmnt`/`lsblk` + write-test SHA round-trip + per-trial copy SHA verification + `backup_verified` flag; dry-run bypass allowed for Phase B testing, volatile correctly rejected for real backup.

All 17 planned files created; CLI help/error handling verified; parser validated against CSI-VERIFY-001 raw; no hardware actions executed.

---

## 2. Files Created/Modified

### 2.1 New Phase B Files (11 + 6 + 2 docs + 5 metadata = 18 files including analysis_config.json check)

All under `~/` (project root `/home/ubuntu`):

| Purpose | Exact File | Lines | SHA256 | Phase |
|---------|------------|-------|--------|-------|
| **Capture** | `tools/csi_capture/capture_csi_sense.py` | 264 | `8b6d2bd8` | B host-only |
| | `tools/csi_capture/event_logger.py` | 262 | `0048fd78` | B host-only |
| | `tools/csi_capture/validate_raw.py` | 227 | `0c490399` | B host-only |
| | `tools/csi_capture/backup_verify.py` | 373 | `b201c94b` | B host-only (§5.5) |
| **Analysis** | `tools/csi_analysis/parse_csi.py` | 304 | `e95d91a2` | B host-only |
| | `tools/csi_analysis/features.py` | 230 | `1bae77bc` | B host-only |
| | `tools/csi_analysis/baseline_model.py` | 288 | `a820523e` | B host-only |
| | `tools/csi_analysis/pca_spectrogram.py` | 321 | `65164d45` | B host-only |
| | `tools/csi_analysis/temporal_plots.py` | 335 | `14a1beaa` | B host-only |
| | `tools/csi_analysis/statistical_tests.py` | 376 | `a43b116e` | B host-only |
| | `tools/csi_analysis/analysis_config.json` | — | `39a68729` | B committed |
| **Metadata** | `data/CSI-SENSE-001/metadata/study_metadata.json` | — | `046f30a8` | B schema |
| | `data/CSI-SENSE-001/metadata/room_geometry.json` | — | `97ea595a` | B placeholder (filled C) |
| | `data/CSI-SENSE-001/metadata/hardware_identity.json` | — | `f35a5223` | B |
| | `data/CSI-SENSE-001/metadata/firmware_versions.json` | — | `0b286912` | B |
| | `data/CSI-SENSE-001/metadata/capture_config.json` | — | `edcfbf00` | B |
| **Docs** | `data/CSI-SENSE-001/PROTOCOL.md` | — | `d2ea217b` | B |
| | `data/CSI-SENSE-001/README.md` | — | `b204b10d` | B |
| **Data root** | `data/CSI-SENSE-001/checksums.sha256` | 0 entries | empty | B (will populate C) |
| | `data/CSI-SENSE-001/analysis/figures/*` | demo | — | B demo outputs |
| | `data/CSI-SENSE-001/analysis/stats/*` | demo | — | B demo outputs |

### 2.2 Pre-existing Files (not modified, verified unchanged)

- `~/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (75K, `c72b2c4b`, 753 lines) — read-only reference
- `~/Desktop/CSI-SENSE-001_PLAN.md` (v1.0 predecessor, retained)
- `~/Desktop/CSI-VERIFY-001_FINAL_REPORT.md` (265 lines, `d8b669a2`, PASS 7152 vectors)
- `~/Desktop/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` (224 lines)
- `~/Desktop/CSI_RAW_70s_921600_20260906_205638.log` (3,566,098 bytes, SHA `51d47ce9`, 7154 occurrences) — **not modified** (remains `rw-rw-r--`, SHA verified post-tests)
- No modifications to `/dev/ttyUSB0` flash, router, `/cow`, partitions, `nvme0n1` (BitLocker locked), Windows/BIOS.

### 2.3 Directory Structure Created

```
data/CSI-SENSE-001/
  README.md
  PROTOCOL.md
  checksums.sha256 (0 entries — raw empty, awaiting Phase C)
  metadata/{study_metadata.json, room_geometry.json, hardware_identity.json, firmware_versions.json, capture_config.json}
  raw/ (empty — no human data)
  analysis/{figures/*, stats/*}  # demo outputs from validation
tools/csi_capture/{capture_csi_sense.py, event_logger.py, validate_raw.py, backup_verify.py}
tools/csi_analysis/{parse_csi.py, features.py, baseline_model.py, pca_spectrogram.py, temporal_plots.py, statistical_tests.py, analysis_config.json}
```

---

## 3. Architecture

```
Serial 921600 ──> capture_csi_sense.py (wb, no parse) ──> *_raw.log (immutable) ──> .sha256 + capture_meta.json (chmod a-w)
                                      ──> event_logger.py (sidecar wall_clock_ns + chip_seq) ──> events_trialXX.jsonl
                                      ──> validate_raw.py (counts, seq, len/channel/BSSID stability, inter-arrival)
                                      ──> backup_verify.py (inspect volatile vs persistent, write-test, copy+SHA, checksums)

*_raw.log ──> parse_csi.py (re.finditer, handles glued, malformed detection) ──> parsed.csv + parsed.npz + parse_meta.json
      ──> features.py (amp=sqrt(I²+Q²), phase=atan2 unwrapped detrended, mean/std/null mask) ──> features.npz
      ──> baseline_model.py (μ_k, σ_k, Σ regularized ε=1e-6, deviation Euclidean/Mahalanobis/z, window variance) ──> baseline_model.npz
      ──> pca_spectrogram.py (PCA fitted on baseline only, STFT 2s 90% overlap) ──> pca_spectrogram.npz
      ──> temporal_plots.py (amp_deviation/RSSI/heatmap/variance + events + walk_duration annotation)
      ──> statistical_tests.py (Q1..Q6 distribution-dependent, Shapiro→Mann-Whitney, FDR BH, effect sizes d/r reference NOT proof, speed covariate)
      ──> analysis_config.json (seeds, windows, versions, walking reference, effect-size note)
```

- **Language:** Python 3.14.4, dependencies `pyserial 3.5`, `numpy 2.5.3`, `scipy 1.18.1`, `matplotlib 3.11.1` (installed via `pip --break-system-packages`).
- **Reproducibility recorded:** software versions, parser regex, analysis_config, random seed 42, input/output SHA-256, timestamp UTC, command line — per output JSON.
- **Walking speed v1.1:** `0.8–1.2 m/s` kept only as `reference_range_mps` target in metadata/analysis_config; actual `walk_duration_s`/`estimated_speed_mps` recorded per `events` + `env_trial.json` as covariate (Spearman correlation in stats), not pass/fail.

---

## 4. Tests Executed (Host-Side Only, Safe)

| Test | Command | Result |
|------|---------|--------|
| CLI help | `capture_csi_sense.py --help`, `event_logger.py --help`, `validate_raw.py --help`, `backup_verify.py --help`, `parse_csi.py --help` | PASS — all show usage, epilog “HOST-SIDE ONLY” |
| CLI error handling | `capture_csi_sense.py` (no args) → error required `--trial`; `--trial abc` → error numeric; `parse_csi.py` (no args) → error | PASS — proper exit codes 2 |
| Parser vs CSI-VERIFY-001 raw (glued handling) | `parse_csi.py --file ~/Desktop/CSI_RAW_70s... --out-dir /tmp/phaseB_test_parse` | PASS — 7166 occurrences, 7152 valid, 14 malformed (0.195%), len 128 100%, channel 1 100%, seq 5355→12506 missing 0, continuity 7151/7151 — matches FINAL_REPORT 7152 valid. Raw SHA `51d47ce9` unchanged. Outputs: `parsed.csv` (3.2M, `fc39b68c`), `parsed.npz` (728K, `dae43a91`) |
| Validate health | `validate_raw.py --file ~/Desktop/...` | PASS — VALID: `valid_trial true`, `malformed 0.195% ≤0.5%`, `missing 0 ≤1%`, `no gap >500ms`, rate 140.9 Hz chip, RSSI -63..-52 mean -53.9 |
| Features | `features.py --npz /tmp/.../parsed.npz` | PASS — 7152 packets 64 subcarriers, `amp_mean_global 19.76`, `zeros_per_packet_mean 9.02`, `null_subcarriers 9`, detrended slope mean 0.047 |
| Baseline | `baseline_model.py --features ...` | PASS — `mu_mean 19.77`, `sigma_mean 2.09`, `intra_var 3 windows dist mean 2.19`, `amp_deviation median 13.11 p95 27.66` |
| PCA | `pca_spectrogram.py --features ...` | PASS — PC1 58.3% explained, top subcarriers [4,3,5,2,6,7,53,52,54,51], STFT 101 freq ×349 time |
| Temporal plots | `temporal_plots.py --features ... --baseline ...` | PASS — 4 PNGs generated (timeseries, rssi, heatmap, variance) each with SHA recorded |
| Stats demo | `statistical_tests.py --demo` | PASS — synthetic A vs C p=0.0 r=0.66 d=-1.39, C vs D p=0.0 r=0.71 d=-1.59, speed Spearman -0.21 (demo) |
| Capture dry-run | `capture_csi_sense.py --trial 99 --duration 2 --dry-run --no-chmod --output-dir /tmp/phaseB_capture_test` | PASS — creates `*_raw.log` 291B SHA `d764de53`, `capture_meta_trial99.json` with wall/monotonic timestamps |
| Event logger non-interactive + validate | `event_logger.py --trial 99 --event walk_start --seq 101` ×5 events, then `--validate` | PASS — 5 events, walk pair true, `walk_duration 0.14s`, monotonic wall clocks |
| Parse dry-run raw | `validate_raw.py --file /tmp/.../dry_raw.log` + `parse_csi.py --file ...` | PASS — 3 valid, seq 1→3, VALID true |
| Glued/malformed fixture | Synthetic with glued without newline + truncated + normal mix: `validate_raw --file /tmp/glued_test.log` (4 valid, 1 missing 25%, malformed 20%), `parse_csi --file ...` (4 valid) | PASS — correctly detects malformed rate and glued handling via finditer (see §7) |
| Metadata/schema validation | Python `json.loads` checks `schema_version 1.0` in 5 metadata + `analysis_config` walking covariate true, `reference_is_not_proof true` | PASS — all 5 metadata have 1.0 |
| Checksums round-trip | Mock `/tmp/persistent_mock` 2 files → `backup_verify.py --checksums` 2 entries, then correct `data/CSI-SENSE-001/raw` 3 files → `checksums.sha256` + `--verify-checksums` 3/3 ok 0 mismatches | PASS |
| Backup verifier dry-run | `backup_verify.py --trial 01 --dest /tmp --dry-run` | PASS — would_copy 3, WARNING volatile but allowed for dry-run per testing bypass |
| Backup volatile detection | `backup_verify.py --inspect /tmp` → `is_volatile true` reasons `[tmpfs]`, `--inspect /home/ubuntu` → `[overlay,cow]` | PASS — correctly flags Live volatile |
| Write-test volatile rejection | `backup_verify.py --write-test /tmp --size-mb 1` → FAIL `dest appears volatile` exit 5 | PASS — gate correctly refuses volatile for real backup (§5.5) |
| Dry-run on volatile allowed | After patch, `--trial 01 --dest /tmp --dry-run` exit 0 vs `--inspect /tmp` exit 5 | PASS — testing bypass works while gate remains |

**All tests host-side, no serial opened except dry-run mock; no RF collected.**

---

## 5. Test Results — Summary

- **Parser:** Handles glued `...,-97,0,1CSI_DATA,5354...` fragments (0 newline) via `re.finditer` — 14 truncated headers correctly classified as malformed (e.g., `",-97,0,1CSI_DATA,5354..."` missing timestamp/ant/sig_len), 7152 valid correctly extracted. Data integrity: 64 subcarriers, I/Q ints, `amp` via `hypot`, phase detrended.
- **Validate:** Implements §3.7 criteria: missing seq, malformed, `len==128`, `channel==1`, `BSSID`, gap >500ms — trial VALID only if all thresholds met; walking speed not a gate.
- **Features:** Correct formulas documented in output `phase_note`.
- **Backup:** Inspect logic uses `df -hT` (tmpfs on `/tmp`, overlay on `/`, squashfs on `/rofs`), `findmnt -T`, `lsblk`, `/proc/mounts` — Live system has no persistent mount (all volatile), so gate correctly reports `is_volatile true` and `free_sufficient_5GB false` for `/` and `/tmp`; Phase C must provide external USB persistent (verified later via `--write-test 100`).
- **Checksums:** Generation and `sha256sum -c` style verification work; `checksums.sha256` currently 0 entries (raw empty, awaiting Phase C) — verified ok.
- **CLI:** All tools show help and exit 2 on missing required, exit 0 on `--help`.

---

## 6. Known Limitations (Phase B)

- **Live USB volatile:** `/` is `overlay` on `/cow` (7.7G) and `/tmp` is `tmpfs` (7.7G); **no persistent filesystem currently available** — demonstrated by backup verifier consistently returning `is_volatile true`. This is expected per §5.5 context; Phase C requires external persistent USB verified before any human data.
- **Statistical trial 01 heuristic:** When real data is present, `statistical_tests.py --trial 01` used heuristic 50/50 split for demo because no event boundaries yet (raw empty). Real segmentation will use `events_trialXX.jsonl` (wall_clock_ns + chip_seq) after Phase C; current demo outputs `q1 error empty group` correctly signals missing segmentation — not a bug.
- **Single trial baseline fit:** Current validation fitted PCA on single trial's 7152 packets; multi-trial ICC repeatability (Q3) requires N≥8 trials — will be computed in Phase C.
- **No live capture tested:** `capture_csi_sense.py` real path (`serial.Serial`) not exercised against `/dev/ttyUSB0` (requires hardware); dry-run path exercised. Real capture will be validated in Phase C pre-trial with 10s test.
- **Walking-speed file not yet created:** `env_trialXX.json` template defined in PROTOCOL §6, but no real trial has filled `walk_duration_s`/`estimated_speed_mps` yet — will be created per trial.
- **Room geometry placeholder:** `room_geometry.json` has `null` coordinates until tape measurement in Phase C.

---

## 7. Unexecuted Hardware-Dependent Tests (NOT EXECUTED — REQUIRES HARDWARE/PHASE C)

Per scope, marked **NOT EXECUTED**:

- Live CSI capture session `capture_csi_sense.py --trial 01 --duration 310` on `/dev/ttyUSB0` real ESP32 — requires hardware + persistent backup.
- RF data collection and human presence trials (A→F) with subject S01 walking — requires Phase C approval, geometry, environment, backup.
- ESP32 flash/erase verification — explicitly forbidden in Phase B; not executed.
- Router configuration change — not executed.
- Real persistent USB write-test 100MB round-trip on external device — cannot execute because no persistent device currently attached; would be `backup_verify.py --write-test /media/ubuntu/External --size-mb 100` in Phase C.
- Per-trial backup copy to persistent `backup_verify.py --trial 01 --dest <persistent>` (non-dry-run) — requires persistent dest.
- Analysis on real human vs empty data (Q1-Q6 with events) — requires collected data.

---

## 8. Raw-Data Integrity Verification

- **CSI-VERIFY-001 raw preserved:** `~/Desktop/CSI_RAW_70s_921600_20260906_205638.log` SHA `51d47ce9` verified before and after all Phase B tests — unchanged (`rw-rw-r--`, not `chmod a-w` per “do not alter existing CSI-VERIFY-001 raw captures” rule).
- **Derived separates:** Parse outputs written to `/tmp/phaseB_test_parse` and `data/CSI-SENSE-001/raw/trial_01` (test fixture) then cleaned; final `data/CSI-SENSE-001/raw` empty with `checksums.sha256` 0 entries — no raw overwritten.
- **Parser never modifies raw:** `parse_csi.py` opens with `read_bytes` + `decode(errors=ignore)` read-only; writes to separate `parsed*.csv/npz`.
- **Capture tool guarantees:** New raw files written once then `chmod a-w` (unless `--no-chmod` for testing); companion `.sha256` generated.

---

## 9. Backup-Verifier Verification

- **Volatile detection:** Tested `--inspect /tmp` → `tmpfs` volatile true (4 reasons), `--inspect /home/ubuntu` → `overlay`/`cow`/`squashfs` volatile true, `--inspect /tmp --write-test` → `ok false` with error. Logic covers 6 substrings + 4 fstypes + `/proc/mounts` snippet.
- **Write-test:** Code generates `os.urandom` 1–100MB, writes, `fsync`, `sync`, reads back SHA, compares, unlinks — returns `sha_match` bool. On volatile correctly returns `ok false` before write, demonstrating gate.
- **Dry-run bypass for testing:** `--trial 01 --dest /tmp --dry-run` now exits 0 with `would_copy` count, warning but not failing — allows Phase B testing without persistent; real backup still fails gate (volatile refusal) as intended.
- **Checksums:** `generate_checksums` walks `root.rglob("*")`, SHA per file, writes `checksums.sha256` with `sha  rel`; `verify_checksums` resolves relative to `DATA_ROOT/raw` and checks `actual==expected`.
- **Per-trial copy:** `copy_trial_to_dest` uses `shutil.copy2` (not move), verifies `src_sha==dst_sha` per file, writes log with `ok` and updates `env_trial.json:backup_verified` if present (not yet in Phase B).

Future Phase C backup workflow supported: raw, metadata, `events_trialXX.jsonl`, `env_trialXX.json` (with walking speed), analysis `figures/stats`, reports, `checksums.sha256` — all with SHA verification.

---

## 10. Confirmation of Scope Compliance

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No ESP32 flash/erase | ✅ PASS | No `idf.py flash`, `write_flash`, `erase_flash` in tools; grep only finds comments “Does NOT flash”; `/dev/ttyUSB0` never opened except dry-run mock |
| No ESP32 firmware modify/rebuild/replace | ✅ PASS | No `sdkconfig`, `build`, `firmware_change` executed; `firmware_versions.json` notes `proven_reused true` |
| No Xiaomi router modify | ✅ PASS | No `nmcli`, `iw`, router API calls in tools; router BSSID only logged |
| No Windows/BIOS/partition/SSD modify | ✅ PASS | No `nvme0n1` writes; `ls -la /` shows Live `/cow` untouched; `grep -R partition` only in docs |
| No human CSI data collected | ✅ PASS | `data/CSI-SENSE-001/raw` empty (0 entries); no `*_raw.log` created except dry-run mocks in `/tmp` |
| No Phase C started | ✅ PASS | No `trial_XX` human data; `PROTOCOL.md` gates checked before Phase C |
| No experimental results claimed | ✅ PASS | All analysis outputs are demo/synthetic or validation on empty baseline; `statistical_tests_demo` marked `demo true`; no human detection claimed |
| No final ML model trained | ✅ PASS | No `sklearn` classifier training executed; stats only |
| No 3D RF Vision UI | ✅ PASS | No UI code; only host-side capture/analysis CLI |
| Host-side only | ✅ PASS | All 11 tools are pure Python host-side, no privileged operations |
| Effect-size reference not proof | ✅ PASS | `analysis_config.json` `reference_is_not_proof: true`, `d>=0.5 r>=0.3` noted in stats outputs |
| Walking speed covariate not gate | ✅ PASS | All env templates and stats note `speed_is_covariate_not_gate true`, validate never rejects on speed |

**Review of created files for accidental hardware actions:** `grep -R "flash|erase|idf.py|write_flash"` in `tools/` returns only documentation comments; no subprocess calls to flashing.

---

## 11. Exactly Next Approval Required

**STOP after Phase B.** Do not proceed to Phase C.

To authorize human data collection, you must reply:

```
CSI-SENSE-001 — APPROVED for Phase C
```

Only that **separate explicit approval after you have reviewed**:

1. This Phase B report + all tooling (`tools/csi_capture/*`, `tools/csi_analysis/*`, `analysis_config.json`),
2. Room geometry recorded (`data/CSI-SENSE-001/metadata/room_geometry.json` + photos),
3. Experimental environment ready (§10 checklist),
4. **Persistent backup verified (§5.5 gate):** `persistent_destination_path`, `filesystem`, `size_avail_gb >=5`, `write_test_sha_match: true` via `backup_verify.py --inspect` + `--write-test 100` on actual external device — with `study_metadata.json:persistent_backup` updated,

may Phase C begin:

```bash
# Phase C (requires human, ~6 min/trial) — NOT authorized until APPROVED for Phase C
python3 tools/csi_capture/capture_csi_sense.py --trial 01 --duration 310 --baud 921600 --port /dev/ttyUSB0
# in parallel: python3 tools/csi_capture/event_logger.py --trial 01
# per trial: python3 tools/csi_capture/validate_raw.py --trial 01 && python3 tools/csi_capture/backup_verify.py --trial 01 --dest <persistent>
```

Without that second approval, Phase C does not begin. This Phase B approval alone authorizes **only** host-side tooling (already completed).

---

## 12. Appendix — Test Commands for Reproduction

```bash
# 1. Parser vs CSI-VERIFY-001 raw (proves glued handling, preserves raw)
python3 tools/csi_analysis/parse_csi.py --file ~/Desktop/CSI_RAW_70s_921600_20260906_205638.log --out-dir /tmp/phaseB_test_parse --print-summary
python3 tools/csi_capture/validate_raw.py --file ~/Desktop/CSI_RAW_70s_921600_20260906_205638.log
sha256sum ~/Desktop/CSI_RAW_70s_921600_20260906_205638.log  # must remain 51d47ce...

# 2. Feature pipeline on parsed
python3 tools/csi_analysis/features.py --npz /tmp/phaseB_test_parse/parsed_*.npz --out-dir /tmp/phaseB_test_parse

# 3. Backup verifier Dry-run & volatile gate
python3 tools/csi_capture/backup_verify.py --inspect /tmp --write-test /tmp --size-mb 1  # expect FAIL volatile
python3 tools/csi_capture/backup_verify.py --trial 01 --dest /tmp --dry-run  # expect PASS dry-run bypass
python3 tools/csi_capture/backup_verify.py --checksums /home/ubuntu/data/CSI-SENSE-001/raw
python3 tools/csi_capture/backup_verify.py --verify-checksums /home/ubuntu/data/CSI-SENSE-001/checksums.sha256

# 4. CLI validation
python3 tools/csi_capture/capture_csi_sense.py --help
python3 tools/csi_analysis/statistical_tests.py --demo  # demo safe without hardware
```

---

*Phase B complete — all host-side software implemented, tested via synthetic/minimal fixtures and CSI-VERIFY-001 raw, with glu/garbage handling, checksums, backup volatile detection, and reproducibility metadata. Awaiting Gate 2 for Phase C.*

