# RFVISION-003R-C2 — 60-Second CSI Golden Test Report

**Final status: PASS.**

"RFVISION-003R-C2 PASS — CURRENT-BOARD 60-SECOND CSI GOLDEN BASELINE
VERIFIED." Next phase is separate and requires explicit approval.

## 1. Objective

Establish a sustained 60 s genuine CSI baseline for the current receiver
after C1 PASS. Controlled validation only: no human-sensing experiment,
no models, no localization, no UI/architecture changes, no flash/erase/
rebuild/reset, no router or Wi-Fi changes.

## 2. Current-board identity

ESP32-D0WD-V3 Rev 3.1, MAC `b0:3f:d3:70:20:3c`, 4 MB flash (c4/6016),
CP2102 s/n 0001 → `/dev/ttyUSB0`. NEW physical board; never associated
with historical `f4:65:0b:56:0e:18`.

## 3. Environment

Same router, position, USB port, cable, firmware, Wi-Fi config as C1.
Ambient room, no human subject, no deliberate movement, no heavy
network/RF activity. `research-data/rfvision-003r-c2/` created;
117 GB free. Host UTC vs journal clock skew observed (hours) —
durations measured by monotonic timers; event ordering proven by
firmware sequence continuity (C1 15001 → C2 126007, monotonic, no
reset).

## 4. Firmware identity

esp-csi `8633d67152db2808f141cc1595970aa9cf406045` + ESP-IDF v5.4.4
(`296b6eab9445fd720e71aecb961e2d3fbca9944`), app
`bc7a5cd5…` (C1 creds-baked build). Preflight: artifact SHA matches C1,
`git status` shows no source changes, port free, CP2102 present.
esptool deliberately NOT invoked (it hard-resets; forbidden here) —
identity continuity rests on same-port/cable, 1:1 artifact SHA, and
unbroken firmware sequencing.

## 5. Preflight (C2.0) — PASS

ttyUSB0 present, CP2102 enumerated, no holders, artifact SHA exact,
disk ample, no human experiment active. No STOP condition met.

## 6. 2-second sanity (C2.1) — PASS with documented anomaly

First window: 240 CSI_DATA/2 s at 56 kB/s (plausible) but with a binary
open-transient head. Forensics (4 open/read trials) root-caused it:
**intermittent host/bridge-side duplication** — 1–3 tiny tail chunks
replayed up to ~84k times at up to ~8× line rate (trial1: 593 KB/2 s,
84,082 tails, 3 distinct). It is NOT firmware data (zero seq
advancement inside duplicates; distinct count ≤3) and NOT the B-series
g garbage family (that had zero newlines; this is duplicated ASCII
tails). Clean sessions exist (trial2: 210 full / 0 tails). SOP adopted:
single continuous session, 3 s clean peek gate (294 records, 0 tails),
then uninterrupted capture — zero reopens.

## 7/8. Capture details + raw SHA-256 (C2.2)

ONE 62 s passive capture, raw bytes only, no parse-while-recording:
`research-data/rfvision-003r-c2/csi_golden_60s_b03fd3203c_921600.bin`
(2,197,175 B, 35.4 kB/s @ 921600 — plausible, cap 115.2).
SHA-256 `944668b317dd395a1edf157230e95fac1eace6e9c4ae38c77c8cd9b494f13459`
(+ `.sha256` sidecar). A first attempt opened into a duplication storm
(1.15 MB of dup tails before first header, then cleared) and was
DISCARDED, not promoted. Raw file byte-for-byte unchanged since capture.
Raw stays out of Git (new `research-data/.gitignore` guard).

## 9/10. Validation statistics + adapter result (C2.3)

Strict unmodified `EspCsvAdapter`, full 22-metric output
(`validation.json` beside the raw):

- occurrences 4654 / valid 4654 / malformed 0 → 100.0 % (≤0.5 % ✓)
- seq 121353→126007, missing 1 ([121765], 0.02 % ≤1 % ✓), 1 gap
- inter-arrival median 5.91 ms, p95 11.42, p99 36.04, max 289.94 ms;
  ZERO gaps >500 ms ✓
- channel 1: 100 % (≥99 % ✓); single BSSID ✓; coherent seq ✓
- RSSI −69…−57, mean −58.00 ± 0.18; noise floor −97
- CSI len 128 → 62 complex tones; all I/Q finite; per-packet delta 2.31
  (variable ✓); ZERO all-zero vectors; amp 0–47.17, mean 19.26 ± 12.73
- record rate 75.06 Hz (≈100 Hz stimulus; environmental variance, see
  §11); serial 35.4 kB/s (plausible ✓)
- adapter ACCEPTS all valid records, no relaxation ✓
- no garbage recurrence inside the accepted capture (0 malformed) ✓

## 11. C1 comparison (C2.4, stability only)

Rate 101.2 → 75.06 Hz (−26 %; ping-driven, AP-traffic dependent —
expected inter-capture variance, not a defect); valid 99.9 % → 100 %;
RSSI −54.2 → −58.00 ± 0.18 (4 dB lower, near-constant — environment,
same position); amplitude mean 19.95 → 19.26 (stable); gaps: C1 zero,
C2 one isolated missing seq; length/tones identical (128/62). No
sensing claims, no localization math, no training.

## 12. Anomalies / warnings

1. Intermittent duplication bursts at open (host/bridge side, §6) —
   excluded from the golden capture by single-session SOP; any future
   capture MUST apply the same peek-gate; recurrence inside a capture
   body would be a FAIL data-integrity event.
2. One discarded storm-open attempt (documented, not promoted).
3. Host clock skew (UTC vs journal) — durations and seq used instead.
4. Ad-hoc scripts emitted `ComplexWarning` (diff casts) — analysis
   code only, never pipeline code.

## 13. Baseline status (C2.5)

**NEW CURRENT-BOARD 60-SECOND CSI GOLDEN BASELINE VERIFIED** under MAC
`b0:3f:d3:70:20:3c`, recorded permanently in `docs/hardware/BASELINE.md`
+ `research-data/rfvision-003r-c2/{capture_metadata,validation,manifest}.json`.
No sensing/localization/ML/XAI/live-UI claims enabled — later
experiments required.

## 14. Scientific limitations

Single 62 s ambient capture, one board position, one AP, no controlled
perturbation: proves sustained transport + genuine varying CSI, NOT
sensing capability. 75 Hz vs 100 Hz stimulus and the −4 dB RSSI shift
are environmental, uncharacterized further. Duplication anomaly root
layer (bridge vs xhci driver) unidentified — phenomenology only.

## 15. Next-phase recommendation

60 s golden done. Next: EITHER controlled perturbation/human-presence
trials (separate approval + safety constraints) OR `LiveProvider`
binding against this baseline for the web console. Nothing starts
automatically.
