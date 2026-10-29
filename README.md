# RF Vision

RF Vision is a working engineering prototype for real-time Wi-Fi Channel State
Information (CSI) acquisition and visualization. Two ESP32 receivers stream CSI
over USB serial into a local Python backend; a vendored React console shows
measured A/B activity and an illustrative 3D RF presentation.

**Status: demo-ready engineering checkpoint with zero validated sensing
claims.** Real dual-receiver CSI acquisition and live A/B visualization are
verified. Human-presence association remains exploratory, and no validated
presence/activity classifier, coordinates, trajectory, pose, obstacle detection,
localization, or reconstructed geometry exists. See
[`docs/research/SCIENTIFIC_VALIDATION_STATUS.md`](docs/research/SCIENTIFIC_VALIDATION_STATUS.md).

## What it does now

- Captures real CSI from two ESP32-D0WD-V3 receivers over USB serial.
- Synchronizes the two node streams on the host and exposes explicit
  `LIVE_VERIFIED`, `SYNCED`, and `RF_READY` states.
- Delivers independent A/B CSI frames to Live Sensing and Visualization; this
  was verified in a prior live browser session.
- Shows live amplitude, RSSI, validity, per-node activity history, and a 3D
  room presentation. Reference View waves and room geometry are **illustrative**,
  not measured time-of-flight or surveyed geometry.
- Supports explicit, bounded raw-CSI recording and audio-guided research trials.
- Recovers WebSocket connections indefinitely with capped backoff; the previous
  reconnect-budget exhaustion is corrected.
- Serializes recording finalization so a stop during auto-stop cannot publish
  `bytes=0` / `sha256=null` for a nonempty file. The historical correction for
  `WT-20261029T193657Z` remains append-only and unchanged.

### Scientific boundary

- **Verified:** dual ESP32 CSI acquisition, backend synchronization/readiness,
  and live measured A/B delivery.
- **Observed:** relative RF activity changes in some sessions.
- **Exploratory:** association between RF changes and a human in the path.
- **Illustrative:** Reference View room and wave animation.
- **Not validated:** human detection, tracking, coordinates, pose, obstacle
  detection, obstacle localization, and reconstruction.

Two audio-guided `Nihaal` human-presence trials were completed
(`WT-20261029T194753Z` primary, `WT-20261029T193657Z` supplementary). Event
timing and reference quality remain limited. The VCET reference trial
`WT-20261029T121111Z` parsed to 11,027 A / 11,559 B CSI vectors; the older
9,071 / 9,517 metadata values are cumulative source counters, not trial totals.
Obstacle reconstruction and new sensing features are deferred until after the
demonstration.

## Hardware architecture

```
2.4 GHz Wi-Fi AP
   ├── ESP32-A receiver (ESP32-D0WD-V3, csi_recv_router firmware)
   └── ESP32-B receiver (ESP32-D0WD-V3, csi_recv_router firmware)
             │
             └── USB serial @ 921600 8N1 → host backend → browser
```

The validated router baseline is documented in
[`docs/hardware/BASELINE.md`](docs/hardware/BASELINE.md). An operator-provided
2.4 GHz hotspot is also supported for field sessions. The ESP32 nodes are
receivers; the AP is not a second sensing receiver. Firmware remains the
validated `firmware/esp32/csi_recv_router/` build (ESP-IDF v5.4.4); no flashing
is part of this checkpoint.

## Software components

| Path | Role |
|---|---|
| `web/` | Local Python stdlib HTTP + WebSocket backend and vendored React console |
| `web/source.py` | Off/fixture/simulated/live providers, CSI envelope generation, recording lock |
| `web/dual_node.py` | Two-node session, host timestamps, synchronization |
| `web/network.py` | Network discovery, password-safe provisioning, RF readiness |
| `web/trials.py` | Bounded trial recorder and metadata finalization |
| `web/vision.py` | Conservative per-node engineering evidence |
| `sensing/` | Presence/motion/activity/state inference and reference tracker |
| `csi/`, `dsp/` | CSI parsing, validation, transport, preprocessing, features |
| `localization/`, `ai/`, `realtime/`, `visualization/` | Research foundations |
| `tests/` | Unit, integration, contract, and browser-driver regression coverage |
| `research-data/` | Local raw CSI and derived data, Git-ignored |
| `docs/` | Architecture, hardware, research, development, and provenance |

The frontend is vendored and needs no Node/npm build step. The backend binds to
`127.0.0.1` only and is intended for a single local operator.

## Web application sections

The React console has five hash-routed sections:

- `#/live` — live frame validity, A/B health, and measured signal charts.
- `#/visualize` — per-node measured activity history and illustrative 3D room.
- `#/hardware` — network inspection/provisioning, dual-session control, RF READY.
- `#/research` — bounded recording, checksums, trial state, and analysis context.
- `#/system` — health, WebSocket state, appearance, and safety boundaries.

The preserved legacy console is available at `/legacy`; `/` serves the current
React console.

## Supported development environment

- Ubuntu Linux; verified on Ubuntu 26.04.1 with Python 3.14.4.
- Python with the `requirements-base.txt` stack (numpy, scipy, pandas,
  scikit-learn, matplotlib, PyYAML, joblib, pyserial).
- No Node/npm build step; the React and Three.js assets are vendored.
- Google Chrome for the browser-tested UI (verified with Chrome 156).
- ESP-IDF v5.4.4 only for firmware builds; not required to run the web console.

Full environment details:
[`docs/development/DEVELOPMENT_ENVIRONMENT.md`](docs/development/DEVELOPMENT_ENVIRONMENT.md).

## Setup and startup

```bash
git clone https://github.com/NihaalGharat/RF_Vision.git
cd RF_Vision
/usr/bin/python3 -m pip install -r requirements-dev.txt
./tools/run_rfvision_ui.sh
```

Open `http://127.0.0.1:8130/`. The launcher accepts an optional port and pins
the system Python used by the verified environment; override it with
`RFVISION_PYTHON=/path/to/python3` if needed. The equivalent direct command is:

```bash
python3 -m web.server --port 8130
```

Optional extras: `requirements-gui.txt` for the Qt dashboard and
`requirements-ml.txt` for the PyTorch MLP. Neither is required for the web demo.

## Testing

```bash
python3 -m pytest tests/ -q
```

Current verified regression: **325 passed** on the Python suite. Focused
recorder/WebSocket coverage: 12 passed. Offline browser smoke: **13/13** checks
across all five routes, using synthetic fixtures (UI plumbing only). No test
requires hardware.

Hardware-dependent commands are documented but are not part of the test gate:

```bash
python3 -m sensing.inference_engine --port /dev/ttyUSB0
python3 -m tools.csi_record --port /dev/ttyUSB0 --duration 60
```

The operator sequence and honest fallback wording are in
[`docs/development/DEMO_RUNBOOK.md`](docs/development/DEMO_RUNBOOK.md).

## Research data and evidence

Raw CSI and derived research data live under `research-data/`, which is
Git-ignored. Detailed trial evidence bundles, browser screenshots, and live
logs are also retained locally and intentionally not published because they
contain environment-specific diagnostics and identifiers. They are not an
independent off-device backup.

- `research-data/MANIFEST.md` records local dataset sizes and SHA-256 values.
- Verify sidecars with `sha256sum -c <file>.sha256`.
- Do not convert residual-energy ratios into accuracy, confidence, or
  probability claims.

## Documentation

- [Architecture](docs/architecture/RFVISION_ARCHITECTURE.md)
- [Data schema](docs/architecture/RFVISION_DATA_SCHEMA.md)
- [Hardware baseline](docs/hardware/BASELINE.md)
- [Development environment](docs/development/DEVELOPMENT_ENVIRONMENT.md)
- [Demo runbook](docs/development/DEMO_RUNBOOK.md)
- [Scientific validation status](docs/research/SCIENTIFIC_VALIDATION_STATUS.md)
- [Dependencies](docs/software/DEPENDENCIES.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## Provenance and licenses

All third-party code is attributed in `THIRD_PARTY_NOTICES.md`, with per-file
provenance in `docs/third_party/SOURCE_PROVENANCE.md`. RF Vision native code is
MIT (`LICENSE`). `thkimKETI/csi-sensing` was studied but no code was taken.
