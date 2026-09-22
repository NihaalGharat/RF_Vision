# RFVISION-003R-B4 — ESP32 Capability Characterization Report

Operation: RFVISION-003R-B4, Phases A–D executed. No flash/erase/write
beyond read-only inspection, no firmware/router changes, no CSI capture,
no experiments, no code modified, no credentials touched. esptool used
for READ commands only (`chip_id`, `read_mac`, `flash_id`,
`read_flash_status`, v5.4.0); its standard RTS post-command reset is the
only control-line activity besides one diagnostic DTR/RTS reset-pulse
per boot-capture (reboot only, non-destructive). Port opened via
`sudo -n -g dialout` group context (operator is in `dialout`; shell
groups stale) — nothing modified.

**Final verdict: CAPABILITY TEST BLOCKED** — UART is healthy, but the
aboard AT application never reaches its command prompt (Phase C FAIL),
and Phases E–F require separate explicit WRITE approval (not given).

## 1. Exact hardware identity (Phase A — all observed, nothing inferred)

- SoC: ESP32-D0WD-V3, chip revision 3 (bootloader log `chip revision: 3`;
  esptool stub confirms ESP32; `chip_id` → no numeric ID on ESP32, MAC
  read instead). CPU 240 MHz class (D0WD-V3; validated-fw config uses
  240 MHz — silicon booted the app image without revision complaint,
  `min. application chip revision: 0`).
- Crystal: NOT measured — unknown, do not infer.
- Flash: manufacturer `c4`, device `6016`, 4 MB, 3.3 V strapping,
  status `0x0000` (esptool `flash_id` + `read_flash_status`).
- MAC: `b0:3f:d3:70:20:3c` (esptool ×2). Different physical board from
  the historical CSI board `f4:65:0b:56:0e:18` — identities never merged.
- USB-UART: CP2102 s/n `0001`, full-speed 12 M, driver cp210x, direct
  motherboard port, clean enumeration, zero USB errors, port free.
- Partition layout (bootloader print, entries 0–2 scrolled past capture
  start; 003R-A previously recorded nvs/phy_init/atcustom/atca on this
  board): observed `3 at_customize / 4 ota_0 (0x100000, 1.5 MB) /
  5 ota_1`, app loads from ota_0, 7 image segments, RNG entropy off.
- RAM as reported by firmware: UNAVAILABLE — the AT console never comes
  up (§3), so no heap figure exists; do not infer (nothing claimed).

## 2. Firmware identity

- Aboard: ESP-AT `v2.3.0.0_esp32c3-142-g5641e0a-d` (May 20 2022 build
  string; the `esp32c3` tag on ESP32 silicon is recorded as-is, origin
  unknown — a franken/foreign build is possible). Boot print:
  `module_name:WROOM-32`, `max tx power=78,ret=0`, `2.4.0`. Then the app
  goes permanently silent (§3). **This firmware cannot emit CSI under any
  configuration — AT Wi-Fi capability would not equal CSI capability
  even if AT worked.**

## 3. UART capability (Phase B) — PASS, with anomaly history flagged

All four health criteria met in this session:

- Readable output: YES — full IDF bootloader log + partition table +
  app boot lines at 115200 (`/tmp/rfv-003rb4-boot12.bin`, 1319 B, 18
  newlines, sha256 `27f6d01d…`).
- Baud-dependent framing: YES — same reset observed at 921600 yields
  3711 B of null-dominated misframing, zero newlines
  (`/tmp/rfv-003rb4-boot921600.bin`, `32b09955…`), differing from the
  115200 capture. Textbook mismatch framing, plausible burst size.
- Plausible throughput: YES — ~1.3 kB boot burst, idle silence otherwise.
- No garbage TODAY: the pre-reset 4 s captures at both bauds returned
  exactly 0 bytes (empty sha256 `e3b0c442…`) — expected idle for a
  long-booted AT board that never speaks unprompted.
- Flagged variance (NOT reproduced, NOT explained): the ~950 kB/s
  12-symbol garbage of 003/003R-B/003R-B3 is absent today. The only
  deliberate change since B3 is reset discipline (esptool/DTR resets
  plus fresh opens). Hypothesis, unproven: the bridge/host path wedges
  into a spewing state only from particular open sequences. Monitoring
  required — any recurrence re-opens the transport question.

## 4. Wi-Fi capability (Phase C) — AT console FAIL; radio NOT TESTED

- AT responsiveness: FAIL (deterministic across resets). Post-boot
  `AT`, `AT+GMR`, `AT+CWMODE?`, `AT+CIPSTA?` → total silence; 12 s
  post-boot window silent; boot text is byte-identical across resets
  (single boot, no crash loop, no panic — the app simply never prints
  `ready` and never answers).
- Wi-Fi mode / scan / router visibility / RSSI / association: NOT
  TESTED — blocked by the dead console; no scan was possible, no
  association attempted, router untouched.
- 2.4 GHz operation: INCONCLUSIVE — WROOM-32 module + `2.4.0` print
  suggest it, but no radio emission was ever observed.

## 5/6. CSI capability + sustained CSI (Phases E–F) — NOT TESTED

- Blocked twice over: (a) no WRITE approval (required, not given);
  (b) moot on current firmware — AT cannot do CSI regardless.
- No `tests/fixtures/live_csi/` created (no genuine CSI exists;
  nothing fabricated).

## 7. RF Vision adapter compatibility (Phase D — paper verification only)

- Validated baseline on file: esp-csi `8633d671`, IDF `v5.4.4`
  (`296b6eab`), example `csi_recv_router`, target esp32.
- `sdkconfig.defaults`: `CSI_ENABLED=y`, console UART0 @ 921600,
  240 MHz, AMPDU TX/RX disabled, 1 kHz FreeRTOS — matches the 003-era
  validated config family.
- `app_main.c`: ping-the-gateway CSI stimulus (`interval 1000 /
  CONFIG_SEND_FREQUENCY`, target = gateway IP) + `CSI_DATA,…` schema
  (legacy 25-col and extended header variants) — the schema the RF
  Vision `EspCsvAdapter` parses.
- Build compatibility: NOT VERIFIED — no `idf.py` toolchain on this
  host. No flash performed.

## 8. Historical comparison

| | Historical `f4:65:0b:56:0e:18` | Current `b0:3f:d3:70:20:3c` |
|---|---|---|
| Result | 003 FAIL: 0 CSI records, ~951 kB/s garbage | UART healthy; AT app dead; CSI untested |
| Firmware aboard | unknown (never identified) | ESP-AT v2.3.0.0 (identified) |
| Baseline status | reference evidence only | NO baseline established |

No shared baseline exists. If current-board CSI ever passes, a NEW
current-board baseline under this MAC must be recorded.

## 9–12. Limitations / proven / disproven / unknown

- Measured limitations: (i) AT console dead — all Wi-Fi characterization
  blocked without flashing; (ii) historical serial garbage unexplained;
  (iii) no IDF toolchain on host — build unverified.
- Proven: silicon identity, 4 MB flash, MAC, partition layout family,
  healthy UART transport, validated-fw paper compatibility.
- Disproven: "aboard firmware is usable for anything" (AT app never
  reaches prompt); "UART path is permanently broken" (it speaks today).
- Still unknown: crystal, RAM figure, every radio property, CSI
  behavior, sustained-capture stats, adapter-vs-live compatibility,
  sensing/localization/XAI (all NOT TESTED, none claimed).

## 13. Recommendation

Two independent blockers, either unblocks progress: (1) user issues
explicit 003R-C/Phase-E WRITE approval → flash validated
`csi_recv_router`, which bypasses the dead AT app entirely (recommended;
the AT firmware is worthless to this project either way); (2) atypical
alternative — diagnose/replace the AT build to restore the console, only
useful for radio recon, never for CSI. Separately: install ESP-IDF
v5.4.4 (`296b6eab`) to verify the build before any flash. Then STOP —
no sensing/localization begins automatically.
