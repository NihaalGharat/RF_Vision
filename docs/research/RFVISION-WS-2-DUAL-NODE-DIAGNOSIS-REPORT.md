# RFVISION WS-2 — CONTROLLED READ-ONLY DUAL-NODE DIAGNOSIS REPORT

- **Date:** 2026-09-26 (UTC)
- **Repo:** `~/Desktop/RF Vision`, branch `main`, HEAD `1711c9e`
- **Mode:** READ-ONLY. No port opened, no bytes sent, no esptool, no server started, no reset/reflash/provision/reseat/power-cycle, no file modified.
- **Second pass:** independent subagent re-verified all observations from scratch — AGREES, no disagreement.

## 1. Overall Decision

```text
BOTH NODES CURRENTLY HEALTHY / NO CURRENT FAULT OBSERVED
```

Scoped: USB/transport/ownership layers verified healthy on both nodes; no anomaly signal anywhere observable. ESP32 runtime/firmware/RF layers explicitly UNKNOWN (observing them requires approval-gated actions). No failure layer claimed for either node.

## 2. ESP32-A Diagnosis

```text
Identity: esp32-a, MAC b0:3f:d3:70:20:3c (recorded, live binding unverified — esptool prohibited).
  by-path usb-0:5.4 -> /dev/ttyUSB1, unambiguous single match. RESOLVED by topology.
Current state: USB present (sysfs 3-5.4: CP2102 10c4:ea60, s/n 0001, via hub 1a40:0101,
  cp210x driver bound). Port FREE (fuser/lsof//proc-fd all clean). Backend idle, no session.
  No CSI/framing/rate observation (approval-gated — NOT attempted).
Current fault: NO CURRENT FAULT OBSERVED (observable layers).
Failure layer: none established (no anomaly -> no layer claimed).
Evidence: by-path symlink + sysfs descriptor + driver bind + triple-checked free ownership +
  stable topology across all checks this session.
Remaining unknowns: ESP32 runtime/firmware/RF state; live MAC binding; whether the
  recommended physical reseat/power-cycle (2026-09-23 diagnosis) was ever performed.
```

## 3. ESP32-B Diagnosis

```text
Identity: esp32-b, MAC 04:b2:47:20:1a:dc (recorded, live binding unverified — esptool prohibited).
  by-path usb-0:1 -> /dev/ttyUSB0, unambiguous single match. RESOLVED by topology.
Current state: USB present (sysfs 3-1: CP2102 10c4:ea60, s/n 0001, direct attach,
  cp210x driver bound). Port FREE (triple-checked). Backend idle, no session.
  Same diagnostic scrutiny as A; no CSI/framing/rate observation (approval-gated).
Current fault: NO CURRENT FAULT OBSERVED (observable layers).
Failure layer: none established.
Evidence: same classes as A (see comparison table).
Remaining unknowns: ESP32 runtime/firmware/RF state; live MAC binding.
```

## 4. A/B Comparison

| Evidence | ESP32-A | ESP32-B | Interpretation |
|---|---|---|---|
| USB presence | present (3-5.4) | present (3-1) | both enumerate |
| by-path | usb-0:5.4 → ttyUSB1 | usb-0:1 → ttyUSB0 | matches recorded map, unambiguous |
| identity | resolved by topology; MAC unverified | resolved by topology; MAC unverified | symmetric |
| ownership | FREE (3 methods) | FREE (3 methods) | no contention either node |
| bridge | CP2102 10c4:ea60 s/n 0001, via hub | CP2102 10c4:ea60 s/n 0001, direct | serials useless (both 0001); hub attach is topological, not behavioral |
| passive output / framing / CSI rate / seq / BSSID / ch / RSSI | NOT OBSERVED | NOT OBSERVED | symmetric gap, approval-gated |
| runtime errors | none observable | none observable | dmesg/usbserial unavailable (host permission, not node fault) |
| current health | no fault observed (L1–L2) | no fault observed (L1–L2) | symmetric |

No material behavioral difference. B was NOT assumed healthy (prior success labeled historical); A was NOT assumed faulty (prior failures labeled historical, fixed/recovered).

## 5. Historical vs Current

```text
CURRENT FACTS: both by-paths present and stable; both CP2102 bridges bound; both ports FREE;
  no backend process, no listening RFVISION port, no acquisition session; wlp0s20f3 UP /
  enp47s0 NO-CARRIER; zero serial handles open; zero state-changing ops performed.
HISTORICAL FACTS: A COMMIT-join race (root-caused, quiesce-fixed, verified closed); A E1 runtime
  crash w/ unframed binary blobs (recovered post-RTS-reset, Class B, reseat recommended);
  2026-09-25 dual SYNCED/RF_READY then NVS-wiped to Kconfig Nihaal, both streaming.
HYPOTHESES (ranked, unproven): H1 port/topology mismatch; H2 ownership/transport; H3 wrong mapping;
  H4 firmware prov-task/runtime (incl. silent UART-unavailable exit); H5 hardware/power.
UNKNOWNS: ESP32 runtime state on both nodes; live MAC bindings; reseat performed?; hotspot availability.
```

Critical nuance: USB enumeration proves the CP2102 bridge only — a crashed ESP32 still enumerates (E1 precedent). Hence runtime UNKNOWN, not healthy-by-assumption.

## 6. Minimum Next Action

```text
ESP32-A:
Next action: approval-gated passive serial observation (open via validated CLOCAL raw path,
  read-only, no TX) to confirm framing/CSI rate/continuity; escalate to RFV_NET_STATUS only if
  passive read implicates provisioning.
Why necessary: only remaining distinguishing observation for runtime layers H4/H5.
Approval required: YES — any port open / any UART transmission.

ESP32-B:
Next action: same as A (symmetric scrutiny).
Why necessary: same.
Approval required: YES.

No corrective action currently justified (no current anomaly established).
```

Boundaries hit, NOT crossed: `RFV_NET_STATUS` (however non-mutating) requires sending bytes → `APPROVAL REQUIRED — NOT EXECUTED`. `esptool read_mac` asserts RTS/reset → `APPROVAL REQUIRED — NOT EXECUTED`. No physical intervention performed/required by evidence.

## 7. Second Verification

Independent second-pass subagent re-ran every observation (git/by-path/sysfs/ownership/processes/permissions/sources) with its own commands: all VERIFIED. Bias questions answered NO/NO/NO (no B-healthy assumption, no A-faulty assumption, no state change). Verdict: AGREES — no disagreement, NOT UNRESOLVED.

## 8. Integrity

```text
Product modifications: NONE (status 59 = baseline 59; tracked diff identical 8 files +495/-4)
Hardware mutation: NONE
Firmware mutation: NONE
Credential mutation: NONE
NVS mutation: NONE
Provisioning: NOT EXECUTED
Serial handles opened: ZERO (verified via /proc fd scan)
Backend left running: NO (verified)
Temp artifacts in repo: NONE (.pytest_cache/__pycache__ gitignored, pre-existing)
Commit: NOT AUTHORIZED
Push: NOT AUTHORIZED
```

## 9. Unexpected Issues

- `lsusb` returns empty with rc=0; `/proc/tty/driver` and `dmesg` permission-denied in this environment — host tool/permission gaps, not node faults. Identity established via sysfs + by-path instead.
- `git status` reads 59 vs 58 at pre-audit baseline; +1 entry unattributed (this execution performed zero repo writes; tracked diff byte-identical). Non-blocking; noted for the record.

```text
WS-2: DIAGNOSIS ONLY — EXECUTED READ-ONLY
WS-3: NOT EXECUTED
Repair/provision/reflash/reset: NOT EXECUTED, NOT AUTHORIZED without approval
Commit: NOT AUTHORIZED
Push: NOT AUTHORIZED
```

**STOP.**
