# RFVISION-004 — RuView UI / Architecture Audit Report

Operation: RFVISION-004-RUVIEW-AUDIT. READ-ONLY analysis; RF Vision tree
unmodified except this report + the three companion docs listed in §1.
No code copied, no installs, no builds, no hardware touched, no humans,
no training. Upstream: https://github.com/ruvnet/RuView.

**RFVISION-004 STATUS: COMPLETE — PROPOSAL ONLY. AWAITING USER APPROVAL
before any extraction or implementation.**

Companion docs (all new, all inside RF Vision):
- `docs/third_party/RUVIEW_REUSE_AND_LICENSE_AUDIT.md` (license audit)
- `docs/hardware/RUVIEW_RFVISION_HARDWARE_COMPATIBILITY.md` (HW compat)
- `docs/architecture/RUVIEW_TO_RFVISION_COMPONENT_MAP.md` (component map)
- `docs/architecture/RFVISION_UI_DESIGN_DERIVED_FROM_RUVIEW.md` (design)

## 1. Repository snapshot

- Source: `https://github.com/ruvnet/RuView`, `main` branch tarball
  (61 MB) fetched 2026-09-21 into `/tmp/ruview-audit/` (outside RF Vision;
  no `.git`, no submodules initialized). LIMITATION: tarballs carry no
  commit hash — pin an exact commit before any extraction.
- Snapshot root: `AGENTS.md CLAUDE.md Makefile PROOF.md README.md
  aether-arena archive assets benchmarks dashboard data docker docs
  examples firmware harness integrations logging monitoring plans plugins
  python references releases requirements*.txt scripts semconv templates
  tests tools ui v2 vendor verify wifi-veil wifi_densepose` (+ tarball).
- Size drivers (114 MB tree): `assets/` 26 MB, `docs/` 22 MB, `v2/`
  20 MB, `archive/` 13 MB (incl. 10 MB sample CSI JSON), `firmware/`
  7.4 MB. Models are KB-scale; `vendor/` is EMPTY (uninitialized
  submodules — 10 declared in `.gitmodules`).
- Core truth: the ACTIVE system is Rust-first (`v2/`, 70+ crates;
  `sensing-server/src/main.rs` 14,018 lines, 76 routes). Top-level
  `python/` is PyO3 bindings + clients, NOT a server; root
  `pyproject.toml`/`requirements.txt` are legacy; `archive/v1/` is
  deprecated; top-level `wifi_densepose/__init__.py` facade is
  stale/broken at root. `dashboard/` is an unrelated NV-diamond
  magnetometer sim; `v2/.../homecore-server/ui` is a smart-home UI;
  `aether-arena/` is benchmark commons; `wifi-veil/` is a privacy
  countermeasure. The audit target that matters is `ui/` + the sensing
  server contract.

## 2. RuView architecture

- Firmware (`firmware/esp32-csi-node`, ESP32-S3 prod / C6 research,
  ESP-IDF v5.4+, native CSI driver — not an esp-csi fork) → UDP binary
  ADR-018 (`0xC5110001` + I/Q, vitals `0xC5110002`, sync `0xC511A110`)
  → Rust server (UDP :5005 → per-node state → vitals/pose/field fusion →
  `SensingUpdate`) → HTTP :8080 + WS :8765 (`/ws/sensing`,
  `/api/v1/stream/pose|events`, `/health/*`, `/api/v1/*`) → `ui/` web app
  (services → tabs → Three.js scene + canvas viz). Optional MQTT/Matter/
  HA, OTA/WASM :8032, ESP-NOW mesh sync, mmWave/display/PIR extras.
- Serial carries logs + onboarding text ONLY (`RUVIEW_HELLO_OK_V1…`,
  115200 baud) — never CSI. This single fact rules out firmware/transport
  reuse.

## 3. UI architecture

- `ui/` (~23k core lines, zero `node_modules`): `index.html` (static
  tab buttons) + `app.js` (`WiFiDensePoseApp.init`: backend-detect →
  mock-or-health → banner → sensing) + `style.css` (4,189-line tokens,
  light/dark) + `config/api.config.js` (URL builders) +
  `services/` (12: api, websocket multiplex w/ heartbeat+backoff+tickets,
  sensing, pose, health, stream, model, training, data-processor,
  websocket-client, ws-ticket) + `components/` (15: TabManager — DOM-query
  tabs, lazy SensingTab, callbacks; Dashboard/Hardware/LiveDemo/Sensing/
  Training/Model/Settings tabs; scene/environment/body-model/
  gaussian-splats/signal-viz/dashboard-hud 3D modules; 1,887-line
  LiveDemoTab orchestrator; 1,552-line PoseDetectionCanvas) + `utils/`
  (22: mock-server, backend-detector, data-source-banner,
  connection-status, pose-renderer, theme, i18n EN/PL, perf-monitor,
  command-palette, PWA manifest+sw.js, …) + `tests/` + node `*.test.mjs`.
- `pose-fusion.html`, `observatory.html` (6k-line cinematic room),
  `viz.html` are SEPARATE pages (not tabs); mobile is an Expo app (~120
  files); `v2` homecore UI is panel-based JS-rendered (different product).

## 4. UX/design analysis

- Token system (`--space/--radius/--duration`, containers 640–1280),
  Inter/JetBrains-Mono (remote fetch), pill nav-tabs with badges/keyboard
  support, grid tab layouts, green/amber/purple/red status language,
  global + per-tab + header + per-frame source states, toasts +
  NotificationCenter + per-canvas error overlays, reconnect buttons,
  responsive breakpoints + reduced-motion + hamburger + PWA offline shell.
- Verdict: professional product console; directly adaptable as a pattern
  library, but identity, hierarchy (research-first), and honesty states
  (explicit no-hardware empty state) must be redesigned.

## 5. 3D visualization analysis

- `scene.js`: PerspectiveCamera(55, 8,7,10), ACESFilmic + PCFSoftShadow,
  OrbitControls, `onUpdate` loop. `environment.js`: 8×6×3 m room, TX/RX
  cones + path dashes, 3 zones, 20×15 heatmap planes, Y-up meters.
  `body-model.js`: 24 DensePose parts, T-pose meters, COCO17→room mapping,
  6-person pool w/ 3 s expiry. `gaussian-splats.js`: shader Points field
  20×20 + breath pulse + node markers + custom orbit. `signal-viz.js`:
  30×40 heatmap + phase line + doppler bars + motion ring.
- three.js sourcing is FRAGMENTED (r128 UMD + 0.160.0 importmap + r165 +
  npm 0.183.2) — pin ONE version at implementation. `X Bot.fbx` is
  Mixamo-proprietary (user-download only). Scene-graph module split
  (scene→environment→bodies→field) is the reusable architecture; all
  CONTENT (mesh-room, skeletons-as-claims) must be reimplemented for our
  1-D link + uncertainty rendering.

## 6. Backend/frontend contract

- HTTP: `/health/{health,ready,live,metrics,version}`,
  `/api/v1/{info,status,metrics}`, `/api/v1/pose/*` (current/analyze/
  zones/activities/historical/stats/calibrate), `/api/v1/stream/*`
  (status/start/stop/clients/broadcast/metrics), `/api/v1/models/*`,
  `/api/v1/train/*`, `/api/v1/recording/*`, `/api/v1/ws-ticket`
  (single-use WS tickets, ADR-272), `/api/v1/sensing/latest`,
  `/api/v1/{radar,csi/*,rf/nodes/mesh/vital-signs/edge-vitals,…}/latest`,
  OAuth, dev/config routes. (Server has 76 routes; UI consumes a subset;
  mobile paths partly stale/mismatched.)
- WS: `/ws/sensing` (canonical; `ping/pong`, `connection_established`,
  `sensing_update`, `pose_data`, `edge_vitals`), `/api/v1/stream/pose`,
  `/api/v1/stream/events`, `/ws/train/progress` (raw, no ticket/reconnect).
- Canonical `sensing_update` (`types.rs:119` struct, serde JSON):
  `{type, timestamp, source, tick, nodes[{node_id, rssi_dbm, position,
  amplitude[], subcarrier_count}], features{mean_rssi, variance,
  motion_band_power, breathing_band_power, dominant_freq_hz,
  change_points, spectral_power}, classification{motion_level,
  presence, confidence}, signal_field{grid_size[20,1,20], values[400]},
  vital_signs?, posture?, signal_quality_score?, pose_keypoints?,
  persons?[{id, confidence, keypoints×17, bbox, zone, position,
  motion_score}], estimated_persons?, node_features?[]}`.
- Provenance: `/api/v1/status → {source, source_state}` with
  `source_state ∈ {synthetic, live_verified, live_unverified, stale,
  disconnected}`; client maps to live/server-simulated; strict opt-in
  client sim (`?simulate=1` / localStorage, off by default) after a
  2026-08-28 misdiagnosis incident. Four UI indicator layers.
- vs RF Vision (`docs/architecture/RFVISION_DATA_SCHEMA.md`,
  `unity/integration/MESSAGE_FORMATS.md`): DIRECTLY COMPATIBLE — none
  (different transports/stacks). ADAPTER REQUIRED — `sensing_update`
  field groups → `SensingResult`/`RealtimeEvent` (mappable: nodes≈link
  state, features≈FeatureVector, classification≈presence/motion,
  signal_field≈heatmap view, tick/timestamp≈seq/ts). CONCEPT ONLY —
  endpoint layout, ticket-auth idea, stream control plane, zone/pose REST
  shape. INCOMPATIBLE — UDP/serial wire, ADR-018 binary vs 25-col CSV,
  zone/pose/model/train APIs (no RF Vision counterpart).

## 7. Hardware compatibility

Full analysis in `docs/hardware/RUVIEW_RFVISION_HARDWARE_COMPATIBILITY.md`.
One line: every hardware layer differs (S3/C6 vs D0WD-V3; custom UDP
firmware vs validated `csi_recv_router`; UDP binary vs serial CSV;
115200-logs vs 921600-data; any-AP+self-ping vs Xiaomi-ch1+ping-trigger;
1–6-node mesh+ESP-NOW vs single link). Firmware/transport/format are
REJECT; reusable across the gap: frame-envelope shape, endpoint layout,
sync DESIGN notes, single-channel + self-stimulus discipline.

## 8. CSI compatibility

- RuView: ADR-018 LE binary (magic/node/ant/nsub/freq/seq/RSSI/noise/
  PPDU/flags + I/Q), 56 (S3) / ≤256 HE (C6) subcarriers, UDP :5005 @~20 Hz,
  vitals/feature/fused/compressed packet family.
- RF Vision: ASCII `CSI_DATA,<25 cols>` @921600 8N1, LLTF len 128 → 64
  complex int8, `EspCsvAdapter` strictness (25 cols, int8 range, len match).
- No shared parser, no shared transport, no shared subcarrier grid.
  Common ground is CONCEPTUAL (both: int8 I/Q arrays + RSSI + seq +
  per-node/per-link state + strict input validation). Any future network
  envelope should mirror `sensing_update` field groups to keep adapters thin.

## 9. Scientific claim audit

| Claim | RuView implementation? | Evidence? | Grade |
|---|---|---|---|
| Presence | edge variance+hysteresis + fusion + AETHER head | deterministic proof PASS; AETHER 82.3% held-out (100% retracted) | IMPLEMENTED, VALIDATED (narrow) |
| Localization/multi-node/mapping | multistatic fusion + TDM + field model + MAT triangulation | ESP-NOW sync measured (99.56%, 2-board logs); NO held-out position error | IMPLEMENTED; sync VALIDATED; accuracy CLAIMED-ONLY |
| Pose 17-kp | Candle Conv1d+MLP (`pose_v1`, 496 KB) | PCK@20 3.0% / PCK@50 18.5% (target ≥35%) — weak | IMPLEMENTED (weak); SOTA numbers are OUT-OF-DOMAIN (MM-Fi/Atheros≠ESP32) |
| Vitals BR/HR | bandpass + zero-crossing/autocorr (+firmware tier) | DSP benches only; groundtruth harness w/o paired results; "experimental, not medical" | IMPLEMENTED, NOT validated |
| Activity/fall/count | motion-band + accel + heuristic + counter cog | host latency 305 µs; accuracy tests are flags/dedup only | IMPLEMENTED; latency VALIDATED-on-host |
| 105 edge "cogs" (sleep/apnea/emotion/weapon…) | DSP skeletons + disclaimer gate | none (`PROOF.md` honest: UNVALIDATED) | CLAIMED-ONLY |
| Identity/re-ID | AETHER + bfld risk | explicitly RETRACTED ("gap≈0.0005") | CLAIMED-ONLY (retracted — commendable) |
| World-model mapping | `ruview-unified` encoder+Gaussian+synth | SYNTHETIC/L0 by crate contract | CLAIMED-ONLY |

RF Vision lesson: their `PROOF.md` honesty (MEASURED/CLAIMED/GATED +
retractions) is the model for our claim board; their weak-pose UI is the
anti-pattern (18.5% PCK must never get a production-looking skeleton
view — which maps exactly onto our IMPLEMENTED ≠ VALIDATED policy).

## 10. License audit

Summary; full text in `docs/third_party/RUVIEW_REUSE_AND_LICENSE_AUDIT.md`:
root MIT (© 2024 rUv); `v2/` MIT-OR-Apache-2.0; wifi-veil dual; no
GPL/AGPL deps (FeitCSI-GPL is external-tool-only — keep boundary);
UI libs (three MIT, Lit BSD-3, Lucide ISC, TF/MediaPipe Apache-2.0)
inferred upstream, not vendored — retain notices. DO NOT TOUCH:
`vendor/*` (empty — audit upstream pins), `assets/*` (no grant),
`X Bot.fbx` (proprietary), ALL weights/checkpoints + HF `ruvnet/*`
(no weight license), FeitCSI binary. RF Vision caution: keep any
MIT-derived web UI license-separated from the PyQt6 (GPL) path.

## 11. Reusable components (REUSE DIRECTLY → none verbatim; ADAPT list)

Tab shell + lazy lifecycle; service-layer pattern (api/ws/health/stream/
sensing); URL-builder config; reconnect/backoff/heartbeat; ws-ticket auth
IDEA; 4-layer source-transparency machinery (banner/labels/dot/provenance —
  most valuable non-visual takeaway); scene-graph module split;
HUD + signal-viz patterns; custom-canvas 2D (no chart deps); token theming
+ status language; mock-interceptor + seeded-scenario demo patterns;
shape-test discipline (contract tests before UI). All ADAPT, none forked.

## 12. Components to adapt (require RF Vision rework)

Everything in §11 (identity restyle; research panels added; endpoints
reimplemented against our future API; 3D content rebuilt for 1-D link +
uncertainty; dashboard re-homed on packets/adapter/validation metrics;
hardware tab re-homed on ESP32+router+serial; three.js pinned to ONE
version and vendored/lockfiled).

## 13. Components to reimplement (concepts only, our code)

Network API + envelope (`sensing_update`-shaped, `RealtimeEvent`-compatible);
3D room/link/uncertainty content; research panels (provenance, calibration,
XAI, experiment, validation, debug); offline-fixture player (recorded
`CsiSample`, never synthetic-as-live); future multi-node sync (design
notes only now).

## 14. Components to reject

Sensing backend (Rust server), ALL DSP/vitals/pose/model code, ALL
weights, S3/C6 firmware, `vendor/*`, `assets/*`, `X Bot.fbx`, FeitCSI
binary, observatory/pose-fusion pages, mobile app, nvsim dashboard,
homecore UI, training/model-registry, HA/MQTT/Matter, Rust rewrite of
anything, any board purchase, any baseline change.

## 15. RF Vision mapping (20 requirements → RuView coverage)

1 System Overview — ADAPT (DashboardTab pattern). 2 Live CSI Status —
ADAPT (SensingTab + banner + `is_online` analog). 3 Node Status — ADAPT
(HardwareTab pattern, single-node content). 4 CSI signal viz — ADAPT
(signal-viz + PoseDetectionCanvas pattern). 5 Subcarrier heatmap — ADAPT
(30×40 pattern → our 64). 6 Amplitude — ADAPT. 7 Phase — ADAPT (gated).
8 Motion — ADAPT (motion ring/bars → our FeatureVector). 9 Presence —
ADAPT (state + confidence; no new claims). 10 Activity/state — PANEL
RESERVED (heuristic only until validated). 11 Localization — REIMPLEMENT
(1-D + uncertainty; no mesh visuals). 12 2D room map — REIMPLEMENT (our
geometry). 13 3D room — ADAPT shell / REIMPLEMENT content. 14 RF field —
ADAPT (gaussian-splat pattern → our subcarriers). 15 Human tracking —
ABSENT until validated (weak-pose rule). 16 XAI panel — REIMPLEMENT (no
equivalent). 17 Confidence/uncertainty — ADAPT (their confidence →
mandatory bands + caveats). 18 Experiment controls — REIMPLEMENT (session/
dataset/record flow). 19 Dataset/session info — REIMPLEMENT (SHA-256
provenance). 20 Research/debug — ADAPT (debug panel + event log patterns).

## 16. Proposed RF Vision UI architecture

Web research console (adapted `ui/` architecture) alongside the existing
PyQt6 bench view (license-separated): tab shell (Overview / Sensing /
RF Field / Localization / XAI / Experiments / Hardware / Models-reserved /
Settings) → service layer (config-builder, api, ws-multiplex, health,
sensing-adapter `SensingResult`→scene) → 2D canvas viz → three.js link
scene (ONE pinned version) → research panels (§15 items 16–20). Backend
stays Python (`live_app` lineage); network envelope mirrors
`sensing_update` groups over `RealtimeEvent`. Full translation in
`docs/architecture/RFVISION_UI_DESIGN_DERIVED_FROM_RUVIEW.md`.
Conceptual layout per brief §14 (sidebar tabs + 3D twin + bottom
CSI strip + node/RF status rails). NOT implemented in this operation.

## 17. Proposed technology stack (proposal, not decision)

Thin web UI: dependency-free custom canvas + ONE pinned three.js
(vendored/lockfiled, single version) + no chart lib + no framework
(their zero-`node_modules` `ui/` proves this scales to our needs).
Python backend (`live_app` lineage) + shape-tested JSON contracts.
PyQt6 retained bench-side, license-isolated. No npm build, no Rust, no
mobile, no PWA commitment until approved. License check (MIT vs PyQt6-GPL
separation) precedes any file creation.

## 18. Integration risks

- Contract drift (their mobile-vs-server path mismatch is the warning):
  mitigate with shape tests before UI code.
- Three-version fragmentation: mitigate by pinning one + vendoring.
- Porting `#CSI`/CSV assumptions into a WS-JSON UI: mitigate with a
  single `SensingResult`→scene adapter boundary.
- Scope contagion (mesh/fleet/training/model-registry surface): mitigate
  with the §14 rejection list enforced at review.
- Offline/CDN risk (unpkg/cdnjs + Google Fonts): mitigate by vendoring
  or lockfile + self-hosted fonts (OFL preserved).
- Baseline erosion (pressure to "just flash S3 firmware"): mitigate —
  003R stays on D0WD-V3 + `csi_recv_router`, no exceptions.

## 19. Dependency risks

- `vendor/*` submodules unaudited (empty snapshot) — never depend on
  them without per-repo pinned audit.
- CDN/npx floating versions (`three@0.160.0` today, r128 elsewhere) —
  pin everything.
- Weights/model URLs (`huggingface.co/ruvnet/*`) unlicensed — never fetch
  into the research pipeline.
- PyQt6-GPL vs MIT-derived web code — architectural separation until a
  licensing decision is recorded.
- FeitCSI-GPL boundary — external-tool-only if ever touched.

## 20. Performance considerations

- Their measured numbers (host latency 305 µs, wheel ≤5 MB discipline,
  pixelRatio≤2 caps, ResizeObserver-driven canvases, lazy tab init,
  500 ms sim cadence, 30 s health cadence) are sane budgets to adopt.
- Our constraint is serial-fed ~100 Hz × 64-subcarrier ASCII parsing
  (the 003 anomaly showed the cost of assuming the stream) — the UI must
  degrade by STATING stall (`is_online`-style freshness timeout ≤3 s),
  never by interpolating fiction. Backpressure: drop-to-latest on viz,
  lossless record on disk (separate paths, as their recorder/broadcast
  split).
- 3D budget: single link scene is trivially cheap vs their 6-person +
  400-splat field — performance is not a risk; honesty states are.

## 21. Recommended implementation sequence (post-approval only)

1. Pin upstream commit + record provenance; settle web-vs-PyQt6 license
   separation. 2. Define network envelope (`sensing_update`-shaped over
   `RealtimeEvent`) + shape tests FIRST. 3. Shell + tab lifecycle + global
   banner + health polling (against stub). 4. 2D viz (heatmap/sparkline/
   bars from recorded fixtures). 5. Three.js link scene (pinned, single
   link + uncertainty). 6. Research panels (provenance → calibration →
   experiment → validation → debug → XAI). 7. Offline-fixture mode +
   mock interceptor. 8. Live serial bind (only after 003R re-capture
   passes). No step renders unvalidated sensing; each step ends green.

## 22. FINAL DECISION MATRIX

| RUVIEW COMPONENT | → RF VISION ACTION | TECHNICAL REASON |
|---|---|---|
| UI shell + TabManager + theming | → ADAPT | Clean DOM-tab lifecycle + token system; needs research identity/panels |
| Service layer (api/ws/health/stream) | → ADAPT pattern / REIMPLEMENT endpoints | Patterns sound; their endpoints serve a different stack |
| WS multiplex + backoff + tickets | → ADAPT / REFERENCE | Resilient realtime discipline; tickets only when we have a net API |
| Source-transparency machinery | → ADAPT (mandatory) | Maps 1:1 onto IMPLEMENTED≠VALIDATED + live-vs-sim policy |
| SensingTab + HUD + signal-viz | → ADAPT | Direct pattern for our FeatureVector/amplitude/RSSI views |
| LiveDemoTab orchestrator | → REFERENCE ONLY | 1,887 lines coupled to their backend; do not port |
| Scene-graph module split | → ADAPT architecture | Swappable scene→room→body→field layers; proven separation |
| 3D content (mesh room, skeletons) | → REIMPLEMENT | Our geometry is one 1-D link; skeletons would fabricate claims |
| three.js (one pinned version) | → ADAPT (vendored/lockfiled) | MIT, capable; their 3-concurrent-version sprawl rejected |
| `sensing_update` envelope | → ADAPT field groups | Keeps future adapter thin over our `RealtimeEvent` |
| Endpoint layout `/health/*` `/api/v1/*` | → ADAPT | Sane operations surface for our Python backend later |
| Mock interceptor + demo scenarios | → ADAPT pattern | Offline UI dev + regression demos from OUR fixtures |
| Shape/contract tests | → ADAPT practice | Prevents their mobile-vs-server drift failure |
| Rust backend + all DSP/vitals/pose | → REJECT | Wrong silicon/transport/format; validated baseline stays |
| S3/C6 firmware + UDP path | → DO NOT REPLACE PROVEN ESP-CSI BASELINE | 003R continues on D0WD-V3 + `csi_recv_router` |
| Weights/checkpoints/HF models | → REJECT (unlicensed) | No grant; also out-of-domain accuracy |
| `vendor/*`, `assets/*`, `X Bot.fbx`, FeitCSI bin | → REJECT | Unaudited / no-grant / proprietary / GPL |
| observatory/pose-fusion/mobile/nvsim/homecore | → REJECT | Wrong scope/product for this track |
| Training/model-registry/HA/MQTT/Matter | → REJECT | No RF Vision counterpart; scope contagion |
| AETHER/vitals DSP structure | → REFERENCE ONLY | Algorithm notes only, never code |
| `PROOF.md` honesty discipline | → ADAPT (claim board) | MEASURED/CLAIMED/GATED + retractions = our model |
| Rust rewrite / board purchase / reflash | → REJECT | Out of scope, out of authority, out of need |
