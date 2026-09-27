# RFVISION-011 PRESENCE PILOT v1.0 — FROZEN PROTOCOL
**Status:** FROZEN — approved for execution on explicit human GO only. No data collected yet.
**Baseline:** RFVISION-010 `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`.
**Lineage:** promotes `RFVISION-011-PRESENCE-PILOT-PROPOSAL.md` (preserved); supersedes the
v1.4 3×2 grid experiment for execution (v1.4 file preserved byte-identical).
**Rule:** Measurement → Validation → Statistical evidence. Stops at statistical evidence.
No ML, localization, imaging, classifiers, XAI, or UI claims from this experiment.

## A. Question and hypotheses
> Does a human standing at a controlled, repeatable position along the Router–ESP32 RF
> path produce a reproducible CSI change compared with the empty-room condition?
- **H0:** Human-present trials are indistinguishable from empty-room variation plus drift.
- **H1:** Human-present trials show a trial-level CSI difference vs empty-room variation,
  supported across all repeated presence trials. H0 default; negative valid.

## B. Fixed setup (recorded, not to be altered mid-session)
- Node A `b0:3f:d3:70:20:3c` on `usb-0:5.4`; Node B `04:b2:47:20:1a:dc` on `usb-0:1`;
  same laptop; both ceiling-facing; separation 3 ft / ~0.9144 m (max practical, v1.4 rule).
- AP Nihaal / `8c:53:c3:5b:e1:59` / ch 1 / 2412 MHz; firmware `0a490737…dd`.
- Phones airplane-mode, parked aside. Position PATH-FIXED: taped foot marks + facing
  line on the Router→ESP path (photo outside Git).

## C. Trial matrix (11 trials, pre-registered fixed order)
| Seq | ID | Block | Condition |
|---|---|---|---|
| 1–2 | R11P-01/02 (E1, E2) | PRE | Empty |
| 3–5 | R11P-03/04/05 (P1–P3) | BLOCK 1 | Human-present |
| 6 | R11P-06 (E3) | MID | Empty (interleaved) |
| 7–9 | R11P-07/08/09 (P4–P6) | BLOCK 2 | Human-present |
| 10–11 | R11P-10/11 (E4, E5) | POST | Empty |
Full order in `research-data/rfvision-011-presence/order/trial_order.csv`. No grid, nothing
to randomize. Blocks minimize entry/exit transients; E3 + PRE/POST brackets handle drift.

## D. Capture procedure (per trial)
Confirm ID/condition/participant/nodes/AP → start synchronized dual capture → 15 s
warm-up → 60 s clean window (+5 s margins) → stop → immediate §K validation → metadata
sidecar → SHA-256 → anomaly log. 921600 baud, both nodes simultaneous. Raws Git-ignored,
`chmod 444` post-session. No silent repair/drop/interpolation/normalization.

## E. Human procedure checklist (operator, every presence trial)
Feet on marks; same facing; stationary; arms at sides; same participant/clothing/posture;
no phone interaction; touch nothing (ESP32s, laptop, router, cables, furniture); enter/exit
only on cue; log any movement/interruption — repeat only on human decision, never automatic.

## F. Metadata (one JSON sidecar per trial)
`experiment_id`, `trial_id`, `block`, `condition`, `position_id=PATH-FIXED`, foot-mark ref,
facing, posture, clothing, UTC start/end, node/AP/firmware IDs, per-node quality counters,
sync state, env (door/window/fan/AC/outsiders/RF events), electronics confirmation,
`baseline_ref` (P1–P3 → mean(E1+E2); P4–P6 → E3), `c_ref` (Block 1 → E3; Block 2 → none),
geometry ref, operator, verdict PENDING, anomalies []. E4/E5 POST drift-only, never retroactive.

## G. Statistics (trial = replication unit; records within are repeated measurements only)
A (raw) + B (baseline-relative) PRIMARY; C supporting Block 1 only. Per-tone
presence-vs-empty differences over all 62 tones with aggregates (median/quartiles |Δ|,
fraction exceeding empty scatter); no top-k. Trial-pair distances within-condition vs
between-condition; separation ratio = median between / median within, no threshold.
No 1-NN (single class — dropped with reason); block-to-block consistency is the repeat
check. Drift in the same framework (PRE vs mid vs POST), qualitative, no threshold.

## H. Integrity (§K adapted) and abort
62 tones, finite IQ, valid_pct ≥ 99% (FLAG if < 99%), gaps/dups/ooo (FLAG if gaps > 10),
BSSID/channel/MAC identity, monotonic host ts, SYNCED ≥ 95% of window, 60 ± 2 s,
≥5000 records/node. Abort: AP change, non-LIVE > 30 s, SYNCED < 95% twice in a row,
moved nodes/furniture, second person, power event, any uncovered decision. FLAGs kept,
analyzed separately, reported.

## I. Verdicts
**GO** (effect reproduced across all 6 presence trials beyond empty variation + drift →
multi-position study justified, nothing more) / **LIMITED** (partial/inconsistent) /
**INCONCLUSIVE** (quality prevents conclusion) / **NO-GO** (no effect, valid negative).

## J. Claims
CAN: whether a stationary human at this fixed path position perturbs CSI reproducibly on
this setup. CANNOT: spatial discriminability, localization, generalizability (positions,
people, rooms, clothing, traffic), imaging, identification. Single body/session/regime.

## K. Execution sequence
1. Freeze (this file). 2. Confirm setup §B + checklist §E. 3. Health check ≥60 s. 4. E1,E2.
5. P1–P3. 6. E3 (+validate). 7. P4–P6. 8. E4,E5. 9. Per-trial §K. 10. Hashes + manifest.
11. §G analysis. 12. Verdict §I with evidence. DO NOT EXECUTE — awaiting explicit human GO.
