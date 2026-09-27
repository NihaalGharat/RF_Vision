# RFVISION-011 — Practical-Constraint Assessment Report

**Phase:** Controlled Spatial Discriminability Pilot — student-constraint amendment path
**Protocol:** `RFVISION-011-PROTOCOL-v1.3.md` (v1.3 FINAL, frozen, unaltered — no v1.4 created)
**Baseline commit:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0` (branch `main`, tracked tree clean)
**Report date (UTC):** 2026-09-23
**Status:** STOPPED — E1 not started, no commit, no push

No experimental data collected. No firmware/AP/USB/config change. No ML,
localization, imaging, or UI work.

---

## 1. Assessment (per required format)

```text
RFVISION-011 PRACTICAL-CONSTRAINT ASSESSMENT

Maximum achievable node separation: NOT YET MAXIMIZED (operator step outstanding;
  use longest existing USB cables, same laptop, then measure)
Actual measured separation: 0.49 m (1.6 ft from coords; operator stated 1.5 ft)

Node height: operator to use ordinary furniture to approach 1.0-1.5 m if safe
Actual measured height: 0.55 m (1.8 ft) both nodes

Same-laptop USB: RELIABLE (both ports stream; topology incident in §2)

Node orientation: NOT FIXED ("+Z" ambiguous — confirm meaning)

Room geometry: INCOMPLETE (origin corner, wall distances, furniture missing)

Zone grid: INCOMPLETE (Z1-Z6 not supplied; >=1.0 m spacing unverified)

Acquisition rate (measured, variable with AP traffic):
Node A: 55.8 Hz (65 s raw; alive on new port, rate re-check due)
Node B: 80.8 Hz (65 s raw); 62.1 Hz avg + 29.8 rolling (25 s validated)

Synchronization: FAIL (dual session cannot start — Node A cable moved to
  usb-0:5.1; validated resolver demands usb-0:5.4 and must not be bypassed)

Scientific status: BLOCKED (practical-pilot framing accepted, execution gated)

Remaining human actions:
1. Move Node A USB cable back to the recorded port (usb-0:5.4); do not swap A/B.
2. Maximize separation with existing cables; re-measure both node coordinates.
3. Raise nodes toward 1.0-1.5 m on stable furniture if safe; record actual H.
4. Confirm orientation meaning; supply origin, walls, furniture, AP fix.
5. Supply all six zone definitions (center/size/distances).
6. Confirm the 3 gate NOs (orientation fixed, phone parked, grid marked).
7. Then authorize the final-placement diagnostic re-check (rate+sync) before E1.
```

## 2. USB topology incident

Node A's board was unplugged/replugged into a different hub port at 01:28
(`usb-0:5.4` → `usb-0:5.1`, re-enumerated as ttyUSB0). Chip eFuse re-verified
the board is still ESP32-A (`b0:3f:d3:70:20:3c`) and streaming. The frozen
resolver requires `usb-0:5.4` and refuses to guess `ttyUSBn` — no code was
changed to bypass it. Resolution is physical: restore the recorded port.

## 3. Validated Node B diagnostic (25 s, NOT a trial, data discarded)

`LIVE_VERIFIED`, gate passed: valid 1555, malformed 0, valid_pct 100.0,
gaps/dups/ooo 0, **62 tones**, IQ finite, channel 1, BSSID unanimous,
RSSI stable ~−65 dBm. Rates vary with AP traffic across runs (reported, not
reconciled): the §K ≥5000-records/60 s arithmetic must be judged at session time.

## 4. Proposed amendment (NOT applied — awaiting approval)

Demote v1.3 §D "~3 m separation" from requirement to recorded ideal
(`planned_ideal_separation ≈ 3 m`, `actual_separation` = measured); add priority
order USB-reliability > max-practical-separation > stability > height >
orientation; retitle the phase "Controlled Spatial Discriminability Pilot under
practical student-scale constraints." All of §8's analysis requirements unchanged.

## 5. Participant/environment gate (standing)

YES (7): single participant, posture fixed, electronics cleared, room fixed,
env documented, no extra people, nodes fixed. NO (3): orientation fixed,
phone parked away, grid marked → gate FAILED until confirmed.
