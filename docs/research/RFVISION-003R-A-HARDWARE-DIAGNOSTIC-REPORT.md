# RFVISION-003R-A — Hardware/Serial Diagnostic Report

Operation: RFVISION-003R-A (READ-ONLY). No flash, no erase, no firmware
modification, no router changes, no manual/board reset, no power cycle,
no human experiment, no training. No WRITE operation was performed or
approached. One pre-existing tree modification
(`M docs/research/RFVISION-008-DATA-CONSOLIDATION-REPORT.md`, from a later
operation) was left untouched.

**RFVISION-003R-A STATUS: FAIL** — the unit under test does not conform to
the validated baseline on two independent, each-fatal layers (§11). (The
diagnosis itself completed; FAIL describes baseline conformance.)

## 1. Exact commands and results (in operation order)

### 1.1 Repository/environment sanity [READ-ONLY]

- `git status --short` → only the pre-existing `M` above; `git log
  --oneline -1` → `8d60785`; Python 3.14.4; `/dev/ttyUSB0` present
  (`crw-rw-rw- root dialout`, 188:0).

### 1.2 USB/CP2102 identity [READ-ONLY]

- `lsusb -d 10c4:ea60 -v` → `idVendor 0x10c4 Silicon Labs`,
  `idProduct 0xea60 CP210x UART Bridge`, `iProduct "CP2102 USB to UART
  Bridge Controller"`, `iSerial "0001"`, `bcdDevice 1.00`, 100 mA.
- `lsusb -t` → Bus 003 Port 005 Dev 006, `Driver=cp210x`, 12M
  (full-speed). sysfs (`/sys/bus/usb-serial/devices/ttyUSB0/../../`):
  `manufacturer "Silicon Labs"`, `product` as above, `serial "0001"`,
  `speed 12`.
- Verdict: bridge identity HEALTHY and as expected. USB-serial path
  enumerates correctly; driver bound; full-speed link.

### 1.3 Serial process ownership [READ-ONLY]

- `/proc` fd scan for `/dev/ttyUSB0` (ino 1338): **no holders — port
  free**. No contention, no stale lock, no competing reader/writer.

### 1.4 ESP32 chip identity [READ-ONLY]

- Installed `esptool 5.4.0` via `pip install --user
  --break-system-packages` (user-site only; no OS packages touched).
- `python3 -m esptool --port /dev/ttyUSB0 --baud 115200 chip_id` →
  `Chip type: ESP32-D0WD-V3 (revision v3.1)`, `Features: Wi-Fi, BT, Dual
  Core + LP Core, 240MHz`, `Crystal 40MHz`, download-mode sync OK.
- NOTE: esptool's ROM sync + session end print `Hard resetting via RTS
  pin` (tool-implicit line toggle, inherent to any esptool use). No
  separate manual/EN reset, button press, or power cycle was performed.

### 1.5 MAC [READ-ONLY]

- `chip_id` + `read_mac` (two sessions, identical): MAC
  **`b0:3f:d3:70:20:3c`**.
- **MISMATCH: expected baseline `f4:65:0b:56:0e:18`.** Different OUI,
  different device. The plugged board is NOT the MAC-recorded baseline
  unit (or the baseline MAC was mis-recorded — user to adjudicate).

### 1.6 Flash identity/size [READ-ONLY]

- `flash_id` → `Manufacturer c4, Device 6016, Detected flash size: 4MB`.
  Matches the 4 MB baseline. `read_flash_status` → `0x0000` (no
  write-protect bits set — informational only).

### 1.7 Board identity comparison

| Attribute | Expected | Observed | Match |
|---|---|---|---|
| Silicon | ESP32-D0WD-V3 rev 3.1 | ESP32-D0WD-V3 rev 3.1 | YES |
| Crystal | 40 MHz | 40 MHz | YES |
| Flash | 4 MB | 4 MB (c4/6016) | YES |
| Bridge | CP210x → /dev/ttyUSB0 | CP2102 s/n 0001, cp210x, 12M | YES |
| MAC | f4:65:0b:56:0e:18 | b0:3f:d3:70:20:3c | **NO** |
| Firmware | csi_recv_router (esp-csi 8633d671) | ESP-AT v2.3.0.0 (see §1.8) | **NO** |

### 1.8 Firmware-state evidence without writing [READ-ONLY]

`read_flash` is a device READ (no modification); three bounded reads:

- `read_flash 0x0 0x10000 /tmp/rfv-boot-region.bin` → boot magic `E9 03`
  @0x1000; partition-table magic `AA 50` (= 0x50AA LE) @0x8000; table:
  `phy_init, otadata, nvs, at_customize (0x40/0x00 @0x20000), ota_0
  (@0x100000), ota_1 (@0x280000)` — an **AT-command layout**; NO factory
  app, NO app at 0x10000 (where `csi_recv_router` would live).
- `read_flash 0x100000 0x1000 /tmp/rfv-appdesc.bin` → app magic `E9`,
  version string **`v2.3.0.0_esp32c3-142-g5641e0a-d`, built May 20 2022**
  (ESP-AT release naming; `esp32c3` is AT's era naming quirk, chip is
  ESP32 per §1.4), plus `qa-test-v4.3.3-20220423` factory-test string.
- `read_flash 0x110000 0x10000 /tmp/rfv-appbody.bin` → 1,370 printable
  strings: AT command set (`AT+RST`, …), BLUFI/BLE strings, **zero hits
  for `CSI_DATA`, `csi_recv`, `csi_send`, `esp-csi`/`ESP-CSI`**.
- Verdict: board runs **Espressif AT firmware v2.3.0.0 (2022-05-20)**,
  which cannot emit CSI. Repository firmware source matches nothing on
  this board (as warned: source ≠ installed proof).

### 1.9 USB port/cable diagnostic [READ-ONLY]

- Single cable/port observed (Bus 003 Port 005); physical re-plug or swap
  requires hands on site — NOT performed (no physical access).
- `dmesg` is inaccessible in this environment (empty output) — USB error
  counters unobservable; recorded as a limitation, not as health.
- Descriptor-level link is healthy (§1.2); no evidence implicates the
  cable specifically, and §1.11 shows the failure reproduces independent
  of electrical detail available here.

### 1.10 Router association/path observation [READ-ONLY]

- `ip neigh` → only `192.168.31.1 dev wlp0s20f3 … REACHABLE` (the LAN
  gateway); `ip route` → host on `192.168.31.0/24`.
- ESP MAC `b0:3f:d3:70:20:3c` is NOT in the neighbor table: the board is
  not visible as an IP station from this host (consistent with default
  unprovisioned AT state; no IP claim made either way).
- No router access attempted (forbidden). Association/path: UNOBSERVED.

### 1.11 003 anomalous-stream reproduction [READ-ONLY]

Short binary-safe captures AFTER identity work (allowed), plus the
surviving 003-era 5 s probe:

| Capture | Baud | Bytes/5 s | Rate | NL/CR | Distinct | Head |
|---|---|---|---|---|---|---|
| `/tmp/rfv-repro-115200.bin` | 115200 | 671,744 | 134,349 B/s | 0/0 | 2 (`00`,`80`) | `0080 0080…` repeating |
| `/tmp/rfv-repro-921600.bin` | 921600 | 671,744 | 134,349 B/s | 0/0 | 2 (same) | **byte-identical file** |
| 003 `csi_raw_60s.bin` (head) | 921600 | 57 MB/60 s | 950,880 B/s | 0/0 | 12 | `707c 0070…` |
| 003-era `/tmp/rate_probe.bin` | 921600 | 4.87 MB/5 s | ~973 kB/s | — | 11 | identical to 003 head |

- Reproduced the anomaly CLASS: baud-independent, newline-free,
  fixed-pattern, super-line-rate streams (115200 baud caps at ~11.5 kB/s;
  observed 134 kB/s–951 kB/s). The two repro files are byte-identical
  across an 8× baud change — impossible for genuine UART traffic.
- Pattern family is STATE-dependent (00/80 now, post-esptool-reset;
  12-symbol family in the 003 era) while remaining baud-independent —
  characteristic of a serial-PATH artifact (stuck/break/framing-garbage
  or bridge/host-driver artifact), not firmware output.

## 2. Comparison with RFVISION-003

003 concluded "board is not emitting validated output; root cause
unverified (reset/flash/cable actions out of authority)". 003R-A closes
that gap WITHOUT writing: (a) the board provably runs ESP-AT, so 003's
zero-`CSI_DATA` finding is fully explained — no CSI firmware exists to
emit it; (b) the serial path provably delivers baud-independent garbage
at impossible rates, so even correct firmware could not be received
through this path today. 003's 57 MB capture
(`sha256 c64e5a00…`) is consistent with path garbage, not truncated CSI.

## 3. Likely failure layer (two independent, each-fatal layers)

- **LAYER 1 (certain, fatal): wrong firmware.** ESP-AT v2.3.0.0 aboard;
  `csi_recv_router` absent (no factory partition, no CSI strings in
  68 KB of app image). Fix requires FLASHING — 003R-C, explicit WRITE
  approval needed.
- **LAYER 2 (certain behavior, fatal): serial path delivers non-UART
  garbage.** Baud-independent fixed patterns at 10–80× line cap, zero
  text framing, state-dependent alphabet. Candidate causes (unranked,
  need hands): cable quality/length, port/hub behavior, CP210x driver
  state, TX-line electrical fault (break/stuck), or bridge fault.
- Secondary anomaly: **MAC mismatch** (`b0:3f:d3…` vs recorded
  `f4:65:0b…`) — wrong unit on the bench, or baseline MAC mis-recorded.

## 4. Unresolved uncertainty

- Which physical unit is the "true" baseline board (adjudicate MACs).
- Electrical root of the path garbage (needs hands: cable/port swap,
  preferably short quality cable direct to motherboard port; driver
  rebind; a second known-good bridge/board if available; `dmesg` from a
  privileged shell).
- Whether AT firmware was factory state or a later flash (history
  unknown; irrelevant to the fix).
- Router association unobserved (blocked by no-router-access rule; moot
  until firmware + path are fixed).
- AT NVS may hold stale Wi-Fi credentials — irrelevant post-flash.

## 5. Recommendation for 003R-B (requires USER physical action + approvals)

1. User: confirm which board is the baseline unit (MAC check); move the
   shortlisted board to a short, quality USB data cable on a motherboard
   port (no hub); report `dmesg` USB lines if obtainable.
2. 003R-B (read-only, my side): re-run stream sanity at 115200/921600 —
   PASS criterion is READABLE TEXT (AT `ready`/echoes pre-flash), not CSI.
3. 003R-C (WRITE, needs explicit approval — NOT this operation): flash
   `firmware/esp32/csi_recv_router/` from pinned esp-csi `8633d671` +
   IDF v5.4.4, then verify boot text at 921600, then re-run the 60 s
   golden capture.
4. STOP rule stands: no flash/erase/reset-by-hand until the user approves
   003R-C explicitly.

STORAGE: raw reads retained outside git at `/tmp/rfv-boot-region.bin`,
`/tmp/rfv-appdesc.bin`, `/tmp/rfv-appbody.bin`, `/tmp/rfv-repro-*.bin`
(volatile; the report above is the durable record).
