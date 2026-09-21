# Source Provenance — where every third-party component came from

Companion to `THIRD_PARTY_NOTICES.md`. Format per component: upstream
path @ commit → RF Vision destination → modifications (or "verbatim").

## A. esp-csi @ 8633d671 (Apache-2.0)

| Upstream path | RF Vision destination | Modifications |
|---|---|---|
| `examples/get-started/csi_recv_router/` (whole directory: root `CMakeLists.txt`, `sdkconfig.defaults`, `README.md`, `main/{app_main.c, CMakeLists.txt, idf_component.yml}`) | `firmware/esp32/csi_recv_router/` (identical layout) | verbatim |
| `examples/get-started/tools/csi_viewer.html` | `visualization/rf/csi_viewer_reference.html` | verbatim (renamed for clarity) |
| `examples/get-started/tools/csi_data_read_parse.py` | `docs/reference/csi_data_read_parse.py` | verbatim (known AGC-index quirk on legacy frames — see WIRE_FORMATS) |
| `examples/get-started/tools/requirements.txt` | `docs/reference/requirements.txt` | verbatim (reference only) |
| `examples/get-started/csi_send/main/app_main.c` | `docs/reference/csi_send_app_main.c` | verbatim (renamed; not built) |
| `examples/get-started/csi_recv/main/app_main.c` | `docs/reference/csi_recv_app_main.c` | verbatim (renamed; not built) |
| `docs/en/*.md` (6 files) | `docs/background/*.md` | verbatim (background reading) |

A `README_RFVISION.md` alongside the firmware records the provenance pin
and the do-not-replace policy (upstream `README.md` untouched).

## B. ESP32-WiFi-CSI-Human-Sensing @ d978e103 (MIT)

| Upstream path | RF Vision destination | Modifications |
|---|---|---|
| `python/csi_parser.py` | `csi/parser/csi_parser.py` | import path only (none needed — stdlib+numpy) |
| `python/serial_receiver.py` | `csi/capture/serial_receiver.py` | imports → absolute; **removed duplicated writer-init/write/callback block** (double record + double infer per packet) |
| `python/preprocessing.py` | `dsp/preprocessing/preprocessing.py` | imports → absolute; removed double `accepted+=1`; `drop_first_word_invalid` → `trim_first_word_invalid` (+legacy alias); `expect_length` wired as `length_unexpected` telemetry; removed `__CHUNK_END__` marker; docstring updated |
| `python/feature_extraction.py` | `dsp/features/feature_extraction.py` | imports → absolute |
| `python/inference.py` | `sensing/inference_engine.py` + `sensing/{state, motion, presence, activity}/` | imports → absolute; `SystemState`→`sensing.state`, `MovementDetector`→`sensing.motion` (verbatim moves, re-exported); presence EMA→`PresenceSmoother`, activity map→`label_activity` (identical math); scaler double-reshape cleaned |
| `python/position_filter.py` | `localization/tracking/position_filter.py` | imports (none needed) |
| `python/calibrate.py` | `localization/calibration/calibrate.py` | imports → absolute |
| `python/dataset.py` | `ai/datasets/dataset.py` | imports → absolute |
| `python/dataset_collector.py` | `ai/datasets/collector.py` | imports → absolute (renamed for clarity) |
| `python/models/baseline_model.py` | `ai/training/baseline_model.py` | none |
| `python/models/neural_network.py` | `ai/training/neural_network.py` | none |
| `python/models/__init__.py` | `ai/training/__init__.py` | relative → absolute re-exports |
| `python/train.py` | `ai/training/train.py` | imports → absolute |
| `python/evaluate.py` | `ai/evaluation/evaluate.py` | imports → absolute |
| `python/config.py` | `config/settings.py` | default config path → `config/default.yaml`; defaults key renamed (see above); module docstring provenance note |
| `config.yaml` | `config/default.yaml` | key renamed + alias comment |
| `python/main.py` | `realtime/server/live_app.py` | imports → absolute (renamed for clarity) |
| `python/visualization.py` | `visualization/dashboard/visualization.py` | none (self-contained; PyQt6/matplotlib stay optional) |
| `firmware/esp32_ap/esp32_ap.ino` + `README.md` | `firmware/traffic_gen_reference/` | verbatim (reference traffic generator, NOT default) |
| `firmware/esp32_receiver/esp32_receiver.ino` + `README.md` | `docs/reference/esp32_receiver.ino` + `docs/reference/README.md` | verbatim (alt-firmware study, NOT built) |
| `requirements.txt` | `docs/reference/human_sensing_requirements.txt` | verbatim (reference; live pins split into `requirements-*.txt`) |
| `tests/*` (4 scripts) | superseded by `tests/unit|integration|synthetic/` | rewritten as hermetic pytest/unittest suite (upstream tests had import fragility + missing fixture) |

Structural note: upstream `python/` was flat; RF Vision places modules in
the `csi/dsp/sensing/localization/ai/realtime/visualization/config/`
packages. Upstream `signal/` block lives at `dsp/` (stdlib collision —
see `dsp/README.md`).

## C. ESP32-CSI-Tool @ cce5b1a0 (MIT)

| Upstream path | RF Vision destination | Modifications |
|---|---|---|
| `python_utils/{read_stdin,wait_timer,serial_append_time,serial_measure_rate}.py` | `csi/capture/helpers.py` | **clean re-implementation, no copied lines** (same behaviours) |
| `python_utils/example_csi.csv` | `docs/reference/example_csi.csv` | verbatim specimen |
| `python_utils/parse_csi.py`, `serial_plot_csi_live.py` | NOT imported (formula/specimen notes in `csi/formats/WIRE_FORMATS.md`) | — |
| `docs/bibtex/esp32_csi_tool_{percom,wowmom}.bib` | `docs/third_party/bib/` | verbatim |
| `active_ap/`, `active_sta/`, `passive/`, `_components/` | EXCLUDED (ESP-IDF v4.3, unbuildable, buggy) | — |

## D. thkimKETI/csi-sensing @ 898f7f33 — NO CODE

Nothing copied. Study notes: `docs/third_party/CSI_SENSING_STUDY_NOTES.md`.
