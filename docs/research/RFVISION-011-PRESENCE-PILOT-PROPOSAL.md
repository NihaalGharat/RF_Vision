# RFVISION-011 Presence Pilot v1.0 — PROPOSAL (not a protocol, not approved)

**Status:** PROPOSAL ONLY — AWAITING HUMAN APPROVAL — NO DATA COLLECTED.
**Lineage:** replaces the v1.4 3×2 grid experiment (v1.4 retained unchanged); inherits all
validated acquisition, integrity, and trial-level statistics methodology.
**Baseline:** RFVISION-010 `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`.
**Setup assumed:** 3 ft / ~0.914 m node separation, ceiling-facing nodes, same-laptop USB
(`usb-0:5.4`, `usb-0:1`), phones airplane-mode aside, router unchanged.

---

## 1. Scientific question and hypotheses

> Does a human standing at a controlled, repeatable position along the Router–ESP32 RF
> path produce a reproducible CSI change compared with the empty-room condition?

- **H0:** Human-present trials are indistinguishable from empty-room variation plus
  temporal/environmental drift.
- **H1:** Human-present trials show a trial-level CSI difference vs empty-room variation,
  supported across all repeated presence trials.
- H0 is the default; a negative result is valid and reportable.

## 2. Minimum trial matrix (11 trials, pre-registered fixed order — nothing to randomize)

| Seq | ID | Condition |
|---|---|---|
| 1–2 | R11P-01/02 (E1, E2) | Empty PRE |
| 3–5 | R11P-03/04/05 (P1–P3) | Human-present, block 1 |
| 6 | R11P-06 (E3) | Empty mid (interleaved) |
| 7–9 | R11P-07/08/09 (P4–P6) | Human-present, block 2 |
| 10–11 | R11P-10/11 (E4, E5) | Empty POST |

6 presence + 5 empty ≈ 30–35 min session. Blocks (not alternation) minimize
entry/exit disturbance transients; temporal confounding is handled by the interleaved
E3 plus PRE/POST drift brackets. Capture windows per v1.4 §H (15 s warm-up + 60 s clean).

## 3. Fixed-position procedure

Tape foot marks + facing line on the Router–ESP32 path; feet on marks, fixed facing,
arms still at sides, stationary; same participant, clothing, posture all trials;
phones airplane-mode aside (already confirmed); cue-gated entry/exit; any touch/bump
logged and the trial repeated only on human decision. Position photographed (outside Git).

## 4. Metadata (v1.4 §I, `zone_id` → `position_id` = PATH-FIXED)

All v1.4 fields kept; zone fields replaced by fixed-position record (foot-mark ref,
facing, posture, clothing). Per presence trial: `baseline_ref` (P1–P3 → mean(E1+E2);
P4–P6 → E3). One JSON sidecar per trial; raw binaries + SHA-256; Git-ignored.

## 5. Baseline/control strategy

Phase-local empties (Block 1 vs mean(E1+E2); Block 2 vs E3); E4/E5 POST drift-only,
never retroactive. Representation C (supporting): Block 1 → E3 only; Block 2 has no C
(same precedent as v1.4's B3-no-C). A (raw) + B (baseline-relative) PRIMARY.

## 6. Statistical comparison (v1.4 machinery, spatial parts removed)

- Per-tone presence-vs-empty differences over all 62 tones with aggregate summaries
  (median/quartiles of |Δ|, fraction exceeding empty scatter); no top-k inference.
- Trial-pair distances: within-condition (presence–presence, empty–empty) vs
  between-condition (presence–empty); separation ratio = median between / median
  within — same formula, conditions replacing zones; no threshold.
- **1-NN dropped with reason:** classification is meaningless with one position.
- Drift in the same representation/distance framework (PRE vs mid vs POST alongside
  within/between-condition variation), qualitative, no threshold.
- Trial = replication unit; records within a trial are repeated measurements only.

## 7. Integrity/abort (§K + §O retained verbatim, zone refs → fixed position)

62 tones, finite IQ, valid_pct ≥ 99%, gaps/dups/ooo (FLAG if gaps > 10 or valid <
99%), BSSID/channel/MAC identity, SYNCED ≥ 95%, 60 ± 2 s, ≥5000 records/node
(current ~97–115 Hz projects ~5.8–6.9k ✓). Abort on AP change, non-LIVE > 30 s,
moved nodes/furniture, second person, or any uncovered decision. FLAGs kept and
reported; no silent repair, no auto-retry, no selective removal.

## 8. Verdicts

**GO** (presence effect reproduced across all 6 trials beyond empty variation and
drift → multi-position study justified) / **LIMITED** (partial/inconsistent) /
**INCONCLUSIVE** (quality/variability prevent conclusion) / **NO-GO** (no effect —
valid negative). GO here authorizes only a later multi-position experiment, nothing more.

## 9. Claims: can / cannot support

CAN: whether a stationary human at this fixed path position does/does not perturb CSI
reproducibly, with this hardware and geometry. CANNOT: spatial discriminability,
localization, generalizability across positions/people/rooms/clothing/traffic regimes,
imaging, identification. Single body, single session, single RF regime — stated limits.

## 10. Exact changes from v1.4 (complete list)

1. 3×2 grid + zones → one taped fixed path position; zone-pair structure removed.
2. 24 trials → 11 (6 presence across 2 blocks + 5 bracketing empties).
3. Fisher–Yates randomization → pre-registered fixed order (nothing to permute).
4. 1-NN LOTO → dropped (single class); block-to-block consistency replaces B3 generalization.
5. Representation C → Block 1 only.
6. Metadata `zone_id` → `position_id`; + foot-mark/facing/posture record.
7. Gates reworded presence-vs-empty with identical evidence-synthesis logic; GO redefined.
Why: the floor grid is impractical; everything removed is spatial-discriminability
machinery that is meaningless with one position. Nothing added: no methods, no
thresholds, no models.

## 11. Scientific sufficiency

Sufficient for the stated question: 6 presence repetitions across 2 temporally
separated blocks, 5 bracketing empties, trial-level inference, drift accounting,
pre-registered order, zero tuning degrees of freedom. Insufficient (by design) for
any localization claim — that is the next experiment's job.

**STATUS: PROPOSAL ONLY — AWAITING HUMAN APPROVAL — NO DATA COLLECTED**
