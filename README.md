# RF Vision

A near-real-time RF sensing platform using Wi-Fi Channel State Information
(CSI) for human presence detection, motion/activity recognition,
localization, explainable AI, and 3D RF visualization.

**Status: engineering foundation (no validated sensing claims yet).**
This repository contains the integrated acquisition + processing + ML +
realtime codebase assembled from audited open-source components, plus the
native interfaces (data schema, event protocol, Unity bridge, experiment
framework) for the research phases ahead. See
`docs/research/SCIENTIFIC_VALIDATION_STATUS.md` — upstream accuracy claims
were deliberately NOT inherited.

## Hardware baseline (validated, do not replace without a migration plan)

- Xiaomi Mi Router 4C/R4CM (2.4 GHz) + ESP32-D0WD-V3 (`csi_recv_router`)
- ESP-CSI @ `8633d671` · ESP-IDF v5.4.4 · Ubuntu · USB serial @ 921600 8N1
- Details: `docs/hardware/BASELINE.md`, `firmware/esp32/csi_recv_router/`

## Architecture

```
ESP32 → CSI capture → transport → parser → validation → dsp →
features → sensing → localization → ai/xai → realtime → dashboard/Unity
```

Full subsystem docs (purpose, inputs/outputs, maturity, limits):
`docs/architecture/RFVISION_ARCHITECTURE.md`.
Canonical data interfaces: `docs/architecture/RFVISION_DATA_SCHEMA.md`.

## Repository layout

| Path | Contents |
|---|---|
| `firmware/` | Validated ESP32 firmware (untouched) + reference generator + protocol notes |
| `csi/` | Capture, parser (+ESP-CSV adapter), validation, transport, wire-format specs |
| `dsp/` | Preprocessing, amplitude, phase (gated), filtering, 180-d features |
| `sensing/` | Presence / motion / activity / state + realtime inference engine |
| `localization/` | Calibration, geometry, 1-D positioning seed, tracking, sync helpers |
| `ai/` | Datasets, training (KNN/RF/MLP), inference API, evaluation, XAI foundation |
| `realtime/` | Serial streaming, live app entry, versioned JSON event protocol |
| `visualization/` | Qt dashboard, RF reference viewer, digital-twin interface |
| `unity/` | Project scope + Unity integration message formats (foundation only) |
| `experiments/` | Protocols, metadata schema, config overrides, analysis notes |
| `config/` | Central `default.yaml` + settings loader |
| `tools/` | Headless raw-CSI recorder |
| `tests/` | Unit + integration + synthetic generators + fixtures |
| `docs/` | Architecture, hardware, software, research, third-party, background |
| `research/` | Dataset manifests, reports, publication staging (no raw data in git) |
| `research-data/` | Canonical research data: raw CSI + derived sets (**Git-ignored**; see below) |

> `dsp/` implements the `signal/` block of the target architecture. It was
> renamed because a top-level `signal` package irreversibly shadows Python's
> stdlib `signal` module (breaks joblib/pytest). See `dsp/README.md`.

## Research data

Location: `research-data/`

"Raw and large derived research datasets are intentionally excluded
from Git history."

- `research-data/MANIFEST.md` — every dataset file with size, SHA-256,
  experiment/provenance, source and original location (tracked in Git).
- Verify with `sha256sum -c <file>.sha256` sidecars, or the full-tree check
  in `research-data/README.md`.
- Reproduce analysis from the read-only raw captures using the current
  `csi/` + `dsp/` chain; technique reference (not active code) is in
  `docs/research/legacy/TOOL-REFERENCE.md`.

## Setup (Linux)

```bash
git clone https://github.com/NihaalGharat/RF_Vision.git
cd RF_Vision
./tools/run_rfvision_ui.sh
```

Interactive RF console (local-only): `http://127.0.0.1:8130/`
(tabs: Overview, Sensing, RF Field, Hardware, Localization, XAI,
Experiments, Settings). Python dependencies:

```bash
pip install -r requirements-base.txt        # capture → features → sensing → sklearn ML
pip install -r requirements-gui.txt         # live Qt dashboard (optional)
pip install -r requirements-ml.txt          # PyTorch MLP (optional, CPU)
pip install -r requirements-dev.txt         # pytest etc.
```

Firmware build (unchanged baseline, ESP-IDF v5.4.4):
see `firmware/esp32/csi_recv_router/README.md`. No flashing is part of
foundation work.

## Running tests

```bash
python3 -m pytest tests/ -q        # 128 tests, stdlib+numpy+sklearn, no hardware
```

Headless realtime inference (needs the ESP32 on USB):
```bash
python3 -m sensing.inference_engine --port /dev/ttyUSB0
```
Raw capture without parsing: `python3 tools/csi_record.py --port /dev/ttyUSB0 --duration 60`
Live GUI: `python3 realtime/server/live_app.py` (requires `requirements-gui.txt`)

## Research status / known limitations

- Acquisition validated on the baseline path; everything downstream is
  **NOT YET VALIDATED** (session-split evaluation is the minimum bar).
- Position is 1-D `[0,1]` along the link; 2-D/3-D, multi-node sync, XAI,
  digital twin, and Unity scenes are interface-level foundations, not products.
- Phase features are gated OFF by default (ESP32 per-packet offset).
- Full limitation register: `docs/research/SCIENTIFIC_VALIDATION_STATUS.md`.

## Provenance & licenses

All third-party code is attributed in `THIRD_PARTY_NOTICES.md` with
per-file provenance in `docs/third_party/SOURCE_PROVENANCE.md`.
RF Vision native code is MIT (`LICENSE`; copyright-holder line to be
confirmed — see implementation report). `thkimKETI/csi-sensing` was
studied but **no code was taken** (restrictive view-only license).
