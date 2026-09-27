# RFVISION-TOOLS-RESEARCH-002 — RuView + RuVector Technical Evaluation

- **Operation:** RFVISION-TOOLS-RESEARCH-002 (RESEARCH ONLY)
- **Date:** 2026-09-23
- **Upstream inspected:** `https://github.com/ruvnet/RuView` (`main`, live 2026-09-23),
  `https://github.com/ruvnet/RuVector` (`main`, live 2026-09-23)
- **Prior work built upon:** `docs/research/RFVISION-004-RUVIEW-AUDIT-REPORT.md`
  (2026-09-21, UI/architecture audit — not repeated here),
  `docs/third_party/RUVIEW_REUSE_AND_LICENSE_AUDIT.md`,
  `docs/hardware/RUVIEW_RFVISION_HARDWARE_COMPATIBILITY.md`,
  `docs/architecture/RUVIEW_TO_RFVISION_COMPONENT_MAP.md`
- **Method:** read-only web/API inspection. No clone, no install, no execution of
  third-party code, no RF Vision source modification. RF Vision baseline established
  at module-structure level (directory inventory + package READMEs); module file
  contents were NOT audited in this operation.
- **Status:** COMPLETE — PROPOSAL ONLY. No adoption, no integration, no next phase
  without explicit approval.

> Central question: "What, if anything, should RF Vision actually use from these
> repositories, and why is that use necessary?"
>
> Answer: **Nothing is necessary NOW. No ADOPT. Selected methodology patterns are
> REFERENCE for current/next-phase work; algorithmic and infrastructure items are
> DEFERRED to their owning future phase; platform, firmware, model, and claim
> items are REJECTED.**

---

## 1. Executive summary

1. **RuView** is a product-grade, Rust-first WiFi-sensing platform (ESP32-S3/C6 →
   UDP binary → Rust server → WS/HTTP → web UI) with a large DSP/inference
   surface: six peer-reviewed CSI algorithms (`wifi-densepose-signal`), vitals
   extractors, a contrastive 128-dim CSI encoder, per-room calibration/enrollment
   framework (`wifi-densepose-calibration`), evidence/OOD/counterfactual crates,
   and a 105-module edge catalog. Its honesty documentation (retracted 100%
   presence claim, PCK@20 3.0% first-cut pose disclosure) is exemplary.
2. **RuVector** is a generic Rust-native agent-memory vector substrate (HNSW,
   ONNX embeddings, graph, temporal-coherence, SONA learning, snapshots,
   witness logs). It contains **zero RF/CSI content**. RuView is built on it
   (signal pipeline uses `ruvector-mincut/attention/solver`; train/mat use
   `ruvector-temporal-tensor`). MIT licensed, active (4.5k stars, 601 forks,
   3,243 commits) but self-documents incomplete surfaces (compaction not wired,
   incremental snapshots incomplete, Raft incomplete).
3. **Current necessity is NONE.** RF Vision's NOW phase (RFVISION-011 spatial
   discriminability, drift quantification, reproducible trial analysis) is not
   blocked by any problem these repositories solve, and RF Vision already owns
   the module skeleton (`dsp/`, `sensing/`, `localization/`, `ai/`) that any
   future adoption would extend — never replace.
4. **Verdict counts:** ADOPT 0 · ADAPT 0 (code) · REFERENCE 8 · DEFER 7 ·
   REJECT 9 (groups). All REFERENCE items are ideas/patterns to consult when
   their owning work begins, not code to port.

---

## 2. Current RF Vision baseline relevant to this evaluation

| Capability | RF Vision current state (structure-level, 2026-09-23) | Phase owner |
|---|---|---|
| Acquisition | Validated 2-node ESP32 serial CSV @ ~100 Hz, 64 complex int8 tones, seq/BSSID/sync validation, raw capture provenance (context §9–10) | NOW (done) |
| Preprocessing / amplitude / phase / filtering / features | `dsp/preprocessing.py`, `dsp/amplitude/`, `dsp/phase/`, `dsp/filtering/`, `dsp/features/feature_extraction.py` exist | NOW (owned) |
| Presence / motion / activity / confidence / state | `sensing/presence/presence.py`, `sensing/motion/motion.py`, `sensing/activity/`, `sensing/confidence/`, `sensing/state/`, `sensing/inference_engine.py` exist | NEXT (owned) |
| Calibration / geometry / positioning / sync / tracking | `localization/calibration/calibrate.py`, `geometry/`, `positioning/`, `synchronization/`, `tracking/` exist | FUTURE (owned) |
| XAI / evaluation / training / datasets | `ai/xai/xai.py`, `ai/evaluation/evaluate.py`, `ai/training/`, `ai/datasets/`, `ai/inference/` exist | NEXT/FUTURE (owned) |
| Trial analysis | `experiments/analysis/` — **empty** (rules require session splits, checksums, cross-session reporting before claims) | NOW (011) |
| Network/source architecture | Source-agnostic direction defined; no vector/graph memory anywhere | FUTURE |
| Stack | Python + stdlib HTTP/WS + vanilla JS; NumPy/SciPy/pandas; sklearn/Jupyter/statsmodels/PyWavelets conditional; **no Rust toolchain, no ONNX runtime, no vector DB** | Protected |

Implication: every candidate below is judged against an owned skeleton. Replacement
of any validated component is off the table; the only open question is whether an
external *idea* improves a *future or current* task enough to justify its cost.

---

## 3. RuView evaluation

### 3.1 What it is (live evidence, 2026-09-23)

- Product sensing platform, not a research prototype: ESP32-S3/C6 firmware
  (ESP-IDF, native CSI driver) → UDP binary ADR-018 → Rust sensing server →
  HTTP :8080 + WS :8765 → web UI / HA / Matter / mobile. Serial carries
  logs+onboarding ONLY (004 §2) — transport/firmware reuse already REJECTED.
- Documented pipeline (README "How It Works"): mesh TDM capture → multi-band
  fusion (3 ch × 56 = 168 virtual subcarriers) → multistatic N×(N−1)
  attention-weighted fusion → **Coherence Gate** → DSP (Hampel, SpotFi,
  Fresnel, BVP, spectrogram) → RuVector AI backbone → NN → pose/vitals/room.
- Scale since 004: `v2/crates/` now includes `wifi-densepose-calibration`,
  `wifi-densepose-signal`, `-physics`, `-sar`, `-bfld`, `-aether`, `-mat`,
  `-ruvector`, and `ruview-{evidence,ood,counterfactual,groundtruth,witness,
  attest,certify,scorecard,infogain,track,twin,unified,memory,spatial-memory,
  ontology,policy,placement,offaxis,active}`. Breadth confirms product scope;
  each crate below was judged individually, not as a bundle.
- Scientific posture: honest retractions (100% presence → 82.3% held-out
  temporal-triplet; pose_v1 PCK@20 3.0% disclosed; MM-Fi 82.69% explicitly
  out-of-domain for single-ESP32 claims). `PROOF.md` MEASURED/CLAIMED/GATED
  discipline stands as the model for our claim board (004 §9).

### 3.2 Candidate-by-candidate assessment

#### R1 — Six-algorithm DSP core (`wifi-densepose-signal`) → REFERENCE
- Contents (crate README, live): SpotFi conjugate multiplication (`csi_ratio`),
  Hampel filter, Fresnel-zone model (FarSense), STFT spectrogram, WiDance
  variance-based subcarrier selection, Widar-3.0 BVP; plus `CsiProcessor`,
  `PhaseSanitizer`, `MotionDetector`, amplitude/phase/Doppler/PSD features.
  License MIT OR Apache-2.0.
- Relevance test: our `dsp/` skeleton exists; the NOW-phase question is whether
  any *named, peer-reviewed* operator we lack would change an 011 conclusion.
  It would not — 011 uses raw + baseline-relative amplitude with trial-pair
  distances, deliberately representation-minimal. No blocking problem exists.
- Scientific compatibility: compatible *as literature* — every operator traces
  to a published paper (SpotFi SIGCOMM'15, FarSense MobiCom'19, Widar MobiSys'19).
  Concern: subcarrier selection is post-hoc tone selection by another name —
  must never feed 011 inference (frozen constraint: no post-hoc top-k).
- Recommendation: **REFERENCE**. When (not now) our filtering/feature work needs
  a named operator, consult the papers first, the crate second, and reimplement
  in Python against our 64-tone serial data. Never port Rust DSP into the stack.

#### R2 — Calibration/enrollment framework (`wifi-densepose-calibration`) → REFERENCE
- Contents (crate `lib.rs` header + module list, live): "Teach the room before
  you teach the model." Empty-room baseline (their ADR-135) → guided anchors
  with adaptive quality gate (`anchor`, `enrollment`) → transceiver-geometry
  record + fixed-length conditioning embedding (`geometry`, `geometry_embedding`)
  → labelled feature extraction (`extract`) → bank of small specialists + 
  confidence-gated mixture runtime (`specialist`, `bank`, `runtime`) →
  `CalibrationCertificate` with tiers/evidence levels/signatures.
  Invariant: **honest `STALE` degradation when the baseline drifts.**
- Relevance test: this is the closest conceptual mirror of our baseline/drift
  philosophy (§8) found anywhere — certificates, anchor quality gates, and
  STALE-on-drift map 1:1 onto our permanent/adaptive baseline + drift-vs-spatial
  question. But it serves multi-node mesh + specialist *models* (breathing/
  posture/presence heads) we have not validated and do not need in 011.
- Recommendation: **REFERENCE** (strongest idea-level finding). When our
  `localization/calibration/` work activates, borrow three patterns only:
  (1) versioned calibration records with evidence tiers, (2) admission quality
  gates on calibration captures, (3) explicit STALE state on drift. Our code,
  our data, our thresholds — none of theirs.

#### R3 — Presence head + phase-variance fallback → REFERENCE (NEXT phase)
- Contents (README table, live): trained presence head (82.3% held-out
  temporal-triplet, retracted single-class 100%) + a model-free phase-variance
  fallback needing ~30 s ambient calibration; `MotionDetector` with confidence
  in the signal crate.
- Relevance test: presence is NEXT-phase, gated behind 011 spatial evidence.
  No current need. The fallback's *form* (variance vs ambient window +
  hysteresis — consistent with 004's edge variance+hysteresis note) is the
  transferable part, not its constants.
- Recommendation: **REFERENCE** for NEXT-phase presence design. No thresholds,
  no weights, no heads adopted.

#### R4 — Contrastive CSI embeddings (128-dim, HF `ruvnet/wifi-densepose-pretrained`) → DEFER
- Contents: 12.2M steps / 60K frames / 610K triplets, 82.3% temporal-triplet,
  8 KB int4 variant, per-node LoRA adapters. Published `model.safetensors`
  header currently NUL-padded and unloadable (their issue #1522) — maturity flag.
- Relevance test: embeddings answer a question we have not asked (representation
  learning before measurement understanding). ML philosophy (§24) blocks
  promotion before evidence; leakage rules (§11: session/network stratification)
  are unaddressed for our 6-zone trial design. Out-of-domain risk: trained on
  their mesh/geometry, not our single-link 64-tone serial data.
- Recommendation: **DEFER** to post-localization representation research, with
  leakage-probe prerequisites. Weights additionally carry the 004 no-grant
  caution — never fetch into the pipeline.

#### R5 — Vitals extractors (breathing 0.1–0.5 Hz / HR 0.8–2.0 Hz) → DEFER
- Contents: bandpass on wrapped phase, circular variance, zero-crossing BPM;
  `pip install ruview` Python API (`BreathingExtractor`, `HeartRateExtractor`).
  004 grades vitals IMPLEMENTED, NOT validated (DSP benches only, no paired
  ground-truth results; "experimental, not medical").
- Recommendation: **DEFER** (vitals are FUTURE scope; unvalidated upstream).
  Algorithm notes only if vitals ever activate.

#### R6 — Evidence / OOD / counterfactual / witness crates → REFERENCE (ideas) / DEFER (machinery)
- Structure (API listings, live): `ruview-evidence` (36 KB single-module
  evidence bundle), `ruview-ood` (`domain`, `gate`, `certificate` — OOD gating
  with certificates), `ruview-counterfactual` (`hypothesis`, `infer` —
  counterfactual reasoning), `ruview-witness`/`attest` (attestation chain).
- Recommendation: **REFERENCE** the *concepts* (evidence bundles with
  certificates; OOD-gate framing for our drift-vs-spatial comparison;
  counterfactuals as the only XAI form that respects "correlation ≠ causation").
  **DEFER** all machinery — Rust, unvalidated, and our XAI phase requires
  validated models first. No code, no dependency.

#### R7 — Deterministic proof pattern (`verify.py` + `expected_features.sha256`) → REFERENCE (NOW-adjacent)
- Contents (README "Results & proof"): one-command deterministic pipeline replay
  with SHA-256 comparison; benchmark-proof ADR-168; 33-row witness attestation
  matrix (WITNESS-LOG-028); MetaHarness `claim-check`/`verify` operators.
- Relevance test: `experiments/analysis/` is EMPTY and its README already
  mandates checksums + session splits. A hash-pinned replay pattern for the
  forthcoming 011 analysis scripts is the single closest-to-NOW useful idea.
- Recommendation: **REFERENCE** — when 011 analysis is written (separate task),
  mirror the pattern (pinned inputs → deterministic script → published digest).
  Nothing to change today; no code exists to apply it to.

#### R8 — Coherence Gate (accept/reject measurements, multi-day stability) → REFERENCE
- Contents: pipeline-stage gate claimed to hold stability "for days without
  tuning" (README; no independent evidence inspected).
- Recommendation: **REFERENCE** as a design note for future long-running
  capture hygiene. Unvalidated stability claim — treat as hypothesis, and any
  future gate must be traceable per §8 (never silent tuning to amplify effects).

#### R9 — REJECT group (platform, claims, unlicensed, out-of-scope)
**REJECT**, each for an independent load-bearing reason:
1. S3/C6 firmware + UDP/ADR-018 transport + serial-CSV mismatch — every
   hardware layer differs (004 §7); validated `csi_recv_router` stays.
2. Rust sensing server + 76-route API + WS tickets — wrong stack; Python backend
   is protected architecture.
3. All weights/checkpoints/HF models — no weight license (004 license audit);
   pose_v1 weak (PCK@20 3.0%, runtime stub); MM-Fi SOTA out-of-domain
   (multi-antenna NIC ≠ ESP32 single-link).
4. Pose/vitals/activity/fall/count/105-cog claims — unvalidated or
   future-scope; adopting any would violate the staged progression (§3) and
   IMPLEMENTED≠VALIDATED policy.
5. Training pipelines (MM-Fi/Wi-Pose, tch/CUDA) — ML-before-evidence (§24).
6. HA/MQTT/Matter/mobile/PWA/nvsim/homecore/observatory — wrong product scope.
7. `vendor/*` (incl. ruvector submodule pin), `assets/*`, `X Bot.fbx`,
   FeitCSI boundary — unaudited / no-grant / proprietary / GPL (004 §10).
8. OccWorld TransVQVAE world model — synthetic-by-contract; digital-twin rules
   (§26) forbid adopting unvalidated reconstruction.
9. Rust rewrite of anything / board purchase / reflash — out of authority and
   need; frozen constraints (§17, §29).

---

## 4. RuVector evaluation

### 4.1 What it is (live evidence, 2026-09-23)

- Self-description: "Rust native substrate for fast local decisions and agent
  memory" — local ONNX embeddings (`all-MiniLM-L6-v2`), HNSW + flat indexes,
  collections/namespaces, graph + hypergraph (`ruvector-graph`), hybrid
  sparse-dense, temporal-coherence (recency decay + coherence gating),
  SONA MicroLoRA/EWC++ learning from recorded outcomes, snapshots/branches,
  RVF signed artifacts, hash-linked witness logs, replication/Raft primitives,
  MCP/shared Brain, Node/Rust/WASM/Postgres surfaces. MIT license.
- Health: 4.5k stars / 601 forks / 3,243 commits / 125 open issues / 217 PRs —
  active. Counterweight: its own "Known boundaries" admits consolidation not
  wired into default paths, incremental snapshots/scheduling incomplete, Raft
  transport/snapshot paths incomplete, GNN-rerank/MRAgent/Darwin are research
  surfaces, core `quantization` field persisted-but-unapplied. Honest docs;
  immature parts clearly marked — adopt nothing marked incomplete.
- RF relevance: **none directly**. No CSI, signal, sensor, or time-series-sensing
  content in the capability map; embeddings are text-oriented; the
  `timesfm-harness` is an agent-memory evaluation harness, not RF tooling.

### 4.2 Candidate-by-candidate assessment

#### V1 — Whole-project adoption (`ruvector-core` / VectorDB / services) → DEFER
- Relevance test against the 10-question necessity test: (1) problem = durable
  semantic/episodic memory over sessions — (2) RF Vision does not have this
  problem: current memory needs are files + provenance records, fully served;
  (3) nothing blocked; (4) no working solution to replace because no
  requirement exists; (7) cost = Rust or Node runtime + ONNX model downloads +
  new ops surface inside a Python/pytest stack — HIGH for zero current return.
- Recommendation: **DEFER** to FUTURE-phase environmental memory (context §23
  already classifies RuVector FUTURE/RESEARCH). Revisit only when a concrete
  requirement exists (e.g., cross-session RF environment knowledge with
  recall-latency bounds our file store cannot meet).

#### V2 — Temporal-coherence (recency decay + coherence gating) → DEFER (note)
- The *idea* (prefer recent, coherence-supported memories) rhymes with our
  drift handling — but ours is a measurement question answered by PRE/POST
  comparison (§16), not a retrieval-weighting question. No mapping today.
- Recommendation: **DEFER** with the one-line note above, so a future reader
  does not rediscover it as novel.

#### V3 — Witness logs / RVF signed artifacts (tamper-evident provenance) → DEFER (note)
- Rhymes with our provenance requirements (§40: preserve originals, document
  corrections). Our mechanism is SHA-256 records + Git-ignored raw captures —
  adequate, simpler, stack-native.
- Recommendation: **DEFER**. If evidentiary bar ever rises to adversarial
  tamper-evidence (publication artifact disputes), re-evaluate; until then the
  signed-artifact machinery is unjustified weight.

#### V4 — Graph / SONA / hybrid / Matryoshka / PQ / RaBitQ / DiskANN / postgres / MCP Brain → DEFER or REJECT
- **DEFER** as a group: graph relations (future zone/room knowledge),
  SONA lifelong learning (future environmental learning), hybrid retrieval —
  all FUTURE-phase vocabulary with no present requirement.
- **REJECT** for RF Vision purposes: shared/hosted Brain (cloud plane —
  privacy §27 forbids unnecessary external processing), Postgres extension
  (no relational estate), Raft/replication (no distributed deployment).

---

## 5. Relevant components/techniques (consolidated)

| # | Component | Source | Class |
|---|---|---|---|
| R1 | 6 peer-reviewed DSP operators + processor/sanitizer/detector structure | RuView signal crate | REFERENCE |
| R2 | Calibration certificates + anchor quality gates + STALE-on-drift | RuView calibration crate | REFERENCE |
| R3 | Variance-vs-ambient presence fallback form | RuView presence | REFERENCE (NEXT) |
| R6a | Evidence bundles with certificates; OOD-gate framing | RuView evidence/ood | REFERENCE |
| R6b | Counterfactual XAI form | RuView counterfactual | REFERENCE (NEXT/FUTURE) |
| R7 | Hash-pinned deterministic replay + claim-check discipline | RuView proof harness | REFERENCE (NOW-adjacent) |
| R8 | Coherence-gate stability hygiene (hypothesis only) | RuView pipeline | REFERENCE |
| R4 | Contrastive CSI embeddings + LoRA adapters | RuView HF + train | DEFER |
| R5 | Vitals DSP extractors | RuView vitals/python | DEFER |
| V1 | Durable vector/agent memory substrate | RuVector core | DEFER |
| V2–V4 | Temporal-coherence, witness/RVF, graph/SONA, misc retrieval | RuVector crates | DEFER (notes) / REJECT (hosted) |

---

## 6. Evidence supporting each finding

- R1: `wifi-densepose-signal` crate README (live fetch): algorithm→paper table
  (SpotFi/SIGCOMM'15, WiGest'15, FarSense/MobiCom'19, STFT, WiDance/MobiCom'17,
  Widar-3.0/MobiSys'19); module list (`csi_ratio, hampel, fresnel,
  spectrogram, subcarrier_selection, bvp, phase_sanitizer, motion`); license
  MIT OR Apache-2.0. Corroborated by `v2/crates/README.md` + main README
  pipeline section.
- R2: `wifi-densepose-calibration/src/lib.rs` header (live fetch, 2.2 KB):
  "Teach the room before you teach the model"; ADR-151/135/152 stage list;
  exported `CalibrationCertificate{,Tier,Status,Verifier}`,
  `AnchorQualityGate`, `MixtureOfSpecialists`, honest-`STALE` invariant.
  Module sizes (anchor 14 KB … certificate 44 KB) confirm substance.
- R3: main README capability table (live): presence <1 ms + ~30 s ambient
  calibration + phase-variance fallback; 82.3% re-benchmark with retraction note.
- R4: main README + "Model weights: what's real" (live): 12.2M steps / 60K
  frames / 610K triplets / 82.3%; safetensors NUL-pad issue #1522; LoRA adapters.
- R5: main README capability table + PyPI `ruview` quick-start (live): band
  edges 0.1–0.5 / 0.8–2.0 Hz, zero-crossing; "experimental, not medical".
- R6: GitHub API `src/` listings (live): evidence=`lib.rs` 36 KB;
  ood={`domain,gate,certificate`}; counterfactual={`hypothesis,infer`}.
- R7: main README "Results & proof" (live): `verify.py` + SHA-256, ADR-168,
  WITNESS-LOG-028, MetaHarness `claim-check`/`verify`.
- R8: main README pipeline section (live): Coherence Gate accept/reject claim.
- V1–V4: RuVector README capability map + "Known boundaries" §1–11 + repo
  stats (4.5k/601/3,243) + file tree (`crates/`, `docs/adr/`, `schemas/`,
  `benches/`) — all live-fetched 2026-09-23. Zero RF/CSI terms in map.
- Baseline: RF Vision directory inventory 2026-09-23 (`sensing/`, `dsp/`
  incl. `dsp/README.md` naming rationale, `localization/`, `ai/`,
  `experiments/analysis/README.md`).

---

## 7. Current RF Vision comparison (selected)

| Problem | CURRENT RF VISION | EXTERNAL APPROACH | NECESSITY | COMPAT | COST | RECOMMENDATION |
|---|---|---|---|---|---|---|
| CSI denoising/operators | Owned `dsp/` modules; 011 deliberately minimal | 6 paper-traced Rust operators | NOT NOW | Compatible as literature; concerns if ported blindly | High (Rust→Python port + validation) | REFERENCE |
| Calibration records | `localize/calibration/` skeleton; baseline philosophy defined, no certificate format | Versioned certificates + tiers + signatures | FUTURE | Compatible (idea level) | Medium if built ourselves later | REFERENCE |
| Drift handling | PRE/POST + within/between comparison (§16); STALE implicit | Explicit STALE degradation + OOD gate | NOT NOW | Compatible; no evidence their gate beats our comparison | Low (idea only) | REFERENCE |
| Presence detection | Skeleton owned; gated behind 011 | Trained head + variance fallback | NOT NOW (NEXT) | Concerns (their thresholds ≠ our link) | Medium | REFERENCE |
| Reproducible analysis | Rules written; scripts not yet written | Hash-pinned replay + claim-check | NOW-adjacent | Compatible | Low (pattern only) | REFERENCE |
| Embeddings | None — correctly absent per ML philosophy | Contrastive encoder + LoRA | FUTURE | Concerns (domain + leakage) | High | DEFER |
| Vitals | None — future scope | DSP extractors, unvalidated | NONE | Incompatible as claims | High | DEFER |
| Session/environment memory | Files + provenance — adequate | Vector/graph/agent memory DB | NONE | Incompatible stack (Rust/Node vs Python) | High | DEFER |
| Transport/firmware/backend | Validated serial + Python — protected | UDP + Rust + S3/C6 | NONE | Incompatible (all layers differ) | Very high | REJECT |
| Pose/imaging/counting claims | Absent — correctly absent | Weak/unvalidated or OOD | NONE | Incompatible with staged progression | Very high | REJECT |

---

## 8. Scientific compatibility assessment

- **PASS as literature, FAIL as drop-in.** The portable value is published
  algorithms and honesty/process patterns, never binaries, weights, or
  thresholds. Every operator worth referencing traces to a peer-reviewed paper;
  every claim worth ignoring is honestly labeled upstream (retractions,
  first-cut disclosures, OOD caveats) — we verified the labels, not the claims.
- **Specific risks documented:** (a) subcarrier selection ≅ post-hoc top-k
  selection — banned from 011 inference; (b) MM-Fi/contrastive numbers are
  out-of-domain for our single-link 64-tone serial data; (c) ambient-calibration
  and gate constants assume their geometry/traffic — ours differ (Xiaomi-ch1 +
  ping-trigger vs any-AP + self-ping); (d) RuVector recall machinery answers a
  retrieval question we do not have; (e) hosted/shared memory planes conflict
  with privacy-first local processing.
- **No finding in this report weakens, replaces, or reinterprets any frozen
  protocol, threshold, or validated baseline.**

## 9. Integration complexity/risk

No integration is recommended, so this section records the cost of the paths
NOT taken: Rust DSP port (high — language, 56/≤256-HE vs our 64-tone grid,
revalidation of every operator); calibration framework port (high — mesh +
model assumptions baked in); RuVector adoption (high — new runtimes, ONNX
downloads, ops surface, plus incomplete upstream surfaces); weights/thresholds
(unbounded scientific risk — rejected outright). The REFERENCE items cost
nothing until their owning work begins, and then only as reading material.

## 10. Recommendation for each candidate

See §5 table + §14 matrix. Summary: zero ADOPT, zero code ADAPT, eight
REFERENCE (idea/pattern level, timed to owning phases), seven DEFER, nine
REJECT groups.

## 11. What should NOT be adopted

The §3.2-R9 reject list (firmware/transport/Rust server/weights/claims/
training pipelines/product integrations/unaudited-proprietary-GPL
artifacts/synthetic world model/rewrites-reflashes-repurchases) plus, from
RuVector, hosted shared-memory planes and distributed-replication machinery.
Rationale per item is in §3.2-R9 and §4.2-V4 — each fails necessity,
compatibility, or authority independently.

## 12. What should remain future/deferred

- Post-011 measurement work: named DSP operators (R1), calibration
  certificates/gates/STALE states (R2), presence fallback form (R3),
  counterfactual XAI form (R6b).
- Post-localization research: contrastive embeddings with leakage probes (R4).
- Explicitly future scope: vitals (R5), all RuVector memory infrastructure
  (V1–V4), multi-person/counting/pose (rejected until evidence exists).

## 13. Recommended next research targets

1. **Primary sources over ports:** SpotFi (2015), FarSense (2019), Widar-3.0
   (2019) papers directly — cheaper and more authoritative than auditing Rust
   ports line-by-line.
2. **CSIKit** (already landscape REFERENCE): Python-native CSI parsing/
   processing — stack-compatible by construction; evaluate against a concrete
   preprocessing need if one arises.
3. **In-stack statistics:** statsmodels + PyWavelets (already conditional) for
   any time-frequency/drift question 011 actually produces — no new dependency
   class required.
4. **scikit-learn gating:** remains behind the §24 six-gate checklist; 1-NN as
   supporting evidence per protocol is sufficient for 011.
5. **RuView ADRs** (135 baseline, 151 calibration, 168 benchmark-proof, 079
   camera-supervised path): process reading for calibration/validation design —
   no code contact needed.

## 14. Final decision matrix

| CANDIDATE | SOURCE | CURRENT NECESSITY | COMPATIBILITY | COST | RECOMMENDATION | ONE-LINE RATIONALE |
|---|---|---|---|---|---|---|
| 6-algorithm DSP core | RuView signal | NOT NOW | Compatible (papers) / concerns (port) | High | REFERENCE | Papers beat ports; 011 needs no new operator |
| Calibration certs + gates + STALE | RuView calibration | FUTURE | Compatible (idea) | Med (later, ours) | REFERENCE | Best idea-level mirror of §8; our code later |
| Presence head + variance fallback | RuView presence | NOT NOW (NEXT) | Concerns (thresholds) | Med | REFERENCE | Form transfers, constants do not |
| Evidence bundles + OOD gate | RuView evidence/ood | NOT NOW | Compatible (idea) | Low | REFERENCE | Frames drift comparison; no machinery |
| Counterfactual XAI | RuView counterfactual | FUTURE | Compatible (form) | Med (later) | REFERENCE | Only XAI form respecting causation limits |
| Hash-pinned replay + claim-check | RuView proof | NOW-adjacent | Compatible | Low | REFERENCE | Use when writing 011 analysis scripts |
| Coherence-gate hygiene | RuView pipeline | NOT NOW | Unvalidated claim | Low | REFERENCE | Hypothesis note for future long captures |
| Contrastive embeddings | RuView HF/train | FUTURE | Concerns (domain+leakage) | High | DEFER | ML-before-evidence; needs leakage probes |
| Vitals extractors | RuView vitals | NONE | Incompatible (claims) | High | DEFER | Future scope; unvalidated upstream |
| Vector/agent memory | RuVector core | NONE | Incompatible (stack) | High | DEFER | No such requirement exists |
| Temporal-coherence / witness / graph / SONA | RuVector crates | NONE | N/A | High | DEFER (notes) | Future vocabulary, recorded above |
| Hosted Brain / replication / PG ext | RuVector | NONE | Incompatible (privacy/estate) | High | REJECT | Privacy + no-estate + no-fleet |
| Firmware/transport/Rust server | RuView platform | NONE | Incompatible (all layers) | Very high | REJECT | Validated baseline stays |
| Weights/checkpoints/thresholds | RuView artifacts | NONE | Incompatible (license/evidence) | Unbounded | REJECT | No-grant + weak/OOD numbers |
| Pose/vitals/activity/count claims | RuView claims | NONE | Incompatible (staging) | Very high | REJECT | Evidence order matters (§3) |
| Training pipelines / product surface | RuView scope | NONE | N/A | High | REJECT | No counterpart requirement |

---

## Appendix A — Inspection log (evidence of sufficiency)

- `RFVISION-CONTEXT.md` (1,300 lines) + `AGENTS.md` Master Execution Directive:
  read in full.
- RF Vision tree: root + `sensing/`, `dsp/` (+`README.md`), `localization/`,
  `ai/`, `experiments/analysis/` inventories, read-only.
- RuView live: full README (pipeline, capability table with issue refs
  #593/#263/#491/#509/#645/#1522, proof section, hardware table, model-maturity
  disclosures), `v2/crates/` API listing (≈60 crates incl. all `ruview-*`),
  `wifi-densepose-signal` + `v2/crates` READMEs, `wifi-densepose-calibration`
  file list + `lib.rs` header, `ruview-{evidence,ood,counterfactual}` `src/`
  listings. Prior 004 tarball audit (61 MB snapshot, 114 MB tree) incorporated
  by reference for UI/architecture/claim/license findings — not re-done.
- RuVector live: full README (capability map, memory-loop, deployment,
  security, known-boundaries §1–11, benchmarks, license) + repo tree + stats.
- NOT done (out of scope / unnecessary): cloning, installing, executing,
  per-file source audits, benchmark reproduction, weight inspection.

## Appendix B — License / reuse posture (reaffirmed from 004 license audit)

- RuView root MIT; `v2/` MIT OR Apache-2.0 (signal crate badge confirms);
  RuVector MIT. Pattern/idea reuse needs no grant; any future line-level
  adaptation requires retaining `Copyright (c) 2024 rUv` notices and keeping
  MIT-derived web code license-separated from the PyQt6 path.
- Standing prohibitions reaffirmed: `vendor/*`, `assets/*`, `X Bot.fbx`,
  all weights/checkpoints/HF artifacts, FeitCSI binary boundary.

---

*End of report. No code changed, nothing installed, nothing committed. Awaiting
explicit approval before any follow-on work.*
