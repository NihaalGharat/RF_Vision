# Hardware Baseline (validated — do not replace without a migration plan)

| Item | Validated value |
|---|---|
| Router | Xiaomi Mi Router 4C / R4CM, 2.4 GHz Wi-Fi |
| ESP32 | ESP32-D0WD-V3, rev 3.1, 4 MB flash, 40 MHz crystal, CP2102 USB-UART |
| Device node | `/dev/ttyUSB0` (Ubuntu/Linux) |
| Firmware | `firmware/esp32/csi_recv_router/` (esp-csi @ `8633d671`) |
| Trigger | ICMP ping to gateway, 10 ms interval, 1-byte payload (~100 Hz CSI) |
| ESP-IDF | v5.4.4 (commit `296b6eab9445fd720e71aecb961e2d3fbca9944`) |
| Expected frames | HT20 LLTF, `len=128` → 64 complex slots, gain-compensated int8 |
| Serial | 921600 baud, 8N1 (`ets_printf`, bypasses `ESP_LOG`) |

Known firmware quirk: the serial header names a column `rx_format` but
prints `sig_mode` twice — cosmetic; the adapter maps columns by position.

Alternative implementations (Human-Sensing Arduino 2-board JSON firmware in
`docs/reference/`; CSI-Tool v4.3 firmware — excluded) are experimental
candidates, never automatic replacements.

## Current-board 60-second CSI golden baseline (RFVISION-003R-C2, PASS)

Physical receiver: ESP32-D0WD-V3 Rev 3.1, MAC `b0:3f:d3:70:20:3c`, 4 MB
flash (NEW board — not the historical `f4:65:0b:56:0e:18` unit).
Firmware esp-csi `8633d671` + ESP-IDF v5.4.4 (`296b6eab`), app
`bc7a5cd5…` (creds-baked C0 build).

| Item | Golden value |
|---|---|
| Capture | `research-data/rfvision-003r-c2/csi_golden_60s_b03fd3203c_921600.bin` (2,197,175 B, 62 s single session, no reset) |
| SHA-256 | `944668b317dd395a1edf157230e95fac1eace6e9c4ae38c77c8cd9b494f13459` |
| Records | 4654 valid / 0 malformed (100 %), seq 121353→126007, 1 missing (0.02 %) |
| Rate | 75.06 Hz, Ch1, single BSSID, RSSI −58.0 ± 0.18, 62 tones, amp mean 19.26 |

No sensing/localization/ML/XAI claims attach to this baseline — it is
transport + signal evidence only. Full statistics:
`docs/research/RFVISION-003R-C2-60S-GOLDEN-TEST-REPORT.md`.
