> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` (SHA-256 `c72b2c4b141f415713b8aca5c7ab811870a71e4ed2c28a1094c5013372c9d835`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-SENSE-001 — RESEARCH PLAN v1.1 — Does Human Presence/Movement Produce a Measurable CSI Response?
**Status:** PLANNING ONLY — NO HARDWARE/SYSTEM/RF CHANGES EXECUTED  
**Version:** v1.1 (revision of v1.0 `CSI-SENSE-001_PLAN.md` 2026-09-06)  
**Date:** 2026-09-06 revised 2026-09-07 (Live Ubuntu 26.04.1 / Lenovo IdeaPad Gaming 3 15IAH7)  
**Prerequisite:** `CSI-VERIFY-001 PASS` — genuine live CSI verified 2026-09-06 20:56 UTC (see §0)  
**Mode:** PLAN → APPROVAL GATE → (Phases B–E only after explicit approvals — see §13)  
**Author:** planning artifact, no implementation  
**Location:** `/home/ubuntu/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (supersedes v1.0)

**Revision v1.1 changelog (four required changes, structure preserved):**
1. **Effect-size thresholds (§8.2, §9):** `Cohen's d ≥0.5`, `rank-biserial r ≥0.3` retained only as predefined **practical-effect reference thresholds** — explicitly NOT universal proof; smaller effects may still be scientifically meaningful if consistent/reproducible/distinguishable from baseline.
2. **Walking speed (§2.D, §3.1, §5.2, §10):** `0.8–1.2 m/s` demoted from rigid requirement to **reference/target only**; actual traversal time / estimated speed recorded per walking trial as metadata and treated as covariate/confounder; natural repeatable walking allowed.
3. **Persistent data / Live-USB safety (§5.5, §11, §13, §15):** New explicit **data-preservation gate BEFORE Phase C** — NO HUMAN DATA COLLECTION UNTIL PERSISTENT BACKUP HAS BEEN VERIFIED — backup procedure defined for raw/metadata/timestamps/analysis/checksums/reports; no assumption about drive existence.
4. **Proven CSI firmware (§5.1, §11, §13, §15):** Reinforced reuse of already-proven `CSI-VERIFY-001` firmware/configuration; Phase B is **host-side tooling only** unless genuine technical necessity is discovered; any firmware change requires **separate approval gate**, never automatic.

---

## 0. Provenance — What Was Actually Inspected (not assumed)

Before writing this plan, the following **proven** artifacts were read directly (read-only):

| Artifact | Path / Evidence | Key facts carried forward |
|----------|----------------|---------------------------|
| **Final Report** | `/home/ubuntu/Desktop/CSI-VERIFY-001_FINAL_REPORT.md` (265 lines, SHA `d8b669a2`) | PASS 7,152 valid CSI vectors @ 102 Hz wall / 141 Hz chip, `len 128` → 64 subcarriers I/Q, seq `5355→12506` missing 0, RSSI `-63…-52`, BSSID `8C:53:C3:5B:E1:59` Xiaomi ch1 HT20, MAC filter in `app_main.c`, rate `CONFIG_SEND_FREQUENCY 100` → 10 ms ping, jitter median 5,985 µs |
| **Gate Report** | `/home/ubuntu/Desktop/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` (224 lines) | Hardware target `esp32` confirmed, flash `4MB dio 40m`, baud 921600, pinned stack versions |
| **Raw capture** | `/home/ubuntu/Desktop/CSI_RAW_70s_921600_20260906_205638.log` (3,566,098 bytes, 21,429 lines, 7,154 occurrences, SHA `51d47ce9`) + `/tmp/csi_raw.log` + `/tmp/csi_boot.log` (36K, 68 CSI) | Concatenated `CSI_DATA` CSV without newline in fragments (`",-97,0,1CSI_DATA"` glued) — parser must handle; rate stable; first record truncated mid-stream; boot header `=============== CSI RECV ================` |
| **Firmware source** | `/tmp/csi_recv_router/main/app_main.c` (8309 B inspected 2026-09-06) + `sdkconfig.defaults` | `CONFIG_IDF_TARGET="esp32"` + `WIFI_CSI_ENABLED=y` + `CONSOLE 921600` + `MONITOR 921600` + `wifi_csi_rx_cb` with `memcmp(info->mac,ctx)` + `lltf_en true ltf_merge_en true channel_filter_en true` + `ets_printf("CSI_DATA,%d,"MACSTR"...")` header `type,id,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_format,len,first_word,data` — `len 128` for ESP32 HT20 |
| **Pinned versions** | `/tmp/esp-idf-v5.4` `296b6eab9445fd720e71aecab961e2d3fbca9944` `v5.4.4` + `/tmp/esp-csi` `8633d67152db2808f141cc1595970aa9cf406045` | Build `csi_recv_router.bin 723K SHA `ce23861e…`` `bootloader 26K SHA `7d7cf518…`` toolchain `xtensa-esp-elf 13.2.0_20240530` `esptool 4.12.0` `pyserial 3.5` `cmake 4.2.3` |
| **Capture tooling** | `/tmp/capture_csi.py` (70s `serial.Serial /dev/ttyUSB0 921600 read(4096) wb`) + `/tmp/capture_reset.py` (RTS pulse + 15s) | Proven baud 921600, raw binary `wb` no parsing, `write+flush` — reused unchanged |
| **Hardware identity** | `esptool chip_id/flash_id` logs + `iw dev wlp0s20f3 link` + `nmcli --show-secrets` | ESP32-D0WD-V3 rev3.1 MAC `f4:65:0b:56:0e:18` 40 MHz crystal / CP2102 `10c4:ea60` at `/dev/ttyUSB0` Bus 003 Port 001 driver `cp210x` / Xiaomi `Nihaal` BSSID `8C:53:C3:5B:E1:59` ch1 2412 MHz HT20 20 MHz GW `192.168.31.1` RSSI -39 dBm / Host `192.168.31.148/24` Intel AX201 |
| **No RF Vision repo** | `find / -maxdepth 6 -name README.md` found only system + `esp_csi_gain_ctrl` — no `/home/ubuntu/*Vision*` repo | Plan is standalone under `data/CSI-SENSE-001/` as proposed in §6 |

**Assumptions deliberately NOT made:** room dimensions, receiver/router distance, antenna orientation, furniture — all to be measured at collection time and recorded in metadata; human data not yet collected.

---

## 1. RESEARCH OBJECTIVE

### 1.1 Research question (exact)

> **Does a human's presence and movement produce a statistically distinguishable and repeatable CSI response compared with an empty-room baseline, under the current RF setup (Xiaomi 2.4 GHz ch1 HT20 → ESP32-D0WD-V3 csi_recv_router → 921600 baud @ ~100 Hz, len 128)?**

### 1.2 Hypotheses

- **H0 (null):** Conditional distributions of CSI measurands (amplitude per subcarrier, derived temporal variance, etc.) during human-present / movement conditions are indistinguishable from the empty-room baseline up to normal environmental variation; any observed deviation is within baseline false-positive rate and not repeatable across trials.
- **H1 (alternative, non-localizing):** At least one CSI-derived feature (e.g., amplitude variance, subcarrier temporal spread, or deviation from baseline) shows a repeatable, statistically distinguishable shift in at least one human condition (presence or movement) that exceeds baseline variation and replicates across trials.

### 1.3 Scope — what is NOT claimed

- **Not localization.** Even a PASS only shows *detectability* of presence/movement, not where the person is. §9 explicitly states PASS ≠ localization.
- **Not identification**, not counting, not through-wall, not vital signs.
- **Not ML model training** — analysis in §7 is feature characterization; any classifier is *illustrative* and not a final RF Vision model.

### 1.4 Success definition preview

Answerable by §8/§9: Is effect **distinguishable from empty**, **repeatable**, **larger than empty-room noise**, **not dominated by false positives**, and **attributable to human not confounder**?

---

## 2. EXPERIMENTAL CONDITIONS

Six controlled conditions, each with a defined purpose. Order within a trial is **fixed and contiguous** (A→B→C→D→E→F) to observe transitions; repetition across trials provides counterbalancing baseline stability, not condition shuffling (shuffling would introduce uncontrolled door/movement artifacts between conditions).

### A. EMPTY ROOM / BASELINE

- **Definition:** Room empty of humans; door closed; known static occupancy (no pets moving); all confounders as per §10 held constant.
- **Purpose:** Estimate the **noise floor** of CSI under static conditions — temporal variance, inter-packet jitter, RSSI/amp drift, subcarrier baseline mean/covariance. Serves as reference distribution for all deviation metrics. Also quantifies false-positive rate when no human present.
- **Duration:** see §3.

### B. PERSON ENTERS

- **Definition:** Continuous record while subject **crosses the room boundary** (door threshold) and moves to first stationary position (P1, see §4). Marked by event timestamps `door_open`, `threshold_cross`, `arrival_P1`.
- **Purpose:** Capture the **transient** spatial perturbation — often stronger than static occupancy. Tests whether entry produces a spike/edge distinguishable from baseline drift. Useful later for change-point detection.

### C. PERSON STATIONARY

- **Definition:** Subject stands/breathes normally at predefined position **P1** (or P2 in some trials — see geometry), facing a fixed orientation, minimal voluntary motion (no arm waving, no phone use), feet planted.
- **Purpose:** Test whether **static human body** (water, shadowing, multipath change) alone shifts CSI vs empty. Expected effect smaller than movement; its presence distinguishes true occupancy sensing from motion-only sensitivity. If only movement is detectable, result is `PARTIAL` per §9.

### D. PERSON MOVES / WALKS THROUGH DEFINED PATH

- **Definition:** Subject walks at **natural, repeatable pace** along a predefined, taped path (§4: e.g., `P1 → P2 → P3 → loop` or straight `LOS` and `NLOS` traverses). No running, no contact with devices/cables. Path includes walking across the **line-of-sight (LOS)** between router and receiver at least once per traversal. Marked with `walk_start`, `LOS_cross`, `waypoint_P2`, `walk_end`. **Actual traversal time and estimated walking speed are recorded for every walking trial** (see §3.1, §5.2) — see revision note below.
- **Purpose:** **Strongest perturbation** — dynamic multipath/Doppler. Must be clearly distinguishable if the setup is useful. Path pre-defined so spatial fingerprint can later be built from position-annotated data. Repeated traversals test repeatability.

> **v1.1 Revision — Walking speed not a rigid pass/fail:** The `0.8–1.2 m/s` normal-walking range is retained **only as a reference/target** for natural walking. It is **NOT a pass/fail requirement**. The experiment **measures what actually happened**: `walk_duration_s` (from `walk_start` to `walk_end` events) and `estimated_speed_mps = path_length_m / walk_duration_s` are logged per trial in `env_trial.json`. Variation is treated as **experimental metadata and possible covariate/confounder** (see §5.2, §7, §10). Walking should be natural and repeatable, not forced to meet a speed threshold.

### E. PERSON EXITS

- **Definition:** Subject leaves via same boundary to outside; marked `depart_P`, `threshold_cross_out`, `door_close`.
- **Purpose:** Symmetric transient to entry; tests whether CSI returns toward baseline and how quickly. Distinguishes persistent environmental drift from true human effect.

### F. POST-EXIT RECOVERY / EMPTY ROOM

- **Definition:** Room again empty, door closed, **same static state as A**, continuous recording without human re-entry.
- **Purpose:** **Recovery test** — does CSI revert to baseline distribution? If not, suggests drift/confounder rather than human. Allows measurement of hysteresis and baseline re-estimation error. Required before declaring PASS.

**Purpose summary table:**

| Condition | Tests | Later localization value |
|-----------|-------|--------------------------|
| A/F | Baseline stability, false-positive | Reference fingerprints for empty |
| B/E | Transient detectability | Change-point / entry-exit detection |
| C | Static body effect | Static fingerprint per position |
| D | Dynamic path effect | Dynamic / spatial variance map |

---

## 3. EXPERIMENT DESIGN

### 3.1 Proposed durations (justified, not arbitrary)

Justification basis: proven rate **~102 Hz wall (7,152/70s) / 141 Hz chip, median inter-arrival 5,985 µs** — i.e., ~100 CSI records per second. To estimate mean/variance reliably and to see temporal plots without aliasing, need **≥30 s** per static condition (≳3,000 records) and **≥60 s** per baseline for PCA/spectrogram stability. Walking path duration set by geometry, not time.

| Condition | Duration | Records expected (@ ~100 Hz) | Rationale |
|-----------|----------|------------------------------|-----------|
| **A EMPTY baseline** | **90 s** | ~9,000 | Longest — estimates baseline variance precisely, allows 30 s sub-window splitting for intra-baseline stability; compensates for Live USB timestamp drift |
| **B ENTER** | **~10–15 s** (event-driven) | ~1,000–1,500 | Covers door open → arrival; not time-fixed, marked by events; 10 s enough to capture transient |
| **C STATIONARY** | **60 s** | ~6,000 | Long enough for stationary variance, short enough to keep total trial <6 min and avoid fatigue |
| **D WALKING** | **~30–40 s** (2 traversals × ~15 s each) | ~3,000–4,000 | Covers 2 full loops of path; path length (see §4 ~4–6 m) at 1 m/s ~5–6 s per leg. **Reference walking speed `0.8–1.2 m/s` is target only** — actual `walk_duration_s` and `estimated_speed_mps` recorded per trial; variation analyzed as covariate, not failure. |
| **E EXIT** | **~10–15 s** | ~1,000–1,500 | Symmetric to B |
| **F RECOVERY** | **90 s** | ~9,000 | Mirrors A to test return; if A vs F differ significantly, indicates drift — trial flagged |

**Total per trial:** ~280–310 s (≈4.7–5.2 min) + 30 s inter-trial rest = **~6 min/trial**.

**Walking-speed handling (v1.1):** For each trial, `env_trial.json` records `walk_duration_s`, `path_length_m` (from §4 geometry), and `estimated_speed_mps`. Analysis (§7/§8) may include speed as covariate (e.g., correlate `amp_deviation` vs `speed`) but does not invalidate a trial whose speed falls outside `0.8–1.2 m/s` — the value is logged and interpreted, not used as a pass/fail gate. Natural repeatable walking is encouraged over artificial speed enforcement.

### 3.2 Repetitions / trials

- **Minimum `N=10` complete trials** (A→F contiguous) for repeatability claim. 10 is the smallest number allowing non-parametric within-condition variance estimation and leaving 2 trials for hold-out visual inspection without biasing statistics; larger N is better but 10 balances human fatigue, Live USB volatility, and ~60 min total collection (10 × 6 min).
- **Optional extension to `N=15`** if time permits; stopping rule pre-registered: if after N=10 effect size is marginal (`PARTIAL`), extend rather than re-analyze selectively.

### 3.3 Rest periods

- **Inter-trial rest:** 30–60 s empty-room pause, door closed, subject outside, to let CSI settle; not recorded as part of F but as separate `rest` marker. Prevents carry-over and allows timestamp re-sync.

### 3.4 Trial ordering

- **Fixed condition order within trial is A→B→C→D→E→F** — order is the experimental manipulation (arrival → stay → move → leave). Randomizing would create uncontrolled door events between conditions.
- **Trial order is repetition** — all trials identical geometry/path. No counterbalancing of conditions; instead, counterbalance **start position / facing** across trials if position sensitivity is later studied (e.g., odd trials P1 facing router, even trials P1 facing away — pre-register).

### 3.5 Avoiding confounders (summary — details §10)

- Single subject only in room; second person outside at >3 m, no movement near door.
- Door: closed during A/C/F, opened only for B/E — same door, same angle, marked.
- Fans/AC off, appliances unplugged or logged, no phone Wi-Fi hotspot, router untouched, receiver taped down, cable strain-relieved, antenna orientation fixed + photographed.
- Wi-Fi traffic: no large downloads during collection; host ping is the controlled traffic source (see §5).
- Time-of-day: all trials same session; log wall-clock and chip timestamp.
- **Walking speed:** treated as metadata/covariate per v1.1 revision — not artificially forced.

### 3.6 Event boundaries — how marked

- **Not by editing raw.** Raw `CSI_DATA` is immutable (see §5).
- **Separate event log:** operator presses key / runs `event_logger.py` that appends to `events_<trial>.jsonl` with **both UTC wall-clock (`time.time_ns()`) and last seen `seq`/`local_timestamp`** at event moment. Events: `trial_start`, `condition_A_start/end`, `door_open`, `threshold_cross`, `arrival_P1`, `walk_start`, `waypoint`, `LOS_cross`, `walk_end`, `depart`, `door_close`, `recovery_start/end`, `trial_end`, plus `note`. For walking, `walk_start` and `walk_end` are mandatory to compute `walk_duration_s`.
- **Synchronization:** event logger reads the same serial monitor timestamps if possible, else records wall-clock; post-hoc alignment via nearest `seq` within 100 ms tolerance. All events have ≥100 ms granularity — sufficient at 100 Hz (one CSI ≈6 ms).

### 3.7 Valid / invalid trial criteria (pre-registered)

A trial is **VALID** iff:

1. `CSI_DATA` continuity: **missing seq ≤1%** of expected (at ~100 Hz, >99% contiguous) AND `malformed` (parse failure) ≤0.5% — based on proven 0% missing / 0.20% malformed; higher indicates USB/serial dropout.
2. **No Wi-Fi disconnect** — gap >500 ms with zero CSI is invalid (router ping failure).
3. **No extra human movement** detected/logged during A/F/C.
4. **All event markers present** with plausible timestamps (B/E not skipped; `walk_start`/`walk_end` present for D).
5. **Channel/BSSID/len stable** — `channel==1`, `BSSID==8C:53:C3:5B:E1:59`, `len==128` for ≥99% records — change indicates router/config drift.
6. **Receiver not moved** — photo check after trial matches pre-trial.
7. **Walking-speed note:** speed outside `0.8–1.2 m/s` does **NOT** make a trial invalid — speed is logged as covariate. Only missing `walk_duration_s` or unrecorded path makes D segment incomplete.

**INVALID** trials are **retained** on disk with `invalid_reason.json` and **excluded from primary statistics** but included in an appendix sensitivity analysis to avoid selective deletion. At least **8 valid trials required** to claim PASS; if <8, collect more.

---

## 4. ROOM GEOMETRY

### 4.1 Coordinate system

- **2D Cartesian, meters, origin (0,0) at the router's projected floor point** (router is assumed wall-mounted / table height — record `z` as well).
- **X-axis along the longer wall, Y-axis along the shorter wall**, right-handed. All positions recorded to **±0.05 m** with tape measure + photo.
- **Height `z`** recorded for router and receiver (e.g., `z_router ≈1.2 m`, `z_esp ≈0.8 m`); human chest height ~1.3 m noted.

### 4.2 What must be recorded (at collection time — blank until measured)

| Element | Fields to record | Example (to be filled) |
|---------|------------------|------------------------|
| **Room** | `room_length_m`, `room_width_m`, `room_height_m`, `wall_material` (concrete/brick/drywall), `door_position` (wall + offset), `window_position`, `floor_type` | `4.2 × 3.1 × 2.8 m`, door at `x=0, y=1.0` north wall, concrete |
| **Router** | `x,y,z_m`, `orientation` (antenna vertical/horizontal), `model Mi Router 4C/R4CM`, `BSSID`, `channel 1`, `HT20`, `power` (stock) | `(0.0, 0.0, 1.2)` wall-mounted |
| **ESP32 Receiver** | `x,y,z_m`, `antenna_orientation` (PCB antenna facing), `USB cable length/routing`, `fixation` (tape weight), `MAC`, `photo filename` | `(3.5, 1.5, 0.8)` table, antenna facing router (line-of-sight), 1.0 m USB to host, taped |
| **Host laptop** | `x,y` outside LOS if possible, or same table but marked | `(3.8, 1.5, 0.8)` — host not between router↔receiver LOS |
| **Walls/furniture/large RF obstacles** | List each: `type, x1,y1,x2,y2, material, height` — include bed/desk/wardrobe/metal shelf, plus `LOS_obstructed` boolean | e.g., `desk 2.0,0.5–3.0,1.2 wood` |
| **Predefined human positions** | `P1, P2, P3` each `x,y, facing_deg` (0°=toward router) — chosen to sample LOS, NLOS, near-receiver, near-router | `P1 (1.7,1.5, facing 0°)` midpoint LOS; `P2 (3.0,2.5)` far corner NLOS; `P3 (0.8,1.5)` near router |
| **Walking path** | Ordered waypoint list `P1→P2→P3→P1` loop or `P3→P1→P2`; `path_length_m`; `LOS_cross_point` (where path intersects router–receiver line); `floor tape marks photographed` | Loop `~8 m`, LOS cross at `(1.7,1.5)` midpoint |

### 4.3 Design rationale for localization preparation

- Positions sample **LOS midpoint (strongest expected perturbation)**, **near-receiver** and **near-router** (different multipath geometry), and **NLOS corner** (weak but fingerprintable).
- Walking path **must cross LOS at least once per traversal** — this crossing is the most repeatable dynamic feature and will be annotated as `LOS_cross` for later fingerprinting.
- Furniture recorded because **static multipath** changes absolute CSI; without geometry, later fingerprinting is irreproducible.

### 4.4 Diagram (to be created at collection)

- Sketch **top-down** with dimensions, router (R), ESP (E), host (H), door, waypoints, walking arrows, LOS dashed line. Photo of actual room from two angles with visible tape marks. Stored as `metadata/room_geometry_*.jpg` + `room_geometry.json`.

---

## 5. DATA ACQUISITION

### 5.1 Reuse proven path — no firmware change (v1.1 reinforced)

- **Firmware stays** `csi_recv_router` as flashed 2026-09-06 (`ce23861e…` `7d7cf518…` ESP-IDF `v5.4.4` `296b6eab…` ESP-CSI `8633d671…`) — **no re-flash, no sdkconfig change, no router change**. This is the **already-proven CSI-VERIFY-001 firmware/configuration** and must be reused unchanged.
- **Phase B is HOST-SIDE tooling only** unless a genuine technical necessity is discovered (e.g., proven baud/regex incompatibility that prevents parsing — which has already been handled). Host-side tooling creates capture/analysis Python on the host; it does not touch ESP32 flash, router, BIOS, partitions, or internal SSD.
- **If a firmware change ever becomes necessary,** it **must become a separate approval gate** with explicit justification, risk assessment, and pinned version, and must **NOT happen automatically** as part of `CSI-SENSE-001`. No firmware modification is planned or assumed in this study.
- **If host is subject to Live reboot,** re-flash with *identical* pinned versions only after **separate approval** — never silently.
- **Router stays** `Nihaal` ch1 HT20 — **no config change**.
- **Capture stays** `921600 baud` raw `serial.Serial("/dev/ttyUSB0",921600, timeout=1)` `read(4096)` → `wb` **no parsing/filtering** during capture — identical to `/tmp/capture_csi.py` (proven 102 Hz). Only change: add event logger sidecar (see §3.6) that does NOT touch serial stream.

### 5.2 What must be preserved — per record + per trial

**Per `CSI_DATA` record (from proven header) — parsed post-hoc, never filtered during capture:**

- `type ("CSI_DATA")`, `seq (int)`, `mac (BSSID)`, `rssi (dBm)`, `rate`, `sig_mode`, `mcs`, `bandwidth` (`cwb`), `smoothing`, `not_sounding`, `aggregation`, `stbc`, `fec_coding`, `sgi`, `noise_floor`, `ampdu_cnt`, `channel`, `secondary_channel`, `local_timestamp (us, chip)`, `ant`, `sig_len`, `rx_state` (`sig_mode` in app_main), `len`, `first_word_invalid`, `data` (`[I0,Q0,I1,Q1,...]` length 128, signed int8/16 compensated by `compensate_gain`)

**Per trial — sidecar files (see §6):**

- `wall_clock_start_UTC` (`time.time_ns()`), `wall_clock_end_UTC`, `host_monotonic_ns` (for drift vs chip timestamp)
- `condition` label + `trial_number` (1…N) + `subject_id` (e.g., `S01`, anonymized) + `facing_deg`
- **Event timestamps** (`events_<trial>.jsonl`) — every §2 condition boundary + `notes`; for walking, `walk_start`/`walk_end` used to derive `walk_duration_s`
- **Environment notes:** `door_state`, `window_state`, `fan/AC`, `appliances`, `second_person_present bool`, `WiFi_extra_traffic`, `temperature_C` (if thermometer available), `notes free text`
- **Walking metadata (v1.1):** `path_length_m` (from §4), `walk_duration_s`, `estimated_speed_mps = path_length_m / walk_duration_s`, `walk_reference_range_mps: [0.8, 1.2]` (for context), `n_traversals` — speed is covariate, not pass/fail
- **Capture settings:** `baud 921600`, `port /dev/ttyUSB0`, `CONFIG_SEND_FREQUENCY 100`, `capture_script_version`, `pyserial version`
- **Checksums:** `SHA256 raw.log`, `SHA256 events.jsonl`

### 5.3 RAW invariant

```
RAW DATA MUST NEVER BE MODIFIED.
```
- Raw `*.log` written once as binary; any analysis works on **copies** or parsed `*.csv`/`*.npz`. No in-place editing, no line deletion, no re-encoding that drops bytes (keep `\r\n` exactly). Even concatenated `CSI_DATA` glued fragments are preserved — parser handles them post-hoc. **Raw must never be overwritten** — file permissions set read-only after trial; any derived file is a separate copy.

### 5.4 Sampling justification

At ~100 Hz, 90 s baseline yields ~9k points per trial → 90k across 10 trials → sufficient for stable covariance (64 subcarriers) and PCA (need ≫64 samples). Shorter would make variance estimates noisy; longer would increase trial fatigue and Live USB fill (≈3.6 MB per 70s → 90s ≈4.6 MB/trial → 10 trials ≈46 MB raw + parsed ≈100 MB — well within `/tmp 7.7G`).

### 5.5 Persistent data / Live-USB safety — preservation gate (v1.1 new)

**Context:** Host is currently Live Ubuntu (`/cow` overlay, `/tmp` tmpfs — volatile). Irreplaceable research data (raw CSI, metadata, timestamps) must not be collected until a **persistent, verified backup destination** exists. This section defines the gate.

**Rule:**

```
NO HUMAN DATA COLLECTION UNTIL PERSISTENT BACKUP HAS BEEN VERIFIED.
```

**What must be verified BEFORE Phase C:**

1. **Identify persistent destination** — actual available storage inspected at that time (do **not** assume a particular drive exists now). Candidate is any persistent, non-volatile filesystem that survives reboot: e.g., external USB SSD/HDD, second internal partition that is **not** the Live overlay, or network storage — to be verified live before Phase C (see `lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL` + `df -hT` + `findmnt` + write test).
2. **Write test:** `dd` / `fallocate` + `sha256sum` round-trip (write 100 MB, read back, verify SHA) proves destination is writable and persistent across remount (not `/cow`/`tmpfs`/`overlay`).
3. **Backup procedure to be executed after each trial (and verified before next trial):**

| Artifact to preserve | Source | Destination (persistent) | Verification |
|----------------------|--------|--------------------------|-------------|
| Raw CSI captures | `raw/trial_XX/*_raw.log` | `<persistent>/CSI-SENSE-001/raw/trial_XX/` | `sha256sum` source == dest, log in `checksums.sha256` |
| Metadata (study/room/hardware/firmware/capture) | `metadata/*.json` | `<persistent>/CSI-SENSE-001/metadata/` | `sha256sum` + JSON schema validation |
| Event timestamps | `raw/trial_XX/events_trialXX.jsonl` | `<persistent>/.../raw/trial_XX/` | `sha256sum` + event count check |
| Environment notes | `raw/trial_XX/env_trialXX.json` | same | same |
| Analysis outputs | `analysis/figures/*`, `analysis/stats/*.json` | `<persistent>/CSI-SENSE-001/analysis/` | `sha256sum` + file count |
| Reports | `CSI-SENSE-001_FINAL_REPORT.md` (+ Desktop copy) | `<persistent>/CSI-SENSE-001/` + secondary copy | `sha256sum` |
| Aggregate checksums | `checksums.sha256` (recursive) | `<persistent>/checksums.sha256` | `sha256sum -c checksums.sha256` must pass |

   - Backup is **incremental and atomic**: copy trial folder, verify SHA, then mark `backup_verified: true` in `env_trial.json`; never move (keep source until backup verified).
   - **Raw is never overwritten or modified** — destination is a **copy**; source files set `chmod a-w` after write; any re-analysis uses copy or parsed derivative.

4. **Second copy recommended** (if two devices available): one external USB + one network/cloud, but at minimum one verified persistent copy before proceeding. If only one persistent device exists, it must be explicitly identified and its free space confirmed (`≥5 GB` for 10 trials + analysis) before Phase C.

5. **Gate check before Phase C:** The checklist in Phase C approval (§13) must include: `persistent_destination_path`, `filesystem`, `size/avail`, `write_test_sha_match: true`, `backup_procedure_tested: true`. If any check fails, **Phase C does not start**.

**Do not assume a particular external drive exists now.** The plan requires us to **verify the actual available persistent storage before Phase C** — the persistent path is determined at that time and recorded in `study_metadata.json: {persistent_backup_path, filesystem, verified_utc}`.

---

## 6. DATASET STRUCTURE

### 6.1 Directory layout (proposed, not yet created)

```
data/
  CSI-SENSE-001/                         # Study ID — date-stamped at first collection
    README.md                             # §14 — study description, hardware, how to reproduce
    PROTOCOL.md                           # §14 — this plan's §2–§5 as executable protocol
    metadata/
      study_metadata.json                 # §6.2 schema — study-wide (includes persistent_backup_path after gate)
      room_geometry.json                  # §4 — coordinates
      room_geometry_photo_01.jpg
      room_geometry_photo_02.jpg
      firmware_versions.json              # §11 — pinned SHAs
      capture_config.json                 # baud, rate, channel, etc.
      hardware_identity.json              # ESP32 MAC, flash ID, router BSSID
    raw/                                  # NEVER MODIFY — set a-w after write
      trial_01/
        CSI-SENSE-001_20260907T14-00-00_trial01_raw.log        # raw serial binary
        CSI-SENSE-001_20260907T14-00-00_trial01_raw.sha256
        events_trial01.jsonl                                   # event markers
        env_trial01.json                                       # environment notes + walking speed + backup_verified
        parsed_trial01.csv                # parsed CSI (copy, derived — may be rebuilt)
        parsed_trial01.npz                # numpy arrays (amplitude, phase, etc. derived)
      trial_02/ ...
      ...
      trial_10/ ...
    baseline/                             # Symlinks or derived views (optional convenience)
      # symlinks to raw/trial_*/ segments where condition==A
    enter/
      # segments B
    stationary/
      # segments C
    walking/
      # segments D
    exit/
      # segments E
    recovery/
      # segments F
    analysis/                             # Outputs — not raw
      figures/
        timeseries_trial01.png
        pca_baseline_vs_stationary.png
        spectrogram_walking.png
        subcarrier_variance_heatmap.png
      stats/
        deviation_from_baseline.json
        statistical_tests.json
        false_positive_baseline.json
      analysis_config.json               # §11 — committed before D
    checksums.sha256                      # recursive SHA of all raw/ files
    BACKUP/                               # mirror on persistent destination (see §5.5) — not in volatile /tmp
```

**Alternative flat:** If symlinks are cumbersome, `raw/trial_XX/` holds everything and `analysis/` produces `segments/` views via indices without duplicating bytes.

### 6.2 Metadata schema (JSON, pre-registered)

**`study_metadata.json` (study-wide):**
```json
{
  "study_id": "CSI-SENSE-001",
  "research_question": "Does human presence/movement produce distinguishable CSI response vs empty baseline?",
  "prerequisite": "CSI-VERIFY-001 PASS 2026-09-06",
  "created_utc": "2026-09-07T14:00:00Z",
  "host": {"model": "Lenovo 82S9", "os": "Ubuntu 26.04.1", "kernel": "7.0.0-30", "cpu": "i5-12450H"},
  "firmware": {"esp_idf": "v5.4.4 296b6eab9445...", "esp_csi": "8633d67152...", "app": "csi_recv_router", "bin_sha256": "ce23861e...", "bootloader_sha256": "7d7cf51...", "proven_reused": true, "firmware_change": "none — host-side only unless separate approval"},
  "hardware": {"esp32_chip": "ESP32-D0WD-V3 rev3.1", "esp32_mac": "f4:65:0b:56:0e:18", "flash": "4MB 0x68:0x4016 dio 40m 4MB", "bridge": "CP2102 10c4:ea60 /dev/ttyUSB0", "router_model": "Xiaomi Mi Router 4C/R4CM", "router_bssid": "8C:53:C3:5B:E1:59", "router_ssid": "Nihaal", "channel": 1, "freq_mhz": 2412, "bandwidth": "HT20 20MHz"},
  "capture": {"baud": 921600, "config_send_frequency": 100, "expected_rate_hz_wall": 102, "expected_rate_hz_chip": 141, "proven_len": 128, "proven_subcarriers": 64},
  "geometry_ref": "metadata/room_geometry.json",
  "persistent_backup": {"path": null, "filesystem": null, "size_avail_gb": null, "write_test_sha_match": null, "verified_utc": null, "second_copy_path": null},
  "n_trials_planned": 10,
  "trial_duration_s": {"A": 90, "B": 12, "C": 60, "D": 35, "E": 12, "F": 90, "inter_trial_rest": 30},
  "walking": {"reference_range_mps": [0.8, 1.2], "reference_is_target_only": true, "actual_speed_recorded_per_trial": true, "speed_is_covariate_not_gate": true},
  "ethics": {"human_consent": true, "anonymized_subject_id": "S01"}
}
```

**`room_geometry.json`:**
```json
{
  "coordinate_origin": "router floor projection",
  "units": "meters",
  "room": {"length_m": null, "width_m": null, "height_m": null, "wall_material": null, "door": {"wall": null, "offset_m": null}, "window": null},
  "router": {"x_m": 0.0, "y_m": 0.0, "z_m": null, "orientation": null, "photo": null},
  "esp32": {"x_m": null, "y_m": null, "z_m": null, "antenna_orientation": null, "usb_cable_m": null, "fixation": null, "photo": null},
  "host": {"x_m": null, "y_m": null},
  "furniture": [{"type": null, "x1": null, "y1": null, "x2": null, "y2": null, "material": null}],
  "human_positions": {"P1": {"x_m": null, "y_m": null, "facing_deg": null}, "P2": {}, "P3": {}},
  "walking_path": {"waypoints": ["P1","P2","P3"], "path_length_m": null, "los_cross_xy": null, "tape_photo": null}
}
```

**`events_trial01.jsonl` (one JSON per line):**
```json
{"event":"trial_start","wall_clock_ns": 1725736800000000000,"chip_seq":5355,"chip_timestamp_us":46969717,"condition":"A","note":"door closed empty"}
{"event":"condition_A_end","wall_clock_ns":...,"chip_seq":...}
{"event":"door_open","wall_clock_ns":...,"chip_seq":...}
{"event":"threshold_cross_in","wall_clock_ns":...}
{"event":"arrival_P1","wall_clock_ns":...}
{"event":"walk_start","wall_clock_ns":...,"chip_seq":...}
{"event":"LOS_cross","wall_clock_ns":...}
{"event":"walk_end","wall_clock_ns":...,"chip_seq":...}
{"event":"depart","wall_clock_ns":...}
{"event":"door_close","wall_clock_ns":...}
...
```

**`env_trial01.json` (v1.1 — includes walking speed + backup flag):**
```json
{
  "trial": 1,
  "subject_id": "S01",
  "facing_deg": 0,
  "door": "closed_A",
  "window": "closed",
  "fan": "off",
  "ac": "off",
  "second_person": false,
  "wifi_extra_traffic": "none",
  "temperature_c": 28,
  "walking": {
    "path_length_m": 8.0,
    "walk_duration_s": 34.2,
    "estimated_speed_mps": 0.23,
    "reference_range_mps": [0.8, 1.2],
    "reference_is_target_only": true,
    "n_traversals": 2
  },
  "backup_verified": true,
  "backup_persistent_path": "/media/ubuntu/ExternalCSI/CSI-SENSE-001/raw/trial_01",
  "notes": "Natural walking, no artificial speed enforcement",
  "valid": true,
  "invalid_reason": null
}
```

All JSON schemas versioned (`schema_version: "1.0"`).

---

## 7. ANALYSIS PIPELINE — Before Implementation

Pipeline is **read-only on raw**, writes to `analysis/`. Order matters: integrity first, then features, then statistics.

### 7.1 Stage 1 — Raw CSI integrity (per trial, per condition)

- **Parse:** Reuse proven regex (10 fields before noise): `CSI_DATA,seq,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec,sgi,noise,ampdu,channel,secondary,timestamp,ant,sig_len,rx_state,len,first_word,"[I0,Q0,...]"` — handle glued `CSI_DATA` without newline via `re.finditer` on binary-decoded text.
- **Counts:** `total_occurrences`, `valid_parsed`, `malformed`, `malformed_rate`, `seq_missing`, `seq_continuity` (7151/7151 proven).
- **Field stability:** `len` must be 128 for ≥99% (proven 100%); `channel==1`, `BSSID==8C:53:C3:5B:E1:59` for ≥99%; `rate/noise_floor` drift; `sig_len` outliers logged.
- **Continuity:** `inter_arrival = diff(local_timestamp)` — mean/median/min/max/stdev; gap >100 ms flagged; wall-clock vs chip timestamp drift (proven chip diff 50.76s vs wall 70s — chip wraps at reboot).
- **Walking-speed check:** Verify `walk_duration_s` present for D; if missing, D segment incomplete — flag but not invalid gate (see §3.7).
- **Health gate:** If trial fails §3.7 validity, flag `invalid` but keep.

### 7.2 Stage 2 — Subcarrier / I/Q features (per packet)

- **Decompose `data`:** 128 ints → 64 subcarriers ×2: `I_k = data[2k]`, `Q_k = data[2k+1]` for `k=0..63`.
- **Amplitude (correct):** `amp_k = sqrt(I_k² + Q_k²)` — **NOT raw I or Q**. Mean amplitude per packet = `mean_k amp_k`; also per-subcarrier series `amp_k(t)`.
- **Phase (detrended):** `phase_k = atan2(Q_k, I_k)` (radians, wrapped `(-π,π]`). **Do not overinterpret raw phase** — it contains CFO/SFO/phase offset. For analysis: (a) unwrap (`numpy.unwrap`), (b) remove linear trend across subcarriers per packet (fit `phase_k ≈ a·k + b`, subtract — common sanitization), (c) report both raw and detrended; analyze phase variance only after detrending.
- **Zeros / nulls:** Count `amp_k==0` (≈20–23 proven at DC/null subcarriers) — track per-subcarrier mask of permanently zero subcarriers (exclude from PCA).
- **Visualization:** Heatmap `amp_k` vs packet index (subcarrier × time) — baseline should show stable bands, walking should show vertical streaks.

### 7.3 Stage 3 — Temporal variance & deviation from baseline

- **Baseline model:** From condition A (90s) compute per-subcarrier **baseline mean `μ_k` and stdev `σ_k`** (and covariance `Σ` 64×64) — use at least 3k samples (proven 9k available) for stable estimate. Also sub-window baseline (split A into 3×30s) to estimate **intra-baseline variance** (empty-room drift).
- **Deviation metrics per packet (or per 0.5 s window):**
  - `amp_deviation(t) = sqrt( Σ_k (amp_k(t) - μ_k)² )` (Euclidean distance from baseline mean)
  - `mahalanobis(t) = sqrt( (amp(t)-μ)ᵀ Σ⁻¹ (amp(t)-μ) )` — if Σ invertible (regularize with `+ εI`).
  - Per-subcarrier z-score `z_k(t) = (amp_k(t)-μ_k)/σ_k`.
  - `temporal_variance` sliding window (1 s, 0.5 s overlap) stdev of `amp_k` — walking should raise variance.
  - `subcarrier_correlation` matrix per condition — compare A vs D via correlation distance.
- **Covariate analysis (v1.1):** For walking trials, correlate `amp_deviation` / `temporal_variance` with `estimated_speed_mps` across trials (e.g., Spearman) to assess whether speed explains part of walking effect — speed is covariate, not gate.
- **RSSI comparison:** Plot RSSI(t) alongside `amp_deviation(t)` — RSSI is coarse, often less sensitive than CSI amplitude; used as baseline comparison, not success criterion.

### 7.4 Stage 4 — Dimensionality & frequency

- **PCA:** Fit PCA on baseline `amp` matrix (N×64). Project all conditions onto PC1/PC2 — expect A/F cluster, C shifted, D spread along PC1 if human effect exists. Report explained variance, loadings to identify **which subcarriers carry strongest human signal** (answer §8 Q5).
- **Spectrogram / time-frequency:** For walking, compute **spectrogram of `amp_deviation(t)`** or of a mid subcarrier `amp_k(t)` via STFT (e.g., 2 s window, 90% overlap) — walking should introduce 0.5–2 Hz energy not present in stationary. This is exploratory, not thresholded.
- **Temporal plots:** For each trial, overlay `A/C/D/F` segments on same time axis: `amp_deviation`, `RSSI`, `seq continuity`, `event markers` (including `walk_duration` bar) — visual distinguishability is a required success check (§9) before statistics.

### 7.5 Stage 5 — Environmental / noise variation

- **Baseline drift:** Compare `A` vs `F` per trial (both empty) — if drift > effect size, trial is confounded.
- **Noise floor tracking:** `noise_floor` is -97 proven stable; any drift indicates RF environment change — logged.
- **Null subcarrier monitoring:** Truly null subcarriers should stay near-zero; variation there indicates receiver gain change not human.

**Amplitude/phase correctness note (required by §7):** All amplitude results derived from `sqrt(I²+Q²)`; phase results shown only after detrending/unwrapping and accompanied by disclaimer that absolute phase is hardware-offset-contaminated and only *relative* phase variance is interpretable.

---

## 8. STATISTICAL EVALUATION — Objective Tests

Principle: **No test chosen until distribution inspected.** Plan prescribes *procedure* not a fixed p-value threshold; all choices logged in `analysis/stats/statistical_tests.json` with rationale and correction. **Effect-size thresholds are references, not proof — see §8.2.**

### 8.1 Questions to answer (from prompt)

| Q | Test approach (data-dependent) | What is compared |
|---|--------------------------------|------------------|
| **Q1: Is human presence distinguishable from empty?** | Compare `amp_deviation` (or PC1 score, or windowed variance) distribution for **A (empty)** vs **C (stationary)** pooled across trials, per trial, and per-subcarrier. First inspect normality (Q-Q, Shapiro-Wilk on baselines — but not relied upon at small N); if approximately normal, Welch's t-test or paired t per trial; else **Mann-Whitney U** (unpaired A vs C windows) or **Wilcoxon signed-rank** (if paired windows). Report **effect size** (Cohen's d or rank-biserial r) and **confidence interval**, not just p. | Human body static effect |
| **Q2: Is movement distinguishable from stationary?** | Compare **C (stationary)** vs **D (walking)** same metrics + `temporal_variance` and `spectrogram energy 0.5–2 Hz`. Movement expected larger variance, so test windowed variance distribution. Same distribution-dependent choice; movement vs stationary often highly non-normal → Mann-Whitney. Also test correlation of effect with `estimated_speed_mps` (v1.1 covariate). | Dynamic vs static |
| **Q3: Repeatable across trials?** | Compute **per-trial effect** (median `amp_deviation` C vs A) for each of 10 trials; test consistency via **intra-class correlation (ICC)** or simply **sign test** (how many trials show same direction). Repeatability = ≥8/10 trials show same sign and overlapping CI; report trial-wise effect sizes, not just pooled. | Replication |
| **Q4: Larger than empty-room variation?** | Compare **D/C deviation vs intra-baseline variation**: compute **empty-room false-positive deviation** by splitting A into sub-windows (or A vs F) and measuring same `amp_deviation`; human effect must exceed **95th percentile of empty-empty deviation** (empirical threshold, not arbitrary — derived from baseline). Also compare `F vs A` to ensure recovery. | Signal vs noise |
| **Q5: Which subcarriers/features strongest?** | Per-subcarrier **z-score** and **PCA loadings**; rank subcarriers by `|μ_C - μ_A|/σ_A` (standardized mean difference). Report top 10 subcarriers with CI; visualize heatmap of `|z_k|` across k. Also check correlation matrix change `‖Corr_A - Corr_D‖`. | Feature locality |
| **Q6: False-positive during baseline?** | Measure **false-positive rate** when applying same detection threshold (e.g., `amp_deviation > p95(A)`) to **held-out baseline windows** (leave-one-trial-out A). Report FP rate (should be ≈5% if threshold p95). If FP ≫5%, threshold is invalid. | Baseline reliability |

### 8.2 Procedure (not fixed test prescription)

1. **Inspect** — Q-Q plots, histograms of `amp_deviation` for A per trial; test normality only as diagnostic, not gate.
2. **Choose** — If normal + equal variance → parametric; else non-parametric. Document choice per Q.
3. **Correct** — Multiple subcarriers (64) → **Benjamini-Hochberg FDR** (not Bonferroni overly conservative) or limit to PCA 3 PCs to reduce multiplicity; report uncorrected and corrected.
4. **Effect size first — with reference thresholds, not absolute proof:** Report effect size and CI as primary. **Predefined practical-effect references:** `Cohen's d ≥0.5` (medium) and `rank-biserial r ≥0.3` (medium) are **reference thresholds for practical significance** (see §9), **NOT universal scientific proof of success/failure**. **Smaller effects may still be scientifically meaningful if they are consistent, reproducible, and distinguishable from baseline/environmental variation** (§9.2 PARTIAL explicitly allows `d <0.5` with significance + consistency). A `p<0.05` with tiny effect but highly reproducible and above baseline 95th percentile is not automatically dismissed — it is classified per §9 with effect size reported and interpreted. Conversely, a large `d` that is inconsistent or indistinguishable from baseline drift is not PASS.
5. **Visual + statistical** — Both must agree; a significant p without visible separation in temporal plots is flagged as potential artifact.
6. **Walking-speed covariate (v1.1):** For Q2 (walking vs stationary), also report whether walking effect correlates with `estimated_speed_mps`; if speed varies, it may explain part of variance — include as covariate, not as failure gate.

### 8.3 Power / sample size justification

At ~100 Hz, each 60 s stationary segment gives ~6k correlated samples — effective independent samples far fewer (coherence ~100 ms → ~600 independent). With 10 trials, total independent ≳6k per condition — adequate for non-parametric detection of moderate effect (`d≈0.5`) with high power, but formal power analysis deferred until pilot variance (A's stdev) measured; plan states achieved power will be reported post-hoc.

---

## 9. SUCCESS CRITERIA

Defined per prompt, with added quantitative guardrails that are **data-derived, not arbitrary**, and require **both statistical and visual** confirmation. **Effect-size thresholds are references, not absolute gates — see §9.1 note.**

### PASS

Human presence/movement produces a **statistically and visually distinguishable and repeatable CSI response** vs baseline, meaning ALL of:

1. **Visual:** Temporal plots show clear separation — `amp_deviation`/`PC1` during C and especially D is visibly elevated outside A's band for majority of time, and walking `LOS_cross` moments show spikes, with recovery F returning toward A (see §7.3).
2. **Statistical:** Per §8 Q1 or Q2, effect vs A is **significant under chosen test** (documented distribution-appropriate) **and** confidence interval excludes zero. **For practical significance, predefined references `Cohen's d ≥0.5` or `rank-biserial r ≥0.3` are used as guides** — meeting them strengthens PASS but **not strictly required if effect is smaller yet consistent/reproducible/distinguishable per §8.2 point 4**. Smaller effects with narrow CI and repeatability may still be PASS if they exceed baseline variation (§9.1 note).
3. **Repeatable:** Same direction effect in **≥8/10 valid trials** (§3.7) — not pooled-only significance driven by 1–2 trials.
4. **Above noise:** Median human deviation exceeds **95th percentile of empty-empty variation** (A sub-window vs A) — i.e., larger than normal baseline fluctuation — and **F vs A** shows recovery (no persistent drift).
5. **False-positive low:** Baseline false-positive rate (Q6) ≤10% when thresholded at human effect level.

> **v1.1 Note — Effect-size thresholds are reference, not proof:** `d ≥0.5` / `r ≥0.3` are **practical-effect references** (Cohen's conventions) for planning and reporting, **not universal scientific proof** of success/failure. A `d = 0.35` that is highly significant, reproducible in ≥8/10 trials, visible, and above baseline 95th percentile is scientifically meaningful and may be classified as PASS if all other guards hold — with effect size explicitly reported as smaller-than-medium. Conversely, a `d ≥0.5` that is inconsistent or indistinguishable from drift is not PASS. The distinction is documented per trial in the final report.

**PASS does NOT mean localization.** It only enables Phase “localization research next” — no position estimate claimed.

### PARTIAL

A measurable effect exists but **fails one PASS guardrail**, e.g.:

- Only **movement (D)** is distinguishable, while **stationary (C)** vs A is not (motion-sensitive but not presence-sensitive).
- Effect is **statistically significant but small** (`d <0.5`) and **partially consistent** (5–7/10 trials) — meaningful but weak/inconsistent (per v1.1, small `d` alone does not define PARTIAL; it is the combination of small + inconsistency).
- Effect **visible but not statistically robust** after FDR correction.
- Effect **present but baseline drift (A vs F) is comparable** — confounded.

### FAIL

No reproducible human-associated effect can be distinguished from environmental variation, i.e.:

- No visual separation and **no significant effect** under appropriate test, or significant only in pooled but not per-trial, or effect indistinguishable from empty-empty variation, or false-positive rate ≈ detection rate.

**Reporting:** All three outcomes include full statistics, plots, effect sizes with CIs, walking-speed covariate, and per-trial appendix; `PARTIAL`/`FAIL` still valuable for determining whether multi-receiver or different geometry needed. Small-but-consistent effects are explicitly reported as meaningful even if below reference thresholds.

---

## 10. SCIENTIFIC CONTROLS — Confounders & Mitigations

| Confounder | Why it matters | Mitigation / Logging |
|------------|----------------|----------------------|
| **Other people moving nearby** (outside door, next room) | Adds RF perturbation indistinguishable from subject | Single subject inside; second person stays >3 m outside, stationary, logged; door closed; note any corridor traffic in `env_trial.json` notes |
| **Doors/windows** | Opening changes multipath even without human | Door state fixed: closed A/C/F, opened only B/E — same angle — logged `door_open/close`; windows closed + logged |
| **Fans, AC, mechanical motion** | Periodic Doppler mimics human | Fans/AC **off** during all trials; if unavoidable, logged + same state all trials |
| **Appliances (microwave 2.4 GHz, kettle, etc.)** | Burst RF / power-line noise | Unplug or power off all non-essential 2.4 GHz devices; log any appliance on/off; collect at same time-of-day without cooking |
| **Wi-Fi traffic variation** | Rate depends on ping success; extra traffic changes CSI rate | **No large downloads/streaming** during trials; host ping is controlled source (`100 Hz`); log `seq` gaps and `rate` field; if extra traffic needed, log SSID |
| **Router rate variation** | `CONFIG_SEND_FREQUENCY 100` → 10 ms, but observed 6 ms median with jitter | Record `local_timestamp` inter-arrival per trial; if rate drops >20% vs proven 102 Hz, flag trial invalid |
| **Receiver movement / cable movement** | Moving ESP or cable changes CSI as much as human | ESP **taped** to table/shelf with weight, photo before/after; USB cable strain-relieved with tape, **no touch** during trial; operator does not approach ESP |
| **Antenna orientation** | ESP32 PCB antenna is directional; rotation changes RSSI/CSI | Orientation fixed (e.g., antenna facing router along LOS), photographed, marked with tape arrow; not changed between trials |
| **Environmental changes (temperature, humidity, furniture moved)** | Drift changes baseline | All trials same session (≤90 min); room not rearranged; log temperature; furniture list fixed (§4) |
| **Timing errors** | Event marker drift → misaligned condition segments | Event logger uses both `wall_clock_ns` and `chip_seq`; sync tolerance 100 ms; validate event order; reject trials with >2 s event gap anomaly |
| **Host CPU / USB buffer** | Host lag could drop CSI records | Proven `read(4096) wb` loop; monitor CPU idle; `malformed` rate >0.5% flags trial; keep host on AC power |
| **Subject variability (clothing, height, phone)** | Affects scattering | Subject wears same clothing, no phone/Wi-Fi device on body during trials; height/weight logged once anonymized |
| **Walking-speed variation (v1.1)** | Speed changes Doppler/multipath intensity | **Not controlled to rigid range** — `0.8–1.2 m/s` is reference only; **record `walk_duration_s` and `estimated_speed_mps` per trial** (see §5.2); treat as covariate in §7/§8 Q2; natural repeatable walking encouraged; do not artificially force speed |
| **Multipath from subject outside LOS** | Even outside room, human near wall affects CSI | Subject waits outside at fixed distance (>3 m) during A/F, not pacing near wall; logged |
| **Live-USB volatility (v1.1)** | Volatile `/cow`/`/tmp` loss before backup | **Gate §5.5**: persistent destination verified before any human data; per-trial backup + SHA verified; no overwrite of raw; second copy if available (see §5.5) |

**Logging strategy:** Every confounder has a **field in `env_trial.json` or event note** — if a mitigation fails, it is not hidden but analyzed as covariate (e.g., compare trials with/without fan, or correlate speed vs deviation).

---

## 11. REPRODUCIBILITY

Must be sufficient for an independent analyst to recreate study and verify results from raw only.

| Item | Exactly what to record | Where |
|------|------------------------|-------|
| **Firmware/software (proven reused)** | `ESP-IDF v5.4.4 296b6eab9445…` (git rev-parse), `ESP-CSI 8633d67152…`, `app commit SHA`, `build bins SHA` (`ce23861e…` `7d7cf518…`), `sdkconfig.defaults` full text, `python 3.14.4`, `pyserial 3.5`, `esptool 4.12.0`, `cmake 4.2.3`, `numpy/scipy/matplotlib versions` — **noted as reused proven CSI-VERIFY-001 firmware, no modification unless separate gate** | `metadata/firmware_versions.json` + `capture_config.json` |
| **Firmware change policy (v1.1)** | If firmware change ever needed: separate approval with justification + new pinned SHAs + `firmware_change.json` with reason | Only if triggered — not planned |
| **Hardware identity** | `ESP32-D0WD-V3 rev3.1 MAC f4:65:0b:56:0e:18` `flash 4MB 0x68:0x4016`, `CP2102 10c4:ea60 S/N 0001`, `Xiaomi model BSSID 8C:53:C3:5B:E1:59`, `host Lenovo 82S9 BIOS JMCN48WW` | `metadata/hardware_identity.json` |
| **Room geometry** | §4 full coordinates, photos, tape marks | `metadata/room_geometry.json` + `.jpg` |
| **Capture settings** | `port /dev/ttyUSB0`, `baud 921600`, `CONFIG_SEND_FREQUENCY 100`, `capture_script SHA`, `event_logger version`, `wall_clock` (UTC ISO8601) + `monotonic_ns` + `chip local_timestamp` | Per-trial `env_trial.json` + `events.jsonl` header |
| **Walking metadata (v1.1)** | `path_length_m`, `walk_duration_s`, `estimated_speed_mps`, `reference_range [0.8,1.2]` (target only) | `env_trial.json:walking{}` per trial |
| **Timestamps** | Both `wall_clock_ns` (host UTC, NTP-synced if possible, note offset) and `local_timestamp_us` (chip) + `seq` per CSI | Per CSI record + per event |
| **Trial IDs** | `trial_01`…`trial_N`, `subject_id S01` anonymized, `condition` labels A–F, `repetition` index | Directory + file names + JSON |
| **Dataset naming** | `CSI-SENSE-001_YYYYMMDDThh-mm-ssZ_trialXX_raw.log` where timestamp is **wall-clock at `trial_start` UTC**; `events_trialXX.jsonl`; `env_trialXX.json` | §6 layout |
| **Checksums** | `SHA256` of every raw `.log` (per file + aggregate `checksums.sha256`), also `SHA256` of parsed `.csv` + `events` | `raw/trial_XX/*.sha256` + root `checksums.sha256` (run `sha256sum raw/trial_*/* > checksums.sha256`) |
| **Persistent backup (v1.1)** | `persistent_backup_path`, `filesystem`, `size_avail_gb`, `write_test_sha_match`, `verified_utc`, `backup_verified per trial` | `study_metadata.json:persistent_backup` + `env_trial.json:backup_verified` |
| **Analysis config** | `analysis_config.json`: `python version`, `library versions`, `random seed` (e.g., 42), `window sizes`, `PCA components`, `STFT params`, `statistical test chosen per Q with rationale`, `FDR method`, `effect-size reference thresholds d≥0.5 r≥0.3 noted as reference not proof` | `analysis/analysis_config.json` (committed before analysis to avoid p-hacking) |
| **Raw preservation** | **Never modified or overwritten** — raw kept read-only (`chmod a-w`), parsed copies only; retention: raw kept indefinitely, backed up to persistent + optional cloud | Filesystem perms + README + §5.5 procedure |

All files text-based or binary with SHA; study can be re-run from `raw/` alone (persistent copy).

---

## 12. FUTURE LOCALIZATION VALUE — Without Claiming It Now

This experiment **does not claim localization**, but it **creates the reusable foundation** for it.

| Measurement collected now | How it enables future localization |
|---------------------------|------------------------------------|
| **Per-subcarrier amplitude `amp_k(t)` at known positions P1/P2/P3** | **Spatial fingerprinting** — `μ_k(P)` mean vector per position is a fingerprint; future k-NN or Bayesian classifier compares live `amp(t)` to stored fingerprints. Quality depends on now-measured separation C vs A and stability across trials |
| **Walking path with `waypoint` + `LOS_cross` timestamps + speed** | **Position-dependent CSI time series** — path data plus now-recorded `estimated_speed_mps` is a dense spatial sample with speed covariate; can later train **position-regression** (`amp(t) → x,y`) or **trajectory** models accounting for speed; now only used to show movement effect |
| **Per-subcarrier variance / correlation / PCA loadings** | Tells **which subcarriers are most informative** — future models can weight/select top-k subcarriers (Q5), reducing dimensionality from 64→10 and improving robustness |
| **Baseline covariance `Σ` and intra-baseline drift** | **Calibration model** — future localization needs baseline subtraction/normalization; `Σ` from now is the normalization basis; if drift large, future work knows to re-calibrate per session |
| **Recovery F vs A** | **Environment drift model** — future long-term deployment must handle drift; now measures hysteresis |
| **Single-receiver LOS geometry** | **Designs multi-receiver experiments** — if single receiver gives only `PARTIAL` (movement-sensitive), the next step is **second/third ESP32 at orthogonal LOS** (triangulation) — geometry file from now makes placement reproducible; data format already supports adding `receiver_id` field |
| **Event-synchronized timestamps + valid/invalid criteria** | **Training data pipeline** — future supervised learning needs clean labeled segments; now validates that event alignment works at 100 ms accuracy and that validity gates keep label noise low |

**Explicit NOT now:** no position estimate, no accuracy claim (e.g., “1 m”), no heatmap UI, no trained classifier evaluated as localization — any such claim would be rejected. The next milestone after this study would be `CSI-LOCATE-001` which uses the fingerprints above.

---

## 13. IMPLEMENTATION PLAN — Explicit Phase Distinction (v1.1)

> **Phases are strictly separate. Phase B does not perform the human experiment. Phase C requires a separate explicit approval after tooling review + geometry + environment + backup verification. Approvals must not be collapsed.**

| Phase | What | Requires explicit approval? | What would happen |
|-------|------|------------------------------|-------------------|
| **PHASE A — Research planning** | This document (`CSI-SENSE-001_PLAN_v1.1.md`), inspection of proven setup, no RF/system changes | **DONE (this file)** — review gate | Read-only inspection (§0); write only planning markdown; no flash/capture |
| **PHASE B — Host-side capture/analysis tooling** | Build **host-side** capture & analysis tooling **only** | **YES — Approval after reviewing this v1.1 plan** (`CSI-SENSE-001 — APPROVED for Phase B`) | Create files (see §14) — `capture/` Python scripts (reuse + add event logger + backup verifier), `analysis/` Python (parse, amp/phase, PCA, plots, stats with speed covariate), `metadata/` schemas; **no ESP flash, no router change, no human data, no data collection**; code + schema review on host only. Firmware **not** modified. |
| **PHASE C — Controlled human data collection** | Execute N=10 trials A→F per §3/§4/§5 | **YES — Separate explicit approval AFTER:** (1) Phase B tooling reviewed, (2) room geometry recorded (§4), (3) experimental environment ready (§10), **(4) persistent backup verified (§5.5)** — `CSI-SENSE-001 — APPROVED for Phase C` | Operator + subject perform trials with live CSI logging per §5; files written to `data/CSI-SENSE-001/raw/` and **immediately backed up to verified persistent destination per §5.5**; no firmware flash (identical re-flash only if Live reboot and only after its own gate); human participation required (S01, consent), ~60–90 min in room; no system/partition/BIOS/Windows changes |
| **PHASE D — Analysis** | Run pipeline §7 on collected data | **NO — Continues C** (analysis on already-collected data) but results reviewed before E | Produce `analysis/figures/` + `analysis/stats/` from raw; no new collection; walking speed covariate analyzed |
| **PHASE E — Scientific evaluation** | Classify PASS/PARTIAL/FAIL per §9, write final report | **NO — Concludes D** | Write `CSI-SENSE-001_FINAL_REPORT.md` with visual + statistical evidence (effect sizes with CIs, walking-speed analysis), per-trial appendix, checksums, backup verification, limitations, and future localization path; stop |

**Approval gates summary (v1.1 — must not be collapsed):**

- **Gate 1 (now):** Review this `CSI-SENSE-001_PLAN_v1.1.md` — if `CSI-SENSE-001 — APPROVED for Phase B`, proceed **only** to Phase B (host-side tooling). No human data.
- **Gate 2 (later):** Review Phase B tooling + room geometry record + environment readiness + **persistent backup verification per §5.5** — if `CSI-SENSE-001 — APPROVED for Phase C`, proceed to Phase C (collection). **This gate is separate and explicit** — Phase B approval does not authorize Phase C.
- **Firmware gate (if ever needed):** If any ESP32 firmware change becomes necessary, it triggers **Gate 3** — separate justification + pinned version + risk — never automatic.
- No phase flashes ESP or changes router/BIOS/partition/Windows without its gate; only Phase C involves human presence.

---

## 14. FILES TO CREATE (proposed — NOT yet created)

All paths relative to study root `data/CSI-SENSE-001/` except tooling which may sit at repo root for reuse. Listed with exact filenames; **none created now** except this plan and its predecessor v1.0.

| Purpose | Exact filename (proposed) | Created in which phase | Description |
|---------|---------------------------|------------------------|-------------|
| **Experiment protocol** | `data/CSI-SENSE-001/PROTOCOL.md` | B | Executable version of §2–§5/§10 — checklist the operator follows trial-by-trial; includes event marking + walking-speed recording + valid/invalid checklist + backup steps |
| **Metadata schema** | `data/CSI-SENSE-001/metadata/study_metadata.json` | B | Schema from §6.2 — study-wide (now includes `persistent_backup` + `walking` reference) |
| | `data/CSI-SENSE-001/metadata/room_geometry.json` | B (filled C) | Coordinates from §4 — filled after tape measure + photos |
| | `data/CSI-SENSE-001/metadata/hardware_identity.json` | B | ESP32/router/host identity |
| | `data/CSI-SENSE-001/metadata/firmware_versions.json` | B | Pinned SHAs — reused proven, not modified |
| | `data/CSI-SENSE-001/metadata/capture_config.json` | B | Baud/rate/channel/etc. |
| **Capture tooling** | `tools/csi_capture/capture_csi_sense.py` | B (host-only) | Reuse of `/tmp/capture_csi.py` 921600 raw `wb` + per-trial file naming + SHA + backup helper; **no parsing during capture** |
| | `tools/csi_capture/event_logger.py` | B (host-only) | Sidecar key-press → `events_trialXX.jsonl` with `wall_clock_ns + chip_seq` sync; never touches serial |
| | `tools/csi_capture/validate_raw.py` | B (host-only) | Post-trial quick check: counts, malformed, missing seq, len==128 — warns if invalid |
| | `tools/csi_capture/backup_verify.py` | B (host-only) **new v1.1** | §5.5 procedure: `lsblk`/`df` inspection, write-test SHA round-trip, per-trial copy + `sha256sum -c`, `backup_verified` flag |
| **Analysis tooling** | `tools/csi_analysis/parse_csi.py` | B (host-only) | Proven regex → `parsed.csv`/`npz` (amp/phase), handles glued fragments |
| | `tools/csi_analysis/features.py` | B (host-only) | `amp=hypot(I,Q)`, `phase=atan2`, detrended phase, per-packet mean/variance; also derives `walk_duration`/`speed` if needed |
| | `tools/csi_analysis/baseline_model.py` | B (host-only) | `μ_k, σ_k, Σ`, windowed variance, deviation metrics |
| | `tools/csi_analysis/pca_spectrogram.py` | B (host-only) | PCA + STFT spectrogram |
| | `tools/csi_analysis/temporal_plots.py` | B (host-only) | Overlay A/C/D/F + events + speed annotation → `figures/` |
| | `tools/csi_analysis/statistical_tests.py` | B (host-only) | Distribution inspection → test choice → effect size + CI — logs rationale; includes walking-speed covariate (v1.1) |
| | `tools/csi_analysis/analysis_config.json` | B (committed before D) | Seeds, windows, versions, effect-size references noted as not proof |
| **README** | `data/CSI-SENSE-001/README.md` | B | Study overview, hardware, how to reproduce, directory map, ethics note, backup requirement |
| **Final report** | `data/CSI-SENSE-001/CSI-SENSE-001_FINAL_REPORT.md` (also copy to `~/Desktop/`) | E | Visual + statistical evidence, PASS/PARTIAL/FAIL per §9 (with effect-size context + speed analysis), per-trial appendix, checksums, backup verification, limitations, future localization path |
| **This plan** | `~/Desktop/CSI-SENSE-001_PLAN_v1.1.md` (this file) | A | Planning artifact v1.1 — read-only |
| **Predecessor** | `~/Desktop/CSI-SENSE-001_PLAN.md` (v1.0) | A | Retained for audit — superseded by v1.1 |

**Total new files if approved:** ~17 files (5 metadata JSON + 4 capture incl. backup_verify + 6 analysis + PROTOCOL + README + final report) + per-trial data (`raw/trial_XX/` ×10). All preserve raw; Phase B creates only host-side software, not data.

---

## 15. CSI-SENSE-001 — FINAL APPROVAL GATE (v1.1)

### What is now planned

- Research question & H0/H1 (§1) — presence/movement vs empty baseline, not localization.
- Six controlled conditions A→F with purpose (§2) — **D walking now with natural repeatable pace, `0.8–1.2 m/s` as reference/target only, actual `walk_duration_s`/`estimated_speed_mps` recorded per trial as covariate** (§2.D, §3.1, §5.2).
- Experiment design: durations (A 90s, C 60s, D ~35s, B/E ~12s, F 90s), N=10 trials (~6 min each), 30 s inter-trial rest, fixed order A→F, event marking via sidecar `events.jsonl` (wall + chip timestamps, 100 ms), validity criteria (§3/§5).
- Room geometry coordinate system (origin router, X/Y meters, Z height) with router/ESP/waypoints LOS cross recorded (§4).
- Data acquisition **reusing already-proven CSI-VERIFY-001 firmware/configuration** (`v5.4.4 296b6eab`, `8633d671`, `ce23861e`, 921600 baud raw `wb`) — **no firmware/router/BIOS/partition change**; capture adds event sidecar only (§5.1, §5.2, §11).
- **Persistent backup gate (§5.5):** Live-USB safety procedure — raw/metadata/timestamps/analysis/checksums/reports backed up to verified persistent destination with SHA verification, second copy recommended, gate checked before Phase C.
- Dataset structure `data/CSI-SENSE-001/{metadata,raw/trial_XX,analysis/{figures,stats}}` with JSON schemas now including `walking` and `persistent_backup` (§6).
- Analysis pipeline (§7): integrity → I/Q → `amp=sqrt(I²+Q²)` + `phase=atan2` detrended → baseline `μ_k Σ` → deviation/Mahalanobis/z → walking-speed covariate → RSSI compare → PCA → spectrogram → plots → noise tracking.
- Statistical evaluation (§8): Q1 human vs empty, Q2 movement vs stationary (+ speed correlation), Q3 repeatable, Q4 above empty-empty 95th percentile, Q5 top subcarriers, Q6 false-positive — **effect-size thresholds `d≥0.5`/`r≥0.3` are practical references only, not universal proof; smaller consistent effects may still be meaningful** (§8.2, §9).
- Success criteria (§9): **PASS** requires visual+statistical+repeatable+above noise+low FP with effect-size note; **PARTIAL** allows small-but-significant or motion-only; **FAIL** otherwise — PASS ≠ localization.
- Controls for 14 confounders including walking-speed variation and Live-USB volatility with mitigations (§10).
- Reproducibility (§11): firmware/hardware/geometry/capture/timestamps/trial IDs/naming/checksums/persistent backup/analysis config — firmware reuse explicitly noted.
- Future localization value (§12) without claiming it now.
- **Explicit phase distinction (§13):** `PHASE A` planning / `PHASE B` host-side tooling only / `PHASE C` controlled human data collection / `PHASE D` analysis / `PHASE E` evaluation — **Phase B approval ≠ Phase C approval**.
- Exact file list (§14) — ~17 host-side files plus per-trial data — none yet created.

### What has NOT been executed

- **No ESP32 flash/erase/write** — firmware remains `CSI-VERIFY-001` `ce23861e` as proven.
- **No router configuration change** (still `Nihaal` ch1 HT20).
- **No Windows/BIOS/partitions/internal SSD modification** — `nvme0n1` untouched.
- **No human experiment data collected** — no presence/movement trials run.
- **No hardware purchased, no room measured, no tooling built beyond inspection** — `data/CSI-SENSE-001/` directory not created, capture/analysis scripts not written (`tools/csi_capture/*`, `tools/csi_analysis/*` absent), metadata not filled, `backup_verify.py` not created, persistent backup **not yet verified** (gate pending).
- **No analysis, no statistics, no model training, no UI, no localization claim.**
- **No firmware modification** — Phase B is host-side only; any firmware change would require separate Gate 3.

### What software/files would be created in Phase B (host-side only)

If `APPROVED for Phase B`, host creates **only software/tools, not data**:

- `data/CSI-SENSE-001/PROTOCOL.md`, `README.md`
- `data/CSI-SENSE-001/metadata/{study_metadata.json, room_geometry.json, hardware_identity.json, firmware_versions.json, capture_config.json}` (schemas + placeholders, geometry filled in C)
- `tools/csi_capture/{capture_csi_sense.py, event_logger.py, validate_raw.py, backup_verify.py}` — 921600 raw capture + sidecar + SHA + backup verification (host, no flash)
- `tools/csi_analysis/{parse_csi.py, features.py, baseline_model.py, pca_spectrogram.py, temporal_plots.py, statistical_tests.py, analysis_config.json}` — parsing/features/PCA/stats with walking-speed covariate (host, no data yet)
- **No `idf.py flash`, no `write_flash`, no router change, no human data.**

### Whether any hardware/firmware changes are planned

- **No hardware/firmware changes are planned for CSI-SENSE-001.** Reuse proven `CSI-VERIFY-001` firmware/configuration is explicit (§5.1). Phase B is **host-side tooling only**. Any firmware change, if ever genuinely necessary, is **not part of CSI-SENSE-001** and would require a **separate explicit approval gate** with justification and pinned version — it will not happen automatically.

### What data will eventually be collected (only if Phase C later separately approved)

- **N=10 valid trials** × ~5 min = **~46 MB raw + ~100 MB parsed** total, each trial ~9k (A) +6k (C) +3k (D) +9k (F) CSI records at `len 128` with full fields + wall/chip timestamps + `walk_duration_s`/`estimated_speed_mps` + events + env notes — all per §5, written to `data/CSI-SENSE-001/raw/trial_XX/` **and immediately backed up to verified persistent destination per §5.5 with SHA match**. Invalid trials retained with `invalid_reason.json`. No data collected in Phase B.

### What human participation will be required (only Phase C)

- **Single subject (S01, anonymized, consented)** — same person all trials, same clothing, no phone/Wi-Fi device on body, performing: enter → stand 60 s at P1 → walk defined path at **natural repeatable pace** (reference `0.8–1.2 m/s` target only, actual speed recorded) 2 traversals → exit. Outside trials, subject waits >3 m away. Duration ~60–90 min total including setup. No other participants moving during trials. No medical/physiological data. **No participation required in Phase B.**

### The backup requirement

- **NO HUMAN DATA COLLECTION UNTIL PERSISTENT BACKUP HAS BEEN VERIFIED (§5.5).** Before Phase C, the actual available persistent destination (external USB or other non-volatile filesystem — **not** `/cow`/`/tmp`/`overlay`) must be **verified live** via `lsblk`/`df -hT`/`findmnt` + 100 MB write-test SHA round-trip + `sha256sum -c` pass, with `≥5 GB` free for 10 trials + analysis. After each trial, raw/metadata/events/env/analysis/checksums/reports are **copied (not moved)** to `<persistent>/CSI-SENSE-001/` and verified via SHA (`backup_verified: true` in `env_trial.json`). Raw is **never overwritten or modified** (`chmod a-w`). Second copy recommended if available. The persistent path is recorded in `study_metadata.json:persistent_backup{path, filesystem, verified_utc}`. **Do not assume a particular drive exists now — verify at Phase C gate.**

### Exactly what approval is needed to begin Phase B

- Reply **`CSI-SENSE-001 — APPROVED for Phase B`** (or `APPROVED v1.1 for Phase B`).

  Upon this approval, **only host-side Phase B** may proceed:
  ```bash
  # Phase B start — host-side tooling only, no RF/system/human data
  mkdir -p data/CSI-SENSE-001/{metadata,raw,analysis/{figures,stats}} tools/csi_capture tools/csi_analysis
  # create tools/csi_capture/capture_csi_sense.py (reuse 921600 wb + SHA + backup helper)
  #       tools/csi_capture/event_logger.py
  #       tools/csi_capture/validate_raw.py
  #       tools/csi_capture/backup_verify.py   # §5.5 verifier
  #       tools/csi_analysis/parse_csi.py (proven regex, walking-speed aware)
  #       tools/csi_analysis/{features,baseline_model,pca_spectrogram,temporal_plots,statistical_tests}.py
  #       data/CSI-SENSE-001/{PROTOCOL.md,README.md,metadata/*.json}
  # No idf.py flash, no router change, no data collection.
  ```

### Exactly what separate approval will later be needed before Phase C

- After Phase B is complete **and** you have reviewed:
  1. Phase B tooling (capture/analysis scripts + `backup_verify.py`),
  2. **Room geometry** recorded (`metadata/room_geometry.json` + photos),
  3. **Experimental environment** ready (§10 checklist),
  4. **Persistent backup verified** (§5.5 gate — `persistent_destination_path`, `filesystem`, `size/avail`, `write_test_sha_match: true`),

  you must reply **`CSI-SENSE-001 — APPROVED for Phase C`** (separate, explicit).

  Only then Phase C may begin collection:
  ```bash
  # Phase C start — controlled collection (requires human, ~6 min/trial) — NOT authorized by Phase B approval
  python3 tools/csi_capture/capture_csi_sense.py --trial 01 --duration 310 --baud 921600 --port /dev/ttyUSB0
  # in parallel: python3 tools/csi_capture/event_logger.py --trial 01  # records walk_duration_s / LOS_cross
  # per trial: python3 tools/csi_capture/validate_raw.py --trial 01 && python3 tools/csi_capture/backup_verify.py --trial 01
  ```

  Without this **second explicit approval**, Phase C does not begin. Phase B approval alone authorizes **only** host-side tooling.

**STOP after this v1.1 plan and approval gate. No implementation, no tooling creation, no CSI collection, no flash until approvals.**

---
*This v1.1 plan is grounded in CSI-VERIFY-001 PASS evidence: 7,152 varying len-128 vectors at 102 Hz over Xiaomi ch1 HT20 → ESP32-D0WD-V3 — all durations/rates justified from observed 102Hz/5.985ms/malformed 0.20%. Effect-size thresholds are reference; walking speed is measured not forced; persistent backup is gated; firmware reuse is explicit. PASS here means detectability, not localization.*
