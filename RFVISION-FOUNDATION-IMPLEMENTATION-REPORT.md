# RFVISION-FOUNDATION-IMPLEMENTATION-REPORT (RFVISION-FOUNDATION-002)

## 1. Operation summary

Consolidated the RFVISION-REPO-FOUNDATION-001 analysis into one
authoritative repository at `~/Desktop/RF Vision`
(`main` branch). Extracted the approved minimum-useful components
(esp-csi acquisition verbatim; Human-Sensing chain adapted + fixed;
CSI-Tool idioms re-implemented; csi-sensing excluded), added native glue
(adapter, validation, protocol, XAI seed, experiment framework), wrote
68 passing tests, and committed a clean foundation. No hardware touched,
no CSI captured, no models trained on real data, no experiments run.

## 2. Final repository location

- Project root: `~/Desktop/RF Vision`
- Git root (verified `git rev-parse --show-toplevel`): same path
- Remote: none configured (local-only; see §21-equivalent note below)

## 3. Git status

- Branch `main`, working tree clean after commit. No competing RF Vision
  git roots (checked `~/Desktop`, `~/Documents`; only audit docs in
  `~/Documents/RFVISION-REPO-FOUNDATION-001/` and read-only upstream
  snapshots in `/tmp/` — both outside the project by design).
- Identity is repo-local (`RF Vision Foundation <rfvision@localhost>`);
  global git config untouched. git binary used: user-space install
  (`~/.local/gitroot`, no root needed).

## 4. Final architecture

`docs/architecture/RFVISION_ARCHITECTURE.md` (+ schema
`RFVISION_DATA_SCHEMA.md`). One pipeline, one firmware, one adapter;
`dsp/` naming deviation documented (`dsp/README.md`).

## 5. Integrated repositories

- espressif/esp-csi @ `8633d671` (Apache-2.0) — firmware + viewer + docs
- everythingfreee/ESP32-WiFi-CSI-Human-Sensing @ `d978e103` (MIT) — full
  Python chain + config + reference firmware
- StevenMHernandez/ESP32-CSI-Tool @ `cce5b1a0` (MIT) — re-implemented
  host idioms + citations + format specimen

## 6. Extracted components

29 files placed per `docs/third_party/SOURCE_PROVENANCE.md`: csi_recv_router
firmware (6 files, verbatim, upstream layout), csi_viewer.html, 14 adapted
Python modules, config pair, live_app, dashboard GUI, AP reference
firmware, receiver reference firmware, 3 reference scripts, 6 background
docs, 2 bibtex, 1 CSV specimen, 3 license texts. Native additions (12):
ESP-CSV adapter, validators, capture helpers, transport constants,
amplitude/phase/filter front-ends, presence/motion/activity/state split,
geometry/1-D/sync, XAI, event envelope, recorder, synth generators.

## 7. Rejected components

- csi-sensing code/weights/thresholds (restrictive view-only license).
- CSI-Tool firmware (ESP-IDF v4.3, unbuildable, buggy).
- Human-Sensing Arduino receiver as default (reference only).
- esp-radar closed-component demos, esp-crab, duplicate parsers, CUDA stack.

## 8. Source provenance — `docs/third_party/SOURCE_PROVENANCE.md`

## 9. License findings

Apache-2.0 + MIT combine cleanly (notices preserved, headers intact,
texts in `docs/third_party/licenses/`). No copyleft anywhere. csi-sensing
fully excluded. Project LICENSE is MIT with placeholder holder
`RF Vision Contributors` — **user must confirm the copyright holder**.
PyQt6 (GPL/commercial) isolated to optional `requirements-gui.txt`.

## 10. Dependency structure

Split pins (`requirements-base/gui/ml/dev.txt`), documented in
`docs/software/DEPENDENCIES.md`. Tested set: numpy, scipy, pandas,
scikit-learn, PyYAML, pyserial, joblib, pytest (Python 3.14, Ubuntu).
torch + PyQt6 optional extras.

## 11. CSI compatibility

Adapter A→`CsiSample` (`csi/parser/esp_csv_adapter.py`) with counters;
both wire paths proven equivalent in integration tests; formats spec in
`csi/formats/WIRE_FORMATS.md`. Raw format never altered.

## 12. Data-schema design — `docs/architecture/RFVISION_DATA_SCHEMA.md` (v1)

## 13. Test infrastructure — 68/68 green

`python3 -m pytest tests/ -q`: adapter, parser math, preprocessing
(incl. bug-regression tests), 180-d contract, sensing math, localization,
envelope, helpers, config, XAI, tools, receiver single-fire, heuristic +
stub-model engine loops, dual-path pipeline agreement, plus a manual
train→evaluate smoke on synthetic data (F1 1.0 on separable blobs —
harness proof only, never evidence).

## 14. Unity integration foundation

Message formats (`unity/integration/MESSAGE_FORMATS.md`) + envelope v1 +
digital-twin interface spec. No scenes/assets (scheduled phase).

## 15. Research infrastructure

Baseline protocol template, metadata schema v1, config overrides,
analysis rules, dataset/report/publication staging (raw outside git).

## 16. Known limitations

- Downstream (sensing→XAI) NOT YET VALIDATED; position 1-D only;
  activity heuristic-only; phase gated; GUI untested headless (no PyQt6
  in this env); adapter golden-tested on synthetic + needs live-CSI
  vector; `LICENSE` holder placeholder; no remote configured.

## 17. Unimplemented areas

Multi-node sync/protocol binding, 2-D/3-D localization, heatmap RF tab,
SHAP/LIME XAI, digital twin, Unity scenes, experiment execution, Git LFS
decision, `requirements.lock` freeze.

## 18. Files created — ~95 (see `git show --stat HEAD`)

## 19. Files modified (post-extraction fixes)

`serial_receiver.py` (dedup), `preprocessing.py` (counter/key/telemetry),
`inference_engine.py` (split/scaler), `config/settings.py` + `default.yaml`
(path/key), all cross-module imports → absolute, `signal/` → `dsp/`.

## 20. Files excluded — §7 list; upstream `.git`/artifacts never copied.

## 21. Git commit hash

- Foundation commit: `COMMIT_HASH_PLACEHOLDER`
- (Recorder commit, if any, follows in history.)

## 22. Recommended next development phase

RFVISION-003 (proposed): live-CSI golden test (record 60 s on baseline
hardware → adapter acceptance vector, raw stays external); GUI bring-up
in a Qt env; calibration dry-run without subjects; freeze
`requirements.lock`; configure remote + LFS policy. Still no sensing
claims until CSI-SENSE-001 protocol executes with session-split scoring.
