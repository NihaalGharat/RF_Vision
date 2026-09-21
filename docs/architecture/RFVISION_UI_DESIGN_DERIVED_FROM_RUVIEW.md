# RF Vision UI Design Derived from RuView (RFVISION-004)

Conceptual translation only — NO implementation in this operation. Target
layout from the operation brief (§14) is retained; this file records what
to keep, what to change, and the RF Vision-only panels RuView cannot supply.

## 1. Principles to RETAIN from RuView

- Tab shell with lazy init + tab-change lifecycle (their `TabManager`:
  DOM-query tabs, per-tab init/teardown, change callbacks).
- Service layer separation (api / websocket / health / stream / sensing),
  URL-builder config, reconnect-with-backoff + heartbeat discipline.
- Four-layer source transparency: global banner + per-tab label + header
  dot + per-frame provenance flag (`live` vs `simulated` vs `reconnecting`
  vs `unreachable`). Non-negotiable for our claim policy.
- 3D scene-graph layering: base scene (camera/lights/controls) →
  environment (room/nodes/zones) → bodies → signal-field overlay, each a
  swappable module (`scene.js` / `environment.js` / `body-model.js` /
  `gaussian-splats.js` pattern).
- Custom-canvas 2D viz (no chart dependency): sparklines, heatmaps, bars.
- Token-based theming (`style.css` `:root` tokens, light + dark), status
  color language (green live / amber reconnecting / purple simulated /
  red error), reduced-motion respect, keyboard navigation, PWA shell.
- Shape-tested contracts: every message/endpoint gets a test before UI
  depends on it.

## 2. Principles to CHANGE

- Identity: RF Vision research instrument, not product console. No
  marketing tabs, no model-marketplace/Training surface, no HA/Matter
  panels, no multi-product pages (observatory/mobile/nvsim equivalents).
- Research-first information hierarchy: provenance, calibration state,
  uncertainty, and experiment context are PRIMARY (header-level), not
  buried in settings.
- Honest states: RuView's `simulated` reached only via opt-in flag after
  the 2026-08-28 misdiagnosis incident — keep that strictness; add an
  explicit `no-hardware` empty state (our 003 capture failure is the
  reference case: the UI must say "no valid frames", never render fiction).
- Single-link first: our geometry is a 1-D A–B link, not their 3–6-node
  mesh. The 3D view must visualize ONE link + uncertainty honestly until
  multi-node exists. No mesh visuals without mesh hardware.
- Amplitude-first: phase gated by policy; pose/vitals/activity panels stay
  ABSENT until independently validated (their weak-pose lesson: PCK@50
  18.5% shipped-looking UI would be a claim violation here).

## 3. Components to REUSE (adapted)

Tab shell, service-layer pattern, health polling, reconnect machinery,
source banner + provenance flags, scene-graph module split, HUD pattern,
signal-viz pattern (heatmap/phase-line/sparkline), mock-interceptor
pattern for offline dev, token theming, toast/notification pattern.

## 4. Components to REDESIGN

- 3D content: our room/link geometry, node A–B markers, position +
  UNCERTAINTY rendering (confidence interval on the link, not a dot
  pretending precision), RF-field plane from OUR subcarriers.
- Dashboard: research metrics (packets/malformed/rate/latency, validation
  warnings, adapter rejection counts) instead of product telemetry.
- Hardware tab: our single ESP32 + router path, serial status, firmware
  identity (esp-csi `8633d671`), NOT their fleet/mesh view.

## 5. RF Vision-specific panels (no RuView equivalent)

1. Provenance panel: firmware commit, ESP-IDF version, adapter version,
   capture SHA-256, config snapshot — every claim traceable.
2. Calibration panel: room geometry, node positions, thresholds, guided
   flow output (extends `localization/calibration/`).
3. XAI panel: `XaiResult` (method, scores, CAVEATS rendered mandatorily).
4. Localization-uncertainty view: raw vs filtered position + confidence
   band on 1-D link, then 2-D/3-D when validated.
5. Experiment panel: session/dataset info, record control (into
   `~/RFVision-Research-Data/`, never git), run notes.
6. Validation panel: test-suite state, adapter stats, claim-status board
   (IMPLEMENTED vs VALIDATED per feature — the anti-weak-pose device).
7. Debug panel: serial stream inspector, validation warnings, event log
   (`RealtimeEvent` types).

## 6. Data views (mapped to our schema)

- `CsiSample` → subcarrier amplitude heatmap + RSSI sparkline + per-packet
  validation flags.
- `FeatureVector` (180-d) → motion/temporal/spectral bars + presence/
  movement state + probabilities.
- `SensingResult`/`SystemState` → HUD + status grid + connection state.
- `LocalizationResult` → 1-D link view (+uncertainty); 2-D/3-D reserved.
- `RealtimeEvent` envelope → event stream / activity log.
- `sensing_update` (RuView) → our future network envelope SHOULD mirror
  its field groups (tick/nodes/features/classification/signal_field) where
  mappable, to keep the adapter thin.

## 7. Technology direction (proposal, not decision)

- Web UI (adapted `ui/` architecture) over the PyQt6 dashboard for the
  research console: MIT three.js + dependency-free custom canvas keeps the
  stack light and license-clean vs PyQt6-GPL isolation burden. PyQt6 view
  retained for bench-side use; the two must not share UI code until the
  licensing question is settled.
- three.js pinned (single version, vendored or lockfiled — their three
  concurrent versions r128/0.160.0/0.183.2 is the anti-pattern).
- Backend stays Python (`live_app` lineage) serving adapted endpoints;
  Rust rewrite explicitly out of scope.
- No build-system commitment in this operation (no installs, no scaffold).

## 8. Sequencing pointer

Details in main report §21: contracts first (envelope + shape tests),
then shell + banner + health, then 2D viz, then 3D link scene, then
research panels, then offline-fixture mode. No step renders unvalidated
sensing.
