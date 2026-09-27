# RFVISION-011 — Node A Recovery + Post-Recovery Health-Check Final Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, unmodified)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`
**Phase scope:** authorized Node A physical recovery (operator-performed
reseat/power-cycle) + post-recovery health validation of Node A with a short
Node B check. No E1/E2/P1, no firmware change, no reflash, no AP/config
change, no experimental data collection, no commit, no push.
**Authorizing diagnosis:** `NODE_A_DIAGNOSIS_COMPLETE —
PHYSICAL RESEAT/POWER-CYCLE RECOMMENDED` (classification B, ESP32
runtime/boot-state issue, confidence HIGH, reflash NOT warranted).
**Report date (UTC):** 2026-09-23

## 1. Physical action (operator-confirmed)

1. Verified no process held the ports (`fuser` empty; no capture/serial
   processes running) before hand-over.
2. Operator confirms: Node A USB unplugged ~10 s, reseated firmly into the
   same port; Node B, router, ESP32 geometry, room setup reportedly
   untouched. No reflash, no configuration changes.
3. **Caveat (measured, not assumed):** post-reseat by-path timestamps show
   `usb-0:1` (Node B's path) re-enumerated at 13:19 while `usb-0:5.4`
   (Node A's path) kept its 12:50 stamp — Node B's USB connection was
   physically disturbed during the reseat window, not (or not only)
   Node A's.

## 2. Post-cycle identity + firmware verification

- `/dev/ttyUSB1` eFuse MAC `b0:3f:d3:70:20:3c` = Node A on `usb-0:5.4` ✓
- `/dev/ttyUSB0` eFuse MAC `04:b2:47:20:1a:dc` = Node B on `usb-0:1` ✓
- Firmware host artifact SHA-256
  `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd` —
  unchanged ✓

## 3. Node A health (921600 baud, real parser, live-path semantics)

All observations passive reads with scratch in `/tmp` only.

- **30 s passive observation:** transient (first 3 s) = 390 valid /
  0 malformed / 1 non-CSI (single binary line at open); **steady-state =
  2610 valid / 0 malformed / 0 non-CSI = 100.0%**, gaps/dups/ooo **0/0/0**,
  unanimous 62 tones, all IQ finite, BSSID unanimous
  `8c:53:c3:5b:e1:59`, channel 1 unanimous, RSSI −60…−54 (mean −57.53).
- **Provider session (6 s):** 552 valid / 0 malformed, `last_update_age_s`
  0.0051, not stale, gaps/dups/ooo 0/0/0. (`LIVE_UNVERIFIED` only because
  the 60 s gate window was not run out — expected, not a finding.)
- **Final re-check:** seqs 51908/51909/51910 consecutive (continuous uptime
  since boot, no resets), correct BSSID, 254 CSI + 1 transient binary line.
  Rate varied ~30–100 Hz across windows — within the documented AP-traffic
  variation (`web/source.py`, C-series phenomenology); sequence continuity
  proves no loss.
- **Node A verdict: HEALTHY.** Post-reset/boot transients (fragments in the
  first post-reset window, one binary line at open) occur only at open and
  never in steady state.

## 4. Node B health — NEW INSTABILITY since the reseat window

Node B was fully healthy at E1 re-run (6306 clean valid, gate passed) and
at diagnosis (859 CSI / 8 s + 1 settle line). After the 13:19 window:

1. **Silent wedge:** port opens cleanly (driver + endpoint alive, no holder
   process) but **zero bytes for 20+ s**, twice independently. Chip alive
   (ROM responds, MAC `04:b2:47:20:1a:dc`); streaming resumed only after an
   RTS reset (fresh boot from seq 0 with WiFi reconnect log to `Nihaal`,
   ch1) — the same recovery signature Node A showed.
2. **Fragment-flood bursts:** every fresh open since begins with 8,000–34,000
   shredded CSI-tail fragments at saturated byte-rate (~91 KB/s at 921600
   8N1), then settles. Pre-reseat opens showed at most 1 settle line.
3. **Depressed/erratic streaming rate:** settled windows run ~30–60 Hz with
   wild per-second swings (2–144) vs the ~95–107 Hz stable baseline.
4. Latest settled windows still parse 100% valid with 0 gaps/dups/ooo and
   correct BSSID/channel/tones — framing recovers, but **stability is not
   demonstrated**.

Working interpretation (not a concluded root cause): Node B suffered a
hub-power disturbance at 13:19 during the physical window and now shows the
same class of runtime instability Node A showed earlier (silent wedge
recoverable by reset, plus a new fragment-flood flavor). Both boards' USB
power/integrity should be treated as suspect until a full clean session
proves otherwise.

## 5. Evidence and scope notes

- No experimental data collected; all observations were passive reads with
  scratch files in `/tmp` only (`node_a_probe*.py`, `node_b_probe*.py`,
  `node_observe.py` outputs). `research-data/` untouched — R11P-01 and
  R11P-01R quarantine intact.
- Tracked tree: only the two pre-authorized Option B files modified
  (`web/source.py`, `tests/unit/test_live_provider.py`); nothing committed
  or pushed.
- No E1, E2, or P1 was run. No recovery action beyond observation and the
  resets implicit in read-only identity checks.

## 6. Verdict

```text
NODE_A_RECOVERY_FAILED — Node A healthy post-cycle (30 s: 100.0% valid 3000/3000, 62 tones, IQ finite, 0/0/0, fresh ts); Node B erratic since reseat window (20 s+ silent wedge with live USB endpoint, then recurring fragment-flood bursts + depressed ~30-60 Hz rate vs ~100 Hz baseline); fresh-E1 readiness NOT established
```

## 7. Decision required (human)

Fresh-E1 readiness needs BOTH nodes demonstrably stable, which now fails on
Node B. Recommended next step: inspect the shared USB hub/power path (both
boards' disturbances cluster around USB power events), reseat/power-cycle
Node B deliberately, then re-run this health check on Node B before any E1
attempt. Nothing further will run without explicit authorization.
