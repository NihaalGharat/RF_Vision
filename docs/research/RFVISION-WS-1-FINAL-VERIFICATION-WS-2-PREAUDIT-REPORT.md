# RFVISION — WS-1 FINAL VERIFICATION + WS-2 PRE-AUDIT REPORT

- **Date:** 2026-09-26 (UTC)
- **Repo:** `~/Desktop/RF Vision`, branch `main`, HEAD `1711c9e`
- **Activities:** (1) WS-1 final runtime verification (2) WS-2 pre-audit / readiness analysis only
- **WS-2 itself was NOT executed.** No repair, provisioning, reflash, reset, NVS erase, credential change, firmware change, or hardware intervention performed.

---

## WS-1 — FINAL RUNTIME VERIFICATION

**Decision:** `VERIFIED PASS WITH DOCUMENTED LIMITATION`

1. **Decision:** `VERIFIED PASS WITH DOCUMENTED LIMITATION`
2. **Browser/runtime result:** PASS — headless Chrome 153 (real product binary, no installs). All 5 React routes (`/react`, `#/live`, `#/visualize`, `#/research`, `#/hardware`, `#/system`) load with **zero uncaught errors / zero failed module requests** across 9 runs. WebGL initializes (frame rendering proven via GL driver messages); only performance-grade `ReadPixels` warnings, no failures. Software-WebGL deprecation notice is environment-only (headless has no GPU).
3. **2D result:** PASS by pixels — dashed UNKNOWN (uncalibrated) room, grid, ROUTER→ESP link render in OFF, SIM (marker at 0.707), and fresh-load states. Null position → no marker in every OFF capture.
4. **3D result:** PASS by pixels — dashed room box, grid floor, router/ESP32 endpoints, link, HUD chip (`1 LINK · Y-up m · ROOM: UNKNOWN · pos: —`) captured in OFF + fresh-SIM runs; `scene-wrap` present with no "3D unavailable" fallback in DOM; three r160 + OrbitControls served 200, `from 'three'` specifier compatible. (Two virtual-time captures showed a blank canvas — proven capture-timing artifact: same runs showed GL frames rendered and DOM correct; real-time capture renders fully.)
5. **LIVE result:** UNVERIFIED — no live provider streaming in this environment (nothing to observe read-only; starting acquisition is state-changing, not authorized). Path shares the verified envelope + WS fan-out; live `position=null` → hidden proven via FIXTURE null-position frames.
6. **Simulation result:** PASS — full cycle: `simulated→STALE→seq 40/277/571, 64 amps, pos 0.583→0.780, UNKNOWN/SIMULATED→stop→off→DISCONNECTED`. SIMULATED banner ("Never evidence, never LIVE"), STALE banner, SIMULATION pills, `0.707 RF-INFERRED (NOT VALIDATED)` + orange link marker all pixel-captured. SIM position cannot leak to LIVE (backend `source_state`-driven).
7. **Fixture result:** PASS — with explicit path: `OFFLINE_FIXTURE, seq 40, pos None, 54 amps, rssi −48` → parked OFF. Fixture without `path` emits no frames (default path exists but pump binds provider at thread start — see §15). Null-position → marker-hidden path exercised.
8. **Control result:** PASS by code + pixels — PAUSE/RESET VIEW buttons present and rendered; handlers touch only `vizStore` (`paused`/`viewToken`), zero acquisition calls in `visualize.js`. Interactive click-through unverified (no automation driver installed; installing one is environment alteration).
9. **Responsive result:** PASS by pixels — tablet 820px and mobile 390px stack cleanly, no page-level horizontal overflow, 2D/3D usable, controls reachable.
10. **Legacy parity:** PASS (independent agent, line-evidence): identical model, identical aria strings, identical HUD composition vs `tabs/rffield.js`.
11. **Scientific-safety audit:** PASS — zero hits for human/person/pose/XYZ/confidence/triangulation/multilateration/localization/ML/XAI/imaging/Kalman; `body/mesh` only in denial comments; `uncertainty` always null literal. LIVE position null unless backend genuinely reports otherwise (it reports null).
12. **Tests:** `241 passed` (this session, `python3 -m pytest tests/ -q`).
13. **Independent second pass:** PASS — fresh agent re-verified all items from scratch, **no disagreements** with first pass.
14. **Diff review:** CLEAN — 58 status entries before/after, tracked diff is the same 8 pre-existing files, no server processes left running, backend parked OFF/DISCONNECTED.
15. **Remaining limitations:** (a) live-RF spatial pixels unobserved (no provider); (b) orbit/damping/resize/pause click-interaction unobserved (no automation driver); (c) pre-existing backend race noted (not WS-1, not touched): `_pump_loop` (`web/server.py:258-283`) binds `provider.frames()` at thread start, so a set_source+start landing inside the old frame sleep keeps pumping the old provider — worked around with stop/settle/start sequencing, documented for backend owners.

---

## WS-2 PRE-AUDIT — ANALYSIS ONLY

**Readiness decision:** `READY WITH EVIDENCE GAPS`

1. **Readiness decision:** `READY WITH EVIDENCE GAPS`
2. **Confirmed facts:** (a) Identity map `csi/transport/nodes.py`: A=`b0:3f:d3:70:20:3c`@usb-0:5.4, B=`04:b2:47:20:1a:dc`@usb-0:1. (b) **Current topology matches**: usb-0:5.4→ttyUSB1, usb-0:1→ttyUSB0, two CP210x bridges, both ports FREE, no server running. (c) Wire protocol (`csi/transport/provisioning.py`): `RFV_PROV_BEGIN→SSID→PASS→COMMIT`, `RFV_OK <token>`/`RFV_ERR <reason>`/`RFV_NET ssid/bssid/channel/ip`, 15 s read timeout, 3 s idempotent resend, 20 s default node timeout. (d) Serial: 921600 8N1, raw termios, **no modem control → open never resets the board** (`web/network.py:157-219`). (e) Firmware (`app_main.c`): UART0 RX task, NVS `rfvision/{ssid,pass}`, 30 s CSI quiet at BEGIN (120 s at COMMIT), error vocabulary `{bad-ssid-length,bad-pass-length,no-ssid-staged,nvs-store-failed,reconnect-failed}`; boot chain stored→Kconfig-fallback→erase+restart; **UART-unavailable → prov task exits silently (provisioning dead until reflash)**. (f) Last documented state (2026-09-25 FINAL-VERIFICATION): B fully wire-PROVISIONED; A's COMMIT join failed twice genuinely (root-caused: retry handler starved `set_config`; quiesce fix), A joined via stored-boot (.142); dual SYNCED + RF_READY; both NVS-wiped to Kconfig Nihaal, both streaming. (g) Provisioning unit tests exist (`test_provisioning.py`, `test_network_api.py`, `test_network_context.py`, `test_rf_readiness.py`) and pass within the 241.
3. **Hypotheses (ranked, NOT causes):** H1 serial-port/topology mismatch; H2 port ownership/transport failure; H3 wrong node↔device mapping; H4 firmware prov-task/runtime (silent UART exit, NVS state, quiet-window); H5 hardware/power (A has a prior brownout-suspect crash history).
4. **Unknowns:** U1 no current A failure is proven — last seen healthy; WS-2 must first establish whether a failure even exists. U2 whether A's recommended physical reseat/power-cycle (2026-09-23 diagnosis) was ever performed. U3 current firmware runtime state on A (no port opened — correctly). U4 live MAC↔port binding today. U5 hotspot availability for any re-provisioning leg.
5. **Provisioning architecture:** UI → `POST /api/v1/network/provision` (409-guarded while streaming, `server.py:601-608`) → `provision_nodes()` (`web/network.py:221-287`) → per-node open/write `RFV_PROV_BEGIN` → await `RFV_OK BEGIN` → SSID/PASS → `RFV_PROV_COMMIT` → `RFV_OK STORED` → reconnect → `RFV_NET` → `NODES_CONNECTING`, verify via `rf_readiness` (CSI+sync gate, never association alone).
6. **A/B identity mapping:** §2(a)+(b) above; `ttyUSBn` numbering differs across boots by design — by-path + eFuse MAC are the only identity keys.
7. **Failure boundary:** last proven A anomalies are (i) COMMIT-join race — fixed, verified, closed; (ii) E1 runtime crash (25 unframed binary blobs, preserved with SHA) — recovered post-RTS-reset, Class B, reseat recommended. Neither is a currently-proven fault.
8. **Minimum evidence procedure (read-only, in order):** ① list `/dev/serial/by-path` + resolve both nodes (no open); ② `fuser`/ownership on both ttyUSB; ③ confirm no live stream (`stream/status`); ④ passive read with validated read-only source (writes forbidden; pyserial opens forbidden — DTR reset risk); ⑤ compare A/B rate/framing/BSSID/seq continuity; ⑥ only if ①–⑤ implicate provisioning: `RFV_NET_STATUS` query (answers without staging); ⑦ BEGIN-write + raw response capture; ⑧ MAC confirmation — **APPROVAL REQUIRED** (`esptool read_mac` performs RTS hard-reset per the diagnosis report).
9. **Approval-required actions:** ANY port open that asserts modem lines; esptool (resets board); reset/reflash/NVS erase/provision/COMMIT/credential handling; physical reseat/power-cycle; firmware modification; AP/credential changes.
10. **Future WS-2 stop conditions:** identity unresolvable/ambiguous; port ownership unclear; live stream cannot be stopped (busy-guard); UART behavior contradicts firmware contract; evidence points at firmware/NVS/hardware intervention; hotspot unavailable for re-provisioning leg; any step requiring an approval-required action without approval.
11. **Independent second-pass audit:** facts re-checked against source lines (nodes.py L60-74, network.py L157-287, provisioning.py L261-296, app_main.c L72/256-307, server.py L601-608); no repair prescribed as fact; no state-changing op performed (zero port opens, zero flashes, backend SIM/FIXTURE probes volatile-only, parked OFF); hypotheses labeled; procedure minimal and complete.

---

```text
WS-1: VERIFICATION ONLY
WS-2: PRE-AUDIT ONLY — NOT EXECUTED
WS-3: NOT EXECUTED
Product modifications: NONE
Commit: NOT AUTHORIZED
Push: NOT AUTHORIZED
```

**STOP.**
