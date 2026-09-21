# RuView ↔ RF Vision Hardware Compatibility (RFVISION-004)

Upstream snapshot: `main` tarball 2026-09-21 (commit unpinned — pin before
extraction). All RuView facts traced to code paths below. Verdict: RuView
hardware is a DIFFERENT platform; nothing transfers except concepts.

## 1. RUVIEW REQUIREMENTS (upstream, verified)

- SoC: **ESP32-S3** (production) + **ESP32-C6** (research: Wi-Fi 6/HE,
  802.15.4, TWT). NOT ESP32-D0WD (classic). Selected in
  `firmware/esp32-csi-node/main.c:331-337`; badge
  `firmware/esp32-csi-node/README.md:8`.
- Boards: ESP32-S3-DevKitC-1, XIAO ESP32-S3, XIAO ESP32-C6
  (`README.md:137-159,195`); 8 MB flash / 8 MB PSRAM footprints
  (4 MB and 16 MB layouts also defined). CP210x USB-UART host driver.
- Firmware: custom `firmware/esp32-csi-node` app (ESP-IDF v5.4+, native
  `esp_wifi_set_csi_*` driver calls in `csi_collector.c:688-690` — NOT an
  Espressif esp-csi example fork). Multi-tier: raw CSI → edge DSP →
  vitals/fall → WASM3+RVF. Console 115200 baud; flash 460800.
- CSI path: **UDP binary** to aggregator (`stream_sender.c`); serial
  carries ONLY logs + onboarding text
  (`RUVIEW_HELLO_OK_V1 nonce=…`, `serial_onboarding.c:73`).
  There is NO serial CSV CSI output — this alone breaks RF Vision's
  serial-adapter assumption.
- Packet protocol ADR-018 little-endian binary (`csi_collector.h:140-153`,
  `README.md:284-330`): magic `0xC5110001` + node/ant/nsub/freq/seq/RSSI/
  noise/PPDU/flags (bit0=40M, bit2=STBC, bit4=sync, bit5=sanitized) +
  raw I/Q. Vitals `0xC5110002` 32 B @1 Hz; feature/fused/compressed +
  32 B sync beacons `0xC511A110`.
- Channel: single-channel default **ch6**, hop table `{1,6,11,36,40,44}`,
  default single-channel hopping off (`Kconfig`, `csi_collector.c:125-131`,
  dwell 50 ms); HT20, 56 subcarriers S3 / up to 256 HE20 C6
  (`edge_processing.h:55-59`). Self-ping gateway @50 Hz OFDM floor
  (`csi_collector.c:478-538`) — needs NO specific router (any 2.4 GHz AP;
  WPA-PSK compat, open-auth fallback).
- Node count: 1 node = single-link presence/motion ONLY; 3–6 nodes/room
  multistatic mesh for 360° (`README.md:172,196-198`).
- Sync: ESP-NOW beacons (99.43–99.56% RX per `docs/WITNESS-LOG-110.md`),
  mesh-aligned 20 ms bucket gate (`csi_collector.c:304-341`); legacy
  802.15.4 timesync broken on IDF v5.4 (D1, documented).
- Server: Rust `wifi-densepose-sensing-server` (14,018-line `main.rs`,
  76 routes): UDP :5005 ingest → HTTP :8080 + WS :8765. Optional
  MQTT/Matter/HA, OTA+WASM :8032.
- Optional extras only: mmWave UART (auto-detect), AMOLED display, LP PIR
  (C6), camera for TRAINING ground truth
  (`docs/adr/ADR-079-camera-ground-truth-training.md`), iPhone LiDAR
  bridge (ADR-340). No phone on subject.

## 2. RF VISION REQUIREMENTS (validated baseline — UNCHANGED)

- ESP32-D0WD-V3 rev 3.1, 4 MB flash; `firmware/esp32/csi_recv_router/`
  from Espressif esp-csi `8633d671`; ESP-IDF v5.4.4 `296b6eab`.
- Xiaomi Mi Router 4C/R4CM, 2.4 GHz, HT20, LLTF `len=128` → 64 complex
  int8 gain-compensated; ping trigger 10 ms / 1 B (~100 Hz).
- Host path: **USB serial 921600 8N1 ASCII `CSI_DATA,<25 cols>` text**
  (`csi/parser/esp_csv_adapter.py`); Ubuntu `/dev/ttyUSB0`.
- Single link, single node, 1-D positioning scope.

## 3. Compatibility verdict (point-by-point)

| Item | RuView | RF Vision | Compatible? |
|---|---|---|---|
| ESP32 variant | S3 / C6 | D0WD-V3 (classic) | NO — different silicon/driver |
| Firmware | custom node app | `csi_recv_router` (esp-csi) | NO — do NOT replace validated baseline |
| CSI transport | UDP binary ADR-018 | serial ASCII CSV | NO — adapter/parser incompatible |
| CSI format | I/Q + flags + vitals pkts | 25-col `CSI_DATA` text | NO — different parser required |
| Subcarriers | 56 (S3) / ≤256 HE (C6) | 64 complex (LLTF len 128) | CONCEPT only (both int8 I/Q arrays) |
| Baud/serial | 115200 logs-only | 921600 data | NO |
| Router | any 2.4 GHz AP + self-ping | Xiaomi 4C, ch1, ping trigger | CONCEPT (both use AP + self-stimulus) |
| Nodes/sync | 1–6 mesh, ESP-NOW sync | single link, no sync yet | CONCEPT (record sync design for later) |
| Server/ports | Rust :8080/:8765/:5005 | Python `live_app`, no net API | CONCEPT (endpoint layout worth adapting) |
| Schemas | `sensing_update` JSON (tick/nodes/features/classification/signal_field/…) | `CsiSample`/`SensingResult`/`RealtimeEvent` | ADAPTER (field-level mapping feasible) |
| Optional HW | mmWave/display/PIR/camera-gt | none | N/A — do not acquire for UI work |

## 4. What this means

- DO NOT port RuView firmware, do NOT buy S3/C6 boards for this track,
  do NOT change the Xiaomi/serial path to match RuView.
- Reusable across the hardware gap: `sensing_update`-style frame envelope
  (adapt fields), endpoint layout (`/health/*`, `/api/v1/*`, `/ws/sensing`),
  ESP-NOW/mesh sync DESIGN notes (for a future multi-node phase), and the
  single-channel-default + self-ping discipline (already mirrored).
- Multi-node, sync, and UDP ingest are FUTURE RF Vision phases at best —
  none are prerequisites for the RuView-inspired UI, which can render RF
  Vision's own serial-fed data behind an adapter.
