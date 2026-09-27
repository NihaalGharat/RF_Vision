# RFVISION-011 — Pre-Session Status Report

**Phase:** Controlled Spatial Discriminability Pilot — pre-session setup
**Protocol:** `RFVISION-011-PROTOCOL-v1.3.md` (v1.3 FINAL, frozen, unaltered)
**Baseline commit:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0` (branch `main`, tracked tree clean)
**Report date (UTC):** 2026-09-23
**Status:** STOPPED — GO declined, E1 not authorized

No experimental data collected. No firmware/AP/USB/config change. No ML,
localization, imaging, or UI work. No commit, no push.

---

## 1. Baseline and repo integrity

- `main` at `d1f12a5`, `git diff` empty; only untracked docs + Git-ignored research-data.
- v1.3 FINAL protocol present and byte-unchanged; single canonical copy
  (older iterations removed per operator instruction).
- `research-data/rfvision-011/{geometry,order,trials,validation,analysis,manifest,hashes}/`
  created; `order/trial_order.csv` holds the exact frozen seeds/orders
  (B1 `11011`, B2 `11012`, B3 `11013`); all contents proven Git-ignored.

## 2. Hardware identity (verified on-device, not inferred)

- Node A `b0:3f:d3:70:20:3c` on usb-0:5.4 → ttyUSB0 — chip eFuse MATCH.
- Node B `04:b2:47:20:1a:dc` on usb-0:1 → ttyUSB1 — chip eFuse MATCH.
- Firmware artifact SHA `0a490737…dd` — MATCH. AP live scan Nihaal /
  `8c:53:c3:5b:e1:59` / ch 1 / 2412 MHz — MATCH.

## 3. Dual-node health check (65 s, non-trial, data discarded)

| Check | Node A | Node B |
|---|---|---|
| Records / measured rate | 3666 / 55.8 Hz | 5278 / 80.8 Hz |
| Seq gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 |
| Stream MAC / channel | AP BSSID / ch 1 (unanimous) | AP BSSID / ch 1 (unanimous) |
| RSSI | −58…−50 dBm | −61…−48 dBm |
| Payload framing | 3666/3666 single-line, 128 ints | 5277/5278 single-line, 128 ints |

Rates are below the validated 95–100 Hz (protocol notes AP-traffic dependence).
At 60 s this yields ~3.3k/4.9k records/node vs §K's ≥5000 criterion — operator
ruled **re-test just before E1**. Tone mapping and sync state deferred to
per-trial §K with the validated stack.

## 4. Operator-supplied geometry (feet as given → meters)

Convention (operator): X = width, Y = length, Z = down from ceiling, H = height above floor.
- Room: 9 × 15 × 8.7 ft = 2.743 × 4.572 × 2.652 m. Origin corner: MISSING.
- Node A: (3.6, 7.8, Z6.9) ft, H 1.8 ft = 0.549 m, orientation "+Z" (ambiguous).
- Node B: (3.6, 9.4, Z6.9) ft, H 1.8 ft = 0.549 m, orientation "+Z" (ambiguous).
- Separation: ~1.6 ft ≈ 0.49 m (operator: 1.5 ft, one laptop).
- AP (router): (3.2, 0.65, Z6.2) ft; stated height 3.2 ft is inconsistent
  (6.2 + 3.2 = 9.4 ≠ 8.7 ceiling) — needs clarification.
- Environment: door closed, window closed, fan ON. Outsiders/other RF: unstated.
- Walls/furniture: MISSING. Zones Z1–Z6: NOT SUPPLIED.

Partial manifest: `research-data/rfvision-011/geometry/geometry.json` (INCOMPLETE).

## 5. Deviations vs frozen protocol

1. Node height 0.55 m vs required 1.0–1.5 m.
2. Node separation ~0.49 m vs required ~3 m — load-bearing: co-located nodes
   undermine the A/B spatial-complementarity premise.
3. Nonstandard Z-from-ceiling convention (recorded verbatim; workable if consistent).

## 6. Participant/environment gate

YES (7): single participant, posture fixed, electronics cleared, room fixed,
env documented, no extra people, nodes fixed.
NO (3): orientation fixed, phone parked away, grid marked → gate FAILED.

## 7. Python runtime — RESOLVED

Installed exactly per `requirements.lock` (operator-authorized); stack imports;
pytest **161/161 passed** in 12 s.

## 8. Verdict

**GO DECLINED.** E1 blocked on: zone grid, three gate NOs, geometry-deviation
ruling (fix to protocol or explicitly accept with weakened premise), origin,
walls/furniture, AP clarification, and the agreed pre-E1 rate re-test.
 standing by for those inputs and a fresh GO.
