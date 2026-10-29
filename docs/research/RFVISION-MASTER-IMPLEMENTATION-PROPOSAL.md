# RF VISION MASTER IMPLEMENTATION PROPOSAL

**Status: PROPOSAL ONLY — APPROVED FOR PLANNING, NOT YET APPROVED FOR
IMPLEMENTATION. No code, firmware, config, protocol, threshold, AP, wiring,
experiment, commit, or push was performed to produce this document.**

- Baseline: `main` @ `d1f12a5`; firmware SHA
  `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd`
  (re-verified read-only during inspection).
- Sources of truth: existing repository, validated acquisition foundation,
  `docs/research/RFVISION-ARCHITECTURE-NETWORK-AGNOSTIC-CHECKPOINT.md`,
  and the project owner's product/research decisions (master directive).
- Operating model on approval:
  `INSPECT → DECIDE → PROPOSE → APPROVAL → IMPLEMENT → VERIFY → REVERIFY → CONTINUE`.

## 1. Current state (verified read-only, not assumed)

- **Baseline matches the directive.** `main` HEAD `d1f12a5`, firmware SHA
  `0a490737…dd` re-verified. Validated foundation = two-node CSI
  acquisition (RFVISION-010): `web/source.py` (784 lines) →
  `web/dual_node.py` (256 lines) → `web/live_serial.py` (POSIX termios, no
  pyserial reset) → `csi/parser/*` → `ClockOffsetEstimator`
  (`localization/synchronization/sync.py`, 106 lines, rate-agnostic) →
  `contracts.py` v2 envelopes.
- **Working tree is dirty (pre-authorized Option B, uncommitted):**
  `web/source.py` single hunk `REC_MAX_SECONDS 30 → 120` +
  `tests/unit/test_live_provider.py` +29 lines (2 new tests: 75 s
  protocol-window honored, bound still enforced). No logic change.
  Disposition required (§9).
- **~20 untracked `docs/research/*.md` session reports** (E1/E2, recovery,
  readiness). Harmless but need a disposition rule (§9).
- **Downstream reality:** deterministic presence/motion/activity heuristics
  integrated but NOT VALIDATED; ML definitions only — **no trained artifact
  exists** (`*.pt/onnx/pkl` absent, Models tab locked,
  `model="none (heuristic)"`); 1-D position framework only; XAI interface
  only (`available:false`); 3D scene explicitly *"no bodies, no mesh, no
  pose"*; UI already honesty-labels (`NOT VALIDATED`, `UNCALIBRATED`,
  `UNKNOWN`).
- **Binding policy** (`docs/research/SCIENTIFIC_VALIDATION_STATUS.md`):
  only CSI acquisition is VALIDATED. Everything else NOT YET VALIDATED.
  Synthetic metrics never quotable. RFVISION-011 v1.4 is deliberately
  threshold-free; 011 stops at statistical evidence.
- **Known load-bearing risks:** dual-node transport fragility (HOME dual 0%
  SYNCED, storms, stuck buffers) — unresolved; spontaneous ESP hangs —
  unresolved; confidence percentages uncalibrated everywhere.

## 2. Checkpoint reconciliation (contradictions found)

The network-agnostic checkpoint's analysis is confirmed accurate **except
three stale paths** that must not propagate into implementation:

| Checkpoint claim | Reality | Correction |
|---|---|---|
| `web/nodes.py`, `web/serial_receiver.py`, `web/serial_config.py` | **Do not exist** (`ls web/` proves) | Actual: `csi/transport/nodes.py` (identity), `csi/capture/serial_receiver.py` (capture + `RawSessionWriter`), `web/live_serial.py` (transport) |
| `RawSessionWriter` in `web/serial_receiver.py:66-71` | Wrong path | `csi/capture/serial_receiver.py` |
| `web/nodes.py:60-74` identity discussion | Wrong path | `csi/transport/nodes.py:60-76` |

Confirmed accurate: firmware CASE_C mechanism, HOME-defaulted
constructors, gate semantics, sync analysis, downstream network-blindness,
RSSI-in-features exposure, 62-tone emergence. **Already implemented** (do
not rebuild): source-abstraction seed (`FakeLineSource`), session-split
datasets, offline fixture builder, envelope v2, 6-state provenance,
calibration flow. **Genuinely missing:** session profiles,
`NetworkContext`, wrap compensation, time-based drift, contextual sync,
leakage probes, RSSI ablation discipline, `CsiSource` interface,
`OfflineFileSource`.

## 3. Target architecture (directive §4, unchanged)

```text
RF SOURCE → CSI ACQUISITION → SOURCE ABSTRACTION → NETWORK CONTEXT/PROVENANCE
→ NORMALIZATION → SYNCHRONIZATION → RF FEATURES → CORE
→ PRESENCE/MOTION/ACTIVITY/SPATIAL → CONFIDENCE+XAI → 3D TWIN → SHOWCASE/RESEARCH
```

Router = measurement condition with a serial number, never a hidden
feature. Network context is provenance/validation/stratification/
diagnostics — never a silent shortcut feature.

## 4. Architecture gaps (showcase-blocking first)

1. **Showcase vertical slice incomplete:** 3D human = link abstraction only
   (correct per evidence, but directive asks for "3D HUMAN" — scope as
   honest link-figure, §7); trajectory = 1-D only; confidence
   uncalibrated; XAI unavailable; two-node → single-node degrade path
   exists in contracts/store but unproven under real node failure.
2. **Sync policy vs transport:** 2 ms / 64-sample rule fails under measured
   transport distress; no contextual policy.
3. **Network-agnostic host items:** no session profiles, no
   `NetworkContext`, no wrap handling, index-based drift, HOME defaults in
   code.
4. **Research hardening:** no leakage probe, no RSSI ablation harness, no
   context-columns policy, no leave-one-network-out eval.

## 5. Implementation phases (small vertical slices)

- **Phase 0 — Baseline hygiene.** Verify dirty Option B diff (run
  unit + integration suites, confirm 68+2 green), decide commit vs revert
  (§9), set untracked-docs rule. Touch: disposition only.
- **Phase 1 — Truthful showcase slice (priority).** Deterministic
  presence/motion → `RF EVIDENCE CONFIDENCE` (renamed, explicitly
  uncalibrated) → honest 3D link-scene + RF field strip + 1-D trajectory
  with persistence-fade → XAI "NOT AVAILABLE" states kept → two-node
  primary with proven degraded-single-node honesty. No new estimators, no
  thresholds changed.
- **Phase 2 — Network-agnostic host layer.** Session-profile config (HOME
  values out of constructors), `NetworkContext` capture/display,
  timestamp-wrap compensation, time-based drift, contextual sync policy
  behind feature flag with old policy default, geometry-aware dims. No
  firmware, no protocol change.
- **Phase 3 — Research-ready hardening.** Dataset context columns,
  stratified-split utilities, context-only leakage probe as eval gate,
  RSSI ablation harness, per-session-empty checklist support,
  leave-one-network-out eval scaffold.
- **Phase 4 — Deferred future (no code yet).** Phase features, 2-D/3-D,
  multi-person, room-photo twin init, pretrained-model adoption per
  directive §8 gates.

## 6. File-level changes (proposed, per phase)

- **P0:** `web/source.py`, `tests/unit/test_live_provider.py`
  (disposition only).
- **P1:** NEW `sensing/confidence/` (evidence-confidence aggregator,
  uncalibrated-labeled); EDIT `web/contracts.py` (confidence fields +
  degrade states), `web/server.py` +
  `web/static/js/tabs/{overview,sensing,rffield,localization,xai}.js`
  (honest states only), `sensing/state/state.py`
  (ABSENT/DETECTED/MOVING/STATIONARY/LOW_CONFIDENCE/EXITING + fade),
  `localization/tracking/position_filter.py` (persistence semantics).
  NO parser/sync/inference-math changes.
- **P2:** NEW `csi/source.py` (`CsiSource` protocol) +
  `config/session_profile.py`; EDIT `web/source.py` + `web/dual_node.py`
  (profile-fed validation), `localization/synchronization/sync.py` (wrap +
  time-based drift, additive), NEW `research/context.py` (`NetworkContext`
  frozen dataclass, provenance-only).
- **P3:** EDIT `ai/datasets/{collector,dataset}.py` (context cols),
  `ai/evaluation/evaluate.py` (leakage probe + ablation + LONO scaffold).
  No model-architecture changes.

## 7. Tests and validation strategy

Each slice: unit (new behavior + honesty states) → integration (synthetic
wire → UI payload, session-split, leakage-probe-must-fail-on-leaky-fixture)
→ contract checks → hardware-free runtime (fixture/simulated providers) →
architecture / scientific-integrity / regression reviews per directive
§14–15. Real-hardware runs only under already-frozen protocols (no new
experiments proposed). Verdict `PASS` only on all layers; otherwise
`FAIL → DIAGNOSE → FIX → VERIFY AGAIN`.

## 8. Risks

Dual-transport root cause dominates all timelines (unresolved,
network-independent); ESP hangs; hotspot rate personality untested (needs
authorized VCET session, not proposed here); conditioning-path leakage in
P3; scope creep of "3D HUMAN" into fabrication — mitigated by binding
honesty labels + directive §18 escalation rule 7 (stop if the only way to
succeed is to fabricate).

## 9. Decisions

**OpenCode decides autonomously:** module/file layout, naming, internal
APIs, test design, UI details, refactor within scope, slice decomposition,
P0 disposition recommendation (recommendation: **verify then commit**
Option B diff — bounded, tested, protocol-motivated — separately from P1).
**Requires human approval:** P0 commit vs revert; P1 scope lock (esp. "3D
HUMAN" = honest link-figure, no avatar/pose); any
frozen-protocol / firmware / hardware / threshold / methodology touch (none
proposed); provisioning-path selection (deferred decision checkpoint, no
action proposed); untracked-docs rule (recommendation: leave untracked, add
disposition note — or commit; owner call); P1→P2→P3 phase gates.

## 10. Paths

- **Immediate showcase:** P0 → P1 → hardware demo on HOME under existing
  validated acquisition (no new experiment).
- **Research-ready:** P2 → P3 → next protocol revision defines
  multi-network claims (011 untouched).
- **Deferred future:** phase features, 2-D/3-D, multi-person, photo-init
  twin, pretrained models — interfaces reserved only.

## 11. Remain untouched

Firmware, `sdkconfig`, acquisition parsing math, gate thresholds, sync
constants (until P2 flag), frozen `RFVISION-011*` / `PRESENCE-PILOT*`,
`research-data/`, historical artifacts, git history.

## 12. Decision log (seed; extend during implementation)

- *P0 commit recommendation:* Option B diff is bounded + tested +
  protocol-motivated → verify, then commit separately. Awaiting approval.
- *"3D HUMAN" scoping:* honest link-figure, no avatar/pose — evidence does
  not support more. Awaiting approval.
- *Checkpoint stale paths:* corrected in §2; implementation must use real
  paths only.
- *Provisioning path:* deferred to decision checkpoint; blocks
  multi-network research regardless of downstream readiness.

## 13. Environmental Reference & Obstacle-Sensing Roadmap (2026-10-29)

Planning update only. This section adds the environmental-reference track; it
does not supersede the earlier proposal status. No source, API, model, firmware,
hardware, network, trial, or evidence file was changed. Baseline:
`feature/rfvision-validated-react-ui` @ `b698e07`; offline suite last reported
`319 passed`; reference diagnostics focused suite `12 passed` during this
inspection.

Binding rule: **IMPLEMENTED ≠ OFFLINE_VERIFIED ≠ LIVE_VERIFIED ≠
SCIENTIFICALLY_VALIDATED**. No RF difference is obstacle detection, and no
current capability reconstructs room geometry.

### 13.1 Proven existing support

- Per-node measured CSI amplitude vectors already reach the frontend in
  `sensing.snapshot.payload.amplitudes`; A/B routing and isolation already
  exist.
- `sensing/reference.py` implements explicit `capture()`, `evaluate()`,
  `reset()`, robust per-tone median/MAD statistics, gain/structural residual
  separation, coverage checks, and `ABSENT/IMMATURE/INVALID/STALE/VALID`.
- `/api/v1/nodes` exposes node identity, MAC, port, observed BSSID/channel,
  tone count, validity, rates, gaps, and connection/source state.
- `LiveProvider.live_stats()` does expose `session_id`, but the node contract
  does not currently publish it; `GET /api/v1/experiment` reports
  `NO_ACTIVE_SESSION` during dual operation.
- The reference tracker is not connected to an API, runtime capture action,
  frontend, inference, or persistence. `/api/v1/nodes` has no session ID,
  expected BSSID/channel, tone-layout fingerprint, or reference state.

### 13.2 Decision table

| Requirement | Existing support | Proven gap | Minimum change (if later authorized) | Risk | Test |
|---|---|---|---|---|---|
| Measured A/B amplitude vectors | `payload.amplitudes` per node, existing A/B isolation | None for current 62/64-tone path | None | Low | Existing routing + contract tests |
| Robust reference statistics | `ReferenceTracker.capture/evaluate`, offline real-capture analysis | No runtime path | Reuse module; do not reimplement in JS | Medium | Existing 12 reference tests + malformed/stale cases |
| Explicit reference capture | Offline `capture()` only | No operator action, bounded window, or capture state | Add explicit capture-only state and window | Medium | Valid/insufficient/duplicate capture tests |
| Session identity | `session_id` in provider stats | Omitted from `/api/v1/nodes`; experiment is `NO_ACTIVE_SESSION` in dual | Additive session ID to node payload | Medium | Contract + cross-session invalidation tests |
| Network identity | Observed BSSID/channel per node; `/api/v1/network` target | No expected/observed pair on node payload | Add observable expected/observed provenance | Medium | Network-change invalidation tests |
| Tone configuration | Tone count only | No exact tone-layout/config fingerprint | Expose existing config identity if available; otherwise count/shape guard plus limitation | Medium | Incompatible-shape/config rejection |
| Current-vs-reference difference | `evaluate()` offline | No API/UI or operator-visible result | Single read-only comparison path bound to capture provenance | High | A/B independence, gain, coverage, invalid/stale |
| Stale/disconnected gating | Connection/source-state/freshness exist | Not bound to reference lifecycle | Gate comparison and require recapture | Low | Stale/disconnected tests |
| Obstacle detection | None | No ground truth or controlled trials | M3 experiments only; no threshold/classifier | High | Operator-confirmed trial-level evaluation |
| Spatial localization | Coarse uncalibrated zones only | No validated position estimate | M4 known-position study; may remain blocked | High | Held-out uncertainty/repeatability |
| Geometric reconstruction | Illustrative scene only | No validated spatial evidence | M5 deferred | High | No mesh without validated evidence |

### 13.3 Stage gates

#### M1 — Environmental baseline capture

Status: `OFFLINE_VERIFIED` (robust capture/evaluation statistics only; runtime
operator capture is deferred).

Goal: capture one bounded reference window from measured CSI, with no silent
first-frame baseline.

Required provenance where available: node ID/MAC, session ID, SSID/BSSID/
channel, CSI tone configuration, capture start/end and window, valid sample
counts, tone coverage, and signal quality.

Acceptance gate: explicit operator action; bounded window (start with 10–30 s);
at least 16 comparable vectors and 50% usable tones per node; identical vector
shape/tone layout; no mixed session/network/node; immutable capture; explicit
`ABSENT/IMMATURE/INVALID/STALE/VALID`; insufficient or incompatible references
are rejected, not degraded into a comparison.

Current blocker: no runtime capture path or session/tone-layout provenance in
the node contract. `ReferenceTracker` must not be auto-attached to live frames.

#### M2 — Environmental RF change detection

Status: `PLANNED` (comparison maths exists offline; no runtime/UI integration).

Goal: when a valid compatible reference exists, show independent A/B
current-versus-reference gain, structural disturbance, disturbed-tone fraction,
coverage, reference age, and state. Display no result when incompatible.

Acceptance gate: same node/session/network/tone layout; exact shape; coverage
threshold; stale/invalid explicitly neutral; A/B storage and rendering
independent; no detection threshold, classifier, position, or geometry; explicit
recapture after invalidation.

Boundary: a difference is “environmental RF change”, never “obstacle detected”.

#### M3 — Controlled obstacle validation

Status: `PLANNED`.

Goal: determine repeatability and false-alarm behaviour under operator-
confirmed ground truth.

Required trials: stable baseline; object introduction; object removal;
no-change control; human movement; fan/environmental interference. Repeat
trials, record fixed geometry/conditions, and evaluate at trial level on
held-out data. No detection claim before this gate.

#### M4 — Spatial localization feasibility

Status: `PLANNED`; current validated 3-D localization capability is `BLOCKED`.

Goal: test whether the available amplitude-only two-receiver CSI supports any
defensible object-position estimate. Require known-position experiments,
uncertainty estimates, repeatability, and held-out validation. Do not assume two
amplitude-only links uniquely determine 3-D position; phase/arrays/more links
would be a separate research decision.

#### M5 — Geometric reconstruction

Status: `BLOCKED`.

Goal: render approximate obstacle geometry only after M3/M4 produce validated
spatial evidence with stated uncertainty. Until then, no obstacle meshes,
coordinates, or reconstructed room geometry may be generated or shown as
measured.

### 13.4 Cross-cutting rules

- Preserve acquisition, parsing, synchronization, readiness, WebSocket,
  recording schemas, models, and the current A/B activity-history presentation.
- Invalidate references on incompatible session, node, network, tone layout, or
  stale/disconnected input; require explicit recapture.
- Keep references in-memory unless persistence is proven necessary for
  correctness.
- No synthetic CSI, fabricated reference values, inferred obstacle labels,
  coordinates, shapes, or room geometry.
- Any future runtime implementation must be additive, tested offline first, and
  must stop if it threatens the VCET demonstration.

### 13.5 Current decision

`IMPLEMENTATION_DEFERRED`: the reference algorithm is offline-capable, but the
runtime reference comparison is not demonstrably safe because session identity
and exact tone-layout provenance are missing from the frontend contract, and
there is no explicit capture API/window. Adding those plus a new comparison path
before the VCET demonstration would exceed the permitted minimal-risk scope.

Smallest justified next action: after VCET, add the additive per-node
`session_id` plus expected/observed network and tone provenance to
`/api/v1/nodes`, with contract and incompatibility tests, then reassess a
capture-only reference path.

---

**Awaiting approval:** (1) proceed with P0 verification + commit-or-revert?
(2) lock P1 scope as defined? (3) untracked-docs rule? On approval execute
PLAN → IMPLEMENT → VERIFY → REVERIFY → REGRESSION → REPORT per slice.
Final completion condition per directive §21:
`RF VISION TASK VERIFIED — READY FOR NEXT APPROVED TASK`.

## 14. Latest factual status addendum (2026-10-30)

Documentation-only status update; it does not approve implementation and does
not supersede the environmental-reference deferral.

- Baseline: `feature/rfvision-validated-react-ui` @
  `b698e079888717147210102afd49e8fc72d1efd5`; current checkpoint adds the
  verified source, tests, and documentation on top of that baseline.
- Real dual-ESP32 CSI acquisition, host synchronization, and `RF_READY` were
  verified in a prior live session. Independent A/B CSI delivery to Live
  Sensing and Visualization was verified in a prior live browser session; this
  checkpoint did not run a new hardware trial.
- WebSocket reconnect-budget exhaustion is corrected with indefinite capped
  backoff. The recording-finalization race was reproduced and corrected with a
  narrow lock; regression coverage compares metadata bytes/SHA against raw
  files.
- Verification: full Python suite **325 passed**; focused recorder/WebSocket
  suite **12 passed**; offline browser smoke **13/13** across the five React
  routes. These are engineering checks, not a new scientific validation.
- VCET reference trial `WT-20261029T121111Z`: raw parse yielded **11,027 A /
  11,559 B** CSI vectors. The `9,071`/`9,517` values in the original metadata
  were cumulative source counters, not trial totals. The later channel-6 live
  session is distinct from that channel-11 reference session; identifiers are
  retained only in local evidence.
- Two audio-guided `Nihaal` human-presence trials were completed
  (`WT-20261029T194753Z`, `WT-20261029T193657Z`). Relative RF activity was
  observed; human-presence association remains exploratory. Event timing and
  reference quality remain limiting. The supplementary trial's original
  ESP32-B metadata discrepancy is preserved with an append-only correction;
  no historical value was silently repaired.
- Boundary: Reference View waves and room geometry are illustrative. Human
  detection/tracking, coordinates, pose, obstacle detection, obstacle
  localization, and reconstruction are not validated. Obstacle reconstruction
  and new sensing features are deferred until after the demonstration.
- Detailed evidence bundles, raw CSI, logs, screenshots, and recovery snapshots
  are local-only; do not publish environment-identifying material.
