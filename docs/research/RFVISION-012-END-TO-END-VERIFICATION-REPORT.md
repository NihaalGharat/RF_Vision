# RFVISION-012 — END-TO-END VERIFICATION REPORT

- **Date:** 2026-09-25 (UTC)
- **Task:** Active verification task (verify, do not redesign/refactor/extend)
- **Method:** Verification first; minimal fix only where clearly necessary
- **Status:** PARTIALLY VERIFIED (see §7)

---

## 1. Pre-check

- Tracked diff: exactly 2 files — `firmware/esp32/csi_recv_router/main/app_main.c`, `web/server.py`. No other tracked file modified.
- New files: exactly 9 intended files (3 host modules, `web/network.py`, 4 unit-test files, `RFVISION-012-UNKNOWN-WIFI-PROVISIONING-REPORT.md`).
- Research protocol untouched: `RFVISION-011-PROTOCOL-v1.4.md` (2026-09-23) and `RFVISION-011-PRESENCE-PILOT-v1.0.md` (2026-09-23) predate this work; `research-data/` and `experiments/` unchanged.
- Secret scan over new/modified Python + firmware sources: clean (no passwords, no SSID assignments, redaction asserted by tests).
- `python3 -m pytest tests/ -q` → **240 passed** (196 pre-existing + 44 new), re-confirmed after the §3 fix.

## 2. Firmware build — AVAILABLE, SUCCESS

- Toolchain found: ESP-IDF v5.4 at `~/esp/esp-idf` + full `~/.espressif` tools (xtensa, cmake, ninja). Initial `idf.py` absence was a PATH matter (`tools/idf.py` + `export.sh`), not a missing toolchain.
- One environment repair (not a project change): pinned `pyparsing>=3.1.0,<3.3` in the pre-existing IDF venv (installed 3.3.2 violated IDF constraints; `export.sh` refused to activate).
- Build exposed one genuine implementation bug: `rfv_emit_net_status()` used `ap.ssid_len`, which does not exist on IDF v5 `wifi_ap_record_t` (fixed 32-byte `ssid`, no length member). Minimal in-scope fix applied (2 lines): bounded `strnlen((const char *)ap.ssid, sizeof(ap.ssid))`.
- Rebuild → **SUCCESS**: `build/csi_recv_router.bin` (756,368 bytes). Build outputs are git-ignored; no artifacts leak into the diff.

## 3. Hardware E2E — live chain verified on known network (no flash)

Flashing was deliberately NOT performed (validated firmware protected; consequential operation requiring approval). All non-invasive checks executed:

| # | Check | Evidence | Result |
|---|-------|----------|--------|
| 1 | Laptop active interface | `wlp0s20f3` via nmcli | PASS |
| 2–6 | SSID / BSSID / channel / frequency / band | `Nihaal / 8c:53:c3:5b:e1:59 / ch 1 / 2412 MHz / 2.4GHz` (nmcli + `/api/v1/network`) | PASS |
| 7 | RF Vision discovery | `GET /api/v1/network` → `NETWORK_DETECTED` + compatibility reason | PASS |
| 8 | Provisioning initiation | Unit-tested (44 tests); wire run skipped — nodes run pre-RFV firmware, no second-AP credentials exist | BLOCKED (§7) |
| 9–10 | Node identity | A=`b0:3f:d3:70:20:3c` @ usb-0:5.4, B=`04:b2:47:20:1a:dc` @ usb-0:1 — match baseline | PASS |
| 11–12 | Association / reachability | Both `LIVE_VERIFIED` over 76 s dual session | PASS |
| 13 | CSI availability | A 7492 valid, B 5811 valid frames | PASS |
| 14 | BSSID/channel validation | Both nodes `8c:53:c3:5b:e1:59` / ch 1, match expected | PASS |
| 15 | Acquisition health | ~99/76 Hz class, both nodes streaming, no transport death | PASS |
| 16 | Sync health | `SYNCED` (7492/5811 obs ≥ 64; jitter 159/253 µs ≤ 2 ms) | PASS |
| 17 | RF readiness | `rf_ready:true, degraded:false`, "full chain verified" | **RF READY — genuine** |

Honesty checks: `/api/v1/rf_readiness` with no session → `NODE_MISSING, rf_ready:false` ("2 of 2 expected nodes absent — never substitute one node for another"). RF READY was reported only because every check actually passed.

## 4. Failure-state classification

No failure states triggered. Chain evaluation confirmed honest negatives where applicable (`NODE_MISSING` without session). No environmental problem was mislabeled as a source failure; the one source failure (compile error) was diagnosed with compiler evidence and fixed minimally.

## 5. Regression check — PASS

The known-network path (identity → CSI → sync → RF READY) works end-to-end on current hardware; 240/240 pytest; acquisition/sync policy, protocols, research data untouched. Ports released, verification server stopped, throwaway probes removed from `/tmp`.

## 6. Re-verification (second pass) — PASS

- Unknown-network discovery works (2.4 GHz gate + `NETWORK_UNSUPPORTED` path unit-verified; live `NETWORK_DETECTED` on Nihaal).
- Provisioning HW run: not possible yet (§7) — not faked.
- Identity correct, CSI actually available, sync actually healthy, RF READY reflects reality, no network change during session (`changed:false`), known-network behavior intact, no credentials exposed, protocols untouched, no unnecessary source changes (one 2-line compile fix only).

## 7. Remaining verification (blocked, honest)

**HARDWARE VERIFIED: NO** (for the new-network provisioning leg only)

**BLOCKER:**
1. User approval to flash the verified `build/csi_recv_router.bin` onto both nodes.
2. Credentials for a genuinely different compatible 2.4 GHz network (none available in this environment; must not be invented).

**REMAINING VERIFICATION:** flash → `POST /api/v1/network/provision` → restart session with new `expected_bssid`/`expected_channel` → `GET /api/v1/rf_readiness` → expect `RF_READY`; then regression re-check on the known network.

---

*End of report. No commit, no push performed.*
