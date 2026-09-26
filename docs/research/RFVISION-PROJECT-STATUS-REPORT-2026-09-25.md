# RFVISION — PROJECT STATUS REPORT

- **Date:** 2026-09-25 (UTC)
- **Branch:** `main`
- **HEAD:** `1711c9e` — feat: reference-matched instrument UI (icon rail, 5 destinations, research/system split)
- **Prior commits:** `51684bd` (minimal-optimal UI revamp) · `2f2a227` (truthful showcase foundation P1, contract v3, UNCALIBRATED) · `d1f12a5` (validated two-node CSI acquisition foundation)
- **Type:** Status report including RFVISION-012 unknown-WiFi work: implemented, verified, flashed, evidence-fixed (all uncommitted).

---

## 1. Working tree

- Tracked modifications (2 files, task-authorized):
  - `firmware/esp32/csi_recv_router/main/app_main.c` (+318/−2: NVS/UART provisioning + 3 evidence-backed fixes — `%s` net-status, provisioning quiet window, race-absorbing join + non-aborting fallback)
  - `web/server.py` (+39, three additive routes)
- New files (all task-required): `csi/transport/network_context.py`,
  `csi/transport/rf_readiness.py`, `csi/transport/provisioning.py`,
  `web/network.py`, 4 unit-test files,
  `RFVISION-012-UNKNOWN-WIFI-PROVISIONING-REPORT.md`,
  `RFVISION-012-END-TO-END-VERIFICATION-REPORT.md`,
  `RFVISION-012-NEW-WIFI-FLASH-FIXES-PHASE-REPORT.md`.
- No commit, no push performed (not authorized).

## 2. Test health

- `python3 -m pytest tests/ -q` → **240 passed** (196 pre-existing + 44 new), re-verified after every change.
- Firmware `idf.py build` (ESP-IDF v5.4) → **SUCCESS**, binary `5203638a…` (756,560 bytes, hash-verified flashes).
- Live discovery: `NETWORK_DETECTED` — `wlp0s20f3 | Nihaal |
  8c:53:c3:5b:e1:59 | ch 1 | 2412 MHz | 2.4GHz`.
- Live routes: `/api/v1/network` → DETECTED; `/api/v1/rf_readiness` →
  `NODE_MISSING, rf_ready:false` without session (honest).
- `CONTRACT_VERSION` stays 3; no existing payload shape changed.

## 3. Module inventory (present)

- `sensing/` — presence, motion, activity, confidence, state, `inference_engine.py`
- `dsp/` — preprocessing, amplitude, phase, filtering, features (`feature_extraction.py`), `README.md`
- `localization/` — calibration (`calibrate.py`), geometry, positioning, synchronization, tracking
- `ai/` — xai (`xai.py`), evaluation (`evaluate.py`), training, datasets, inference
- `csi/transport/` — nodes (identity), serial_config, **network_context**,
  **rf_readiness**, **provisioning** (bold = new, RFVISION-012)
- `web/` — server (+3 network routes), **network.py** (new), contracts (v3),
  source, dual_node, live_serial (all preserved)
- `web/static/js/tabs/` — 12 tabs including `research.js` / `system.js` split
- Firmware `csi_recv_router` — validated CSI/ping path preserved; NVS
  runtime provisioning additive; Kconfig fallback (`Nihaal`) intact;
  `sdkconfig.defaults` still credential-free.

## 4. Hardware state (verified live)

- ESP32-A (`b0:3f:d3:70:20:3c` @ usb-0:5.4 → `/dev/ttyUSB1`) and ESP32-B
  (`04:b2:47:20:1a:dc` @ usb-0:1 → `/dev/ttyUSB0`) both flashed with
  `5203638a…`, both streaming CSI on Nihaal, both answering `RFV_NET`
  correctly. Node B recovered from a stale-NVS boot-loop via the fixed
  fallback (zero panics since).
- 76 s dual session on Nihaal: both `LIVE_VERIFIED`, 7492/5811 valid CSI,
  BSSID/channel match, `SYNCED` (jitter 159/253 µs ≤ 2 ms) →
  genuine `RF_READY, degraded:false`.
- Node B flash needed 4 attempts (transient USB-serial flakiness on
  `/dev/ttyUSB0`, classified environment; right device confirmed each time).

## 5. Research posture

- Frozen protocol `docs/research/RFVISION-011-PROTOCOL-v1.4.md` + pilot `RFVISION-011-PRESENCE-PILOT-v1.0.md` present and **untouched**.
- `research-data/` contains `rfvision-011`, `rfvision-011-presence`, legacy sets (`legacy-csi-sense-001`, `legacy-csi-verify-001`), `rfvision-003/003r-c2/010b/010dual`, plus `MANIFEST.md` / `README.md` — untouched.
- `experiments/analysis/` holds only `README.md` — 011 analysis scripts not yet written.
- Tools research `RFVISION-TOOLS-RESEARCH-002-RUVIEW-RUVECTOR.md` complete: zero ADOPT verdict (8× REFERENCE, 7× DEFER, 9× REJECT groups).

## 6. Acquisition baseline (per `RFVISION-CONTEXT.md` §§9–10)

- Two-node ESP32 serial CSI, ~100 Hz class, 62 complex subcarrier tones, seq/BSSID/sync validation, raw capture provenance.
- Sync policy (64 obs / 2 ms MAD) and gate policy unchanged.
- Known limitations remain documented: occasional print fragmentation, short soak gaps, transport/load sensitivity (plus `/dev/ttyUSB0` flakiness observed during flashing).

## 7. NOT YET VERIFIED

- New-network provisioning leg: owner chose phone hotspot, credentials
  staged in a 0600 file (never in chat/logs/Git), but the hotspot SSID
  was not broadcasting at last scan. Pending: hotspot ON → provision A+B
  → laptop switch → dual-session CSI/sync/`RF_READY` → change-detection →
  NVS-restore regression on Nihaal.
- Frontend "CONNECT RF NODES" control omitted (UI workstream boundary).

## 8. Scientific integrity

- PASS — no thresholds, protocols, datasets, or claims touched; no results manufactured; frozen-protocol discipline preserved; negative/honest states (NODE_MISSING, PROVISIONING_FAILED, fallback warnings) reported, never masked; every firmware change evidence-backed by observed boot/serial logs.

---

*End of report. No commit, no push performed.*
