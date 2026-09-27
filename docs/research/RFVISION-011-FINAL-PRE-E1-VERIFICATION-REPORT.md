# RFVISION-011 — Final Pre-E1 Verification Report

**Phase:** Controlled Spatial Discriminability Pilot, practical student-scale (v1.4)
**Protocol:** `RFVISION-011-PROTOCOL-v1.4.md` (AMENDED; v1.3 FINAL preserved, SHA `d3870779…`)
**Baseline commit:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0` (branch `main`, tracked tree clean)
**Report date (UTC):** 2026-09-23
**Status:** NOT READY (human-side setup data) — E1 not started

No experimental data collected. No firmware/AP/USB/config/code change. No ML,
localization, imaging, or UI work. No commit, no push.

---

## 1. Repository integrity — PASS

`main` at `d1f12a5`; `git diff` empty; v1.4 present; v1.3 FINAL byte-unchanged;
statistical methodology untouched per prior hunk-level audit.

## 2. Node identity — PASS

Chip eFuse queried on both live ports: ttyUSB0 = `b0:3f:d3:70:20:3c` (Node A),
ttyUSB1 = `04:b2:47:20:1a:dc` (Node B). Identity measured, never inferred.

## 3. USB by-path status — PASS (restored)

`usb-0:5.4 → ttyUSB0`, `usb-0:1 → ttyUSB1`. The dual session resolved with zero
workarounds; the validated resolver is unmodified.

## 4. Firmware status — PASS

Build artifact SHA `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd`
exact match. No flash, no change.

## 5. AP status — PASS

Live scan: Nihaal / `8c:53:c3:5b:e1:59` / channel 1 / 2412 MHz. No AP changes.

## 6. Dual-node health check — 65.3 s, validated stack, discarded (NOT E1)

| Check | Node A | Node B |
|---|---|---|
| Records / valid / malformed | 6308 / 6308 / 0 | 7464 / 7464 / 0 |
| Valid % | 100.0 | 100.0 |
| Rate (avg / rolling Hz) | 97.0 / 154 | 114.8 / 106.6 |
| Gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 |
| 62 tones / IQ finite | 62 / true | 62 / true |
| RSSI mean (stable) | −63.4 dBm | −56.3 dBm |
| BSSID / channel | unanimous / 1 | unanimous / 1 |
| Session gate | LIVE_VERIFIED, passed | LIVE_VERIFIED, passed |
| Host-ts anomalies | none | none |

Watch item (not a blocker): one duplication-storm epoch latched on Node A with
zero identical lines and a passed gate — consistent with the post-identity-check
reboot burst; steady state clean. Monitor in E1 under standing abort rules.

## 7. Synchronization — SYNCED

Both nodes ready: A jitter 216 µs / 6308 obs, B 110 µs / 7464 obs (criterion
≤2 ms, ≥64 obs). Host-side clock mapping only, per protocol.

## 8. Actual node separation — 3 ft / ~0.9144 m

Operator-confirmed final; maximum practical same-laptop USB separation.
Recorded in `research-data/rfvision-011/geometry/geometry.json` with
`planned_ideal_separation ≈ 3 m` retained. Context/limitation, never pass/fail.

## 9. Geometry available / missing

Available: room 2.743 × 4.572 × 2.652 m; node coordinates and heights (0.55 m,
handled under the v1.4 height rule); AP coordinates (height figure inconsistent —
clarification outstanding); environment (door/window closed, fan ON).
MISSING: origin corner, wall distances, furniture, all six zone definitions
(center/size/node distances), ≥1.0 m center-spacing check.

## 10. Human setup confirmations

Confirmed: positions final, 3 ft separation held, single participant, posture
fixed, electronics cleared, room fixed. NOT confirmed: orientation meaning
("+Z" ambiguous), operator phone parked, floor grid marked, zone labels present.

## 11. §K readiness — PASS (diagnostic level)

valid_pct 100 ≥ 99; gaps 0; 62 tones; IQ finite; SYNCED; current rates project
~5.8k/6.9k records per 60 s window (≥5000). Per-trial §K validation remains
mandatory during execution; FLAGs reported, never silently dropped.

## 12. Final status

```text
NOT READY — zone grid/definitions missing (protocol step 3 precedes E1),
plus phone-parking and orientation confirmations outstanding
```

All automated checks pass; the block is human-side setup data only. E1 was not
collected. Awaiting the zone grid, remaining confirmations, and a fresh human GO.
