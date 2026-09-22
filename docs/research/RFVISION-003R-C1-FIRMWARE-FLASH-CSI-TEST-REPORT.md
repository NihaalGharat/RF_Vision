# RFVISION-003R-C1 — Firmware Flash + 10-Second CSI Test Report

Operation: RFVISION-003R-C1, executed under explicit WRITE authorization.
Board: ESP32-D0WD-V3 Rev 3.1, MAC `b0:3f:d3:70:20:3c`, 4 MB, CP2102
`/dev/ttyUSB0`. This is the NEW board — never labelled as historical
`f4:65:0b:56:0e:18`.

**Final status: PASS.**

"003R-C1 PASS — CURRENT BOARD CSI VERIFIED; 60-SECOND GOLDEN TEST
AWAITING SEPARATE APPROVAL"

## 1. Pre-flash identity (all verified, STOP-criteria armed)

- `/dev/ttyUSB0` present, CP2102 s/n 0001, holders: none.
- `read_mac` → `b0:3f:d3:70:20:3c` ✓; `flash_id` → c4/6016, 4 MB ✓.
- C0 artifacts present with EXACT C0 SHAs (app `c61e978e…`,
  bootloader `63232ae3…`, partition table `7f00b6c0…`); offsets
  0x1000/0x8000/0x10000 confirmed via `flasher_args.json`. No mismatch —
  flashed.

## 2. Credential handling (no exposure)

- Real router SSID/password supplied by the user went ONLY into the
  local gitignored `sdkconfig` (`CONFIG_EXAMPLE_WIFI_SSID/PASSWORD`;
  the approved Kconfig mechanism — `example_connect()` bakes them at
  compile time, verified in IDF source). Neither value appears in any
  command output, log, report, or the repo. `sdkconfig` remains
  gitignored (`.gitignore:27`), never committed.
- Consequence, recorded honestly: a creds-ONLY rebuild was unavoidable
  (Kconfig is compile-time). Source files untouched — `git status`
  showed zero tracked-file changes. Bootloader and partition-table
  binaries are BIT-IDENTICAL to C0 (`63232ae3…`, `7f00b6c0…`); new app
  SHA `bc7a5cd586c6e9e136607a042760aa2d2b939fa671a38ff64aa6eb5b4927e321`
  (delta = credentials only).

## 3. Flash (authorized write; no erase_flash)

- Tool: esptool.py v4.12.0 (IDF v5.4.4 env). Command (from
  `firmware/esp32/csi_recv_router/`, IDF exported):
  `python -m esptool --chip esp32 -p /dev/ttyUSB0 -b 460800 --before
  default_reset --after hard_reset write_flash --flash_mode dio
  --flash_size 2MB --flash_freq 40m 0x1000
  build/bootloader/bootloader.bin 0x8000
  build/partition_table/partition-table.bin 0x10000
  build/csi_recv_router.bin`
- Window: 2026-09-21T20:38:43Z → 20:39:00Z. Result: SUCCESS — bootloader
  + partition table + 740,144 B app (496,845 compressed) @0x10000 in
  12.4 s (479.3 kbit/s), hash of data verified, hard reset after.
- Incident: first attempt failed `PermissionError` (replug had reset the
  node to 660; shell groups stale). Retried under `-g dialout` group
  context — no system modification, operator is in `dialout`. No
  erase, no repartition, no router/BIOS/NVMe interaction.

## 4. Post-flash identity + boot verification @921600

- `read_mac` after flash → `b0:3f:d3:70:20:3c` (same chip) ✓.
- 15 s boot capture (`/tmp/rfv-c1-boot.bin`, 722,669 B): one ROM-boot
  misframed line at 921600 (expected — ROM speaks 115200, benign),
  then immediate `CSI_DATA` streaming. Readable records, no garbage —
  the B-series serial anomaly is absent on the flashed firmware.

## 5. 10-second CSI test (`/tmp/rfv-c1-10s.bin`)

- 483,356 B @ 48.3 kB/s at 921600 (line cap 115.2 — plausible ✓).
  SHA-256 `60bf5edeb54d3c0c3415e781465ade6185aa7d2871e96b35e52267c8dc490e0c`.
  1013 `CSI_DATA` occurrences / 1012 newlines (one mid-line tail cut —
  correct).
- Validation via RF Vision `EspCsvAdapter` (`parse_esp_csv_line`,
  strict, 25-col): **1012 parsed, 1 rejected** (the truncated tail line
  — strictness working as designed, parser untouched).
- Sequence 13990→15001, ZERO gaps, 101.2 records/s (≈100 Hz ping
  stimulus; esp_timer median dt 9.5 ms) ✓.
- Channel 1 / secondary 0; single BSSID (associated AP); RSSI
  −56…−52 (mean −54.2); noise floor −97 ✓.
- CSI length 128 raw → 62 complex tones after documented first-word
  trim; amplitude 0–48.27, mean ≈20, varying packet-to-packet
  (mean |Δ| 16.5); ZERO all-zero packets ✓.
- No impossible throughput; every §6 criterion met. Historical packet
  counts NOT required and NOT compared numerically — new baseline.

## 6. Adapter result + fixture (§8)

- `EspCsvAdapter` accepts all 1012 genuine records — no relaxation.
- Created `tests/fixtures/live_csi/` from the first 50 genuine records
  (seq 13990–14039, byte-exact wire lines) + `manifest.json` (board
  MAC, fw `8633d671`, IDF `296b6eab`, raw SHA, fixture SHA
  `4616001a…`, adapter + schema versions). Ambient room, no human
  subject — labelled board evidence, never sensing evidence.

## 7. Failures / warnings

1. Flash attempt #1 permission-denied (stale groups) — resolved, no
   consequence.
2. Creds-ONLY rebuild required (Kconfig compile-time) — new app SHA
   recorded; C0 source-byte-equivalence preserved.
3. `ComplexWarning` appeared ONLY in the ad-hoc validation one-liner
   (complex diff cast) — not in adapter, parser, or pipeline code.
4. Router BSSID is recorded as associated-AP metadata (not a
   credential); password never printed, committed, or stored in git.

## 8. Current-board baseline status

**NEW CURRENT-BOARD CSI BASELINE established** under MAC
`b0:3f:d3:70:20:3c`: 101 Hz, Ch1, RSSI ≈ −54, 62-tone CSI, amp mean
≈20, zero-gap sequencing. Historical board (`f4:65…`, 0 records) kept
as reference only — identities never merged. 60-second golden capture
is a separate operation; no sensing/localization/training/UI work
started.
