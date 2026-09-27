# RFVISION-011 Presence Pilot v1.0 — Readiness Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN this session; v1.4 preserved byte-identical)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`, tracked tree clean
**Report date (UTC):** 2026-09-23 — NO DATA COLLECTED, no commit, no push

## Hardware / environment (exact)
- Node A: ESP32 `b0:3f:d3:70:20:3c` (eFuse) on `usb-0:5.4` → ttyUSB0, ceiling-facing
- Node B: ESP32 `04:b2:47:20:1a:dc` (eFuse) on `usb-0:1` → ttyUSB1, ceiling-facing
- Firmware SHA-256: `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd` (unchanged)
- AP: Nihaal / `8c:53:c3:5b:e1:59` / ch 1 / 2412 MHz (live scan)
- Separation: 3 ft / 0.9144 m (operator final, max practical same-laptop USB)
- Phones: airplane mode, parked aside (operator-confirmed)

## Trial matrix (11, frozen order)
E1,E2 PRE → P1–P3 block 1 → E3 MID → P4–P6 block 2 → E4,E5 POST.
Full order: `research-data/rfvision-011-presence/order/trial_order.csv` (baseline_ref + c_ref per row).
Sidecar template: `trials/SIDECAR_TEMPLATE.json` (PLANNED, TBD completed at capture).

## Acquisition settings
921600 baud, simultaneous dual capture, 15 s warm-up + 60 s clean + 5 s margins per trial;
raw binaries + per-trial JSON sidecar + SHA-256; Git-ignored; `chmod 444` post-session.

## Health-check measurements (65.0 s dual session, validated stack, discarded)

| Gate | Node A | Node B | §K |
|---|---|---|---|
| Session gate | LIVE_VERIFIED, passed | LIVE_VERIFIED, passed | — |
| Valid / malformed | 6169 / 0 | 6334 / 0 | — |
| Valid % | 100.0 | 100.0 | ≥99 PASS |
| Rate (Hz) | 95.4 (avg 94.9) | 97.8 (avg 97.4) | 60 s→~5.7k/5.8k ≥5000 PASS |
| Gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 | gaps≤10 PASS |
| 62 tones / IQ finite | 62 / true | 62 / true | PASS |
| RSSI (stable) | −59.1 | −60.1 | present PASS |
| BSSID / channel | unanimous / 1 | unanimous / 1 | PASS |
| Storm / impossible TP | none / false | none / false | PASS |
| Host-ts fresh / anomalies | 2 ms / none | 1 ms / none | PASS |
| Sync | ready, jitter 256 µs, 6169 obs | ready, jitter 121 µs, 6334 obs | — |
| Session sync | SYNCED (criterion ≥64 obs, ≤2 ms) | | ≥95% PASS |

## Readiness gates (15-point) — ALL PASS
1. tracked tree clean ✓ 2. baseline `d1f12a5` ✓ 3. v1.3/v1.4/proposal present, v1.4 hash `8ec4c4e5…` unchanged ✓
4. both nodes on recorded by-paths ✓ 5. eFuse MACs match ✓ 6. firmware SHA unchanged ✓
7. AP/BSSID/channel live-verified ✓ 8. 62 tones both ✓ 9. IQ finite both ✓ 10. valid 100% ✓
11. zero gaps/dups/ooo, no storms ✓ 12. SYNCED, jitter ≪2 ms ✓ 13. live CSI both ✓
14. `research-data/rfvision-011-presence/` skeleton + order + template ready, all ignored ✓
15. no stale run files (presence dir fresh; only grid-track geometry/order remain under superseded `rfvision-011/`, clearly separate) ✓

## Operator checklist (confirm at GO, every presence trial)
Feet on taped marks; one fixed facing (state its value); stationary, arms at sides; same
participant/clothing/posture; no phone interaction; touch nothing; enter/exit on cue only;
log any disturbance — repeat only on human decision.

## Remaining physical actions
1. Confirm taped foot marks + facing line in place; state the facing value.
2. Confirm clothing/posture choice for the session.
3. Confirm participant ready, phones aside, room as documented.
4. Say GO — then E1 starts under the frozen protocol; per-trial §K applies throughout.

```text
READY_FOR_E1 — HUMAN GO REQUIRED
```
