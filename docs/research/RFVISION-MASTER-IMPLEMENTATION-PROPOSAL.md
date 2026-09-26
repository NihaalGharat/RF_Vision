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

---

**Awaiting approval:** (1) proceed with P0 verification + commit-or-revert?
(2) lock P1 scope as defined? (3) untracked-docs rule? On approval execute
PLAN → IMPLEMENT → VERIFY → REVERIFY → REGRESSION → REPORT per slice.
Final completion condition per directive §21:
`RF VISION TASK VERIFIED — READY FOR NEXT APPROVED TASK`.
