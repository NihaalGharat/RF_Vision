# RFVISION-011 — E1 Execution Report (R11P-01E, fresh run)

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, byte-identical, unmodified)
**Git baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`
**Authorization:** human APPROVED — exactly one fresh E1 (this report covers E1 ONLY; E2 NOT started)
**Qualification prerequisite:** `DUAL_NODE_STABILITY_PASS — READY_FOR_FRESH_E1` (prior phase)
**Condition:** E1 EMPTY ROOM (participant absent entire clean window, per operator-maintained setup)
**Run ID:** `R11P-01E` (fresh; NOT R11P-01 / R11P-01R)
**UTC:** 2026-09-23T08:25:46+00:00 → 08:26:46+00:00 (warm-up 15.24 s + clean 60.26 s)

## 1. No-disturbance compliance
No esptool, no read_mac, no RTS/DTR toggling, no reset/replug/reflash, no USB
changes, no firmware/AP/CSI/geometry changes, no second diagnostic. Ports were
opened only by the acquisition stack itself at session start (normal stack
behavior). No hardware command of any kind was issued during E1.

## 2. Capture (validated production path, recorder cap 120 s)
`web/dual_node.DualNodeSession`, 921600 baud simultaneous; recording armed
before warm-up, single span 75.5 s < 120 s cap — **no 30 s truncation** (files
2,497,098 B / 1,602,377 B, complete). No restart, no record removed, no repair.

## 3. Node integrity — clean window (live windowed counters; file parse corroborates)
| | Node A | Node B |
|---|---|---|
| Valid / malformed | 4272 / 0 (100.0%) | 2518 / 0 (100.0%) |
| Non-CSI in clean | 0 | 0 |
| Gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 |
| Tones / IQ | 62 unanimous / all finite | 62 unanimous / all finite |
| BSSID / channel / MAC | unanimous, expected | unanimous, expected |
| RSSI (file) | −58…−54, mean −57.13 | −57…−51, mean −53.4 |
| Live source state / gate | LIVE_VERIFIED / passed | LIVE_VERIFIED / passed |
| Stale | none (last age 0.50 s) | none (last age 0.01 s) |
File parse: A 5377/0/1-noncsi; B 3125/0/6782-noncsi (all 6782 in warm-up);
0 malformed either file; 1-record live-vs-file delta on B (trailing buffer,
immaterial). Host-ts: no anomaly observed (estimator operated, transport error-free).

## 4. Dual-node sync (1 Hz samples across clean window)
`SYNCED 42 / SYNCING 11 / UNSYNCED 0 (n=53)` = **79.2% SYNCED**.
SYNCING recurred mid/late window (samples 4, 20–22, 35–37, 48, 51–53 incl.
final 3); final estimator state SYNCING (A ready, jitter 0.56 ms; B NOT
ready, jitter ~425 ms, drift/sample ~30.6 ms vs A ~20.1 ms — B's depressed,
irregular rate destabilized its clock mapping).

## 5. Mandatory §H gate results
| Gate | Result |
|---|---|
| 62 tones, finite IQ (both nodes) | PASS |
| valid_pct ≥ 99% (100.0% both) | PASS |
| gaps/dups/ooo (0/0/0 both) | PASS (FLAG threshold gaps>10 untouched) |
| BSSID/channel/MAC identity | PASS |
| Monotonic host ts | PASS (no anomaly) |
| **SYNCED ≥ 95% of window (79.2%)** | **FAIL** |
| 60 ± 2 s (60.26 s) | PASS |
| **≥ 5000 records/node (A 4272, B 2518)** | **FAIL** |
| No 30 s truncation / cap 120 s active | confirmed |

## 6. Anomalies (startup transients vs clean-window)
- Startup transient (allowed, not in clean window): B emitted 6782 non-CSI
  boot/log lines during warm-up — consistent with a board reset when the
  stack opened the port (no operator reset performed) — incl. one
  32-identical-line storm epoch; A had 1 warm-up non-CSI line. Clean window
  on both nodes: pure valid CSI.
- Clean-window anomalies (gates): depressed per-node record rates (A ~71 Hz,
  B ~42 Hz — traffic-dependent, but below the count gate) and recurring
  SYNCING driven by B's clock-mapping jitter. Preserved as evidence; no
  retry per STOP rule.

## 7. Artifacts
- `research-data/rfvision-011-presence/trials/R11P-01E/R11P-01E_node-a_raw.bin`
  SHA-256 `45a4d7a83ec382d418ead58cb900dd6bc2dd02270873a689611fcf7ee7e9561f` (chmod 444)
- `research-data/rfvision-011-presence/trials/R11P-01E/R11P-01E_node-b_raw.bin`
  SHA-256 `dcfe027eee595ebd7270d2f1f74a107c8dcb30693b88464ea1b90d8e39c1131b` (chmod 444)
- `R11P-01E_sidecar.json` (metadata §F), `R11P-01E_capture_stats.json`
  (live stats + sync series), `R11P-01E_file_validation.json` (offline parse)
- Complete intended clean window preserved; quarantined (verdict FAIL).

## 8. Boundary confirmations
No localization/ML/imaging/XAI/classification/testing performed. E2 NOT
started. No commit/push/branch change; protocol/firmware untouched. Working
tree: baseline `d1f12a5`, modified `web/source.py` + `tests/unit/test_live_provider.py`
(pre-authorized Option B only); untracked = this + prior authorized reports;
`research-data/` ignored.

## 9. Verdict
```text
E1_FAIL — E2_BLOCKED — SYNCED 79.2% of clean window (< 95% gate); record count 4272/2518 per node (< 5000 gate)
```
STOPPING. Failed run preserved as quarantined evidence. Awaiting human decision.
