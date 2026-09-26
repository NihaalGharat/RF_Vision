# RFVISION WS-2B — RF WEB APP ACTIVATION & DUAL-NODE REACTION VERIFICATION

- **Date:** 2026-09-26 (UTC). Repo `main` @ `1711c9e`. Status 60 entries, tracked diff 8 files `+495/-4` — identical before/after.
- **Activation actor:** real backend `python3 -m web.server --port 8130` + its own HTTP workflow (the exact calls the Hardware/Acquisition tabs make). No manual serial, no esptool, no reset/flash/NVS/physical/source changes. Credentials via Kconfig default + discovery SSID; password never displayed, printed, or recorded.
- **Second pass:** independent subagent re-verified all source claims — AGREES, no disagreement.

## 1. Baseline
- Branch `main`, HEAD `1711c9e`, status 60, diff unchanged; no RFVISION procs/ports; both ttyUSB FREE.
- App loads: `GET /` 200, `GET /react` 200, health `ok/DISCONNECTED`. Hardware tab: Network section, Nodes section, `#rf-connect CONNECT RF NODES` visible in source.
- Network pre: `NETWORK_DETECTED` — SSID Nihaal, BSSID `8c:53:c3:5b:e1:59`, ch 1, 2412 MHz, 2.4 GHz, gw 192.168.31.1. Intended test network (matches Kconfig SSID + host Wi-Fi).
- Nodes pre: dual not started, `[]`. RF readiness pre: `NODE_MISSING`, `rf_ready false`. Stream pre: off/DISCONNECTED.
- Identity map (source): esp32-a `b0:3f:d3:70:20:3c` @ usb-0:5.4→ttyUSB1; esp32-b `04:b2:47:20:1a:dc` @ usb-0:1→ttyUSB0.

## 2. ESP32-A Activation Trace
```text
PRE: absent (no session) / DISCONNECTED / NODE_MISSING
→ POST /api/v1/network/provision {discovered SSID, Kconfig password} (HTTP 200, 10.1 s total)
→ PROVISIONED + ASSOCIATED (BSSID ch1, ip .163)
→ live on /dev/ttyUSB1: STALE → LIVE_UNVERIFIED → LIVE_VERIFIED, session gate passed
→ CSI ACTIVE: 2207 valid / 0 malformed, 65.4 Hz, seq advancing, 0 gaps/dups,
   RSSI -58 stable, ch1 + expected BSSID, 128-len frames
→ stream stop → source off → DISCONNECTED (ports free)
FINAL: ASSOCIATED + CSI ACTIVE verified; SYNC/RF READY unobservable (app-contract, §5)
```

## 3. ESP32-B Activation Trace
```text
PRE: absent (no session) / DISCONNECTED / NODE_MISSING
→ same provision POST → PROVISIONED + ASSOCIATED (BSSID ch1, ip .10)
→ live on /dev/ttyUSB0 (UI default): LIVE_VERIFIED, gate passed
→ CSI ACTIVE: 4733 valid / 0 malformed, 100.8 Hz, seq advancing, 0 gaps/dups,
   RSSI -57 stable, ch1 + expected BSSID
→ stop/off → DISCONNECTED
FINAL: ASSOCIATED + CSI ACTIVE verified; SYNC/RF READY unobservable (app-contract, §5)
```

## 4. First A/B Divergence
No stage-level divergence. Both: discovered → transported → BEGIN/staged → COMMITTED → associated (expected BSSID/ch) → CSI active (gate passed, 0 malformed, seq advancing). First difference is quantitative only, inside CSI acquisition: non-CSI serial-line volume (ttyUSB1/A-path 14612 vs ttyUSB0/B-path 86) and valid rate (65.4 vs 100.8 Hz; rate varies with AP traffic per source docs). Not a failure on either node.

## 5. RF Readiness
```text
A: rf_ready: false (contract) | CSI: ACTIVE verified | SYNC: unobservable | final: ASSOCIATED, idle, port free
B: rf_ready: false (contract) | CSI: ACTIVE verified | SYNC: unobservable | final: ASSOCIATED, idle, port free
```
`rf_ready false` is app-contract behavior, not a node failure: node checks require a DUAL session (`dual_info=None → nodes=[] → NODE_MISSING`), and no UI control / HTTP route / WS command starts one (verified in source; only tests attach). Single-node RF_READY branch unreachable via app surface. `POST /api/v1/network/provision` itself returns `NODES_CONNECTING` with "verify via rf_readiness (CSI + sync gate RF READY, never association alone)".

## 6. Failure Classification
```text
A — Layer: NO CURRENT FAILURE. Evidence: PROVISIONED+associated expected BSSID/ch,
  LIVE_VERIFIED, gate passed, 0 malformed, advancing seq. Historical issue reproduced?: NO.
B — Layer: NO CURRENT FAILURE. Evidence: same classes (4733 valid, 100.8 Hz).
  Historical issue reproduced?: n/a (none). Current issue?: none on either node.
SYNC/RF READY: not a node layer — unreachable through current app surface (contract gap).
```

## 7. Historical vs Current
```text
CURRENT FACTS: both provisioned+associated via app workflow (10.1 s, HTTP 200); both CSI ACTIVE
  with gates passed, 0 malformed, advancing seq, stable RSSI, expected BSSID/ch; rf_ready false
  by contract (no dual-start path); system settled to idle, ports free, repo untouched.
HISTORICAL FACTS: A COMMIT-join race (fixed/verified); A E1 runtime crash w/ unframed binary
  (recovered post-RTS-reset); 2026-09-25 dual SYNCED/RF_READY then NVS wipe.
HYPOTHESES: H1-H3 (topology/ownership/mapping) not implicated — both nodes communicated,
  staged, committed, associated. H4/H5 not implicated — no runtime anomaly observed.
UNKNOWNS: content of non-CSI lines on A-path; dual SYNC behavior (no app path to observe it).
```

## 8. Minimum Next Action
1. **Wire the existing DualNodeSession into the app** (UI control/route) so SYNC → RF READY is reachable via the real product path — needs product decision + authorization; NOT EXECUTED.
2. **Sample A-path non-CSI serial content** via read-only observation to classify the 14612-line chatter — diagnostic only; authorization per standing serial rules; NOT EXECUTED.
3. No node repair justified: no current failure established on either node. Do not reset/reflash/reseat.

## 9. Second Verification
Independent second pass: all source claims CONFIRMED (routes, UI wiring, board_mac default, no dual-start path, readiness contract); bias questions all NO (no PROVISIONED/RF READY confusion, no history-based assumptions, no out-of-workflow actions); port-param live session acceptable. **AGREES — NOT UNRESOLVED.**

## 10. Integrity
```text
Product source modifications: NONE (status 60 = baseline 60; diff byte-identical)
Firmware modifications: NONE | Provisioning code modifications: NONE | UI modifications: NONE
Protocol modifications: NONE | Research modifications: NONE
Manual UART commands: NONE | esptool: NOT USED | Manual reset: NONE | NVS erase: NONE
Firmware flash: NONE | Physical intervention: NONE | AP/router changes: NONE
Credential changes: NONE (re-stored same network creds via app workflow; password never exposed)
Temporary artifacts: REMOVED (/tmp driver + server log deleted; no repo artifacts)
Unexpected processes: NONE (server stopped, port 8130 free, serial ports free)
Commit: NOT AUTHORIZED | Push: NOT AUTHORIZED
```

## 11. Unexpected Issues
- `/api/v1/live board_mac` is a constructor default (`web/source.py:234`), never measured — a first-pass swap suspicion was raised and correctly retracted after source check (second pass confirms). It cannot identify A vs B.
- `duplication.storm: true, storm_epochs: 1` on both nodes with zero identical-consecutive and no impossible throughput — symmetric, likely startup artifact; noted, not classified.
- No `curl` in this environment — app driven via stdlib HTTP (same routes/bodies as the UI).

```text
WS-2B: ACTIVATION VERIFICATION — EXECUTED VIA REAL APP WORKFLOW
WS-3: NOT EXECUTED
Repair/reflash/reset/reseat: NOT EXECUTED, NOT AUTHORIZED without approval
Commit: NOT AUTHORIZED | Push: NOT AUTHORIZED
```

**STOP.**
