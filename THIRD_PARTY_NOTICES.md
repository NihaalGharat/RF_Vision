# THIRD_PARTY_NOTICES — RF Vision

RF Vision combines original code (MIT, see `LICENSE`) with attributed
third-party components below. Per-file provenance (original path →
destination → modifications) is recorded in
`docs/third_party/SOURCE_PROVENANCE.md`. Never remove upstream license or
copyright notices.

## 1. Espressif esp-csi — Apache License 2.0

- Repository: https://github.com/espressif/esp-csi
- Owner: Espressif Systems (Shanghai) CO LTD
- Commit: `8633d67152db2808f141cc1595970aa9cf406045` (master, 2026-04-22)
- In RF Vision: `firmware/esp32/csi_recv_router/` (verbatim, unmodified),
  `visualization/rf/csi_viewer_reference.html` (verbatim),
  `docs/reference/csi_data_read_parse.py`,
  `docs/reference/csi_send_app_main.c`,
  `docs/reference/csi_recv_app_main.c`, `docs/background/*.md` (6 tutorial
  files, verbatim with this notice file as attribution record),
  `docs/reference/requirements.txt` (esp-csi host-tool pins, reference).
- Modifications: none to vendored files.
- License text: Apache-2.0 (see `docs/third_party/licenses/Apache-2.0.txt`).
  SPDX/FileCopyright headers preserved in all vendored sources.

## 2. ESP32-WiFi-CSI-Human-Sensing — MIT License

- Repository: https://github.com/everythingfreee/ESP32-WiFi-CSI-Human-Sensing
- Author: Sanaullah Shaheer — Copyright (c) 2026
- Commit: `d978e103a787fa7c337228e19e61a2abf67b7b94` (main, 2026-09-01)
- In RF Vision: `csi/parser/csi_parser.py`, `csi/capture/serial_receiver.py`,
  `dsp/preprocessing/preprocessing.py`, `dsp/features/feature_extraction.py`,
  `sensing/inference_engine.py` (+ split modules `sensing/presence|motion|
  activity|state/`), `localization/tracking/position_filter.py`,
  `localization/calibration/calibrate.py`, `ai/datasets/dataset.py`,
  `ai/datasets/collector.py`, `ai/training/{baseline_model,neural_network,
  train}.py`, `ai/evaluation/evaluate.py`, `config/settings.py`,
  `config/default.yaml`, `realtime/server/live_app.py`,
  `visualization/dashboard/visualization.py`,
  `firmware/traffic_gen_reference/esp32_ap.ino` (+ README, reference),
  `docs/reference/esp32_receiver.ino` (+ README, reference),
  `docs/reference/human_sensing_requirements.txt`.
- Modifications: package import standardization; serial double-callback/
  double-write removal; preprocessor counter fix + first-word key rename
  (`trim_first_word_invalid`, legacy alias kept) + length telemetry;
  inference scaler cleanup + sensing-module split (identical math).
  Full list: `docs/third_party/SOURCE_PROVENANCE.md`.
- License text: MIT (see `docs/third_party/licenses/MIT-Human-Sensing.txt`;
  copyright line retained).

## 3. ESP32-CSI-Tool — MIT License

- Repository: https://github.com/StevenMHernandez/ESP32-CSI-Tool
- Author: Steven M. Hernandez — Copyright (c) 2020
- Commit: `cce5b1a055fae5b01b30d1d39c5cfa1e0c656696` (master, 2023-03-29)
- In RF Vision: `csi/capture/helpers.py` is a clean re-implementation (no
  copied lines) of the `read_stdin / wait_timer / serial_append_time /
  serial_measure_rate` idioms; `docs/reference/example_csi.csv` (format
  specimen, verbatim); `docs/third_party/bib/esp32_csi_tool_{percom,
  wowmom}.bib` (verbatim citations). Firmware NOT reused.
- License text: MIT (see `docs/third_party/licenses/MIT-CSI-Tool.txt`).
- Papers to cite when the tool concept is referenced: PerCom Demos 2020
  ("Performing WiFi Sensing with Off-the-shelf Smartphones"); WoWMoM 2020
  ("Lightweight and Standalone IoT Based WiFi Sensing…").

## 4. thkimKETI/csi-sensing — ALL RIGHTS RESTRICTED (no code reused)

- Repository: https://github.com/thkimKETI/csi-sensing (commit `898f7f33`,
  2026-04-01). Authors: Taehyeon Kim, Dongwoo Kang, Korea Electronics
  Technology Institute (KETI). License: custom restrictive v1.0 (2025),
  view-and-reference only, NOT OSI-approved.
- Statement: **no file, snippet, weight, or threshold value from this
  repository is included in RF Vision.** Design facts studied (input shapes,
  MQTT grouping pattern, heatmap GUI pattern) are summarized in
  `docs/third_party/CSI_SENSING_STUDY_NOTES.md` as research notes only.
