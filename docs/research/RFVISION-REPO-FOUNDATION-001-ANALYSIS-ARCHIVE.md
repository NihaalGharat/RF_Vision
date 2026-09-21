# RFVISION-REPO-FOUNDATION-001 — Analysis Archive (merged, read-only history)

This file is the merged archive of operation RFVISION-REPO-FOUNDATION-001
(repository research, extraction & foundation analysis, completed
2026-09-21 UTC, ANALYSIS ONLY — nothing was modified, flashed, captured,
or trained). The 12 working documents from
`~/Documents/RFVISION-REPO-FOUNDATION-001/` were consolidated here and the
folder removed, so this repository is the single authoritative location.
Operative decisions now live in the canonical docs referenced below; this
archive preserves the evidence and reasoning behind them.

Canonical successors: `THIRD_PARTY_NOTICES.md`,
`docs/third_party/SOURCE_PROVENANCE.md`, `docs/architecture/`,
`docs/research/SCIENTIFIC_VALIDATION_STATUS.md`,
`docs/software/DEPENDENCIES.md`, `docs/hardware/BASELINE.md`,
`csi/formats/WIRE_FORMATS.md`,
`docs/third_party/CSI_SENSING_STUDY_NOTES.md`,
`RFVISION-FOUNDATION-IMPLEMENTATION-REPORT.md`.

## 1. Sources pinned (from REPOSITORY_SOURCES.json, inspected 2026-09-21)

Validated baseline: ESP-CSI `8633d67152db2808f141cc1595970aa9cf406045`,
ESP-IDF v5.4.4 (`296b6eab…`), `examples/get-started/csi_recv_router`,
ESP32-D0WD-V3 rev 3.1, Xiaomi Mi Router 4C/R4CM, `/dev/ttyUSB0`, Ubuntu.

| ID | Repository | Branch | HEAD | Date | License | Stars | Role |
|---|---|---|---|---|---|---|---|
| A | espressif/esp-csi | master | `8633d671` | 2026-04-22 | Apache-2.0 (Espressif Shanghai) | ~1578 | Acquisition foundation (RETAIN) |
| B | everythingfreee/ESP32-WiFi-CSI-Human-Sensing | main | `d978e103` | 2026-09-01 | MIT (Sanaullah Shaheer, 2026) | 0 | Primary extraction source |
| C | thkimKETI/csi-sensing | main | `898f7f33` | 2026-04-01 | Custom restrictive v1.0, NOT OSI | 14 | REFERENCE ONLY (license-blocked) |
| D | StevenMHernandez/ESP32-CSI-Tool | master | `cce5b1a0` | 2023-03-29 | MIT (2020) | ~559 | Ideas + citations; firmware DISCARD |

Decisive fact: esp-csi HEAD == validated baseline commit (zero drift).
Additional candidates (web search 2026-09-21): `outputlayer/espectre-sense`
(MIT, 3× S3 + Rust server, reference-only pattern) and
`s-shrikanth/WiFi-CSI-Human-Detection` (1 commit, adds nothing — rejected).
XAI / 3D localization / digital twin / Unity: NO reusable repository found
→ native work packages.

## 2. Repository inventory (from 01, condensed)

- **A esp-csi**: `get-started/{csi_send,csi_recv,csi_recv_router,tools}`,
  `esp-radar/{console_test,connect_rainmaker,wifi_sensing_demo}` (closed
  `esp_radar`/`esp_wifi_sensing` deps), `esp-crab` (dual-C5 HW, out of
  scope), 6 tutorial docs, PyQt + Web Serial viewers. IDF floor ≥4.4.1.
  Lacks: ML, localizer, datasets, XAI, dashboard (filters only named).
- **B Human-Sensing** (~5,444 lines): 14 Python modules + 2 models,
  2 Arduino sketches (AP traffic-gen + STA JSON receiver @ 921600),
  4 tests, `config.yaml`, honest README. No dataset shipped. Defects
  found: `serial_receiver` duplicated write+callback block; double
  `accepted+=1`; misleading `drop_first_word_invalid` (trim-and-keep);
  dead `expect_length_20mhz`; test import fragility + missing real-CSV
  fixture. Transport (`#CSI {JSON}`) mismatches esp-csi (`CSI_DATA` text).
- **C csi-sensing**: `model.py` (TinyCSINet + TinyTransformerNet; TCN/Large
  dead), 4 scripts, MQTT templates, 55-pin CUDA stack, no firmware, no
  weights (Drive links). `1D_csi_sensing_svm.py` is corrupt (x86-64 machine
  code misnamed `.py`). MQTT-grouped `{CSI_DATA}`, amplitude-only, 180×114
  windows, hardcoded `cuda`. License grants view-and-reference ONLY.
- **D CSI-Tool**: v4.3-era C++ firmware (`active_ap/sta`, `passive`,
  `_components`), 7 python utils, PerCom/WoWMoM bibtex. Archived
  (2019–2022 substance); `esp_spi_flash.h`, legacy CSI/SDSPI APIs, real
  bugs (`va_list` reuse, `sendto(&data)`). Will not build on IDF v5.4.4.

## 3. Capability matrix (from 02 — verified in source, not README claims)

✅ reusable · ◐ partial/reference · ❌ absent · ⛔ excluded · 🔧 fix/adapt

| Capability | A | B | C | D | RF Vision need |
|---|---|---|---|---|---|
| CSI capture firmware | ✅ router mode | ◐ Arduino 2-board | ❌ | ⛔ v4.3 unbuildable | Keep A |
| CSI parser | ◐ CSV demo | 🔧 strict JSON | ◐ MQTT regex | ◐ fragile demo | Adopt B + A-adapter |
| Amplitude | ◐ viewer `abs` | ✅ Hampel+EMA+mask | ✅ /15+Butterworth | ◐ demo | Adopt B |
| Phase | ◐ viewer `atan2` | 🔧 helper, unused | ❌ discarded | ◐ swapped labels | B helper, gated |
| Filtering | ❌ (closed) | ✅ Hampel/EMA/LP | ✅ BW+mean | ❌ | Adopt B |
| Feature extraction | ❌ | ✅ 180-d | ❌ | ❌ | Adopt B |
| Presence | ◐ closed thresh | ✅ heur+KNN/RF/MLP | ◐ heur+classif | ❌ | Adopt B |
| Activity | ◐ closed demo | ◐ heuristic only | ◐ weights absent | ❌ | B heuristic; C shapes studied |
| Localization | ❌ | ◐ 1-D [0,1] | ◐ 2-class zones | ❌ (tooling only) | B 1-D seed; rest native |
| ML / DL | ❌ | ✅ KNN/RF + MLP | ◐ SVM/CNN/Transf. | ❌ | Adopt B |
| XAI / 3-D / twin / Unity | ❌ | ❌ | ❌ | ❌ | Gap → native |
| Real-time | ◐ viewers | ✅ threaded+Qt | ✅ MQTT+mp+Qt | ◐ demo plot | Adopt B |
| Visualization | ✅ HTML+PyQt | ✅ room+debug | ✅ heatmaps | ◐ 1-subcarrier | Adopt B; C informs |
| Dataset tooling | ❌ | ✅ collector+splits | ◐ hard-coded dump | ❌ | Adopt B |
| Calibration | ◐ closed | ✅ guided routine | ❌ | ❌ | Adopt B |
| Multi-receiver | ❌ | ❌ | ◐ 2-node MQTT | ❌ | Gap → native |

## 4. Architecture comparison (from 03)

- A: firmware → serial → demo parser → viewer (chain ends; no
  dataset/model/API; radar variants need closed components).
- B: AP beacons → STA probes 60 Hz → serial thread → strict parse →
  Hampel/EMA → 64/stride-8 180-d → movement heur → presence → 1-D
  position → Qt GUI; plus collector/calibrate/train/evaluate (closed loop).
- C: 1–2× S3 → MQTT groups → /15 amp → 180×114 → Butterworth+mean →
  CNN+Transformer (cuda) → heatmap GUI (study only).
- D: UDP-TX → CSI-RX CSV (+SD) / promiscuous sniffer → scrub/timestamp/
  rate → demo plots (ideas only).
- Consolidation: ONE pipeline (B) + ONE firmware (A) + ONE adapter;
  C/D patterns re-implemented natively; no dual pipelines or GUIs.

## 5. Extraction map (from 04 — minimum useful extraction)

- From A: `csi_recv_router/*` (firmware, keep as-is), `csi_viewer.html`,
  `csi_data_read_parse.py` + requirements (reference), `csi_send/csi_recv`
  `app_main.c` (reference), 6 `docs/en` tutorials (background).
- From B: `csi_parser`→`csi/parser`; `serial_receiver`→`csi/capture` (+
  `realtime/streaming`) FIX duplication; `preprocessing`→signal FIX
  counters/key/`expect_length`; `feature_extraction`→features;
  `inference`→`sensing/`+`ai/inference` FIX scaler; `position_filter`→
  tracking; `calibrate`→calibration; `dataset`+`dataset_collector`→
  `ai/datasets`; models+`train`+`evaluate`→`ai/`; `config`+`config.yaml`;
  requirements (lock input); AP `.ino` (traffic-gen reference);
  receiver `.ino` (docs reference); tests (fix+harden); README (style).
- From D: 4 host-utility idioms re-implemented; `parse_csi.py` +
  `example_csi.csv` as specimen; 2 bibtex cites. Firmware excluded.
- From C: study only, zero lines.
- Never: `.git`, caches, artifacts, datasets (none shipped), closed
  demos, esp-crab, dead code, corrupt file, credentials (only
  `change_this`/`CSI_SENSOR` placeholders found).
- Dedup ruling: single parser/filter-chain/feature-vector/trainer/GUI.

## 6. CSI format compatibility (from 05)

Baseline (A, legacy 25-col): `CSI_DATA,seq,mac,rssi,rate,sig_mode,mcs,
bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,
noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,
sig_len,rx_state,len,first_word_invalid,"[I,Q,…]"` @ 921600 8N1; Q,I
interleaved int8, gain-compensated; HT20 → `len=128`/64 slots; `rx_format`
header quirk cosmetic. B (`#CSI {JSON}`): ADAPTER REQUIRED (map
`bandwidth→cwb`, `len→csi_len`, payload→`csi`, stamps; count malformed).
C (MQTT groups, 192/114 assumes): incompatible defaults, no adapter (not
reused). D (26-col bracketed, 128/384 B): legacy-incompatible, specimen
only. Ruling: primary parser = B's; adapter mandatory with auditable
counters; phase available end-to-end but default amplitude-only.

## 7. Scientific claims audit (from 06 — IMPLEMENTED ≠ VALIDATED ≠ CLAIMED)

A: positioning/human-detection/breathing claims → bring-up + closed demos,
no evidence → NOT VERIFIED (acquisition on our path: VALIDATED). B: 1-D
position + movement → real code, session splits, zero shipped evidence →
NOT VERIFIED (disclaimers adopted as policy; regression test fixture
absent). C: zones/activities → code without weights/training/metrics →
NOT VERIFIED. D: "device-free localization" → collection tooling only →
cite as tool. Binding policy: no inherited numbers; protocol-first;
session-split minimum + cross-session reporting; phase gate; derived-data
lineage (source+transform+version+config+checksum+timestamp).

## 8. License audit (from 07 — files read in full)

A Apache-2.0 (Espressif Shanghai): CLEARED vendored subset (retain
notices, note changes). B MIT (©2026 Shaheer): CLEARED adaptation.
D MIT (©2020 Hernandez): CLEARED idioms/citations. C custom v1.0 (2025
KETI, NOT OSI, consent-required for any use incl. research/training):
EXCLUDED, zero lines. Apache-2.0 + MIT combine cleanly; no copyleft.
Commercial/closed redistribution needs re-confirmation later.

## 9. Dependency audit (from 08)

A firmware: IDF ≥4.4.1 (v5.4.4 satisfies); host pyserial/viewer deps
(prune unused). B: current floors (pyserial/numpy/scipy/pandas/
sklearn/matplotlib/PyYAML/joblib/PyQt6; torch commented-out CPU) —
lock on import, pytest added, torch/PyQt6 as extras. C: 55-pin CUDA
stack, `cuda` hard-coded — excluded. D: 2020-era — nothing to lock.
Posture: base lean-headless + gui + ml-cpu extras; no conflicts.

## 10. Foundation proposal P1–P8 (from 09 — executed in 002)

P1 proven acquisition unchanged · P2 parser + native A-adapter +
re-implemented D helpers · P3 signal chain (fixes) + gated phase ·
P4 sensing + 1-D seed (scaler fix) · P5 AI datasets/training/evaluation ·
P6 realtime + GUI + field viewer · P7 native packages (multi-node
protocol, heatmaps, XAI, 2-D/3-D, twin, Unity, experiments) · P8 hygiene
(config/logging/schema/errors, lockfile, pytest/ruff, synthetic suite,
golden-vs-validated comparison, raw immutable). Prototype path:
P1→P2→P3→heuristic GUI→calibrate→collect→train→evaluate→dashboard v1.

## 11. Third-party notices draft (from 10 — PROMOTED)

Promoted to `THIRD_PARTY_NOTICES.md` (license texts under
`docs/third_party/licenses/`). C recorded with an explicit no-reuse
statement.

## 12. Final audit answers (from RFVISION-REPO-FOUNDATION-AUDIT)

Useful: A (acquisition only), B (processing/ML/realtime), D (idioms/
cites), C (design study). Reuse per §5. Foundation stays esp-csi router
mode (HEAD == validated commit). Processing/ML/localization seeds per §5;
rewrites per §10-P7/P8. Licenses/deps per §§8–9. Native vs third-party
vs discarded per §5. Architecture per §4. Prototype path per §10.
Closed with: "RFVISION-REPO-FOUNDATION-001 COMPLETE — AWAITING USER
APPROVAL FOR EXTRACTION AND RESTRUCTURING" (approval granted via
RFVISION-FOUNDATION-002).
