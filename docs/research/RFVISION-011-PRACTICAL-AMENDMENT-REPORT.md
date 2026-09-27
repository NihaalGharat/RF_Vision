# RFVISION-011 — Practical Amendment Report

**Phase:** Controlled Spatial Discriminability Pilot — approved student-scale amendment
**Protocol:** `RFVISION-011-PROTOCOL-v1.4.md` (AMENDED; v1.3 FINAL preserved byte-identical)
**Baseline commit:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0` (branch `main`, tracked tree clean)
**Report date (UTC):** 2026-09-23
**Status:** AWAITING FINAL PHYSICAL SETUP — E1 not authorized

No experimental data collected. No firmware/AP/USB/config/code change. No ML,
localization, imaging, or UI work. No commit, no push.

---

## 1. Amendment applied

New file `docs/research/RFVISION-011-PROTOCOL-v1.4.md`; v1.3 FINAL untouched
(SHA `d3870779172c819bad95ba80c27af683e684c16d91184212659f1b1177555c31`).
Hunk-level diff proves changes exist only in: title/status header, new v1.4
revision notes (v1.3 notes retained verbatim as history), §A (student-scale
characterization + no-definitive-claims), §D (placement rule rewritten),
§I (+`planned_ideal_separation`, +`actual_separation`), §S step 1.

## 2. Statistical methodology preserved — UNCHANGED

6 zones; 18 occupied + 6 empty = 24 trials; E1/E2 PRE, B1→E3, B2→E4, B3, E5/E6
POST; frozen B1/B2/B3 orders; baseline assignment + `baseline_ref`; A+B primary,
C supporting; 62 tones; trial replication unit; within-vs-between + separation
ratio; supporting 1-NN; drift analysis; no top-k; no accuracy threshold; no
auto-retries; no selective removal; full anomaly reporting; four verdicts.

## 3. Geometry rule (single, authoritative — §D)

> The experiment uses the maximum practical node separation achievable with the
> existing same-laptop USB setup. Approximately 3 m is retained as the ideal
> reference geometry. Actual separation is measured and reported as an
> experimental condition and limitation.

Priority: USB reliability > max separation > stability > height (1.0–1.5 m
preferred, actual recorded) > orientation. Actual separation is context, never
pass/fail. Never fabricated, rounded upward, or called ~3 m unless true.

## 4. Consistency audit — PASS

Full-document sweep for `3 m`, `separation`, `ideal`, `height`: one mandatory
rule (§D). §C records only; §E spans any inter-node gap; §K by-paths unchanged;
§Q reseat rule consistent; H1 "separation" is trial-space statistics; gates hold
zero distance criteria; `actual_separation` in §D and §I. No contradictions.

## 5. Remaining physical actions

1. Restore Node A cable to `usb-0:5.4` (currently 5.1 — dual session blocked).
2. Maximize separation on existing cables; re-measure coordinates + actual separation.
3. Approach 1.0–1.5 m height on safe furniture; record actual H.
4. Confirm orientation; supply origin, walls, furniture, AP fix, all six zones.
5. Confirm the three gate NOs (orientation fixed, phone parked, grid marked).
6. Final-placement health check (rate + sync), then fresh GO.

## 6. Final status

```text
RFVISION-011 PRACTICAL AMENDMENT

Protocol:
AMENDED (v1.4; v1.3 FINAL preserved)

Statistical methodology:
UNCHANGED

3 m ideal reference:
PRESERVED

Maximum practical separation:
APPROVED

Actual separation:
TO BE MEASURED

Same-laptop USB:
REQUIRED

E1:
NOT AUTHORIZED

STATUS:
AWAITING FINAL PHYSICAL SETUP
```
