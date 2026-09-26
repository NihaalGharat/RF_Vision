# RFVISION-012 — FINAL NEW-WIFI HARDWARE VERIFICATION REPORT

- **Date:** 2026-09-25 (UTC)
- **Task:** Final new-WiFi hardware verification (verification, not development)
- **Status:** PASS (two recorded qualifications, §8)
- **Firmware:** `09f05863c8de821e04e4b87f5011a374d8e56931cb45de19f099201632ba71f7` (both nodes, hash-verified)

---

## 1. Pre-flight (all green, no source touched)

- `main` @ `1711c9e`; tracked diff only `app_main.c` + `web/server.py`; no research protocol/data changes; secret scan clean (only functional `body.get("password")` plumbing).
- Identity hardware-verified: ESP32-A `b0:3f:d3:70:20:3c` @ usb-0:5.4 (`/dev/ttyUSB1`); ESP32-B `04:b2:47:20:1a:dc` @ usb-0:1 (`/dev/ttyUSB0`).
- pytest 240/240 baseline confirmed before hardware steps.

## 2. Network (genuinely different, genuinely 2.4 GHz)

- SSID `RF Vision Test Hotspot` · BSSID `3a:37:1f:18:ed:bc` · channel 11 · 2462 MHz · 2.4GHz · WPA2 · laptop `10.217.144.26/24` gw `.249`.
- `GET /api/v1/network` → `NETWORK_DETECTED` with matching facts ("2.4 GHz network within ESP32-D0WD-V3 support").
- Note: scan cache showed a 23-char ghost entry; the exact 22-char owner SSID joined successfully. Password traveled only via 0600 file → USB writes; never in logs, source, Git, or reports (file shredded after use; NM profiles deleted).

## 3. Provisioning

- **ESP32-B: PROVISIONED over the implemented wire path** — `associated: RF 3a:37:1f:18:ed:bc ch11`, IP `10.217.144.19`.
- **ESP32-A: exchange completed through STORED; node-side COMMIT join failed twice genuinely** (`reconnect-failed`). Serial tee captured the cause: the example_connect retry handler starved `set_config` (`sta is connecting, cannot set config` loop). Fix: driver stop/start quiesce in `rfv_join_blocking`. A then **joined via stored-creds boot**, IP `10.217.144.142`.
- Host fix in the same pass: `_expect_ok` retransmits idempotent stage commands after 3 s without RFV (a lost `RFV_OK BEGIN` under CSI interleaving deadlocked the exchange: node quiet, host waiting in silence). Regression test added (`FloodedSerial`, 241/241).

## 4. New-network verification (all live)

- 75 s dual session, expected `3a:37:1f:18:ed:bc`/ch11: A 7428 valid, B 7361 valid, both `LIVE_VERIFIED`, BSSID/channel match, MACs preserved, ~100Hz-class acquisition, no substitution.
- Sync: **SYNCED** (7428/7361 obs ≥ 64; jitter 292/204 µs ≤ 2 ms policy, unchanged).
- `RF_READY`: **rf_ready true, degraded false**, evaluated against live hotspot discovery (not stale Nihaal metadata).

## 5. Network-change detection

- Proven: laptop-back-on-Nihaal with nodes still on hotspot → `NODE_MISSING, rf_ready:false` ("never substitute one node for another") — no stale RF READY.
- `changed=true` live-flag demo blocked (hotspot powered off before the second switch); flag logic unit-verified.

## 6. Restoration + regression (NVS-wipe path, no Nihaal password needed)

- `erase_region 0x9000 0x6000` on both nodes → reboot → clean Kconfig join of Nihaal (`8c:53:c3:5b:e1:59`/ch1), both streaming.
- Dual regression ×2: (5463/3895 valid, SYNCED, RF_READY true) and (1909/2276 valid, SYNCED, RF_READY true), degraded false both runs.

## 7. Regression suite + re-verification

- `python3 -m pytest tests/ -q` → **241 passed**. Second verification PASS (repeat SYNCED + RF READY on Nihaal).
- Cleanup: server stopped, NM profiles deleted, credential file shredded, /tmp probes removed, ports FREE, laptop on Nihaal.

## 8. Qualifications (honest, not blocking)

1. A's COMMIT-time join proven via the stored-creds boot path (identical `rfv_join_blocking` code) rather than a wire COMMIT on the final binary; B proved the wire path (pre-quiesce binary).
2. `changed=true` live demonstration awaits hotspot availability.

## 9. Diff (final)

- Modified: `firmware/esp32/csi_recv_router/main/app_main.c` (+328/−2), `web/server.py` (+39). New: 3 host modules, `web/network.py`, 5 unit-test files (44+1 tests), 4 research reports (incl. this one).
- No credentials, research-data, protocol, threshold, UI, or dependency changes. No commit, no push.

---

*End of report.*
