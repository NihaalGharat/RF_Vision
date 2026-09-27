# RFVISION-SYS-ROOTCAUSE-001 — VCET HOTSPOT ASSOCIATION CHECK

**Question:** Can the currently deployed ESP32 setup associate with the current
`VCET Lab` mobile hotspot without firmware modification, reflashing, or
persistent configuration changes?

**Answer:**

```text
CASE_C_REQUIRES_REFLASH_OR_PERSISTENT_WRITE
VCET_CREDENTIALS_NOT_FOUND
```

No modification, reset, flash/NVS write, RTS/DTR use, or out-of-stack port
access was performed. No E1/E2/P1. No VCET experimental data.

## A. Current state (validated stack only, identity via stack, no esptool)

| | Node A | Node B |
|---|---|---|
| MAC (stack-reported) | `b0:3f:d3:70:20:3c` | `04:b2:47:20:1a:dc` |
| Port | `/dev/ttyUSB1` (`usb-0:5.4`) | `/dev/ttyUSB0` (`usb-0:1`) |
| Current BSSID | `8c:53:c3:5b:e1:59` (HOME) | `8c:53:c3:5b:e1:59` (HOME) |
| BSSIDs seen | `[HOME]` only | `[HOME]` only |
| Channel | 1 | 1 |
| RSSI last / mean | −61 / −60.4 | −56 / −59.35 |
| CSI state | LIVE_VERIFIED, gate passed | LIVE_VERIFIED, gate passed |

Sources: A from fresh 30 s stack probe `LIVE-b03fd370203c-1790157360`
(quarantined HOME-environment capture, `/tmp/vcetdiag/`); B from an 8 s
stack status observation just now (286 valid / 0 mal / 0 non-CSI / 0 gaps,
no recording written). Mapping matches the existing known mapping; both MACs
independently stack-confirmed.

## B. Existing firmware mechanism (read-only source inspection)

- `firmware/esp32/csi_recv_router/main/app_main.c:206-221` — `app_main()` does
  exactly: `nvs_flash_init()` (required by the Wi-Fi driver; no credential
  storage use), `esp_netif_init()`, event loop, **`example_connect()`**,
  `wifi_csi_init()`, `wifi_ping_router_start()`. No UART console, no command
  interpreter, no provisioning flow, no serial credential command, no NVS
  credential read/write anywhere in `main/`.
- Wi-Fi credentials are **build-time Kconfig** consumed by
  `protocol_examples_common` (`example_connect()`):
  `firmware/esp32/csi_recv_router/sdkconfig:418`
  `CONFIG_EXAMPLE_WIFI_SSID="Nihaal"`, `:419` password entry
  (value present in repo file — PASSWORD REDACTED, never quoted here).
- `sdkconfig:416` — `CONFIG_EXAMPLE_WIFI_SSID_PWD_FROM_STDIN is not set`:
  the only IDF-supported runtime (stdin) credential path is **compiled out**.
- `sdkconfig.defaults` contains no SSID/password overrides — only CSI, UART
  (921600), WDT, CPU, buffer tuning.
- `wifi_csi_rx_cb` (`app_main.c:179`) filters CSI by the *associated* AP's
  BSSID (`esp_wifi_sta_get_ap_info` → `s_ap_info.bssid`): records can only ever
  come from whichever AP the build-time credentials join.

## C. Existing VCET credentials

```text
VCET_CREDENTIALS_NOT_FOUND
```

- No `VCET` string in `sdkconfig`, `sdkconfig.defaults`, or `main/`.
- Deployed configuration contains only the HOME SSID (`Nihaal`,
  PASSWORD REDACTED). No VCET SSID/password, no multi-network table,
  no provisioning store.

## D. Association path classification

```text
CASE_C_REQUIRES_REFLASH_OR_PERSISTENT_WRITE
```

## E. Safety assessment (hypothetical future authorized operation)

Associating the boards with `VCET Lab` would require: setting the SSID/password
via menuconfig/`sdkconfig.defaults`, a full firmware rebuild, and flashing over
USB serial with esptool — i.e. **flash writing, board reset/reboot, persistent
state change, and USB serial intervention**. It cannot be done without firmware
modification + reflash. (Note: the hotspot's locally-administered BSSID is
irrelevant to provisioning — `example_connect()` selects by SSID with
all-channel scan — but the SSID/password themselves are not provisioned.)

## F. Next-step recommendation (NOT performed)

If a future authorization permits it: set the VCET hotspot SSID/password in
`sdkconfig.defaults` (or menuconfig), rebuild `csi_recv_router`, verify the new
binary hash, flash both boards via esptool over their existing by-path ports,
then confirm association by BSSID `12:c5:f3:7d:04:3d` in fresh CSI records via
the validated stack before running any VCET baseline. Until then, the boards
stay on HOME and no VCET-labeled captures may be taken.

## Integrity confirmation

- Firmware unchanged; SHA re-verified
  `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd`.
- No flash writes, no NVS writes, no resets, no RTS/DTR manipulation,
  no USB changes, no AP changes; acquisition/sync source and thresholds
  unchanged; RFVISION-011 unchanged; git history unchanged
  (`d1f12a5`; only pre-authorized Option B tracked mods);
  no commit, no push, no E1/E2/P1, no VCET experimental data, no commit.
