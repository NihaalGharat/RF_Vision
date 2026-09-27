# RFVISION-011 v1.4 — CONTROLLED SPATIAL DISCRIMINABILITY PILOT PROTOCOL (AMENDED)
**Status:** PROPOSAL v1.4 AMENDED — single approved practical-geometry amendment applied. No data collected, no code changed, no commit, no push.
**Baseline:** RFVISION-010 `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`, validated + pushed.
**Supersedes:** `RFVISION-011-PROTOCOL-v1.3.md` FINAL (preserved unchanged).
**Rule:** Measurement → Validation → Statistical evidence → Modeling → Visualization.
RFVISION-011 stops at statistical evidence. No localization, ML, imaging, or UI implementation.

---

## Revision Notes — v1.4 (single approved amendment to v1.3, with reasons)
**Amendment A — practical student-scale geometry (APPROVED, the only change).**
The ~3 m node separation is no longer a mandatory execution requirement: ~3 m is
retained as the planned ideal reference geometry, while the experiment uses the
maximum practical node separation achievable with the existing same-laptop USB
setup. The actual measured separation is recorded and reported as an experimental
condition and limitation — never fabricated, rounded upward, or described as ~3 m
unless it actually is. Node height keeps the 1.0–1.5 m preferred target using safe
existing furniture, with the actual height recorded. Priority order: (1) reliable
same-laptop USB acquisition, (2) maximum practical separation, (3) stable
positioning, (4) same approximate height, (5) consistent orientation. Acquisition
reliability must never be sacrificed for extra separation. Sections changed: §A
(pilot characterization), §D (placement rule rewritten), §I (two metadata fields
added), §S step 1 (version reference). Reason: the student operator cannot reliably
reproduce a laboratory-grade 3 m geometry with one laptop; the pilot remains
scientifically useful as a student-scale constraint study.
**Everything else is byte-identical to v1.3 FINAL.** No change to trial matrix,
randomization, baselines, representations, tones, replication unit, metrics,
gates, thresholds (none), abort criteria, or verdicts. The geometry limitation
must not be used to weaken the statistical analysis.

## Revision Notes — v1.3 (retained history; final changes v1.2 → v1.3)
1. **Explicit empty-baseline assignment (§F).** The six empty trials are fixed by position:
   E1–E2 PRE, E3 after B1, E4 after B2, E5–E6 POST. Temporal ordering is preserved; empties
   are never pooled blindly, and drift is evaluated against nearby/interleaved empties.
2. **Primary separation ratio defined (§M).** Separation Ratio = median between-zone
   trial-pair distance / median within-zone trial-pair distance, per node (A, B, concatenated
   A+B) under primary representations A and B. >1 / ≈1 / <1 interpreted as evidence only —
   no threshold, no pass/fail rule.
3. **Gate 2 made reproducible (§N.2).** Every zone reports all 3 presence trials individually,
   the aggregate zone-level effect, the comparison with empty-room variation, and direction/
   magnitude stability across reps — no identical-sign rule, no thresholds.
4. **1-NN reporting made explicit (§M).** Total correct/total, accuracy, 1/6 chance baseline,
   full 6×6 confusion matrix, per-zone correct/error counts, repeatedly confused pairs. No
   accuracy threshold; supporting evidence only.
5. **PRE/POST drift operationalized (§N.4).** Drift vs spatial effect compared in the same
   trial-level representation + distance framework (PRE-vs-POST drift, within-zone repeat
   variation, between-zone variation), judged qualitatively with no threshold.
6. **Methodology preserved.** No new experiments, features, models, hardware, thresholds,
   p-value fishing, or statistical complexity. Four verdicts kept with evidence synthesis.
7. **Final freeze:** phase-local baseline assignment for B fixed in §L.3 (B1→E1+E2, B2→E3,
   B3→E4; E5+E6 drift-only; C strictly nearest-interleaved with no B3 C) plus `baseline_ref`
   in §I metadata; subjective Gate 3 phrases ("systematically exceed", "sensible confusion
   structure") replaced with explicit reporting language; Gate 2 "reproducible" tied to the
   stated three-trial reporting procedure. Nothing else added.

---

## A. Scientific objective (v1.4: student-scale characterization added)
RFVISION-011 is a **Controlled Spatial Discriminability Pilot under practical
student-scale constraints**. It determines whether the
validated two-node Wi-Fi CSI system contains repeatable spatial information sufficient to
justify a subsequent localization experiment. It is NOT a definitive localization validation.
The pilot ultimately determines:
> **Are repeated trials from the same physical zone more similar to each other than trials
> from different physical zones, after accounting for empty-room variation and
> temporal/environmental drift?**
This phase answers with statistics only and stops at statistical evidence. No localization,
ML, imaging, classifier, or UI work is designed, built, or implied. No claim is made of
definitive indoor localization, laboratory-grade accuracy, optimal antenna geometry,
generalizable localization performance, RF imaging, or 3D reconstruction; any future
localization work requires a separate validation study.

## B. Hypotheses (retained from v1.1/v1.2)
- **H0 (null):** Between-zone CSI differences are within the range of within-zone
  (repeated-trial) variation plus empty-room background variation; zones are indistinguishable.
- **H1 (alternative): CSI measurements contain reproducible spatial structure such that trials from at least some different zones exhibit greater separation than repeated trials from the same zone, relative to observed background variation.**
- H0 is the default. Confirming H0 (negative result) is a valid, reportable outcome that
  redirects the project per §S/v1.1-Amendment 17. The analysis distinguishes within-zone variation
  (repeats of the same zone) from between-zone variation (different zones) throughout.

## C. Room geometry procedure (retained from v1.0/v1.1/v1.2)
Tape-measured room length (Y), width (X), ceiling height; origin at one floor corner
(X = width, Y = length, Z = height). Record Node A/B `(x,y,z)`, AP `(x,y,z approx)`,
wall distances, node-to-node distance, static obstacles/furniture. Phone photos stored beside
the manifest, never in Git. Re-measure if anything moves. No approximate coordinates where a
tape measure can reach.

## D. Node placement procedure (v1.4: practical-geometry rule — the single authoritative rule)
> The experiment uses the maximum practical node separation achievable with the existing
> same-laptop USB setup. Approximately 3 m is retained as the ideal reference geometry
> (`planned_ideal_separation ≈ 3 m`). Actual separation is measured and reported as an
> experimental condition and limitation (`actual_separation`).
Priority order: (1) reliable same-laptop USB acquisition — never sacrifice acquisition
reliability for extra separation; (2) maximum practical separation with existing cables/
ports (no second laptop, no purchased hardware); (3) stable, repeatable positioning;
(4) same approximate height — 1.0–1.5 m remains the preferred target using safe, stable
existing furniture (no stands to buy, safety over exact height; record actual height,
report any deviation, never fabricate compliance); (5) consistent orientation (record).
Record `planned_ideal_separation` and `actual_separation` in metadata (§I); report the
actual value exactly (0.5 m → 0.5 m, never "approximately 3 m" unless true). The actual
separation is a context variable/limitation — never a pass/fail criterion. Nodes untouched
all session (any bump logged, trials repeated).
Pre-session verify: MACs (`b0:3f…` on `usb-0:5.4`, `04:b2…` on `usb-0:1`), firmware
`0a490737…`, AP Nihaal/`8c:53:c3:5b:e1:59`/Ch1, concurrent dual acquisition healthy ≥60 s.
Do not modify the resolver to accept arbitrary `/dev/ttyUSBn`; restore recorded USB ports
physically instead.

## E. Zone-grid design (retained: 3×2 with fallback)
Six zones Z1–Z6 with measured centers/dimensions/distances to each node; centers ≥1.0 m apart;
grid spans inter-node region plus one off-axis row. Floor tape + labels. Fallback if room
cannot fit: 2×2 or 1-D 4-point line — record why, never squeeze. ASCII as in v1.0 (replace
proportions with measured values at setup).

## F. Trial matrix (v1.3: explicit empty-baseline assignment)
| Position | Trials | Condition |
|---|---|---|
| PRE baseline, before any presence trials | E1, E2 | Empty |
| B1: six randomized zone trials, then | E3 | Interleaved empty control after Block B1 |
| B2: six randomized zone trials, then | E4 | Interleaved empty control after Block B2 |
| B3: six randomized zone trials | — | Repeat, re-randomized (no interleaved empty) |
| POST baseline, after all presence trials | E5, E6 | Empty |
Session order: **PRE (E1, E2) → B1 (6 zones) → E3 → B2 (6 zones) → E4 → B3 (6 zones) →
POST (E5, E6)**. 24 trials (18 zone = 3 reps × 6 zones; 6 empty), IDs `R11-<block>-<nn>`.
Use E1–E6 to characterize temporal/background variation. Do not pool them blindly; preserve
their temporal ordering and use the appropriate nearby/interleaved empty trials when
evaluating drift (§L.2, §N.4).
**Pilot limitation (v1.1/Amendment 9):** three repetitions per zone serve initial controlled
assessment only and cannot by themselves establish generalizable localization performance.
Promising evidence → expanded dataset before any strong localization claim. No complexity
added to inflate N.

## G. Randomization/order strategy (retained from v1.0)
Independent Fisher–Yates order per block (seed recorded); interleaved empties break temporal
runs and track drift; PRE/POST fixed as drift brackets; cue-gated entry/exit. Order sheet
printed before capture.

## H. Capture duration (retained from v1.1/v1.2)
Warm-up 15 s + **60 s clean window** + 5 s pre/post margins; ~85 s/trial port time, 60–90 s
transitions; session ≈60 min + 30 min setup.
*Justification:* a 60-second clean window provides substantial temporal coverage for estimating
trial-level statistics while limiting environmental drift. Statistical uncertainty must account
for temporal dependence rather than assuming every CSI record is independent. Representative
trials receive the lightweight stability/autocorrelation inspection of §L. No advanced
time-series modeling in this pilot.

## I. Metadata schema (v1.4: two geometry fields added; all v1.3 fields retained)
v1.0 fields (`experiment_id`, `trial_id`, `block`, `condition` A/B/C/D, `zone_id`/EMPTY,
UTC start/end, node/AP/firmware IDs, per-node quality counters, sync state, geometry ref,
person/posture/orientation, order index, operator, verdict) plus: compact environmental state
(door, window, fan, AC, people outside region, unusual movement, Wi-Fi events, setup changes —
structured fields + free notes), participant-electronics confirmation (no devices on body, phone
location if active), facing direction, clothing/footwear note, and the assigned baseline
reference (`baseline_ref` per §L.3, recorded explicitly for each presence trial). One JSON sidecar per trial.
Amendment A additions: `planned_ideal_separation` (≈3 m reference) and `actual_separation`
(measured physical value, reported exactly) in the geometry manifest and every trial sidecar.

## J. Raw-data structure (retained from v1.0/v1.1/v1.2)
`research-data/rfvision-011/` with `geometry.json`, `trial_order.csv`,
`trials/<trial_id>/{dual_a.bin,dual_b.bin,*.sha256,trial_meta.json,validation.json}`,
`manifest.json`, `analysis/` (derived only). Git-ignored raws, `chmod 444` post-capture,
in-Git convention only via existing MANIFEST.md/README.md if later approved.

## K. Data-integrity checks (retained from v1.0/v1.1/v1.2)
Expected MACs/by-paths, BSSID/channel, 62 tones, finite IQ, valid_pct ≥ 99.0%, gap/dup/ooo
counts (FLAG if gaps > 10 or valid_pct < 99%), monotonic host timestamps, SYNCED ≥95% of
window, 60 ± 2 s, ≥5000 valid records/node. FLAGs analyzed separately and reported, never
silently dropped.

## L. Statistical analysis plan (retained from v1.2; §F references updated)
**The independent experimental replication unit is the trial.** Within-trial CSI records are
repeated measurements used to estimate that trial's characteristics — NOT independent
experimental replicates. All spatial inference operates at trial level (N = 3/zone + 6 empties).
1. **Temporal-dependence check (lightweight):** on representative trials, inspect amplitude
   stability (split-half means), obvious drift (first-half vs second-half), transient events,
   and lag-1 autocorrelation magnitude — judging whether the trial is approximately stable and
   whether effective information is far below the raw record count. No formal time-series models.
2. **Baseline characterization:** E1–E6 tone-wise mean ± std kept as PRE (E1–E2),
   interleaved (E3 after B1, E4 after B2), POST (E5–E6) per §F — drift E1→E6, split-half
   stability; pooled only where drift is shown negligible, with the choice documented. Temporal
   ordering is always preserved; nearby/interleaved empties are used for drift evaluation.
3. **Three representations of every zone trial** (62-dim per-tone amplitude μ + σ per node):
   **(A) raw trial amplitude — PRIMARY; (B) baseline-relative Δμ vs the phase-local empty
   baseline — PRIMARY; (C) temporally contextualized Δμ vs the nearest interleaved empty —
   SUPPORTING robustness/drift check only.** Phase-local baseline assignment for B (temporal
   ordering preserved): B1 → mean of E1+E2 (stable PRE baseline); B2 → E3 (immediately
   preceding interleaved empty); B3 → E4 (immediately preceding empty). E5+E6 are POST
   controls for drift analysis only and are never used retroactively to normalize earlier
   presence trials. C is strictly nearest-interleaved: B1 → E3, B2 → E4; B3 has no C.
   The primary
   spatial conclusion is based on A+B. **Failure of C alone does not invalidate an effect
   supported by A and B.** C is not required for B3 (which has no interleaved empty) and is
   not required to independently pass. No feature pipeline.
4. **Effect description over all 62 tones:** per-tone presence-vs-empty differences with
   aggregate summaries (median/quartiles of |Δ|, fraction of tones exceeding empty scatter);
   strongest-tone views are descriptive/exploratory only and labeled as such. **No top-k
   data-selected tones as primary inference** (selection bias); any future reduced-tone analysis
   needs a separate discovery subset or pre-registration. No identical-sign-across-all-62-tones
   requirement — tones may legitimately differ in direction.
5. **Within-vs-between core comparison (§M):** within-zone distances (pairs of different
   trials from the same zone) vs between-zone distances (pairs of trials from different
   zones), at the same trial level, per representation and per node; per-node side-by-side
   plus concatenated dual-node view for complementarity. Separation ratio (§M) and 1-NN LOTO
   as supporting generalization check (§M).

## M. Spatial-separability metrics (v1.3: separation ratio defined, 1-NN explicit)
- **Primary — between vs within (trial-pair level):** distribution of within-zone distances
  (pairs of different trials from the **same** zone) vs between-zone distances (pairs of
  trials from **different** zones) on trial-level vectors (Euclidean, 62-dim per node /
  124-dim concatenated), per representation and per node, with empty-trial scatter as context.
  Plots illustrate; the numbers decide.
  **Pairwise distances are derived comparisons and must not be treated as independent
  experimental observations.**
- **Primary separation ratio:** **Separation Ratio = median between-zone trial-pair distance
  / median within-zone trial-pair distance**, calculated for Node A, Node B, and concatenated
  A+B using primary representations A (raw amplitude) and B (baseline-relative amplitude).
  Ratio >1 indicates greater typical between-zone separation; ≈1 indicates weak separation;
  <1 indicates greater within-zone variation. **No arbitrary threshold — the ratio is
  evidence, not a pass/fail rule.**
- **Secondary — zone-centroid summary/visualization:** pairwise zone-centroid distance matrix
  retained as a compact summary and visualization aid only, not as the primary between-zone
  metric.
- **Zone-pair/group structure (reported, not a pass/fail bar):** explicitly report strongly
  separated pairs/groups, weakly separated pairs/groups, and collapsed/overlapping
  pairs/groups. Some zones separable while others overlap is an expected pilot outcome, not
  an automatic failure; partial overlap can yield LIMITED (§N.3).
- **Supporting — 1-NN leave-one-trial-out:** simplest unbiased "would a new trial land
  correctly" estimator (no training/tuning). Report: total correct / total; accuracy; 1/6
  chance baseline (≈16.7%); complete 6×6 confusion matrix; per-zone correct/error counts;
  repeatedly confused zone pairs; small-sample uncertainty. 1-NN is supporting evidence,
  never proof; **no accuracy threshold is applied** (the former 50% bar remains dropped).
- Rationale retained: trial-level means, medians, and 1-NN involve no hyperparameters to
  overfit at N=3; anything fancier waits for a later phase.

## N. Decision gates (v1.3: reproducible Gate 2, operationalized drift, four outcomes)
Evaluate in order; stop at first NO ( NO → corresponding verdict, do not proceed down the list).
1. **Acquisition validity** — ≥90% trials PASS §K? NO → INCONCLUSIVE (fix acquisition, repeat).
2. **Presence vs empty** — At least one node shows a trial-level presence-versus-empty
   difference that is supported across the three zone repetitions under the reporting
   procedure defined below. For every
   zone report: all 3 presence trials individually; the aggregate zone-level effect; the
   comparison with observed empty-room variation; stability of effect direction and
   approximate magnitude across repetitions. **A and B are the primary evidence; C is
   supporting evidence only where an appropriate interleaved empty reference exists**
   (B1 vs E3, B2 vs E4). Do not require identical signs across all 62 tones and do not
   introduce arbitrary thresholds. NO → NO-GO, report negative.
3. **Zone separability (evidence synthesis — no category must be perfect):**
   (i) Compare the distributions of between-zone and within-zone trial-pair distances and
   report their separation ratio, distributional overlap, and repetition consistency (A+B
   primary, C supporting); (ii) zone-pair/group structure — which pairs are strongly
   separated, weakly separated,
   collapsed/overlapping; (iii) held-out 1-NN behavior as supporting evidence (above chance,
   together with the full confusion matrix, per-zone errors, and repeatedly confused zone
   pairs, weighs for, never proves); (iv) consistency across
   repetitions. Weigh jointly: consistent separation across pairs → toward **GO**; some zones
   separable while others overlap → **LIMITED**; entire spatial structure collapses →
   evidence toward **NO-GO**; conflicting or insufficient evidence → **INCONCLUSIVE**.
   Explicitly, Gate 3 uses no 50% accuracy threshold, no 15-point B3 threshold, no
   separation-ratio threshold, no all-representations-must-pass rule, and no
   perfect-separation-of-all-six-zones requirement. An experiment is never failed
   automatically because some adjacent zones overlap.
4. **Generalization and drift (evidence synthesis, no universal law):** qualitative spatial
   pattern persists into B3; same zones show similar signatures across blocks; B3 above
   chance; within-zone < between-zone holds in B3 (trial-pair level). Using the same
   trial-level representation and distance framework as the primary spatial analysis, report
   PRE-vs-POST empty-room drift alongside within-zone repeat variation and between-zone
   variation, and state whether observed temporal/environmental drift is smaller than the
   spatial effect — without introducing an arbitrary threshold. Weigh jointly with
   uncertainty; the old 15-pp B3 rule stays dropped. C is not required for B3.
5. **Modeling eligibility** — only if gates 1–4 pass: nearest-centroid baseline first in a
   later phase. Verdicts: **GO** (larger localization validation justified) / **LIMITED**
   (presence detectable, spatial discrimination weak/inconsistent or partial) /
   **INCONCLUSIVE** (quality/variability prevent conclusion) / **NO-GO** (no reproducible
   spatial signal).

## O. Failure/abort criteria (retained from v1.1/v1.2)
Abort: AP/BSSID/channel change, node non-LIVE >30 s, SYNCED <95% twice consecutively, moved
furniture/AP, second person, power/severe weather event. FLAG (keep data): person moved/
coughed, RF burst, >10-gap burst, timing error. Photography outside sensing trials only;
operator phone parked in a fixed recorded location during acquisition. All causes logged.

## P. Reproducibility requirements (retained from v1.0/v1.1/v1.2)
Frozen versioned protocol, pre-generated order sheet, immutable raws + SHAs, analysis from
clean checkout with commit hash recorded, regenerable figures, retained FLAG/negative trials,
repeatable by a second operator from this document alone.

## Q. Risks/confounders (retained from v1.1/v1.2)
Posture/fatigue drift, clothing, time-of-day AP traffic (75 vs 100 Hz seen), neighbor Wi-Fi,
HVAC, door/window state, laptop contention (known 5-frame gaps), USB reseat (MAC re-verify),
moved tape marks, cueing bias (timer, not judgment) — controlled by §§H–I single-participant
protocol and electronics ban.

## R. UI relationship (requirements only, retained from v1.1/v1.2)
Future UI must represent acquisition state, node health, trial ID, zone, presence state,
confidence, uncertainty, data quality, synchronization, experimental and localization status —
requirements discovery only, zero implementation. The UI must never visually imply localization
capability before scientific gates justify it.

## S. Exact execution sequence (retained, reference updated to v1.4)
1. Freeze + approve this v1.4 protocol (version it). 2. Measure room (§C). 3. Place/mark nodes
+ grid, record coordinates (§D–E). 4. Verify AP. 5. Verify Node A. 6. Verify Node B. 7. Verify
dual acquisition ≥60 s. 8. Generate/print order sheet (§G). 9. PRE empties E1–E2. 10. Blocks
B1→E3, B2→E4, B3 per §F. 11. POST empties E5–E6. 12. §K validation. 13. chmod 444 + SHA-256.
14. §L analysis (trial-level; A+B primary, C supporting; separation ratio §M).
15. §N gates in order → GO / LIMITED / INCONCLUSIVE / NO-GO. 16. Written verdict with evidence.
DO NOT EXECUTE NOW — awaiting approval.
