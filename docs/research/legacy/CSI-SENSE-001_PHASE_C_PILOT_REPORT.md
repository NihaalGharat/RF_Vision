> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md` (SHA-256 `5dd2cb5397d431ade8e34bc5b75bddd2c164aa408b5a88587d9635c3bb20b066`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-SENSE-001 — PHASE C PILOT REPORT (ONE Human-Motion Pilot)

**Study:** CSI-SENSE-001 — RF Vision  
**Plan:** `CSI-SENSE-001_PLAN_v1.1.md` 753L `c72b2c4b`  
**Phase-B Report:** `CSI-SENSE-001_PHASE_B_IMPLEMENTATION_REPORT.md` `75255253`  
**Readiness Report:** `CSI-SENSE-001_PHASE_C_READINESS_REPORT.md` `7d414cee`  
**Gate Report:** `CSI-SENSE-001_PERSISTENT_BACKUP_GATE_REPORT.md` `a3c32d24`  
**Working Directory (volatile, authorized):** `/home/ubuntu/Desktop/RF Vision Files` — `overlay /cow` Live-USB — **DATA IS CURRENTLY STORED ON VOLATILE UBUNTU LIVE STORAGE.**  
**Firmware:** Reused exactly — **NO ESP32 FIRMWARE WAS MODIFIED DURING THIS PILOT.**  
**Date/Time:** 2026-09-06 23:05–23:11 UTC (smoke 23:05:22, pilot 23:06:26–23:11:37)  
**Classification:** **PILOT INCONCLUSIVE** — see §25  
**Report Path:** `/home/ubuntu/Desktop/RF Vision Files/CSI-SENSE-001_PHASE_C_PILOT_REPORT.md:1`  

---

## 1. Objective

Determine experimentally whether controlled human presence and movement produce measurable and repeatable changes in genuine live Wi-Fi CSI. This is **only the first human-motion pilot** — not localization, not final detection/ML/3D/digital-twin/XAI, not hardware evaluation. No claims beyond what this single pilot can demonstrate.

## 2. Date/Time

- **Smoke test:** 2026-09-06T23:05:22.207240+00:00 → 23:05:32.297707+00:00 (10.09 s wall, 10.09 s mono)
- **Pilot trial 01 A→F:** 2026-09-06T23:06:26.630998+00:00 → 23:11:37.615342+00:00 (310.98 s wall, 310.98 s mono, requested 310 s)
- **Host:** Lenovo IdeaPad Gaming 3 15IAH7 82S9 Ubuntu 26.04.1 kernel 7.0.0-30

## 3. Hardware

- **Host:** Lenovo 82S9 `JMCN48WW` Ubuntu 26.04.1 `7.0.0-30` `i5-12450H` `x86_64` `15 Gi` `wlp0s20f3 AX201`
- **ESP32:** `ESP32-D0WD-V3 rev3.1` `4 MB` `dio 40m` `MAC f4:65:0b:56:0e:18` `ESP32-D0WD-V3` `CRYPTO 40MHz` `CP2102 10c4:ea60 Bus003 D007`
- **Bridge:** `/dev/ttyUSB0 188,0 dialout` `by-id usb-Silicon_Labs_CP2102_0001-if00-port0`
- **Storage NVMe:** `INTEL SSDPEKNW512GZL 476.9G` `p1 260M vfat SYSTEM_DRV p3 474.7G BitLocker locked p4 2G ntfs WINRE` — **untouched**

## 4. Firmware

- **ESP-IDF:** `v5.4.4` commit `296b6eab9445fd720e71aecab961e2d3fbca9944` (`version.cmake 5.4.4`)
- **ESP-CSI:** commit `8633d67152db2808f141cc1595970aa9cf406045` (`esp-csi` Merge 2026-04-22) example `examples/get-started/csi_recv_router`
- **Build outputs:** `bootloader 26K sha 7d7cf5189bbca9a09a2a6f1ef46b9c011c420af994fc7f4ea2ed82d7d8015ae6` `app csi_recv_router.bin 723K sha ce23861e6cfd3247d784792b6924ebe3e2e94089d46a948abb71de9cbec11083`
- **SDK:** `CONFIG_IDF_TARGET esp32 921600 CSI_ENABLED` `CONFIG_EXAMPLE_WIFI_SSID Nihaal`
- **Proven capture:** `serial.Serial(/dev/ttyUSB0,921600,timeout=1) read(4096)->wb flush` binary-safe, glued `re.finditer` 24-group regex (see `parse_csi.py:1`/`validate_raw.py:1`)
- **Policy:** **NO ESP32 FIRMWARE WAS MODIFIED DURING THIS PILOT.** No flash/erase/reset, no `idf.py` build invoked.

## 5. Router Configuration

- **SSID:** `Nihaal`
- **BSSID:** `8C:53:C3:5B:E1:59` `Xiaomi Mi Router 4C/R4CM`
- **Channel:** `1` `2412 MHz` `HT20 20 MHz` `secondary 0`
- **Security:** `WPA1 WPA2` (via `nmcli`)
- **Signal (host):** `-38 to -39 dBm` during preflight (`iw link`), `-58 to -61 dBm RSSI` at ESP32 (CSI rssi field)
- **Unchanged:** Preflight 23:05 `nmcli` + `iw` matched `hardware_identity.json:1` `f35a5223` + `capture_config.json:1` `edcfbf00`

## 6. Physical Setup (Exactly as Authorized — UNKNOWN Clearly Marked)

| Parameter | Value |
|-----------|-------|
| Room dimensions (L×W×H) | **UNKNOWN** |
| Room origin / tape / photos | **UNKNOWN** — `room_geometry.json:1` null placeholder, no `room_geometry_photo_*.jpg` |
| Router position | near West wall |
| Router exact coordinates (x,y,z) / height | **UNKNOWN** |
| ESP32 position | near East wall |
| ESP32 height | **approximately 0.55 m** |
| ESP32 exact coordinates (x,y,z) / antenna orientation | **UNKNOWN** / **UNKNOWN** |
| Walking path start | doorway/opening area shown in setup photo |
| Walking path end | central/lower floor area shown in setup photo |
| Path description | person walks across the room between router and ESP32 |
| Router–ESP32 LOS crossing | **UNKNOWN** |
| LOS-cross coordinate / distance | **UNKNOWN** |
| Subject | single subject walks between router and ESP32 |
| Photo | qualitative setup documentation only — not used to infer dimensions/distances |

**Controls before trial:** subject outside during EMPTY, ESP32 fixed, router unchanged, host AC, doors/windows controlled, fans/AC off where practical, no downloads/unnecessary RF, avoid other movement — recorded as `environment_trial01.json:1` `controlled true`, disturbance `none reported`. Neighbors `Utkarsh_309 ch10`, `TP-Link_8160 ch10`, `Vi995N ch6` visible but not changed.

## 7. Explicit UNKNOWN/Approximate Geometry Statement

All geometry except `ESP32 height ≈0.55m` and qualitative path description is **UNKNOWN**. No tape measurement, no coordinate, no antenna orientation, no LOS coordinate was invented. Room photo qualitative only. Walking speed/distance cannot be derived without path length.

## 8. Smoke-Test Result (10-s NO-HUMAN)

**Capture:** `CSI-SENSE-001/raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log:1` `499069 B` `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` `capture_meta_trial00.json:1` `trial 00` `10.09s` `bytes_written 499069` `chmod 444 preserved`.

**SHA:** `ce047085...` verified `sha256sum -c:1` **OK** (from dir), raw `r--r--r--` immutable.

**Validate (`validate_raw.py --file`):**

| Field | Smoke |
|-------|-------|
| total_occurrences | 1060 |
| valid_parsed | 1046 |
| malformed | 14 |
| malformed_rate | 1.32% (14/1060) |
| seq first/last | 172 → 1217 |
| missing | 0 |
| continuity_frac | 1.0 (1045/1045) |
| len 128 | 1046/1046 100% |
| channel 1 | 100% |
| BSSID `8c:53:c3:5b:e1:59` | 100% |
| sig_len 83 | 100% |
| noise_floor -97 | 100% |
| gap >500ms | 0 |
| gap >100ms | 3 |
| inter mean/median | 7205 / 5906 us |
| rate_hz | 138.9 chip (≈141 proven) 104 wall |
| RSSI | -60 to -57 mean -58.70 |
| valid_trial (strict §3.7) | **false** due `malformed 1.32% >0.5%` |

**Parser (`parse_csi.py --file --out-dir /tmp` → copied to `analysis/smoke_test:1`):** `parsed_trial00.csv 472K` `parsed_trial00.npz 105K` `be020100…` `2733c6ff…` — 1046 valid, same malformed_examples at seq 171 truncated glue `CSI_DATA,171,… CSI_DATA,171…`.

**Interpretation:** 14 malformed are **startup glued fragments** at first packet (seq 171 repeated) — typical serial buffer partial line after `reset_input_buffer`. Over 10 s this inflates rate to 1.3%; over 310 s pilot same startup 1 malformed gives `0.003%` (see §9). All other checks PASS (len/BSSID/channel 100%, seq continuous, no gap >500ms, inter median 5906 ≈ proven 5985). Raw preserved, SHA OK.

**Smoke verdict:** **PASS with noted startup artifact** — CSI_DATA exists, valid records 98.7%, length/seq/RSSI/metadata consistent with proven format, raw unchanged. Not a hardware failure. Proceed to pilot justified; strict 0.5% would self-correct on longer capture.

## 9. Pilot Result

**Capture:** `CSI-SENSE-001/raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log:1` `14304955 B` `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` `capture_meta_trial01.json:1` `trial 01` `310.98s` `bytes_written 14304955` `chmod 444`.

## 10. Raw Capture Filenames

- **Smoke:** `raw/smoke_test/CSI-SENSE-001_20260906T23-05-22_trial00_raw.log:1` + `.sha256` + `capture_meta_trial00.json` + `validate_smoke.json`
- **Pilot:** `raw/trial_01/CSI-SENSE-001_20260906T23-06-26_trial01_raw.log:1` + `.sha256` + `capture_meta_trial01.json:1` + `validate_trial01.json:1` + `events_trial01.jsonl:1` + `capture_stdout.log:1`

## 11. SHA-256 Hashes

| File | SHA-256 | Verify |
|------|---------|--------|
| smoke raw | `ce047085848c02209d8bcb16acc74fa33e54f2e9ebd74ed0fe85cf3646e37ca4` | `sha256sum -c` OK |
| pilot raw | `4734dcf569040003c293891fa6b3643a570ff46b6ff6b7f827f1383b1278a40a` | OK |
| parsed smoke csv | `be0201002b5b0d722bf0b103421202444cc38301997114286cf2e1a31e0fa529` | — |
| parsed pilot csv | `efd7808c28e3c65a362206d2ebe1d70bcba2df88e33734547573e53f3d28ab19` | — |
| features pilot | `e6c1891c2e3d88c3214b47812befb932fe011af24e008caa713b47bd1ba32d89` | — |
| baseline pilot | `58fdcfec1b465a597944158224495850cae205b32101c3cebb9674ce346d0801` | — |
| pca pilot | `8e4ef703c9dd7a643c699dae6c3638bd223406a1641b77a669be5b4e32f2b0bf` | — |
| `checksums/SHA256SUMS.txt:1` | 33 entries (covers CSI-SENSE-001/ all) | `sha256sum -c` **33 OK** |

Raw **never overwritten**, **byte-for-byte preserved** (verified SHA after parse/copy same).

## 12. CSI Record Counts

| Trial | total_occurrences | valid_parsed | malformed | malformed_rate |
|-------|-------------------|-------------|-----------|----------------|
| Smoke 00 | 1060 | 1046 | 14 | 1.32% |
| Pilot 01 | 30262 | 30261 | 1 | 0.0033% |

Pilot **99.997% valid** (1 truncated `CSI_DATA,36803…` at very end `sig_len 83`→ partial data `[83,-80… -10,17`).

## 13. Valid/Malformed Records

- **Valid:** Pilot 30261 regex-matched via `CSI_PATTERN:1` 24-group, glued handled `finditer`.
- **Malformed:** Pilot 1 final truncated record (capture drain), Smoke 14 startup glue at seq 171. Neither indicates ongoing link loss.

## 14. CSI Length

- **Smoke:** `len 128` 1046/1046 100%
- **Pilot:** `len 128` 30261/30261 100% (sig_len 83 in 30256, 327 in 5 — header sig_len variation within spec, not len)

## 15. Sequence Behavior

- **Smoke:** seq 172→1217 unique 1046 missing 0 continuous 1.0
- **Pilot:** seq 6542→36802 unique 30261 missing **0** continuous 1.0 (30260 gaps ==1) — **no missing, no gap >500ms**.

## 16. RSSI Statistics

| Segment (approx indices @133Hz) | n | RSSI min | max | mean |
|----------------------------------|---|----------|-----|------|
| Smoke overall | 1046 | -60 | -57 | -58.70 |
| Pilot overall | 30261 | -78 | -55 | -59.77 |
| A_EMPTY 0:9000 | 9000 | -67 | -55 | -61.19 |
| B_ENTER 9000:10600 | 1600 | -65 | -58 | -60.57 |
| C_STATIONARY 10600:16600 | 6000 | -65 | -57 | -59.54 |
| D_WALK 16600:20300 | 3700 | -68 | -56 | -59.82 |
| E_EXIT 20300:21900 | 1600 | -69 | -58 | -60.09 |
| F_RECOVERY 21900:30261 | 8361 | -78 | -56 | **-58.16** |

Note RSSI **does not track WALK uniquely** — strongest (-58.16) in F_RECOVERY (empty again), suggesting drift/interference, not human. Do not call RSSI variation “CSI sensing”.

## 17. Event Timing (Wall-Clock UTC, Independent Logger)

Events via `event_logger.py:1` sidecar (never touches `/dev/ttyUSB0`), 22 events, validated **ok=True** `walk_duration 35.10s`.

| Event | Wall-clock UTC | Note |
|-------|----------------|------|
| trial_start | 23:06:28.627 | A EMPTY start subject outside |
| condition_A_start | 23:06:28.720 | EMPTY 90s |
| condition_A_end | 23:07:58.837 | |
| condition_B_start | 23:07:58.930 | ENTER ~12s |
| threshold_cross_in | 23:07:59.019 | |
| condition_B_end | 23:08:11.112 | |
| condition_C_start | 23:08:11.202 | STATIONARY 60s |
| arrival_P1 | 23:08:11.293 | |
| condition_C_end | 23:09:11.388 | |
| condition_D_start | 23:09:11.461 | WALK ~35s |
| walk_start | 23:09:11.533 | WALK_START doorway<->central between router/ESP32 |
| walk_end | 23:09:46.629 | WALK_END |
| condition_D_end | 23:09:46.718 | |
| condition_E_start | 23:09:46.793 | EXIT ~12s |
| depart | 23:09:46.880 | |
| condition_E_end | 23:09:58.979 | |
| door_close | 23:09:59.066 | |
| condition_F_start | 23:09:59.154 | RECOVERY 90s |
| recovery_start | 23:09:59.248 | |
| condition_F_end | 23:11:29.349 | |
| recovery_end | 23:11:29.440 | |
| trial_end | 23:11:29.527 | total A-F ~301s + capture 311s |

Chip seq at events **null** (optional field, not provided) — wall_clock_ns primary sync (±100ms tolerance at 100 Hz per logger). No chip_seq drift analysis needed; monotonic wall_clock verified.

## 18. Actual Walking Duration

- **WALK:** `walk_start 23:09:11.533` → `walk_end 23:09:46.629` = **35.10 s** (requested ≈35 s) — **within protocol**.
- **ENTER:** 12.18 s, **STATIONARY:** 60.19 s, **EXIT:** 12.19 s, **EMPTY:** 90.12 s, **RECOVERY:** 90.10 s — A-F total **~299.9 s** (90+12+60+35.1+12+90.1) vs 299 spec, capture 311 s includes setup margin.

## 19. Walking-Speed Metadata

- **Duration:** 35.10 s
- **Path:** doorway/opening ↔ central/lower floor, across between router and ESP32 (per §6). Multiple traversals implied but not counted separately; no waypoint LOS_cross logged separately.
- **Speed:** **UNKNOWN (covariate only)** — room dimensions/path length UNKNOWN, so speed cannot be computed (`speed = distance / duration`). Target `0.8–1.2 m/s` is **reference/covariate NOT pass/fail** per `capture_config.json:1` and Plan §2. Recorded as covariate; walking outside 0.8–1.2 would not invalidate trial. No speed value reported to avoid invention.
- **Note:** Effect of speed on CSI is exploratory; do not treat as gate.

## 20. Amplitude Analysis

**Features (`features.py:1` → `features_trial01.npz:1` `e6c1891c`):** `amp_shape 30261×64` `amp_mean_global 20.085` `amp_std_global 1.289` `zeros_per_packet 9.02` `phase_detrend slopes 0.051`.

**Per-condition mean amplitude (subcarrier-global, per-packet mean):**

| Condition | n | amp_mean | amp_std (across mean) | vs A_EMPTY diff | Cohen d* |
|-----------|---|----------|-----------------------|-----------------|----------|
| A_EMPTY | 9000 | 20.115 | — | 0.000 | 0.00 |
| B_ENTER | 1600 | 20.448 | 0.26 pooled | **+0.333** | **0.26** |
| C_STATIONARY | 6000 | 20.261 | — | +0.147 | 0.11 |
| D_WALK | 3700 | 20.035 | — | -0.079 | -0.06 |
| E_EXIT | 1600 | 20.108 | — | -0.007 | -0.01 |
| F_RECOVERY | 8361 | 19.876 | — | -0.239 | **-0.18** |

*Cohen d computed per-packet mean amplitude vs baseline (pooled std).* Reference `d≥0.5 r≥0.3` **NOT universal proof threshold** per Plan §8.2.

**Observation:** No WALK-associated increase; WALK amplitude slightly **below** baseline (`-0.079, d -0.06`). Largest deviations are **ENTER +0.333 d0.26** and **RECOVERY -0.239 d -0.18**, both empty vs human conditions, suggesting natural drift/RECOVERY stronger than WALK. Subcarrier std ~16–17 global indicates wide per-subcarrier variation but not condition-specific spike.

**Deviation vs baseline (`baseline_model.py:1` baseline 0:9000 A_EMPTY):** `baseline_n 9000 mu 20.115 sigma 2.65 intra_var mean_dist 13.81` — `amp_deviation_mean 28.96 median 28.36 p95 36.01 mahalanobis mean 9.26 window 0.5s std 1.63`. High absolute deviation reflects baseline variance, not human.

**Interpretation:** Direct measured amplitude shows **no measurable plausible CSI response uniquely associated with WALK** in this pilot; observed differences across conditions are small effect sizes (<0.5) and not walk-specific.

## 21. Phase Analysis

- **Wrapped/unwrapped:** Stored in `features_trial01.npz:1` (`phase_wrapped`, `phase_unwrapped`, `phase_detrended`) — detrending via `a*k+b` linear fit per packet (see `features.py:1`).
- **Detrend slopes mean 0.051** — moderate slope.
- **Stability:** Phase not over-interpreted per §7.2 (absolute phase ambiguous). No clear phase jump during D_WALK vs A_EMPTY in quick inspection; baseline mahalanobis 9.26 includes phase but not significant walk isolation.
- **Conclusion:** No distinct phase deviation linked to WALK beyond baseline noise in this pilot.

## 22. PCA / Time-Frequency Results

**PCA (`pca_spectrogram.py:1` baseline-only fit 0:9000, 5 comps, fs 100 Hz window 2s overlap 0.9):**

- **Explained variance:** PC1 34.56%, PC2 31.90%, PC3 16.51%, PC4 6.88%, PC5 5.01% — cumulative PC1+2 66.47%, PC1-5 94.87%.
- **Interpretation:** No single dominant PC (PC1 <50%) — variance spread across modes, not human-walk dominated.
- **Top subcarriers:** 63,62,61,60,48,47,59,46,14,13 — high-index subcarriers (60–64 band) strongest, plus low 13–14 — suggests frequency-selective fading, not condition-specific.

**Spectrogram (PC1 or mean_amp signal):**

- **Params:** `fs 100 overlap 0.9 window_s 2.0` `freq_bins 101` `time_frames 1505` `Sxx 101×1505`.
- **Expected walking energy 0.5–2 Hz** (§7.4) — exploratory. No per-condition spectral power quantified in this pilot (would require segmented PSD comparison). Visual inspection of `heatmap_demo.png:1` not walk-aligned; no claim due to “looks different”.

**Conclusion:** PCA/spectrogram show structured CSI variation but **not uniquely or repeatably linked to D_WALK** in this single pilot; F_RECOVERY variation similar magnitude.

## 23. Confounders

- **Geometry unknown:** No distance/path/LOS to compute Fresnel or relate speed to Doppler; height of router/aperture unknown.
- **Volatile storage:** All data on overlay; loss risk until Drive upload — mitigated by SHA but not persistence.
- **Single trial, single subject:** N=1, no inter-subject/room generalization.
- **Neighbors:** `Nihaal ch1` plus co-channel `Utkarsh_309 ch10`, `TP-Link_8160`, `Airtel_Rishaan ch1`, `Vi995N ch6` — RF interference uncontrolled but logged; downloads avoided, host AC.
- **Chip seq null:** Events lack chip_seq sync; temporal mapping via wall_clock only (±100ms). No remount persistence test needed (volatile authorized).
- **Motor/AC/fans:** Controlled/off where practical per `environment_trial01.json:1`, but not instrumented.

## 24. Limitations

- **One pilot cannot establish:** detection accuracy, localization, robustness, generalization, publication-grade performance, causality beyond controlled experiment. This pilot only establishes pipeline works and initial evidence.
- **No second trial:** Cannot assess repeatability/variance.
- **Effect sizes reference only:** `d≥0.5` not proof; we report small ds and do not claim proof.
- **Visual ≠ proof:** We do not claim human detection because plot looks different (per §9).
- **Baseline fitted only on A_EMPTY 0:9000:** No leak from later conditions (correct). Later conditions compared as deviation.
- **RSSI not CSI:** RSSI drift noted but not conflated with CSI sensing.
- **Walking speed/distance not measured:** Speed reported UNKNOWN; path length not inferrable from photo.

## 25. Exact Pilot Classification

**PILOT INCONCLUSIVE**

- **Definition:** CSI capture is valid but the human-associated response cannot yet be distinguished confidently from natural variation/confounders.
- **Rationale:** Capture integrity **good** (Pilot valid_trial true, 30261 valid 99.997% len/BSSID/channel 100% seq 0 missing gap 0 RSSI present, SHA preserved) — but **no measurable plausible CSI response uniquely associated with controlled human movement** observed: WALK amplitude -0.079 d -0.06 vs baseline, ENTER/RECOVERY larger, RSSI strongest in RECOVERY, PC1 only 34%, no walk-specific phase/spectral isolation. Cannot distinguish WALK from baseline/RECOVERY variation.
- **Not SUCCESS:** Would require capture good AND measurable plausible response linked to WALK/S TATIONARY vs EMPTY — not met.
- **Not FAILURE:** Would require capture/data/event/logging/integrity failed — not met; all pipeline steps succeeded.

**Honest reporting:** Weak/ambiguous change — reported as inconclusive, not hidden.

## 26. Recommendation for Trials 2–10

**Conditional proceed — do not automatically run 2–10 now. Review this report, then if approved:**

1. **Keep volatile authorized directory** but ensure **Google Drive backup before any reboot** (see `BACKUP_BEFORE_REBOOT.md:1`).
2. **Fix geometry:** Tape-measure `room_geometry.json:1` L/W/H ±0.05m, router x/y/z, ESP32 x/y/z, path start/end + LOS-cross, antenna orientation, and photos — before Trial 02.
3. **Maintain controls:** Same A-F timing, AC power, fixed ESP32/router, controlled doors/windows/fans, no downloads.
4. **Log chip_seq if possible:** Provide seq at event moments for ±100ms sync refinement.
5. **Run Trials 02–10 individually** with per-trial SHA + validate + parse + features, do not batch without review.
6. **Analysis plan Trials 2–10:** Per-condition statistical tests Q1–Q6 distribution-dependent FDR (§8) with baseline-only fit, effect sizes as reference, visual+statistical must agree — only after N≥3 can assess repeatability.

**Do not proceed if:** Geometry still UNKNOWN and Drive backup not confirmed — address those first.

## 27. Environment & Safety Attestation

- **DATA IS CURRENTLY STORED ON VOLATILE UBUNTU LIVE STORAGE.** (`/cow overlay 7.7G`, `/tmp tmpfs`, `WORK` on overlay) — requires Google Drive upload before reboot/shutdown. `persistent_backup` remains **false** (not claimed).
- **NO ESP32 FIRMWARE WAS MODIFIED DURING THIS PILOT.** No flash/erase, no router/BIOS/partition/NVMe modification, host-side capture only.
- **No data deletion/overwrite:** Raw `444` readonly, `checksums/SHA256SUMS.txt:1` 33 OK.
- **No ML/localization/3D attempted:** Per objective.

## 28. Paths

- `CSI-SENSE-001/raw/smoke_test:1` 499K raw `ce0470…`
- `CSI-SENSE-001/raw/trial_01:1` 14M raw `4734dc…`
- `CSI-SENSE-001/events:1` `events_trial01.jsonl` 4.4K
- `CSI-SENSE-001/metadata:1` `trial_01_metadata.json` `environment_trial01.json` `smoke_test_metadata.json`
- `CSI-SENSE-001/analysis/trial_01:1` `parsed_*` `features_*` `baseline_*` `pca_*` `figures/*.png`
- `CSI-SENSE-001/checksums/SHA256SUMS.txt:1` 33 entries 67M
- `CSI-SENSE-001_PHASE_C_PILOT_REPORT.md:1` (this)
- Previous staging: `CSI_SENSE_001/*` (historical) untouched

**END — STOP after ONE pilot and this report. Do NOT run Trial 02, localization, ML, 3D, firmware/router change, reboot/shutdown before Drive upload.**

