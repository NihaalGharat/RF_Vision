> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/CSI-SENSE-001_PHASE_C_READINESS_REPORT.md` (SHA-256 `7d414cee6606ad8fa9be1824ed9d4ee730b92ba30a130b0a4ff0ff3e33c2ee75`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-SENSE-001 — PHASE C READINESS REPORT (Pre-Phase-C Audit, No Human Data)

**Study:** CSI-SENSE-001 — Does Human Presence/Movement Produce a Measurable CSI Response?  
**Phase:** C Readiness Audit — NO APPROVAL FOR PHASE C YET (host-side tooling + protocol + environment gate)  
**Date:** 2026-09-06 22:15 UTC (audit executed read-only)  
**Plan:** `~/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (753 lines `c72b2c4b`)  
**Phase B Report:** `~/Desktop/CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` (266 lines `75255253`)  
**Readiness Classification:** **READY WITH REQUIRED ACTIONS** — no software blocker, but Phase-C prerequisites must be completed before any human trial.  
**Scope compliance:** No ESP32 flash/erase, no router/BIOS/partition/nvme0n1 change, no 310s trial, no A→F, no human CSI collected.

---

## 0. Executive Summary

Audit inspected all Phase B tooling (`tools/csi_capture/4`, `tools/csi_analysis/7` incl. config), 5 metadata schemas, `PROTOCOL.md`/`README.md`/`analysis_config.json` against PLAN v1.1 §0–§15. Implementation matches plan; backup gate correctly rejects volatile Live-USB destinations; capture path is binary-safe without parsing; amplitude/phase/baseline/PCA/statistics adhere to §§7–9 with v1.1 corrections (effect-size reference NOT proof, walking-speed covariate NOT gate). **No concrete technical/scientific/safety defect blocks Phase C** — but Phase C must not start until geometry recorded, persistent backup verified, and safe pre-trial smoke test passed.

**Still required before Phase C:** (1) persistent backup verified on real non-volatile device (§5.5), (2) room geometry measured + photos (§4), (3) environment checklist controlled (§10), (4) safe 10-s serial smoke test. See §9 for exact next commands (not executed).

---

## 1. AUDIT ALL PHASE B TOOLING — PASS (no blocking defect)

**Files inspected (11 tooling + 8 data-plane):**
- Capture: `tools/csi_capture/capture_csi_sense.py:1` (264L `8b6d2bd8`), `event_logger.py:1` (262L `0048fd78`), `validate_raw.py:1` (227L `0c490399`), `backup_verify.py:1` (373L `b201c94b`)
- Analysis: `tools/csi_analysis/parse_csi.py:1` (304L `e95d91a2`), `features.py:1` (230L `1bae77bc`), `baseline_model.py:1` (288L `a820523e`), `pca_spectrogram.py:1` (321L `65164d45`), `temporal_plots.py:1` (335L `14a1beaa`), `statistical_tests.py:1` (376L `a43b116e`), `analysis_config.json:1` (`39a68729`)
- Data: `data/CSI-SENSE-001/PROTOCOL.md:1` (`d2ea217b`), `README.md:1` (`b204b10d`), `metadata/study_metadata.json:1` (`046f30a8`), `metadata/room_geometry.json:1` (`97ea595a`), `metadata/hardware_identity.json:1` (`f35a5223`), `metadata/firmware_versions.json:1` (`0b286912`), `metadata/capture_config.json:1` (`edcfbf00`), `data/CSI-SENSE-001/checksums.sha256:1` (0 entries), `analysis/figures/*`/`analysis/stats/*` (demo outputs)

**Match to PLAN v1.1 §14:** Plan table lists 4 capture (`capture_csi_sense.py`, `event_logger.py`, `validate_raw.py`, `backup_verify.py:§5.5`) + 6 analysis py (`parse_csi`, `features`, `baseline_model`, `pca_spectrogram`, `temporal_plots`, `statistical_tests`) + `analysis_config.json` + 5 metadata + `PROTOCOL.md`+`README.md` + `checksums.sha256` — matches. See count resolution below.

**Evidence:**
```
tools/csi_capture: 4 files (capture_csi_sense.py, event_logger.py, validate_raw.py, backup_verify.py)
tools/csi_analysis: 7 files (6 py + analysis_config.json)
metadata: 5 files (study_metadata, room_geometry, hardware_identity, firmware_versions, capture_config)
docs: PROTOCOL.md, README.md, checksums.sha256
total host-side = 4+7+5+2(+1 checksums file) = 18 on disk incl. checksums
```
All contain `STUDY_ID="CSI-SENSE-001"`, `schema_version "1.0"`, `epilog "HOST-SIDE ONLY"`, no `idf.py flash/write_flash/erase_flash` subprocess (grep returns only doc comments).

**Verdict:** PASS — tooling present, pinned versions match §0, no hardware-modifying code.

### 1.1 File-Count Discrepancy 17-vs-18 — RESOLVED (cosmetic)

- Phase B report §2.1 text `All 17 planned files created` vs table `18 files including analysis_config.json` — inconsistency in counting, not implementation.
- PLAN v1.1 §14.1 table prose `~17 files (5 metadata + 4 capture + 6 analysis + PROTOCOL + README + final report)` counts **6 analysis py** separately and implies `analysis_config.json` within analysis tooling (see `README:192` `All 17 files host-side`). On disk we have 6 py +1 json =7 analysis entries → 4+6+5+2=17 logic docs+tooling, or 4+7+5+2=18 counting `analysis_config.json` distinctly. `checksums.sha256` is data-plane generated, not counted in 17. `FINAL_REPORT.md` (Phase E) not yet created — correctly absent.
- **Defect class:** Documentation counting, not software blocker.

**Action:** Keep as-is; optionally clarify report wording to `17 tooling+metadata+docs + 1 checksums file (+ final report Phase E)`. No code change required.

### 1.2 Minor Deviation Flagged (non-blocking)

- `analysis_config.json` resides at `tools/csi_analysis/analysis_config.json` (`39a68729`) while PLAN §6.1 suggests `data/CSI-SENSE-001/analysis/analysis_config.json` committed before D. Both locations are acceptable per PLAN §11 (reproducibility record); recommend Phase C copies committed `analysis_config.json` to `data/CSI-SENSE-001/analysis/` before first trial and records its SHA in `study_metadata.json` to remove ambiguity. Not a gate blocker.

---

## 2. CAPTURE PATH AUDIT — PASS

**File:** `tools/csi_capture/capture_csi_sense.py:1` (264 lines)

**Checks:**

| Criterion | Evidence | Result |
|-----------|----------|--------|
| Real serial path present & correct | `serial.Serial(args.port, args.baud, timeout=1)` `capture_csi_sense.py:151` + `read(4096)` loop `write+flush` `capture_csi_sense.py:163-168`, `reset_input_buffer()` `:157`, `drain remaining` `:172-175` — identical to proven `/tmp/capture_csi.py` | PASS |
| Binary-safe / raw unchanged | Opens `open(raw_path,"wb")` `:134,:163`, `bytes_written` tracked, never decodes; byte content includes `\r\n` exactly; SHA companion `file_sha=sha256_file(raw_path)` `:191` + `.sha256` file `:194`, `chmod 0o444` `:199` unless `--no-chmod`; `raw_path.exists()` refusal `:114` prevents overwrite | PASS |
| No parsing during capture | No `re`, `CSV`, `CSI_PATTERN`, `finditer` in capture file; only in analysis tools — verified by grep | PASS |
| Serial errors / timeout / interruption / partial | `if not Path(port).exists() -> exit 4` `:146`, `try ser=Serial except -> exit 4` `:153`, `except KeyboardInterrupt print Interrupted -> finally ser.close()` `:176-182`, timeout 1 ensures `ser.read` doesn't hang, partial capture still writes SHA/meta and chmod; `validate_baud` warns if !=921600 `:75` | PASS |
| Duration & naming per §5.2 | Default `DEFAULT_DURATION 310` `:37` (90+12+60+35+12+90=299), per-trial `CSI-SENSE-001_<ISO>_trialXX_raw.log` `:107-109` + `capture_meta_trialXX.json` with wall/monotonic timestamps, `request_duration_s`, `proven_len 128` | PASS |
| Dry-run does not touch serial | `--dry-run` branch generates synthetic 3-record raw `:125-138` without importing serial — safe for Phase B | PASS |

**Minor note (non-blocking):** Dry-run mock uses `data "[1,2,3,4]"` (4 ints) while header `len=128` — mismatch but isolated to dry-run path for testing; real capture writes whatever ESP emits (proven 128). No effect on Phase C real path.

**Verdict:** PASS — safe for Phase C real capture after smoke test.

---

## 3. EVENT LOGGER AUDIT — PASS

**File:** `tools/csi_capture/event_logger.py:1` (262 lines)

| Criterion | Evidence | Result |
|-----------|----------|--------|
| Never touches serial | No `import serial`, no `/dev/ttyUSB0` — header `Sidecar event logger — NEVER touches serial` `:4`, description `:171` `does NOT touch /dev/ttyUSB0` | PASS |
| Sidecar operation | Writes to `data/CSI-SENSE-001/raw/trial_XX/events_trialXX.jsonl:78-82` independently of capture process; parallel terminals per `PROTOCOL.md:70-74` | PASS |
| Timestamps + seq sync | Per-event `wall_clock_ns=time.time_ns()` + `chip_seq`/`chip_timestamp_us` optional `:84-90`, `wall_clock_UTC` iso `:88`, `condition`/`note` optional; non-interactive `--seq`/`--chip-ts` `:174-177` maps to nearest `seq` within 100ms per plan §3.6 | PASS |
| A→F alignment | `ALLOWED_EVENTS` `:44-61` includes all §2 boundaries `trial_start…trial_end`, `door_open/close`, `threshold_cross_in/out`, `arrival_P1/P2/P3`, `walk_start/walk_end` (mandatory), `LOS_cross`, `waypoint*`, `depart`, `recovery_*`, `condition_*_start/end`, `note`; `validate` checks monotonic wall_clock, `walk_start/walk_end` pair and computes `walk_duration_s` `:152-168` for §5.2 walking metadata | PASS |

**Verdict:** PASS — suitable for A→F alignment; mandatory `walk_start/walk_end` validated.

---

## 4. RAW VALIDATION / PARSER AUDIT — PASS

**Files:** `validate_raw.py:36-48` + `parse_csi.py:40-71`

**Regex identity:** Both define identical `CSI_PATTERN`:
```
r'CSI_DATA,(\d+),([0-9a-f:]+),(-?\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),"\[([^\]]*)\]"'
```
24 groups per §5.2 header, `proven_len 128`. Both use `re.finditer` on `decode(errors="ignore")` text (`validate_raw.py:48`, `parse_csi.py:71`) — correctly handles glued `",-97,0,1CSI_DATA"` without newline (proven 14 in 7154).

**Tests on actual CSI-VERIFY-001 format:** `~/Desktop/CSI_RAW_70s_921600_20260906_205638.log` (3,566,098B `51d47ce9`) → `parse_csi` 7152 valid / 7166 occ / 14 malformed `0.195%` `len 128 100%` `channel 1 100%` `seq 5355→12506 missing0` matches `FINAL_REPORT` — proven via Phase B (§4). Synthetic glued fixture `4 valid / 1 malformed 20%` correctly counted. Raw file SHA unchanged after parse (`read_bytes` only).

**Raw immutability:** `parse_csi.py:67` `read_bytes` + `errors="ignore"` read-only; writes `parsed_*.csv`/`parsed_*.npz`/`parse_meta_*.json` to separate `out_dir` (`:83-85`), never overwrites raw. `validate_raw.py` never writes raw.

**Validity criteria per §3.7:** Implemented `missing_seq ≤1%`, `malformed ≤0.5%`, `len==128 ≥99%`, `channel==1 ≥99%`, `BSSID==8C:53:C3:5B:E1:59 ≥99%`, `gap >500ms ==0`, `seq_continuous`, `rssi`/`noise_floor`/`sig_len` stability, `valid_trial` flag + `invalid_reasons` (`validate_raw.py:111-139`, `:140-178`). Walking-speed presence checked but explicitly `note ... not gate` `:173`.

**Verdict:** PASS — no modification, correct handling of all edge cases, proven format supported.

---

## 5. BACKUP SAFETY AUDIT — PASS (gate correctly enforced; dry-run bypass isolated)

**File:** `tools/csi_capture/backup_verify.py:1` (373 lines) — detailed line review.

**Volatile rejection:**
- Must reject `/cow`, `/tmp`, `tmpfs`, `overlay`, `/rofs`, `squashfs`, `iso9660` — defines `VOLATILE_SUBSTRINGS` (`:49` includes `/cow`, `/tmp`, `tmpfs`, `overlay`, `/rofs`, `squashfs`, `cow`, `tmpfs` — duplicates harmless, conservative) and `VOLATILE_MOUNT_TYPES` `tmpfs/overlay/squashfs/iso9660` `:50`.
- `inspect_destination` collects `df -hT` (`:61`), `findmnt -T` (`:65`), `lsblk` (`:68`), `/proc/mounts` snippet (`:91`), then lowers `combined=df+findmnt` and checks every substring/fstype (`:74-88`) + `dest` path itself (`:78`). Returns `is_volatile` + `volatile_reasons` + `is_persistent_guess` (`:95-97`) + `free_sufficient_5GB` (`:103`).
- **Live verification:** `backup_verify.py --inspect /tmp` → `is_volatile true ["contains '/tmp'","contains 'tmpfs'","fstype 'tmpfs'"]`, `df_hT tmpfs 7.7G /tmp`, `findmnt tmpfs`; `--inspect /home/ubuntu` → `contains '/cow','overlay','squashfs'` `fstype overlay` — both correctly flagged (see logs §5 §8).
- `write_test` first calls `inspect` then `if is_volatile -> return ok false error volatile` (`:120`) — **no write performed on volatile**. Verified ` --write-test /tmp --size-mb 1` → `ok false` without creating file.

**Inspect correctness:** Uses actual destination's mount (`df -hT dest`, `findmnt -T dest`, fallback to `/` if not exists) plus full `lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT` — identifies underlying filesystem, not assumed. Returns `df_hT`/`findmnt_T`/`lsblk` verbatim for audit.

**Write-test SHA round-trip:** Generates `os.urandom(size_bytes)` (`:125`), `sha_before=sha256(data)` (`:126`), `write_bytes` + `fsync` + `sync` (`:128-132`), `sha_after=sha256_file(test_file)` (`:133`), `ok=sha_before==sha_after` (`:135`), `unlink` (`:137`), returns `size_mb`, `sha_before/after`, `sha_match`, `inspect`, `timestamp_UTC` (`:138-149`). Tested Phase B with 1 MB on mock persistent; on Live volatile correctly refuses before write.

**Phase C cannot accidentally use dry-run bypass:**
- Per-trial backup: `if insp.is_volatile and not args.dry_run -> ERROR refusing trial backup exit 5` (`:332-335`); `elif is_volatile and dry_run -> WARNING dry-run allowed (§5.5 bypass for testing)` (`:336-337`). So **real** ` --trial 01 --dest <volatile>` without `--dry-run` **always exits 5** and refuses copy. Verified ` --trial 01 --dest /tmp` (non-dry non-existent trial) → `ERROR dest /tmp ... volatile — refusing trial backup` code 5; synthetic `/tmp/fake_persistent_test` (tmpfs) same exit 5.
- Top-level gate: `if inspect.is_volatile and not is_dry_run_trial -> exit 5` (`:364-367`) — but correctly allows explicit `--inspect` demonstration without failing dry-run-only trials. No leak: `--write-test` and real `--trial --dest` share same `inspect` gate; `--dry-run` flag is the **only** bypass, and it prints explicit warning and sets `dry_run:true` without copying.
- `copy_trial_to_dest` also requires `trial_dir` existence (`:159`) and when `dry_run false` does `shutil.copy2` + per-file SHA verify + `backup_verified` flag update (`:176-185`).

**Checksums:** `generate_checksums` walks `rglob`, per-file SHA, writes `checksums.sha256` `sha  rel` (`:214-232`); `verify_checksums` resolves relative to `data/CSI-SENSE-001/raw` and reports `mismatches` (`:234-266`). Tested: ` --checksums data/CSI-SENSE-001/raw` 0 entries (raw empty, expected), ` --verify-checksums` `ok true checked 0`.

**Defect scan:** No missing volatile type (covers all Live cases `/cow` overlay + `/tmp` tmpfs + `/rofs` squashfs). Duplicate `tmpfs` substring redundant but not harmful. No path traversal or partition-write code. Does not assume drive existence — inspects actual dest per plan §5.5.

**Verdict:** PASS — safety gate sound; dry-run bypass is explicitly scoped and cannot be accidentally triggered by Phase C real backup.

**Still unsatisfied:** Persistent destination not yet identified — `study_metadata.json:persistent_backup` all `null` (`:45-53`); `--write-test 100MB` on real external not yet executed. This is prerequisite, not software defect.

---

## 6. ANALYSIS AUDIT — PASS (no leaking, no false claims, walking covariate correct)

**Files:** `features.py:53-113`, `baseline_model.py:54-103`, `pca_spectrogram.py:51-134`, `temporal_plots.py:67-307`, `statistical_tests.py:48-365`, `analysis_config.json:1`

**Amplitude correct:** `features.py:107` `amp=np.sqrt(I.astype(float)**2 + Q.astype(float)**2)` — `I=data[:,0::2] Q=data[:,1::2]` (`:104-105`) from 128 ints → 64 subcarriers. Documented `phase_note: amplitude via sqrt(I²+Q²)` (`:165`).

**Phase detrending correct:** `phase_wrapped=atan2(Q,I)` (`:109`, `-π..π`), `unwrapped=np.unwrap(phase_wrapped, axis=1)` (`:60`), then per-packet `lstsq` fit `phase_k ≈ a*k+b` via `np.vstack([k,ones]).T` (`:72-73`), subtract (`:78`), return `phase_detrended`. Slope stats recorded. Note `analysis_config.json:47` `phase_note: Absolute phase contaminated by CFO/SFO; only detrended relative interpretable (§7.2)` — matches plan §7.2.

**Baseline leakage:** `baseline_model.py:54-98` `compute_baseline(amp, baseline_idx)` computes `mu/sigma/cov` **only** on `baseline_amp=amp[baseline_idx]` (`:63`); defaults to first 9000 (`:214`) but Phase C will pass explicit `baseline_idx` from events (plan: condition A 90s). `pca_spectrogram.py:58-59` `X_fit=amp[baseline_idx]` then centers by `mean(baseline)` and fits SVD **only** on baseline, projects all conditions via `amp_masked-mean` (`:111`). No future D/C data used in fit — PASS. Null subcarriers excluded (`amp==0` all packets → `null_mask` `:123`, PCA `keep=~null_mask` `:64-66`).

**PCA/spectrogram claims:** Code is exploratory; `pca_spectrogram.py:255` `signal=PC1 projection` with STFT `2s 90% overlap` (`:144-149` scipy `stft` or manual Hann manual `:153-181`) reports `explained_variance` and `top_subcarriers` without claiming detection. `statistical_tests.py` explicitly gates demo: `evaluate_q1_q2_demo()` (`:147-180`) sets `demo:true`, `demo_note: Synthetic demo — Phase B host-side only, no human data collected` (`:179`), `temporal_plots.py:84-88` synthetic seeded `np.random 20/22/21` with `synthetic=True` and prints warning. No human-detection claim generated from demo — PASS.

**Walking speed covariate not gate:** Confirmed everywhere: `study_metadata.json:65-70` `reference_is_target_only true, speed_is_covariate_not_gate true`; `analysis_config.json:105-111` same; `capture_config.json:46` `walking_speed_not_gate`; `validate_raw.py:173` note; `baseline_model.py:11-12` comment; `statistical_tests.py:308-311` stub `walk_speed single_trial ... requires N>=3` and demo speeds `0.7-1.5` with Spearman (`:165-167`) only if env exists — never invalidates trial. Validation never rejects on speed (`validate_raw.py` has no speed check beyond presence check).

**Statistical assumptions flagged —scientifically sound with notes:**

- Distribution-dependent choice: `statistical_tests.py:68-107` imports `mannwhitneyu, shapiro, ttest_ind`; runs Shapiro on ≤5000 samples (`:85-94`), recommends `t-test (Welch)` if both `p>0.05` else `Mann-Whitney U` (`:98-99`), reports both U + Welch + effect sizes `cohen_d` (`:48-58`) and `rank_biserial_r` (`:60-64`) plus CI stub. Rationale logged (`:106`). Correct per §8.2 `Inspect → Choose → Correct → Effect-size first`.
- Multiple testing: `benjamini_hochberg` (`:116-145`) implements FDR BH (prefers `statsmodels` else manual `q = p*m/rank` with monotonic adjustment) for 64 subcarriers — not overly conservative Bonferroni, per §8.2.
- Effect sizes as reference not proof: `analysis_config.json:78-82` `cohen_d 0.5, r 0.3 reference_is_not_proof true`; `statistical_tests.py:343-344` `interpretation: d>=0.5 r>=0.3 practical references only; smaller consistent reproducible above p95 may still be meaningful` — correctly v1.1.
- **Questionable point flagged but not blocking:** Demo heuristic segmentation `remaining 50/50 C vs D split` (`statistical_tests.py:221-222`, also `baseline_model default`) when no `events_trialXX.jsonl` — noted in code as `heuristic 50/50 split of non-baseline; with real events use event logger` (`:321`). Will be correct once events drive segmentation; adequate for Phase B.
- Q3 repeatability (≥8/10 trials) correctly not computed on single trial; reported as stub requiring N≥8 (`statistical_tests.py` omits Q3 until aggregated).
- Q4 `above empty-empty p95` implemented (`:244-263` `p95_A`, `median_C/D > p95`, `intra_baseline_inter_window`), Q6 FP held-out windows (`:281-295` `fp_rate ≈5% at p95`) — matches §9 guards.
- Power note: plan §8.3 power deferred until pilot variance measured — analysis_config defers correctly.

**Verdict:** PASS — calculations correct, no leaking, no synthetic-claim leakage, walking correctly covariate, assumptions sound (FDR, non-parametric default appropriate for correlated CSI samples).

---

## 7. METADATA / PROTOCOL AUDIT

**Inspected:** `study_metadata.json` (85L), `room_geometry.json` (94L), `hardware_identity.json` (65L), `firmware_versions.json` (83L), `capture_config.json` (69L), `PROTOCOL.md` (187L), `README.md` (192L) against PLAN v1.1 §4 §6 §11.

| File | Matches Plan | Gap Before Phase C |
|------|--------------|--------------------|
| `study_metadata.json:1` | Has `study_id`, `research_question`, `prerequisite PASS 2026-09-06`, `host` model/os/kernel/live `/cow`, `firmware` pinned SHAs `ce23861e/7d7cf51e/296b6eab/8633d67`, `hardware` MAC/BSSID/channel, `capture` baud 921600 len128, `geometry_ref`, `persistent_backup` gate stub, `walking` v1.1 fields, `ethics` S01, `phases` gates — matches §6.2 schema + v1.1 persistent/walking rows (`:44-53` `note Must be verified BEFORE Phase C §5.5`) | **Must fill before Phase C:** `persistent_backup.path/filesystem/size_avail_gb/write_test_sha_match/verified_utc` currently all `null` — must be verified live; `n_trials_planned 10`, `trial_duration_s A90 B12 C60 D35 E12 F90 rest30 total310` correct |
| `room_geometry.json:1` | Has `coordinate_origin router floor projection`, `units meters`, `room` placeholders, `router x0 y0 z null`, `esp32 null` coords, `host`, `furniture` template, `human_positions P1-P3`, `walking_path waypoints [P1,P2,P3] path_length null los_cross null`, `measurement_protocol ±0.05m + photos`, `placeholder true` (`:93`), `reference_speed [0.8,1.2] reference_is_target_only true` (`:90`) — matches §4.2/§6.2 template exactly | **Must fill before Phase C:** All `null` coordinates (`room.length_m/width_m/height_m`, `router.z_m`, `esp32 x/y/z/antenna/usb/fixation`, `host x/y`, `furniture`, `P1-P3 x/y/facing`, `path_length_m`, `los_cross_xy`) plus `room_geometry_photo_*.jpg` (2 angles, tape visible) — currently `null`/`placeholder true` as expected Phase B |
| `hardware_identity.json:1` | Lists `ESP32-D0WD-V3 rev3.1 40MHz MAC f4:65:0b:56:0e:18`, `flash 4MB 0x68:0x4016 dio 40m`, `CP2102 10c4:ea60 Bus003 /dev/ttyUSB0 188,0 dialout`, `Xiaomi Nihaal 8C:53:C3:5B:E1:59 ch1 2412 HT20 -39 dBm GW 192.168.31.1` with `verification nmcli+iw`, `host Lenovo 82S9 BIOS JMCN48WW`, `live /cow 7.7G overlay + /tmp 7.7G tmpfs`, `storage sda HP 32GB /cdrom ro + nvme0n1 BitLocker locked untouched` — matches §0 provenance | PASS — already filled, no action |
| `firmware_versions.json:1` | ESP-IDF `v5.4.4 296b6eab9445` + clone path, ESP-CSI `8633d67152`, `app_main.c 8309B CONFIG_SEND_FREQUENCY 100` `memcmp` filter, `printf CSI_DATA` header, sdkconfig `TARGET esp32 921600 CSI_ENABLED`, build `ce23861e 723K + 7d7cf518 26K cmake 4.2.3 ninja 1.13.2`, flash `dio 40m` result, `capture method Serial /dev/ttyUSB0 921600 read(4096)wb no parsing` + observed rates `wall 102 chip 141` — matches §0 pinned | PASS — `proven_reused true`, `firmware_change_policy separate Gate 3` (`:82`) |
| `capture_config.json:1` | `baud 921600 port /dev/ttyUSB0 config_send_frequency 100 rate 102/141 median 5985 len128 64 subcarriers sig_len 83 ch1 BSSID` + `trial_duration_s A90 B12 C60 D35 E12 F90 total 310` + `valid_trial_criteria missing ≤1% malformed ≤0.5% no gap >500ms no extra human all_events BSSID/ch/len ≥99% walking_speed_not_gate` (`:37-47`) + `backup rule NO HUMAN … VERIFIED` (`:49`) + `analysis` mapping to 6 tools + versions `python 3.14.4 pyserial 3.5 esptool 4.12.0` — matches §5/§6 | PASS — typo `capure_script` (`:21`) non-blocking (value still points correctly to capture script) |
| `PROTOCOL.md:1` | Executable checklist: Pre-Trial Gates §0 (`tooling reviewed`, `geometry recorded`, `environment §10`, `persistent backup verified --inspect/--write-test 100` with `is_volatile false` gate `STOP` `:12-22`), Environment §1 table (other people, doors, fans, appliances, Wi-Fi, receiver movement, antenna, walking speed covariate `:27-42`), Geometry §2 (origin, tape ±0.05m, photos `:44-55`), Per-Trial A→F 310s sequence with events + walk_start/end mandatory (`:58-98`), Post-trial `validate_raw --trial` + `env_trial.json` template walking + `backup_verify --trial --dest` SHA verify (`:95-107`), Analysis order §5, Safety reminders (`:176-182`) — verbatim §2–§5/§10 | PASS — ready to execute after gate |
| `README.md:1` | Study question H0/H1, hardware proven, Conditions table A–F with walking v1.1 note, Dataset Structure `data/CSI-SENSE-001/...` (matches §6.1), How to Reproduce capture/analysis/dry-run commands, Analysis Pipeline 6 stages, Success PASS/PARTIAL/FAIL per §9, Reproducibility, Ethics S01, Phase Gates — matches plan | PASS — `Files Created 17 files` (`:20-192`) counting clarifies discrepancy above |

**Verdict:** PASS — schemas correct, placeholders appropriately null for Phase B; only geometry + backup + env photo/checklist must be filled in Phase C.

**Required actions before Phase C (metadata):**
- Fill `room_geometry.json` all `null` → measured meters + `tape_photo`/`photo` filenames + `furniture` array + `human_positions` + `walking_path.path_length_m` + `los_cross_xy` with photos `room_geometry_photo_01.jpg`×2.
- Verify persistent backup and write `study_metadata.json:persistent_backup` with `path/filesystem/size_avail_gb≥5/write_test_sha_match:true/verified_utc` plus `metadata/firmware_versions.json` unchanged.

---

## 8. HARDWARE / ENVIRONMENT CHECK — PASS (read-only)

**All checks read-only; no flash/router/BIOS/partition/SSD modified per scope.**

| Check | Command/Evidence | Expected | Actual | Result |
|-------|------------------|----------|--------|--------|
| ESP32 present at `/dev/ttyUSB0` | `ls -l /dev/ttyUSB0:1` `crw-rw-rw- 188,0 Sep 6 20:52 /dev/ttyUSB0` + `by-id usb-Silicon_Labs_CP2102... -> ../../ttyUSB0` | CP2102 present | Present, dialout, not flashed in audit | PASS |
| ESP32 identity unchanged | `lsusb Bus003 Device007 10c4:ea60 CP210x` + `hardware_identity.json` `f4:65:0b:56:0e:18`/`4MB 0x68:0x4016`/`ESP32-D0WD-V3 rev3.1` matches esptool chip_id/flash_id logs in PLAN §0 | Same as CSI-VERIFY-001 | Matches; no `idf.py flash` executed (audit grep only doc comments) | PASS |
| Proven firmware/config unchanged | `firmware_versions.json` `bin ce23861e 723K bootloader 7d7cf518 v5.4.4 296b6eab ESP-CSI 8633d671` + `capture_config.json` baud 921600 `CONFIG_SEND_FREQUENCY 100` `len128` | Reused proven | Unchanged; no rebuild/flash in audit (`/tmp/csi_recv_router` intact but not rebuilt) | PASS |
| Router unchanged | `iw dev wlp0s20f3 link Connected to 8C:53:C3:5B:E1:59 SSID Nihaal freq 2412 signal -39 ch1 HT20 20MHz` + `nmcli Nihaal wlp0s20f3` (`iw dev`/`wlp link` logs §8) | Nihaal 8C:53:C3:5B:E1:59 ch1 HT20 | Matches `hardware_identity.json`/`capture_config.json` — no `nmcli`/`iw` config change in tools | PASS |
| No firmware flash required | Tooling docs `firmware_change none — host-side only unless separate approval` (`study_metadata.json:22`, `firmware_versions.json:82`) + `capture_csi_sense.py epilog HOST-SIDE ONLY does not flash` | No flash Phase C | Confirmed; Phase C reuses proven firmware | PASS |
| No Windows/BIOS/partition/SSD modification | `lsblk NAME ... nvme0n1 476.9G BitLocker nvme0n1p3 474.7G + sda vfat /cdrom ro + /cow overlay 7.7G` — `nvme0n1` `RO 0` untouched, `sda` live, no `erase_flash`/`partition-table` write in tools | Untouched | Verified untouched (audit performed no writes) | PASS |
| pyserial/pinned toolchain | `python3 -c import serial; print(serial.VERSION)` `3.5` + `tools` imports `pyserial 3.5 numpy 2.5.3 scipy 1.18.1 matplotlib 3.11.1` installed | Pinned | Installed per Phase B | PASS |

**Volatile environment:** `df -hT` ` /cow overlay 7.7G 4.2G free` `/tmp tmpfs 7.7G 3.8G` `findmnt / overlay /tmp tmpfs` — Live USB volatile confirmed, hence backup gate required (see §5).

**Verdict:** PASS — hardware unchanged, no modifications required or performed.

---

## 9. DO NOT COLLECT HUMAN DATA — COMPLIED

- No `python3 tools/csi_capture/capture_csi_sense.py --trial ... --duration 310` real capture executed.
- No `event_logger.py` human session started.
- No `raw/trial_XX/*_raw.log` human data created (`data/CSI-SENSE-001/raw: empty 0 entries`, `checksums.sha256 0 entries` preserved; CSI-VERIFY log `51d47ce9` unchanged `rw-rw-r--` not `a-w`).
- No A→F trial, no `env_trialXX.json` human record, no Phase C.

**Verdict:** PASS — audit remained host-side dry-run/fixtures only.

---

## 10. FINAL READINESS — READY WITH REQUIRED ACTIONS

### Classification

**READY WITH REQUIRED ACTIONS** = no software blocker, but Phase-C prerequisites still need to be completed before any human experiment.

- **NOT READY** would require concrete technical/scientific/safety defect — none found (capture binary-safe, backup gate enforced, parsing robust, amplitude/phase/baseline/PCA correct, walking covariate not gate).
- **READY** would require geometry+environment+persistent backup all satisfied — they are not (see below).
- Therefore **READY WITH REQUIRED ACTIONS**.

### Per-Check Rollup

| # | Check | Verdict |
|---|-------|---------|
| 1 | Audit all Phase B tooling (17-vs-18 resolved, PLAN §14 match) | PASS |
| 2 | Capture path (binary-safe, no parse, errors/interrupt) | PASS |
| 3 | Event logger (sidecar, wall_ns+seq sync, A→F) | PASS |
| 4 | Raw validation / parser (glued/malformed/missing, raw immutable, proven format) | PASS |
| 5 | Backup safety (reject volatile, inspect, write-test SHA, dry-run isolated) | PASS |
| 6 | Analysis (amp sqrt, phase unwrap+detrend, baseline-only PCA, demo isolated, effect-size reference, walking covariate, Shapiro/FDR) | PASS |
| 7 | Metadata / protocol (schemas match, placeholders correctly null) | PASS |
| 8 | Hardware / environment (ESP32 /dev/ttyUSB0 present, firmware/router unchanged, no flash/BIOS/partition needed) | PASS |
| 9 | No human data collected | PASS — complied |

### Defects Found (none blocking)

1. **Documentation count wording (17 vs 18)** — cosmetic; plan counts 6 analysis py, implementation counts 6 py+1 config json as 7. Not a blocker. See §1.1.
2. **`capture_config.json:21` key typo `capure_script`** — value path correct (`tools/csi_capture/capture_csi_sense.py`); JSON valid; fix in Phase C.
3. **`analysis_config.json` location** `tools/csi_analysis/` vs plan suggested `data/CSI-SENSE-001/analysis/` — recommend copying committed config to data tree before Phase C.
4. **Dry-run mock `len 128` with 4-int data** — isolated to `--dry-run`; real path unaffected.
5. `backup_verify.py` duplicate `tmpfs` in `VOLATILE_SUBSTRINGS` — redundant, safe.

### Required Actions Before Phase C (must satisfy §5.5 gate)

1. **Persistent storage verification** — `persistent storage still needs verification: YES`
   - Identify real persistent device (external USB SSD/HDD or second internal non-Live partition — not `/cow`/`/tmp`/`overlay`/`squashfs`/`tmpfs`). Do **not** assume `/media/ubuntu/PERSISTENT` exists.
   - Record in `study_metadata.json:persistent_backup` after inspection.

2. **Room geometry recording** — `room geometry still needs recording: YES`
   - Tape measure ±0.05m all §4 elements: `room_length/width/height/wall_material/door/window/floor`, `router x,y,z/orientation`, `ESP32 x,y,z/antenna/usb/fixation`, `host x,y`, `furniture` each RF obstacle, `P1/P2/P3 x,y/facing`, `walking_path waypoints/path_length_m/los_cross_xy`, with photos `metadata/room_geometry_photo_01.jpg` + `02` (two angles, tape marks) — fills all current `null` in `room_geometry.json:7-91` and sets `placeholder false`.

3. **Environment ready** — §10 checklist (§10) controlled for all trials: single subject S01 outside >3m stationary during A/F, doors/windows closed/opened only B/E same angle, fans/AC off, appliances/unplugged, no large Wi-Fi downloads, receiver taped cable-strain-relieved antenna fixed photographed, host on AC, walking natural pace logged per `env_trialXX.json:walking` with `path_length_m/walk_duration_s/estimated_speed_mps`.

4. **Safe pre-trial smoke test** — `real serial capture still needs a safe pre-trial smoke test: YES` — a 10-s live capture without human, validating rate/gaps before 310-s trials.

### Exact Commands That SHOULD Be Run Next (do NOT execute gated actions now — for Phase C gate)

```bash
# 1. Identify real persistent destination (replaces /media/ubuntu/PERSISTENT with actual inspected path)
python3 tools/csi_capture/backup_verify.py --inspect /media/ubuntu/PERSISTENT
# expect: is_volatile false, is_persistent_guess true, free_sufficient_5GB true, FSTYPE ext4/xfs/NTFS not tmpfs/overlay/squashfs

python3 tools/csi_capture/backup_verify.py --write-test /media/ubuntu/PERSISTENT --size-mb 100
# expect: ok true sha_match true 100MB, gate PASS
# Then record in data/CSI-SENSE-001/metadata/study_metadata.json:
#   persistent_backup {path, filesystem, size_avail_gb>=5, write_test_sha_match:true, verified_utc:ISO8601}

# 2. After geometry measured + photos taken, validate JSON filled (no null remaining)
python3 -c "import json, pathlib; j=json.loads(pathlib.Path('data/CSI-SENSE-001/metadata/room_geometry.json').read_text()); print('nulls', sum(v is None for v in [j['room']['length_m'], j['esp32']['x_m'], j['walking_path']['path_length_m']])); print('placeholder', j['placeholder'])"
ls -lh data/CSI-SENSE-001/metadata/room_geometry_photo_*.jpg

# 3. Safe pre-trial smoke test (NO HUMAN — room empty, door closed, 10s, proves live rate without starting Phase C experiment)
python3 tools/csi_capture/capture_csi_sense.py --trial 01 --duration 10 --baud 921600 --port /dev/ttyUSB0
python3 tools/csi_capture/validate_raw.py --trial 01
# expect: valid_trial true missing <=1% malformed <=0.5% len128>=99% channel1>=99% no gap>500ms rate ~100Hz
python3 tools/csi_analysis/parse_csi.py --trial 01 --print-summary
python3 tools/csi_capture/backup_verify.py --trial 01 --dest /media/ubuntu/PERSISTENT
# expect: ok true sha match, backup_verified true in env_trial01.json
python3 tools/csi_capture/backup_verify.py --checksums data/CSI-SENSE-001/raw
python3 tools/csi_capture/backup_verify.py --verify-checksums data/CSI-SENSE-001/checksums.sha256
# ONLY AFTER smoke test PASS + geometry + env + backup-verified: proceed to Phase C 310s trials:

# Phase C (requires explicit APPROVAL for Phase C — NOT executed now):
# Terminal 1:
#   python3 tools/csi_capture/capture_csi_sense.py --trial 01 --duration 310 --baud 921600 --port /dev/ttyUSB0
# Terminal 2 (parallel):
#   python3 tools/csi_capture/event_logger.py --trial 01
# After each trial:
#   python3 tools/csi_capture/validate_raw.py --trial 01
#   # fill data/CSI-SENSE-001/raw/trial_01/env_trial01.json with walking {path_length_m, walk_duration_s, estimated_speed_mps}
#   python3 tools/csi_capture/backup_verify.py --trial 01 --dest /media/ubuntu/PERSISTENT
#   # gate: do not start trial 02 until backup_verified true
```

**Do not run** the smoke test or any ` --duration 310` trial until the operator has (a) attached a real persistent device, (b) recorded geometry/photos, and (c) received explicit `CSI-SENSE-001 — APPROVED for Phase C` after this report is reviewed.

---

## Scope Attestation

No ESP32 flash/erase/BIOS/router/partition/internal SSD (nvme0n1 BitLocker untouched) modification performed or required; no hardware purchased; no human CSI collection; no final ML; no localization; no 3D UI; no human requested to enter room. Audit used only synthetic fixtures, dry-runs, and existing `CSI-VERIFY-001` raw.

*Report generated read-only; raw `~/Desktop/CSI_RAW_70s_921600_20260906_205638.log` SHA `51d47ce9` verified unchanged; `/home/ubuntu/data/CSI-SENSE-001/raw` empty pending Phase C.*

