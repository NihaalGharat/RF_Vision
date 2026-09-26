# RF VISION — UI REVAMP READINESS NOTE (post-P1)

**Status: HANDOFF NOTE ONLY. No Revamp implemented (separate task).**
P1 commit: truthful showcase foundation (contract v3). This note is the
§17 deliverable: what the Revamp inherits, must preserve, and must not
touch.

## 1. Current UI architecture

- Dependency-free frontend (`web/static/`): `app.js` boot →
  `SourceStore` (`store.js`, 6 provenance states + STALE timeout) →
  `TabManager` (`tabs.js`, `init/onEvent/onState/onShow/onHide`) →
  9 tabs. Frames flow backend contract → store → `dispatchEvent`.
- REST (`api.js`) for slow state (2 s poll); WebSocket (`ws.js`) event
  stream for frames. Canvas 2-D via `viz2d.js`; 3-D via `scene3d.js`
  (Three.js r160, vendored locally).

## 2. Preserve

- `store.js` provenance discipline + STALE computation + banner wiring.
- Contract envelope shape (`sensing.snapshot` + `source_state` always).
- All honesty labels: NOT VALIDATED / UNCALIBRATED / UNKNOWN /
  NOT AVAILABLE / NO VALIDATED MODELS / ROOM UNKNOWN / PHASE GATED.
- `scene3d.js` single-link scene + uncertainty-box + HUD pattern.
- `viz2d.js` null→placeholder discipline (`drawBars` UNKNOWN slots).

## 3. Likely replaced

- Tab layout/navigation, card grid, CSS visual system, hero section.
- Sensing-tab card arrangement (P1 additions are functional, unstyled).
- 3-D scene dressing (NOT the link-figure honesty model — see §6).

## 4. P1 data/state contracts now available

`sensing.snapshot` payload (contract v3) gained additive keys:
`presence_state` (6 states + UNKNOWN), `rf_evidence_confidence`
(0–1 or null) + `confidence_calibration` (always UNCALIBRATED),
`provenance` (UNKNOWN/TRANSPORT/RF-INFERRED), `node_mode`
(UNKNOWN/SINGLE/DUAL/SINGLE-DEGRADED), `evidence_statement`
(canned factual sentence), `trail` (1-D positions, oldest first, [] =
none). Old fixture envelopes may lack these keys — always fall back
(`??`), never assume presence. `/api/v1/health` may report
`degraded` (node down). `/api/v1/xai` stays NOT AVAILABLE.

## 5. 3-D scene capabilities supported

One link only: amplitude field strip, position marker + uncertainty box,
HUD extras. P1 feeds `presence_state (RF-INFERRED, UNCALIBRATED)` into
the HUD. No bodies/mesh/pose exist anywhere — the Revamp must not add
any human geometry beyond the honest link-figure (marker + state label).

## 6. Scientific honesty states the new UI must preserve

- Presence/motion/position unvalidated until a frozen protocol says
  otherwise. Confidence is UNCALIBRATED — never render as probability
  (no % without the UNCALIBRATED tag; bars show raw 0–1).
- UNKNOWN stays UNKNOWN (no interpolation of missing trail/confidence).
- STALE/DISCONNECTED/SIMULATED badges on every live view.
- XAI tab: NOT AVAILABLE + evidence sentence (factual, not explanatory).
- Degraded node = visible banner/err state + derated confidence.
- Health `degraded` must surface, not be smoothed over.

## 7. Known UI technical debt

- No JS runtime in dev env (no `node`): JS changes verified by review +
  balance checks only — the Revamp should add a syntax/lint step.
- No browser test harness; tabs poll on independent 2 s timers (drift).
- Fixture envelopes predate v3 (missing showcase keys by design —
  recorded history is immutable).
- `position` in live snapshots is None (no models); 2-D room draws link
  ends only.

## 8. Recommended Revamp scope

Restyle + restructure around the P1 showcase states (hero = presence
state + RF Evidence Confidence + node mode), unify polling, add a
degraded-mode banner, keep every §6 label. No new data semantics.

## 9. Dependencies / blockers

- Dual-transport root cause (unresolved) dominates live two-node UX.
- No trained models → position/trail empty in live use; design empty
  states first-class.
- Provisioning-path decision (firmware) gates multi-network work, not UI.

## 10. Explicitly NOT to change during redesign

- Backend contracts (`web/contracts.py`), acquisition (`web/source.py`,
  `csi/`, `localization/synchronization/`), inference math
  (`sensing/`, `dsp/`), frozen protocols, firmware, thresholds,
  `research-data/`. The Revamp is presentation-only: if a state cannot
  be rendered from contract v3 + REST, the answer is a new display of
  UNKNOWN, never a backend semantic change smuggled into a UI task.
