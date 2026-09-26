# RFVISION-012 — UNKNOWN WI-FI AUTO-CONNECTION + ESP32 PROVISIONING
# IMPLEMENTATION REPORT

- **Date:** 2026-09-25 (UTC)
- **Task:** Active implementation task (unknown-Wi-Fi auto-connection + provisioning)
- **Method:** INSPECT → IDENTIFY → DECIDE → IMPLEMENT → TEST → REVERIFY → DIFF → STOP

---

## 1. Prior limitation (verified, not assumed)

- Firmware credentials are **build-time Kconfig only**
  (`firmware/esp32/csi_recv_router/sdkconfig:418-419`, consumed by
  `example_connect()` in `app_main.c:217`); no UART console, no NVS
  credential store, STDIN provisioning compiled out. Every new AP
  required rebuild + reflash (confirmed by
  `RFVISION-SYS-ROOTCAUSE-001-VCET-HOTSPOT-ASSOCIATION-CHECK.md`).
- Host had **zero network discovery** (no nmcli/iw/subnet logic anywhere
  in code) and hard-coded home defaults
  (`8c:53:c3:5b:e1:59`/ch1) in `web/source.py`, `web/dual_node.py`.
- Already network-agnostic (reused, untouched): `expected_bssid` /
  `expected_channel` constructor params, rate-free sync estimator,
  network-blind downstream, transport-agnostic envelope/contracts.

## 2. What was implemented (minimal)

**Host (new, stdlib only):**
- `csi/transport/network_context.py` — read-only discovery (`nmcli` +
  `iw`/`ip` fallback, injectable runner), `NetworkContext` (no
  passwords by construction), 2.4 GHz compatibility gate for
  ESP32-D0WD-V3 (5/6 GHz → `NETWORK_UNSUPPORTED` with reason),
  `network_changed()`, passive `check_client_isolation()` (ESTIMATED).
- `csi/transport/rf_readiness.py` — pure `evaluate_rf_readiness()` over
  the 14-state vocabulary; RF READY only after network + identity +
  CSI/BSSID/channel + acquisition + sync; association alone never
  ready; one-of-two healthy → SINGLE-DEGRADED, never a 2-node claim.
- `csi/transport/provisioning.py` — `Credentials` (redacted repr,
  `clear()`), `ProvisioningSession` over injected serial callables,
  `RFV_*` line protocol, `redact()` on every failure string.
- `web/network.py` — `GET /api/v1/network`, `POST
  /api/v1/network/provision` (409 while live source holds ports;
  passwords never in responses), `GET /api/v1/rf_readiness` (DUAL
  stats → NodeChecks vs live network context + change tracking).

**Firmware (additive patch, `app_main.c` only, +235/-2 lines):**
- NVS `rfvision` namespace (ssid/pass), UART RX task on console UART
  (RX only; TX stays ROM `ets_printf`, CSI output unaffected),
  `RFV_PROV_*` / `RFV_SSID:` / `RFV_PASS:` / `RFV_NET_STATUS` handling,
  `RFV_OK`/`RFV_ERR`/`RFV_NET` replies (never the password).
- Boot: `example_connect()` runs first (validated path identical),
  then NVS reconnect when stored; stale NVS falls back to Kconfig AP
  (never bricks). Reconnect re-runs unchanged `wifi_csi_init()` +
  `wifi_ping_router_start()` (prior ping session retired first —
  the only 2 changed lines in validated functions).
- `sdkconfig.defaults` untouched (still credential-free).

**Server (`web/server.py`, +39 lines):** three routes only; no payload
shape changed; `CONTRACT_VERSION` stays 3.

**Tests (new, 4 files, fakes only — no hardware/ports):**
`test_network_context.py`, `test_rf_readiness.py`,
`test_provisioning.py`, `test_network_api.py` (incl. no-password-in-
`repr`/reason/payload assertions and route-registration check).

## 3. Verification

- New tests: **44 passed**.
- Full suite: **240 passed** (`196` pre-existing + `44` new), zero regressions.
- Live read-only discovery: `NETWORK_DETECTED` — `wlp0s20f3 | Nihaal |
  8c:53:c3:5b:e1:59 | ch 1 | 2412 MHz | 2.4GHz` (matches baseline docs).
- Live route check: `/api/v1/network` → DETECTED; `/api/v1/rf_readiness`
  → `NODE_MISSING ... rf_ready:false` (no session running — honest).
- `git diff`: only `app_main.c` + `server.py` tracked-modified; 8 new
  files untracked; no secrets, no research data, no protocol/threshold/
  sync/acquisition/UI changes.

## 4. NOT YET VERIFIED (honest, not faked)

- **Firmware build** (`idf.py` unavailable in this environment) and
  **hardware E2E** (provision → associate → CSI → sync → RF READY on a
  new SSID) — **no flash performed** per the no-disturbance rule.
- Frontend "CONNECT RF NODES" control intentionally omitted (UI
  workstream boundary; backend API ready for it).

## 5. Operator workflow (after firmware build + flash)

1. `GET /api/v1/network` → confirm `NETWORK_DETECTED` (or honest
   `NETWORK_UNSUPPORTED` on 5 GHz).
2. `POST /api/v1/source {"mode":"off"}` (free the ports).
3. `POST /api/v1/network/provision {"ssid","password"}` → `NODES_CONNECTING`.
4. Restart live/dual with the new `expected_bssid`/`expected_channel`.
5. `GET /api/v1/rf_readiness` → `RF_READY` only when the full chain holds.

---

*End of report. No commit, no push performed (not authorized).*
