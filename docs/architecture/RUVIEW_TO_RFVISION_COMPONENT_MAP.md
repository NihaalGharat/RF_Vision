# RuView → RF Vision Component Map (RFVISION-004)

Decisions: REUSE DIRECTLY | ADAPT | REIMPLEMENT | REFERENCE ONLY | REJECT.
Reasons are technical (compatibility, maintainability, license, burden),
never appearance. Upstream paths are snapshot-relative; pin commit before
extraction. Nothing copied during this operation.

## 1. UI shell & architecture — ADAPT

- `ui/index.html` + `ui/app.js` (WiFiDensePoseApp init) + `ui/style.css`
  (4,189-line token system, light/dark) + `ui/components/TabManager.js`
  (172 lines, DOM-query tabs, lazy SensingTab init, tab-change callbacks).
  ADAPT (not fork): RF Vision needs research panels (XAI, calibration,
  provenance) RuView lacks; restyle to RF Vision identity. Static tabs
  (`architecture/performance/applications`) have no JS class — do not
  mistake them for a framework.

## 2. Service layer — ADAPT (pattern) / REIMPLEMENT (endpoints)

- `ui/config/api.config.js` (URL builders), `services/api.service.js`
  (REST + Bearer interceptors), `services/websocket.service.js` (multiplex,
  heartbeat, backoff `[1,2,4,8,16,30]s ×10`, per-attempt ws-tickets),
  `services/health.service.js` (`/health/*` polling),
  `services/stream.service.js` (control plane), `utils/backend-detector.js`.
  ADAPT the patterns; REIMPLEMENT against RF Vision's own future API —
  our wire is serial-fed `CsiSample`, not their WS JSON.
- `services/ws-ticket.js` (single-use `?ticket=` auth, ADR-272):
  REFERENCE ONLY until RF Vision has any network API.
- `services/pose.service.js`, `model.service.js`, `training.service.js`,
  `services/websocket-client.js` (viz-page standalone): REFERENCE ONLY
  (pose/model/train surface has no RF Vision counterpart yet).
- `services/data-processor.js` (WS→Three.js adapter + demo poses):
  ADAPT the adapter shape for `SensingResult`→scene.

## 3. Live/simulated discipline — ADAPT (mandatory pattern)

- `utils/data-source-banner.js` (global banner, 4 states), per-tab source
  labels (`SensingTab._onStateChange`), header `utils/connection-status.js`,
  opt-in client simulation (`sensing.service.js`, off by default,
  `source: simulated` + `_simulated:true`), server provenance
  (`source_state: synthetic|live_verified|…`, `provenance.rs`).
  ADAPT all of it: RF Vision's claim policy (IMPLEMENTED ≠ VALIDATED,
  live-vs-simulated distinction) maps 1:1 onto this machinery. This is the
  single most valuable non-visual takeaway.

## 4. Sensing tab + HUD + signal viz — ADAPT

- `ui/components/SensingTab.js` (GaussianSplatRenderer + HUD wiring),
  `dashboard-hud.js`, `signal-viz.js` (30×40 heatmap, phase line, doppler
  bars, motion ring), `PoseDetectionCanvas.js`, `utils/pose-renderer.js`
  (custom canvas, zero chart deps). ADAPT: render OUR `FeatureVector`
  (180-d), amplitude/phase, RSSI sparkline, presence/motion state.
- `LiveDemoTab.js` (1,887 lines, orchestrates 5 services): REFERENCE ONLY
  (too coupled to their backend; do not port).

## 5. 3D scene — ADAPT (architecture), REIMPLEMENT (content)

- `components/scene.js` (renderer/camera/controls/lights loop),
  `environment.js` (8×6×3 m room, TX/RX cones, zones, heatmap planes),
  `body-model.js` (DensePose parts + COCO mapping, 6-person pool),
  `gaussian-splats.js` (shader Points signal field 20×20 + node markers).
  ADAPT the scene-graph architecture; REIMPLEMENT content for OUR link
  geometry (1-D A–B link, room sizes from calibration, uncertainty
  overlays). three.js via CDN importmap (0.160.0) — pin + vendor or
  npm-pin at implementation; legacy r128 UMD path REJECT.
- `observatory/js/*` (cinematic room, 6k lines), `pose-fusion/js/*`
  (incl. WASM attention), `dashboard/` (NV-magnetometer sim — unrelated),
  `v2/.../homecore-server/ui` (smart-home UI — unrelated), `mobile/`
  (Expo app): REJECT for this track (scope, burden, or wrong product).

## 6. Backend / sensing / firmware — REJECT (with narrow exceptions)

- Rust `wifi-densepose-sensing-server` (14k-line `main.rs`), all
  `v2/crates/wifi-densepose-*` DSP/vitals/aether/mat/meridian, Python
  PyO3 wheel, `firmware/esp32-csi-node` (S3/C6, UDP ADR-018):
  REJECT — incompatible silicon, transport, and format; validated
  `csi_recv_router` baseline stays. Do not port, do not buy boards.
- Narrow exceptions: `python/wifi_densepose/client/{ws,mqtt,primitives}.py`
  — REFERENCE ONLY for future protocol design; vitals DSP structure
  (preprocess → bandpass → zero-crossing/autocorr) — REFERENCE ONLY as
  algorithm notes, never code.
- `wifi_densepose/__init__.py` facade: REJECT (stale, broken at root).
- `wifi-veil/` (privacy shield): REFERENCE ONLY (ethics/privacy design
  input for human-sensing phases; no code needed now).

## 7. Mock/demo/data tooling — ADAPT (selectively)

- `utils/mock-server.js` (fetch/WS interceptor): ADAPT pattern for
  offline UI development against recorded `CsiSample` fixtures.
- `observatory/js/demo-data.js` (12 seeded scenarios): ADAPT the
  scenario-script idea for regression demos (our own data).
- `aether-arena/` (benchmark commons): REFERENCE ONLY (evaluation
  methodology input for later validation phases).

## 8. Tests & contract discipline — ADAPT

- `ui/services/*.test.mjs`, `ui/tests/*`, mobile jest suites (incl.
  `sensing_update` shape tests), `python/tests/test_client_ws.py`:
  ADAPT the practice — every future RF Vision endpoint/message gets a
  shape test before UI code depends on it.

## 9. Explicitly REJECT (recap)

Sensing backend, all DSP/vitals/pose/model code, all weights
(`*.safetensors/*.onnx/*.rvf`, HF `ruvnet/*` — unlicensed), S3/C6
firmware, `vendor/*` (empty submodules), `assets/*` (no grant),
`X Bot.fbx` (proprietary), FeitCSI binary (GPL), observatory/pose-fusion
pages, mobile app, dashboard (nvsim), homecore UI, training/model-registry
surface, HA/MQTT/Matter integrations.
