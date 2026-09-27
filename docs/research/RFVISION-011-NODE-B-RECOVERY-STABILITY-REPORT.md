# RFVISION-011 — Node B Recovery + Dual-Node Stability Qualification Final Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, unmodified)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`
**Phase scope:** authorized Node B recovery check (Phase 1, 30 s passive) +
dual-node stability qualification (Phase 2, ~136 s simultaneous, NOT a
trial). No E1/E2/P1, no firmware change, no reflash, no AP/config change,
no experimental data, nothing written to trial directories, no commit,
no push.
**Entry state:** Node A healthy post-recovery (30 s steady 2610/0, 100%,
62 tones, 0/0/0); Node B erratic after the previous USB window (silent
wedge, fragment-flood bursts, depressed rate).
**Report date (UTC):** 2026-09-23

## 1. Physical window (operator-confirmed, with measured caveat)

1. Verified no process held the ports before hand-over.
2. Operator confirms: Node B unplugged ~10 s, reseated into the same port;
   Node A, ESP32 positions, router, furniture, room setup reportedly
   untouched.
3. **Measured caveat:** by-path timestamps show the 13:31 re-enumeration hit
   `usb-0:5.4` (**Node A**'s path) while `usb-0:1` (**Node B**'s) is
   untouched since 13:19 — in both physical windows the opposite board's
   connection cycled from what was intended. Readiness in this report is
   established by measurement, not by the physical procedure. Hub cable
   labeling should be treated as unverified.

## 2. Identity + firmware verification (post-window)

- `/dev/ttyUSB0` eFuse MAC `04:b2:47:20:1a:dc` = Node B on `usb-0:1` ✓
- `/dev/ttyUSB1` eFuse MAC `b0:3f:d3:70:20:3c` = Node A on `usb-0:5.4` ✓
  (first A attempt gave a transient stub-sync error ~1 min after A's
  13:31 power-cycle; clean on retry — resolved, reported, not hidden)
- Firmware host artifact SHA-256
  `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd` —
  unchanged ✓

## 3. Phase 1 — Node B recovery check (30 s passive, 921600, real parser)

- Transient (first 3 s): 166 valid / 0 malformed / 1 non-CSI = 100.0%.
- Steady-state: **2041 valid / 0 malformed / 0 non-CSI = 100.0%**,
  gaps/dups/ooo **0/0/0**, unanimous 62 tones, all IQ finite, BSSID
  unanimous `8c:53:c3:5b:e1:59`, channel 1 unanimous, RSSI −58…−53
  (mean −54.06). Per-second rate varied (AP-traffic variation) with perfect
  sequence continuity. **No floods, no silence, no fragments. Phase 1 PASS.**

## 4. Phase 2 — Dual-node stability (135.9 s, validated stack, NOT a trial)

`web/dual_node.DualNodeSession`, both nodes simultaneous; no recording;
telemetry to `/tmp` scratch only (`dual_stability.json`); no human in the
sensing path.

| Check | Node A | Node B |
|---|---|---|
| Source state / gate | LIVE_VERIFIED (112/117; 5 startup) / passed | LIVE_VERIFIED (112/117; 5 startup) / passed |
| Valid / malformed | 4667 / 0 (100%) | 7326 / 0 (100%) |
| Gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 |
| 62 tones / finite IQ | unanimous / all finite | unanimous / all finite |
| BSSID / channel | unanimous / 1 | unanimous / 1 |
| Stale samples | 0 of 117 (max age 2.96 s < 3.0) | 0 of 117 (max age 2.38 s) |
| Valid monotone (no wedge) | yes | yes |
| Storm epochs | 0 | 1, startup-only (see §5) |
| RSSI mean | −57.38 | −52.54 |

- Sync: UNSYNCED×1 → SYNCING×45 → **SYNCED×71** (1 Hz samples); final
  SYNCED, both estimators ready (≥64 observations, jitter ≤ 2 ms). Normal
  convergence; both nodes streaming the full session.
- Rate swung 7.7–163 Hz on both nodes — AP-traffic variation per documented
  C-series phenomenology; 0 gaps throughout proves variation is traffic,
  not loss. Not counted as instability.
- Momentary ages (max 2.96 s / 2.38 s) never reached the 3.0 s stale
  threshold (0 stale of 234 checks) — reported as observation, not failure.

## 5. Node B single storm epoch — disposition: startup transient

- Final duplication block (B): `storm: true` (latched boolean),
  `storm_epochs: 1`, `consecutive_identical: 0`, `impossible_throughput:
  false`; gate passed with `pre_gate_storm: false`.
- Mechanism (verified against code + totals): 32 byte-identical **non-CSI
  boot lines** in the startup burst (B had been RTS-reset by the identity
  check; 62 boot-text lines total, all at open). The epoch latched before
  settle anchored (`settle_epochs = storm_epochs = 1`), so the gate passed
  per design; the parser runs only on valid lines, so the latch was never
  re-observed and `consecutive_identical` ended at 0.
- Proven non-recurring: exactly 1 epoch in 135.9 s, zero binary lines on
  either node all session, no repetition after startup. Satisfies the
  "no recurring binary/fragment-flood behavior after startup" criterion.
  The latched boolean is cosmetic; epochs are the metric.

## 6. USB/power-path hypothesis assessment

**Supported for the transient events; no persistent fault evident.** Every
instability episode (A's garbage blobs, B's silent wedge, B's fragment
floods, the transient stub-sync error) clusters around USB power events —
the 13:19 / 13:31 re-enumerations and RTS resets. Once the connections
settled, both boards stream cleanly for 135 s dual + 30 s single at 100%
validity with full sync. Nothing in the current data indicates an ongoing
hub/power fault. Residual uncertainty: hub cable labeling (see §1).

## 7. Scope notes

- No experimental trial, no E1/E2/P1, no human in the sensing path.
- `research-data/` untouched — R11P-01 / R11P-01R quarantine intact;
  Phase 2 wrote no raw captures anywhere (counters + parser-validated live
  path only).
- Tracked tree: only the two pre-authorized Option B files modified
  (`web/source.py`, `tests/unit/test_live_provider.py`); nothing committed
  or pushed.

## 8. Verdict

```text
DUAL_NODE_STABILITY_PASS — READY_FOR_FRESH_E1
```
