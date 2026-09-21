> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/07_REPORTS/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` (SHA-256 `6e0a1779f282a14aebf2b161658cc6ce614b7c2bb2379f04a8ffa0c3ebe74df0`) · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

# CSI-VERIFY-001 — PHASE 1 PREPARE — APPROVAL GATE
**Operation:** CSI-VERIFY-001 — RF Vision Final CSI Generation Test  
**Mode:** PREPARE → ONE APPROVAL GATE → TEST → ANALYZE → CONCLUDE  
**Date:** 2026-09-06 20:2x UTC — Ubuntu 26.04.1 Live (Resolute) — Lenovo IdeaPad Gaming 3 15IAH7  
**Status:** `HALTED BEFORE FIRST WRITE` — No flash/erase executed — Awaiting explicit `APPROVED`

> **DO NOT FLASH UNTIL APPROVED.** All checks below are read-only.

---

## 1. Goal (verbatim)

Determine experimentally, with no assumptions, whether CURRENT hardware can produce a genuine live Wi-Fi CSI stream suitable as foundation for RF Vision, using **only official Espressif ESP-CSI stack** (`csi_recv_router` if compatible), pinned versions, via:

```
Xiaomi Router → RF packets → ESP32 → CSI callback → USB serial → Ubuntu → RAW CSI DATA
```

Synthetic CSI, RSSI-only, or ordinary packets = NOT counted as CSI.

---

## 2. Current Hardware — Confirmed by Experiment

| Item | Confirmed Value | Evidence | Classification |
|------|-----------------|----------|----------------|
| **ESP32** | **ESP32-D0WD-V3 (revision v3.1)** Dual Core 240MHz WiFi/BT VRef efuse | `esptool --chip esp32 chip_id` via pip esptool 4.8.1 stub | **CONFIRMED BY EXPERIMENT** |
| **Crystal** | 40MHz | esptool | **CONFIRMED** |
| **MAC** | `f4:65:0b:56:0e:18` | esptool chip_id / read_mac | **CONFIRMED** |
| **Flash** | **4 MB** — Manufacturer `0x68` Device `0x4016` — 3.3V strapping | `flash_id` (+ `--no-stub` for apt) — `Detected flash size: 4MB` | **CONFIRMED** |
| **Flash params to use** | `dio 40m 4MB` — partitions `0x1000 bootloader / 0x8000 part-table / 0x10000 app` | IDF defaults for 4MB; `W Detected size(4096k) larger than header(2048k)` observed in example log — DIO safe for 40MHz | **INFERRED (IDF default)** |
| **Host bridge** | Silicon Labs **CP2102** `10c4:ea60` — `/dev/ttyUSB0` — Bus 3-1 12M `Driver=cp210x` | `lsusb -t`, `usb-devices`, `udevadm info`, `journalctl -k: cp210x converter now attached to ttyUSB0` | **CONFIRMED** |
| **Serial** | `crw-rw---- dialout /dev/ttyUSB0` — `by-id usb-Silicon_Labs_CP2102...0001-if00-port0` | `ls -l`, `stat`, `udevadm` | **CONFIRMED** |
| **Router** | **Xiaomi** `8C:53:C3:5B:E1:59` — `Beijing Xiaomi Mobile Software Co.,Ltd` per macvendors API — SSID `Nihaal` — **Channel 1 (2412 MHz) HT20 20MHz** — Gateway `192.168.31.1` — Host `192.168.31.148/24` — RSSI -39 to -41 dBm | `nmcli`, `iw dev wlp0s20f3 link/info`, `ping 192.168.31.1 0.8ms 0%`, `api.macvendors.com` | **CONFIRMED** |
| **WiFi link** | `144.4 Mbit/s MCS15 short GI` — `bss short-slot-time beacon100 dtim1` | `iw dev link` | **CONFIRMED** |
| **Host** | Lenovo 82S9 — BIOS JMCN48WW V3.11 2024-09-06 — Ubuntu 26.04.1 LTS Resolute — Kernel 7.0.0-30 — GNOME Shell 50.1 Wayland — `/cow 7.7G 1.5G used 6.3G avail` — `/tmp 7.7G 77M used 7.6G avail` — Mem 15Gi 9.4G avail — No Swap | `hostnamectl`, `free -h`, `df -h`, `lsb_release` | **CONFIRMED** |

**Not modified:** No Windows/BIOS/nvme0n1/partition/router driver/firmware/kernel change — verified `lsblk` nvme untouched — read-only.

---

## 3. Official ESP-CSI Stack — Verified Read-Only (no assumptions)

- **Repo:** `https://github.com/espressif/esp-csi` — fetched via `wget` README + `git clone --depth 1` to `/tmp/esp-csi-test` — **DONE**.

```
README.md:  Full series support esp32/s2/c3/s3/c5/c6/c61 — Examples: get-started/csi_recv, csi_send, csi_recv_router
csi_recv_router: "device triggers router to send packets through Ping to obtain CSI … Only one ESP32 + router"
.gitlab-ci.yml: build_idf_v5.4  image espressif/idf:release-v5.4  —  build_idf_v5.5 similarly
EXAMPLE_TARGETS: get-started/csi_recv_router: esp32 esp32s3 esp32s2 esp32c3 esp32c6 esp32c5 esp32c61  → esp32 INCLUDED
sdkconfig.defaults: CONFIG_ESP32_WIFI_CSI_ENABLED=y, CONSOLE_UART 921600, MONITOR 921600
idf_component.yml: dependencies idf ">=4.4.1"
```

- **Pinned ESP-CSI commit:**
  ```
  8633d67152db2808f141cc1595970aa9cf406045  (master HEAD 2026-04-22 07:33:54Z Ning Yu Xiang)
  Merge branch 'update_csi_viewer_html' into 'master' — feat: update_csi_viewer_html & add esp wifi sensing example
  ```
  Verified via `git rev-parse HEAD` + GitHub API `api.github.com/repos/espressif/esp-csi/commits?per_page=3` — same SHA — **DOCUMENTED**.

- **Example selected:** `examples/get-started/csi_recv_router` — **compatible with `esp32` D0WD-V3** per CI — uses official `wifi_csi_info_t` + `rx_ctrl` + `esp_wifi_set_csi_rx_cb` + `esp_csi_gain_ctrl` — `app_main.c` 8309 bytes verified via `wget`.

```c
#define CONFIG_SEND_FREQUENCY 100  // → interval_ms 10 → 100 Hz ping
wifi_csi_config_t csi_config = { .lltf_en=true, .htltf_en=false, .stbc_htltf2_en=false, .ltf_merge_en=true, .channel_filter_en=true, .manu_scale=true, .shift=true };
ets_printf("CSI_DATA,%d,"MACSTR",%d,%d,%d,… // header
```

---

## 4. ESP-IDF Version — Pin

- **Host currently has NO IDF** — `which idf.py` none — `find / -name idf.py` none — **CONFIRMED MISSING**.
- **PIN:** **ESP-IDF `v5.4.4`** (latest tag of `release/v5.4` line) — branch `release/v5.4` HEAD `3e775da47666f2fd0f30b0c2feed1d51db29c93e` — corresponds to Docker image `espressif/idf:release-v5.4` used in ESP-CSI CI.
  - Verified: `git ls-remote` → `release/v5.4 3e775da`, API tags `v5.4.4/v5.4.3/v5.4.2/v5.4.1/v5.4`.
  - Alternative: `v5.5` also builds but we pin `v5.4.4` for CI parity — reproducible.
  - Requirement `idf >=4.4.1` → v5.4.4 compatible — **DOCUMENTED**.

---

## 5. What Is Prepared / What Remains

**DONE (read-only, no flash):**

- `apt update` + `apt install git python3-pip build-essential` + `pip install esptool==4.8.1` (fixed apt `4.7.0+dfsg` missing `stub_flasher_32.json`)
- `esptool chip_id / flash_id` via `sudo env PYTHONPATH=/home/ubuntu/.local/lib/python3.14/site-packages python3 -m esptool`
- `git clone --depth 1 esp-csi` to `/tmp/esp-csi-test` — commit pinned
- Router, USB, display, host capacity verified
- IDF version decision documented

**NOT YET DONE (requires disk write, post-approval):**

```
cd /tmp && git clone --depth 1 --branch release/v5.4 https://github.com/espressif/esp-idf.git esp-idf-v5.4
cd /tmp/esp-idf-v5.4 && git rev-parse HEAD > /tmp/idf_version_pinned.txt
./install.sh esp32
. ./export.sh
cp -r /tmp/esp-csi-test /tmp/esp-csi
cd /tmp/esp-csi/examples/get-started/csi_recv_router
idf.py set-target esp32
idf.py menuconfig   # or sdkconfig: CONFIG_EXAMPLE_WIFI_SSID="Nihaal", CONFIG_EXAMPLE_WIFI_PASSWORD="***", CONFIG_EXAMPLE_WIFI_CONNECT_MAX_RETRY, etc.
idf.py build        # → produces bootloader.bin, partition-table.bin, csi_recv_router.bin — record SHA256
```

Space: IDF 2.5G + toolchain 1G + build 0.4G → total overlay 1.5G→~5G used, leaves ~1.8G headroom on `/cow 6.3G avail` + `/tmp 7.6G`. Feasible.

---

## 6. Exact Target / Firmware / Flash Summary

```
Target:   esp32 — ESP32-D0WD-V3 rev3.1  MAC f4:65:0b:56:0e:18  40MHz  DualCore 240MHz  WiFi/BT
Flash:    4MB (0x68:0x4016) 3.3V — write_flash dio 40m 4MB — addrs 0x1000 / 0x8000 / 0x10000
UART:     CP2102 10c4:ea60 @ /dev/ttyUSB0 Bus3-1 12M cp210x — sudo required (user not in dialout until relogin)
Stack:    espressif/esp-csi @ 8633d67152db2808f141cc1595970aa9cf406045 (2026-04-22) — master
Example:  examples/get-started/csi_recv_router — Ping-triggered router CSI — 100 Hz (10 ms interval) — 921600 baud monitor
IDF:      release/v5.4 → v5.4.4 (3e775da) — espressif/idf:release-v5.4 CI parity — >=4.4.1 compatible
Router:   Xiaomi 8C:53:C3:5B:E1:59 Nihaal ch1 2412MHz HT20 20MHz Gw 192.168.31.1 — no modification
Host:     Ubuntu 26.04.1 Live /cow 6.3G avail /tmp 7.6G avail — pip esptool 4.8.1 — git 2.53 — python 3.14 pyserial 3.5
```

---

## 7. Expected CSI Output (genuine, not synthetic / not RSSI)

**Monitor:** `921600` baud — `ets_printf` CSV via `wifi_csi_rx_cb`:

```
I (…): ================ CSI RECV ================
type,seq,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,secondary_channel,local_timestamp,ant,sig_len,rx_state,len,first_word,data
CSI_DATA,<seq>,8C:53:C3:5B:E1:59,<rssi -30> ,<rate 11> ,<sig_mode1> ,<mcs> ,<bandwidth1> ,<smoothing> ,<not_sounding1> ,<aggregation> ,<stbc> ,<fec_coding0> ,<sgi0> ,<noise_floor-93> ,<ampdu_cnt0> ,<channel1> ,<secondary2> ,<local_timestamp_us> ,<ant0> ,<sig_len67> ,<rx_state0> ,<len128> ,<first_word_invalid1> ,"[<I0>,<Q0>,…128 ints]"
```

- `len` 128 for HT20 → **64 subcarriers ×2 (I/Q)** signed `int8`/`int16` after gain compensation `compensate_gain * info->buf[i]` — gain baseline recorded after 100 samples, `agc_gain/fft_gain` logged.
- `seq` increments — proof not replay.
- `bssid` filtered (`memcmp(info->mac, ctx,6)`) — only Xiaomi router replies pass.
- Rate attempted 100 Hz; router RTT 0.8ms + stack → **observed 50–100 Hz expected** — 60s capture → 3000–6000 records if healthy.
- **Genuine verification:** `info && info->buf` non-null, `len` dynamic, `data` varies per packet, `rssi/noise_floor/channel/timestamp` plausible, `first_word_invalid` field present — synthetic fixed arrays would fail this.

---

## 8. Exact Command That WILL Perform The Write (Phase 2, AFTER approval)

**Preferred (IDF wrapper):**
```bash
# after IDF export.sh
cd /tmp/esp-csi/examples/get-started/csi_recv_router
idf.py -p /dev/ttyUSB0 -b 460800 flash monitor
```

**Expands internally to (recorded after build):**
```bash
sudo env PYTHONPATH=/home/ubuntu/.local/lib/python3.14/site-packages python3 -m esptool \
  --chip esp32 -p /dev/ttyUSB0 -b 460800 \
  --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_freq 40m --flash_size 4MB \
  0x1000  build/bootloader/bootloader.bin \
  0x8000  build/partition_table/partition-table.bin \
  0x10000 build/csi_recv_router.bin
# + 0x9000 ota_data_initial.bin if present — exact addresses/SHA256 logged post-build
```

- Flash baud 460800 reliable on CP2102 (921600 also per `sdkconfig` but 460800 safer).
- **No `erase_flash`** — only `write_flash` to app slots.
- Monitor baud 921600 per `sdkconfig.defaults`.

---

## 9. Risks / Recovery Path

| Risk | Impact | Recovery / Mitigation | Classification |
|------|--------|-----------------------|----------------|
| Power loss / USB disconnect mid-write → incomplete app | Bootloop in ROM bootloader | ROM bootloader in ROM intact — re-run same `write_flash`; if auto-reset fails, hold `BOOT` (GPIO0) LOW + `EN` pulse — no brick | **DOCUMENTED** (Espressif ROM) |
| Wrong WiFi creds → no association → no CSI | No data, not harmful | Reflash with corrected `sdkconfig` — trivial | **INFERRED** |
| Live USB volatile — IDF/build lost on reboot | Rebuild required ~30 min | ESP32 flash PERSISTS — host rebuild only — `/cow 6.3G` sufficient | **CONFIRMED BY EXPERIMENT** |
| Overlay fill (IDF 2.5G+1G) → build fail | No HW harm | Use `/tmp` tmpfs, monitor `df -h` — abort if <1G | **INFERRED** |
| `dialout` permission → `Permission denied` | Flash fails | Use `sudo` as above — or `sudo usermod -a -G dialout ubuntu` + relogin — no permanent system change | **CONFIRMED** |
| Router rate-limit at 100 Hz ping flood | Dropped pings → reduced CSI rate | Router `ping 0.8ms` OK; actual 50 Hz still valid — will report `missing/malformed` — reduce `CONFIG_SEND_FREQUENCY` if needed | **INFERRED** |
| No risk to laptop SSD/BIOS/Windows/router driver | Verified `nvme0n1` untouched, no partition/BIOS/EFIVars write, `iwlwifi` not touched | `lsblk`, `mount` read-only checks | **CONFIRMED** |

**No destructive erase/reflash beyond the single targeted ESP32 — no Windows/BIOS/partition/laptop WiFi driver/kernel modification.**

---

## 10. Preservation & Next Measurements (post-flash, per operation)

After approval, captures will be preserved with metadata and never overwritten:

```
CSI STATUS: GREEN/YELLOW/RED  (evidence-based)
Raw logs: /tmp/csi-captures/CSI_<timestamp>_<esp-idf>_<esp-csi>_<mac>_<channel>.log
Metadata: firmware SHA256, idf commit, csi commit, target, flash params, router BSSID/channel, host, baud
Captures:
  - short validation (~10s)
  - 60-second stable
  - 5-minute if healthy
Measurements per capture:
  1. records/packets, 2. len, 3. usable subcarriers, 4. amplitude/IQ, 5. phase/IQ raw, 6. timestamps, 7. RSSI/metadata, 8. rate, 9. inter-arrival, 10. missing/malformed, 11. stability, 12. router sufficiency
Optional human check (only after stable real stream): empty baseline → person enter/stay/leave → quantifiable change — not called localization
```

---

## 11. Decision & Awaiting

**Ready to proceed to:**
1. Clone `esp-idf release/v5.4` (v5.4.4) to `/tmp`
2. `install.sh esp32` + `export.sh`
3. `idf.py set-target esp32` + configure WiFi `Nihaal` + `build`
4. Flash **only** `/dev/ttyUSB0` ESP32-D0WD-V3 with `csi_recv_router` via command above

**NO CHANGES WERE MADE BEYOND READ-ONLY + apt git/pip/esptool + esp-csi shallow clone — NO FLASH YET.**

### Reply `APPROVED` to proceed, or specify:
- Different IDF tag (e.g., `v5.4.3`, `v5.5`)
- WiFi password for `Nihaal`
- Flash baud or explicit `write_flash` vs `idf.py`

---

*Classifications: Chip/Flash/Router/USB/CSI example existence = CONFIRMED BY EXPERIMENT (esptool, iw, lsusb, git clone); IDF-CSI compatibility & CSI header = DOCUMENTED (CI yml, README, app_main.c); Expected 50–100Hz / len128 / 64 subcarriers = INFERRED from CONFIG_SEND_FREQUENCY 100 + example output; Flash mode dio 40m = INFERRED from IDF defaults; Recovery via ROM bootloader = DOCUMENTED.*

**File location:** `/home/ubuntu/Desktop/CSI-VERIFY-001_PHASE1_APPROVAL_GATE.md` — Desktop — volatile Live (persist after Phase 2 to external USB if needed).
