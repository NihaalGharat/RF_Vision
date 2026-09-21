# RFVISION-005 — RuView-Inspired UI Implementation Report

Operation: RFVISION-005 (approved follow-up of RFVISION-004 audit).
No human sensing, no localization experiments, no retraining, no Unity
scenes, no hardware changes, no live capture (003 gate respected).

**RFVISION-005 STATUS: COMPLETE — UI: PASS.**

## 1. RuView commit used

`dd02efe2fe129ae8068e9b805ea35aaa660e47dd` (`main`, 2026-09-16) —
https://github.com/ruvnet/RuView, MIT © 2024 rUv. Pinned in
`docs/third_party/RUVIEW_IMPLEMENTATION_PROVENANCE.md` before any
adaptation. Audited snapshot = `main` tarball 2026-09-21 (HEAD unchanged
since 09-16, so tarball ≡ this commit).

## 2. Source components adapted (patterns reimplemented, zero copied lines)

Tab lifecycle (TabManager.js) → `web/static/js/tabs.js`; service layer
(api.config.js, api/websocket/health/stream/sensing services) →
`js/{config,api,ws,health}.js`; reconnect/backoff/heartbeat discipline →
`js/ws.js` + `web/ws.py`; source-transparency machinery (banner, labels,
provenance.rs) → `js/{store,banner}.js` + six-state contracts;
scene-graph layering (scene/environment/gaussian-splats/signal-viz) →
`js/scene3d.js`; custom-canvas 2D (pose-renderer, sparklines) →
`js/viz2d.js`; seeded demo scenarios → `tools/build_offline_fixture.py`;
`sensing_update` field groups → `web/contracts.py` payload shapes;
endpoint grouping (`/health/*`, `/api/v1/*`, `/ws/sensing`) →
`web/server.py` routes (RF Vision-native payloads).

## 3. Source provenance / 4. License status

Per-file SOURCE/COMMIT/LICENSE/ORIGINAL→NEW/MODIFICATIONS: `THIRD_PARTY_
NOTICES.md` §5 + `docs/third_party/RUVIEW_IMPLEMENTATION_PROVENANCE.md`.
three.js r160 vendored (`web/static/vendor/`, MIT, header retained).
Nothing else taken: no backend/DSP/weights/assets/firmware. License
separation: MIT web console kept independent of the PyQt6 (GPL-isolated)
bench view; no shared UI code.

## 5. UI architecture

`web/server.py` (stdlib http.server + hand-rolled RFC 6455 codec
`web/ws.py`, one port 8130) ← providers (`web/source.py`:
disconnected/fixture/simulated; live REFUSED) ← contracts
(`web/contracts.py`, v1, six source states) → envelopes
(`realtime/protocol/event_envelope.py` v1) → `web/static/js/` shell
(TabManager, store, banner, health, api, ws) → 9 tabs + canvas/three viz.
Run: `python3 -m web.server` (repo root) → http://127.0.0.1:8130/.

## 6. Data contracts

REST: `/api/v1/{health,status,sensing/latest,telemetry,stream/status,
stream/start,stream/stop,source,experiment,calibration,localization,xai}`.
WS `/ws/sensing`: envelope stream + `ping`/`stream:start|stop`/`set_source`
commands. Stream-carried `sensing.snapshot`/`localization.update`/
`system.status` REQUIRE `payload.source_state`. XAI returns
`{available:false,status:"NOT AVAILABLE"}`; localization is `link-1d`
with nulls; unknowns render UNKNOWN. STALE computed at 3 s freshness both
ends. Unity contract untouched (`MESSAGE_FORMATS.md` still authoritative;
a future Unity client can consume the same envelopes over this WS).

## 7. Three.js version

r160, exactly one, vendored locally, importmapped. Details:
`docs/software/THREEJS_VERSION.md`.

## 8. New files / 9. Modified files

- NEW: `web/{__init__,contracts,source,ws,server}.py`;
  `web/static/{index.html,css/{tokens,app}.css,
  js/{config,api,ws,store,tabs,banner,health,viz2d,scene3d,app}.js,
  js/tabs/{overview,sensing,rffield,localization,xai,experiments,
  hardware,models,settings}.js, vendor/{three.module,OrbitControls}.js}`;
  `web/fixtures/offline_demo.{jsonl,manifest.json}` (120 frames via real
  adapter, seed 7, sha256 in manifest);
  `tools/build_offline_fixture.py`;
  `tests/unit/test_web_contracts.py` (28), `tests/integration/
  test_web_server.py` (11); docs: this report, `RUVIEW_IMPLEMENTATION_
  PROVENANCE.md`, `docs/software/THREEJS_VERSION.md`.
- MODIFIED: `THIRD_PARTY_NOTICES.md` (§5 RuView entry). Nothing else —
  backend, DSP, firmware, PyQt view, Unity docs untouched.

## 10. Tests

`python3 -m pytest tests/ -q` → **107 passed** (68 pre-existing + 39 new:
26 contract/schema/state/codec/hygiene + 11 live-server HTTP/WS + 2
frontend-hygiene incl. relative-import guard). New tests cover §21:
schema validity, source-state handling, stale/disconnect, malformed,
empty, fixture playback, viz input shapes, uncertainty shape, XAI state.

## 11. Screenshot/demo status

Headless-Chrome verified (real render, zero console errors): Overview
(banner + pills + UNKNOWN discipline), Sensing (40-frame heatmap over 54
valid subcarriers, RSSI sparkline, unvalidated-field bars + caveat),
RF Field (dashed UNKNOWN room, router/ESP32 nodes, link, amplitude
field strip, HUD, 2D room). Screenshots are volatile (`/tmp/rfv-*.png`,
not committed). During verification TWO real bugs were found and fixed:
(1) tab modules imported `./` instead of `../` (blank shell — now guarded
by `FrontendHygieneTests`); (2) fixture replay had no cadence (busy-loop
pump — now 10 Hz). WS reconnect skew under virtual-time screenshots is a
test-harness artifact, not a product bug (CDP live run: connected).

## 12. Known limitations

No live path (gate); fixture is synthetic-via-real-adapter (labeled, never
evidence); presence/activity/position render as UNKNOWN/nulls (honest, per
policy); 3D shows one link with no bodies/pose; Models tab locked;
no PWA; no mobile; light-theme token typo fixed pre-commit; virtual-time
headless runs distort WS timing (documented artifact).

## 13. Rejected RuView components (enforced)

Rust backend, all DSP/vitals/pose/models, all weights, S3/C6 firmware +
UDP/ADR-018, `vendor/*`, `assets/*`, `X Bot.fbx`, FeitCSI, observatory/
pose-fusion pages, mobile app, nvsim dashboard, homecore UI,
training/model-registry, HA/MQTT/Matter, Rust rewrite, board purchases,
baseline changes — none touched, none installed, none vendored.

## 14. Next phase

RFVISION-003R (hardware triage + golden re-capture) unblocks the live
provider gate; then: bind `LiveProvider` to the validated receiver,
promote `LIVE_UNVERIFIED`→`LIVE_VERIFIED` criteria, CSI-SENSE-001 session
bookkeeping in Experiments tab, calibration-driven geometry into room
views, validated-model unlock of Models/XAI tabs. No sensing claims until
adapter acceptance passes on real frames.

## 15. Git commit

Phase commit: `106f16c` ("feat: add RuView-inspired RF Vision research
interface foundation"), recorded here in the follow-up commit per the
002/003 pattern.
