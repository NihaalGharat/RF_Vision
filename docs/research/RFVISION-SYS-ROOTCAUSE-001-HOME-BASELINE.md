# RFVISION-SYS-ROOTCAUSE-001 — HOME BASELINE

**Type:** read-only system diagnostic (NOT an RFVISION-011 trial). No E1/E2/P1 attempted.
**Network:** HOME Xiaomi router. **Git:** `d1f12a5`, branch `main` (only pre-authorized
Option B files modified; history untouched, no commit/push).
**Recorder cap:** `REC_MAX_SECONDS = 120.0` (`web/source.py:225`).
**Acquisition:** `web/dual_node.DualNodeSession` + `NodeProvider` (unchanged).
**Sync:** `localization/synchronization/sync.py ClockOffsetEstimator`, criterion
`SYNC_MIN_N=64`, `SYNC_MAX_JITTER_NS=2ms` (unchanged, never retuned).
**Firmware SHA-256:** `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd` (verified, unchanged).
**Identity:** existing mapping used (`A=b0:3f:d3:70:20:3c@usb-0:5.4→ttyUSB1`,
`B=04:b2:47:20:1a:dc@usb-0:1→ttyUSB0`); stack-reported MACs matched on every open.
No esptool/MAC reads performed.
**Protocol deviation (1):** after Node B delivered 0 bytes for a full 30 s stack
observation, I opened `/dev/ttyUSB0` once with direct pyserial (outside the stack,
control lines cleared after open) to test the path. This may have delivered a
reset edge to the board. No other out-of-stack access occurred. Impact: B's later
data follows a board reboot; boot transient recorded and excludable; firmware,
config, setup unchanged.

## A. Environment (passive only, no scan, no reassociation)
- Ubuntu 26.04.1 LTS, kernel 7.0.0-31-generic, Python 3.14.4
- `wlp0s20f3`, driver `iwlwifi`, firmware `89.123cf747.0 so-a0-hr-b0-89.uc`
- SSID `Nihaal`, BSSID `8c:53:c3:5b:e1:59`, 2412 MHz / ch 1 / 20 MHz (matches expected)
- Signal −38 dBm (avg −36); RX 1.0 Mbit/s; TX 144.4 Mbit/s MCS 15 short GI
- Power save: ON; tx retries 17, tx failed 0, rx drop misc 52, beacon loss 0
- Link had reassociated ~3 min before inspection (connected time 176 s) — observed, unexplained

## B. Timestamp foundation (no firmware change needed)
Every `CSI_DATA` record carries `cols[18]` = ESP32 `rx_ctrl.timestamp` (signed
32-bit µs; parsed as `ts_esp32_us`/`ts_wifi_us`). Live path stamps true
serial-ingress `ts_host_ns`. ESP-vs-host separation computed offline from
lossless `/tmp` recordings (complete ESP series) + ingress stamps + provider counters.
Proven by code read: stack opens ports via raw `os.open`+termios and **never touches
RTS/DTR** — stack opens cannot reset boards (and cannot revive hung ones).

## C/D. Single-node 30 s (stack, /tmp scratch)
| | Node A | Node B |
|---|---|---|
| Provider valid / malformed / non-CSI | 4245 / 0 / 0 (100%) | 2956 / 1 / 0 (99.97%) |
| Gaps / dups / ooo | 0 / 0 / 0 | 1 / 0 / 0 |
| Live tones / IQ / BSSID / ch | 62 / finite / unanimous / 1 | 62 / finite / unanimous / 1 |
| RSSI | −58…−55 (mean −56.5) | −64…−51 (mean −54.3) |
| Gate / state | passed / LIVE_VERIFIED | passed / LIVE_VERIFIED |
| **ESP rate (complete series)** | **141.5 Hz** (span 29.98 s) | **128.4 Hz** over active span (23.01 s; stream started ~7 s after open — WiFi-assoc-scale delay, 0 boot text) |
| **Host exact rate** | **141.5 Hz** | **98.5 Hz wall / ~128.5 Hz active → ESP ≈ host while streaming** |
| ESP dt median / p95 / p99 / max | 6.29 / 11.0 / 16.9 / 49 ms | 6.14 / 13.0 / 24.3 / 427 ms |
| ESP dt CV | 0.40 | 1.45 |
| UART load | 68.4 KB/s → ~684 kbps ≈ **74% of 921600** | 46.8 KB/s → ~610 kbps ≈ **66% of 921600** |
| Storm epochs | 0 | 0 |

UART not saturated (headroom at peak single-node rates; ~480 B/record ASCII).

## E. Dual 120 s (stack defaults, telemetry only, no human, no trial dir)
| | Node A | Node B |
|---|---|---|
| Valid / malformed / non-CSI | 9213 / 14 / 5813 | 11470 / 64 / 2296 |
| Gaps / dups / ooo | 18 / 0 / 0 | 82 / 0 / 0 |
| Tones / IQ / BSSID / ch | 62 / finite / unanimous / 1 | 62 / finite / unanimous / 1 |
| ESP rate (span) | 115.6 Hz (span 79.7 s — ~40 s startup distress) | 125.5 Hz (span 91.4 s — ~28 s startup distress) |
| Host exact rate (wall) | 76.8 Hz | 95.6 Hz |
| ESP dt median / p99 / max | 6.5 / 33.1 / 756 ms | 6.1 / 37.6 / 330 ms |
| Storm epochs | 3 | 11 |
| Gate / state (end) | **failed / LIVE_UNVERIFIED** | **failed / LIVE_UNVERIFIED** |
| Estimator jitter / drift | 9.06 ms / +0.98 ms/sample | 2.61 ms / −0.016 ms/sample |
| Pipeline (parser/queue) mean / max | 121 µs / 5.3 ms | 107 µs / 5.3 ms |
- **Sync: 0% SYNCED / 98.3% SYNCING / 1.7% UNSYNCED (n=120), final SYNCING.**
  Per-10 s poll rates swung A 13.9–71.8 Hz, B 23.4–65 Hz; **rate ratio A/B = 0.92
  overall** — sync never converged at any imbalance level.
- Non-CSI identity: A's 5813 dominated by ONE identical CSI-tail fragment
  (`7,13,…10]"`) repeated **5656× consecutively** (~4 s stuck buffer); B spread
  mid/late-session across 52 fragment shapes + 1607 binary/control bytes.
  A's distress concentrated in first half (5718/5813 in first 50%); B's grew
  through the session. `overlong_dropped=0`, transports error-free.

## F. Causal separation
1. **AP/RF source → traffic-driven generation volume (HIGH).** Rates 42→144 Hz
   across sessions, 14→72 Hz per 10 s bin; medians glued ~6.1–6.5 ms; ESP≈host
   while streaming. For: matched medians both nodes/sessions; burst timescale =
   traffic timescale. Against: none.
2. **ESP32 generation healthy (MEDIUM-HIGH).** For: regular medians, ESP≈host,
   monotonic signed-32-bit WiFi ts, zero wraps in-window. Against: heavier tails
   in dual (CV 1.4–1.8) — but tails mirror traffic burstiness, and forward seq
   gaps with sub-second time deltas prove loss is *downstream* of seq assignment.
3. **UART/USB transport → dual-only corruption/loss layer (HIGH).** For: storms,
   fragments, binary bytes, forward gaps, malformed appear ONLY with simultaneous
   dual streaming (singles pristine); loss downstream of seq assignment fits
   firmware-TX-ring overflow or USB re-delivery stall (stuck-buffer runs).
   Against saturation-as-cause: 66–74% line utilization (MEDIUM against).
   Exact stall site (firmware TX vs USB vs driver) undetermined (LOW each).
4. **Linux acquisition healthy (HIGH).** For: no control-line touches (code),
   error-free transports, file==stream counts, pipeline ~0.1 ms mean / 5.3 ms max.
5. **Sync estimator threshold too tight for burst regime (HIGH contributor).**
   For: 0% SYNCED over 120 s at 9–11k observations with jitter 2.6/9.1 ms vs
   2 ms bar; E1 reached 79% only in a calmer (71/42 Hz, zero-gap) regime.
   Rate imbalance is NOT necessary for sync failure (ratio 0.92 here) — it
   aggravates (E1: B 425 ms vs A 0.56 ms) but burstiness+gaps alone suffice.
6. **Spontaneous board hangs (HIGH observed, trigger LOW).** B mute 30 s
   (0 bytes, enumeration intact, stack blameless) → streamed after open-edge;
   both boards showed multi-minute-scale startup distress entering dual after
   clean singles. Firmware crash/reboot-proneness is real; trigger unknown.

## G. E1 (R11P-01E) comparison
E1 = traffic-starved regime (A 71 Hz/4272, B 42 Hz/2518, zero gaps/storms) →
SYNCED 79.2% but count gate failed. HOME diag = bursty regime (A up to 144 Hz,
B up to 128 Hz active) → counts plentiful but dual sync 0% + storms/gaps.
Same AP, opposite failure modes: **AP traffic variability is the common driver;
the fixed gates (≥5000 counts AND ≥95% SYNCED AND 2 ms jitter) demand a traffic
Goldilocks zone the HOME AP does not reliably provide.** No E1 reinterpretation.

## H. VCET replication checklist (repeat exactly)
1. Passive host block (§A: kernel/Ubuntu/Python/driver/fw/SSID/BSSID/freq/ch/
   width/signal/RX-TX/MCS/GI/power-save/retries/beacon-loss/connected-time).
2. Software block (commit/branch/status/cap/sync constants/fw SHA).
3. Single A 30 s + single B 30 s via same stack scripts, /tmp raw + per-record
   poll log: ESP rate/span, dt median/p95/p99/max/CV, host exact rate, UART
   B/s + % of 921600, valid/mal/noncsi/gaps, tones/IQ/BSSID/ch/RSSI, startup delay.
4. Dual 120 s defaults: per-node same + sync % series, jitter/drift/readiness,
   convergence time, per-10 s rate bins + sync mix, storm epochs, fragment/binary
   census, gate/state endpoints.
5. Same offline analyzer (`/tmp/sysdiag/analyze.py` logic) on both datasets.

## I. Verdict
```text
HOME_BASELINE_COMPLETE — READY_FOR_VCET_COMPARISON
```
Firmware, protocol, AP, USB topology, positions, source/sync code, git history:
all unchanged (sole exception: one disclosed out-of-stack port open that likely
rebooted Node B; no commit/push; no trial run; no experimental conclusion).
Scratch: `/tmp/sysdiag/` (JSONs, raws, `analysis.json`). E1/E2/P1 untouched.
