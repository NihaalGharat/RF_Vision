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
