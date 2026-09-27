# RFVISION-SYS-ROOTCAUSE-001 — VCET LAB PAIRED BASELINE

**Verdict:**

```text
VCET_DIAGNOSTIC_BLOCKED — boards still on HOME AP; reprovisioning forbidden
```

No VCET comparison data was created. No E1/E2/P1. No experimental conclusion.
Two attempts made; both blocked by the same cause (see Attempt 2, which is decisive).

## Attempt 2 (decisive): laptop on "VCET Lab", boards still on HOME AP

- **Laptop (passive):** SSID `VCET Lab`, BSSID `12:c5:f3:7d:04:3d`
  (locally-administered → hotspot-style MAC, not lab infrastructure),
  **2437 MHz / channel 6 / 20 MHz** (differs from historical reference ch5/2432),
  signal −30 dBm, RX 144.4 Mbit/s MCS15 short GI / TX 130 Mbit/s MCS15,
  power save ON, DTIM 2, beacon 100, tx retries 41, tx failed 0,
  rx drop misc 658, beacon loss 0, connected ~26 s at inspection.
  No scan, no disconnect, no reassociation, no power-save change.
- **Software (read-only):** Ubuntu 26.04.1, kernel 7.0.0-31-generic,
  Python 3.14.4, iwlwifi fw `89.123cf747.0 so-a0-hr-b0-89.uc`,
  git `d1f12a5`/`main` (only pre-authorized Option B files modified),
  `REC_MAX_SECONDS=120.0`, `SYNC_MIN_N=64`, `SYNC_MAX_JITTER_NS=2ms`,
  firmware SHA `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd`.
  USB topology unchanged (`usb-0:1`→ttyUSB0, `usb-0:5.4`→ttyUSB1). Nothing changed.
- **Environment probe — single Node A 30 s via unmodified stack**
  (`LIVE-b03fd370203c-1790157360`, `/tmp/vcetdiag/single_esp32-a_1790157360.json`,
  raw `/tmp/vcetdiag/raw_esp32-a_1790157360.bin`, SHA
  `b1328d4d6b6129dd578a8df8166e160828a16e89da86db810e8c11b089e77d8f`):
  fresh `CSI_DATA` records (seq 438269→440969) report
  **BSSID `8c:53:c3:5b:e1:59`, channel 1** — the HOME Xiaomi router.
  Stack: `bssids_seen=[8c:53:c3:5b:e1:59]`, `channels_seen=[1]`,
  `expected_bssid` matched, gate passed, `LIVE_VERIFIED`.
  Probe telemetry (HOME-environment, NOT a VCET result): 2701 valid,
  9267 non-CSI fragment lines, 1 storm epoch, rate 88.7 Hz, 0 gaps,
  RSSI mean −60.4, 62 tones, finite IQ.

## Why blocked (§18 STOP conditions)

- The measurement path (what the ESP32s hear) is unchanged: HOME BSSID/ch1
  in fresh records. The laptop joining a hotspot named "VCET Lab" does not
  constitute the intended `HOME Wi-Fi → VCET Lab Wi-Fi` environmental change.
- Moving the boards to VCET Lab Wi-Fi requires ESP32 Wi-Fi reprovisioning =
  firmware/AP modification, explicitly forbidden (§3). Any reassociation to
  force the change is forbidden (§3, §5, §18).
- Single-B and dual captures were NOT run: they would record HOME-environment
  data mislabeled as VCET. No pyserial fallback was used.

## Attempt 1 (superseded, same cause)

Laptop still on HOME (`Nihaal`/`8c:53:c3:5b:e1:59`/2412 MHz/ch1); single-A
probe (`/tmp/vcetdiag/single_esp32-a_1790157022.json`) likewise showed HOME
BSSID. Quarantined as HOME-environment data.

## Disposition of probe captures

`/tmp/vcetdiag/` holds two 30 s Node A captures, both HOME-AP data.
Quarantined; excluded from any HOME↔VCET comparison; must not be relabeled VCET.

## Unblock conditions (require explicit authorization)

- Physical presence at the VCET Lab site with the boards associated to the
  real VCET Lab infrastructure AP (verify by BSSID in fresh records before
  running the baseline), AND
- an authorized, non-firmware-modifying path for that association
  (or boards already provisioned for it) —
- then re-run this task from §5. Do not relabel the quarantined captures.

## Integrity confirmation

- RFVISION-011 protocol unchanged; firmware unchanged (SHA verified);
  AP configuration unchanged; USB topology unchanged; node positions unchanged;
  acquisition/sync source and thresholds unchanged; git history unchanged;
  no commit; no push; no E1/E2/P1; no human-presence experiment;
  no scientific trial data created.
- Both probes used only the validated stack with `/tmp` scratch.
