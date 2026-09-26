# RFVISION-012 — NEW-WIFI PHASE REPORT: FLASH + EVIDENCE-BACKED FIXES

- **Date:** 2026-09-25 (UTC)
- **Phase:** Authorized flash of RFVISION-012 firmware + hardware verification
- **Status:** PHASE IN PROGRESS — nodes healthy on fixed firmware; hotspot leg pending (hotspot SSID not broadcasting at last scan)

---

## 1. Pre-flight (all green)

- Firmware SHA (pre-fix binary): app `64192695b75a…`, bootloader `63232ae3…`, partition table `7f00b6c0…`.
- Hardware identity (read-only `esptool read_mac` + by-path): ESP32-A = `/dev/ttyUSB1` @ usb-0:5.4 = `b0:3f:d3:70:20:3c`; ESP32-B = `/dev/ttyUSB0` @ usb-0:1 = `04:b2:47:20:1a:dc`. Both match baseline; correct devices flashed.
- Git diff: only `app_main.c` + `web/server.py`; no research-file changes; pytest 240/240.
- Kconfig fallback SSID confirmed `Nihaal` (safe boot default).
- Credentials staged owner-side in a 0600 file (SSID/password never in chat, logs, source, or Git).

## 2. Flashing

- Node A: first attempt SUCCESS (460800 baud, hash verified).
- Node B: 3 transient serial failures (`chip stopped responding`, `stream stopped`, all on `/dev/ttyUSB0`), then SUCCESS on retry at 460800 (hash verified). Classified ENVIRONMENT (flaky USB-serial), not implementation — `chip_id` worked throughout and MAC confirmed the right device before every attempt.
- Both nodes booted the new firmware and streamed `CSI_DATA` on Nihaal via Kconfig fallback (acquisition path preserved through the patch).

## 3. Provisioning attempt #1 — FAILED (honestly), root-caused, fixed

Result: `PROVISIONING_FAILED` for both nodes, no secrets in reasons.

**Defect 1 — garbled `RFV_NET` (implementation).** Node replied `RFV_NET ssid=%*s bssid=06:3ffcade6:…` — ROM `ets_printf` does not support `%.*s`; the literal was emitted and all following args misaligned. Fix: NUL-terminated local copy + plain `%s`. Verified live: `RFV_NET ssid=Nihaal bssid=8c:53:c3:5b:e1:59 channel=1 ip=192.168.31.163`.

**Defect 2 — replies lost in CSI flood (implementation).** RX path proven working (manual `RFV_NET_STATUS` answered), but multi-step BEGIN→…→STORED exchanges timed out under ~100 Hz CSI TX interleaving (ROM `ets_printf` has no cross-task line atomicity). Fix: CSI output suppressed while a provisioning session is active (set at BEGIN, cleared at ABORT/COMMIT, 30 s auto-expiry refreshed to 120 s at COMMIT so a dropped host can never silence a node).

**Defect 3 — Node B boot-loop on stale NVS creds (implementation, critical).** Attempt #1 had actually gotten far enough on B to store hotspot creds; every subsequent boot tried the (then-down) stored AP, and the fallback path died at `ESP_ERROR_CHECK(rfv_runtime_reconnect_if_stored())` → `ESP_ERR_WIFI_STATE` (race with the example_connect retry handler calling `esp_wifi_connect` concurrently) → `abort()`. Fix: (a) no abort — warn and continue; (b) new `rfv_join_blocking()` absorbing STATE races with disconnect/set/connect retries and returning OK only with a bound IP; (c) stored rounds → Kconfig restore+wait → last-resort poisoned-cred erase + `esp_restart` into the clean Kconfig path. Verified live: B prints `stored network unreachable; falling back to Kconfig AP` / `stored reconnect failed; staying on Kconfig AP`, zero panics, streams CSI on Nihaal.

No host-side, protocol, threshold, sync, acquisition, or UI changes were needed or made.

## 4. Current state (verified)

- Both nodes flashed with fixed binary `5203638a54b0…` (hash-verified writes), healthy: A streams CSI + answers `RFV_NET` correctly; B recovered from boot-loop, streams CSI on Nihaal.
- Diff remains 2 tracked files (`app_main.c`, `web/server.py`) + 9 intended new files; pytest 240/240 (firmware not covered by pytest; verified by build + live).
- Credential file untouched, still 0600, password never displayed or logged.

## 5. Pending (blocked on environment, not implementation)

- The hotspot SSID from the cred file is NOT broadcasting (two scans; only unrelated networks visible). Next steps once it is ON: provision A+B via the implemented path (120 s/node timeout for the weak link) → switch laptop → dual-session CSI/sync/`RF_READY` → change-detection → NVS-restore regression on Nihaal.

---

*End of phase report. No commit, no push performed.*
