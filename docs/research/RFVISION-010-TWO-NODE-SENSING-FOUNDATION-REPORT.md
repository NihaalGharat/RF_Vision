# TWO-NODE SENSING FOUNDATION — IMPLEMENTATION REPORT (code complete, uncommitted)

## Files changed (13 modified, 5 new — additive, no rewrites)
- `csi/transport/nodes.py` (NEW) — NodeIdentity map (by-path + verified MAC), resolve/reverse/all-resolve helpers.
- `csi/parser/csi_parser.py` — `CsiSample.ts_host_ns` (end of dataclass) + `parse_line(..., ts_host_ns)` passthrough.
- `csi/parser/esp_csv_adapter.py` — `parse_esp_csv_line`/`handle_line` passthrough, default `monotonic_ns()`.
- `csi/capture/serial_receiver.py` — ingress stamp + `ts_host_ns` CSV column (new captures only).
- `web/live_serial.py` — `last_line_rx_ns` on SerialLineSource + FakeLineSource.
- `web/source.py` — `_ingest(rx_ns)` threading, dup/ooo counters + stats, `ts_local` preserved.
- `localization/synchronization/sync.py` — `n/jitter/drift_per_sample/stable()` (offset logic untouched).
- `web/dual_node.py` (NEW) — NodeProvider + DualNodeSession, documented SYNCED criterion, honest timing block.
- `web/contracts.py` — CONTRACT_VERSION 1→2 (v1 builders byte-identical), node/nodes payloads.
- `web/server.py` — `DUAL` holder + `set_dual_session` + `GET /api/v1/nodes` (other routes untouched).
- `web/static/js/api.js`, `web/static/js/tabs/overview.js` — nodes endpoint + Nodes card (standby-honest).
- Tests: `test_nodes.py`, `test_dual_foundation.py`, `test_dual_node.py` (NEW); extended `test_localization.py`, `test_web_contracts.py`, `test_web_server.py`.

## Files intentionally untouched
Firmware source, bootloader/partitions, `sdkconfig.defaults`, single-node `LiveProvider` gate/parse semantics, sensing/presence, XAI, models, CI, SECURITY/CITATION, published history, all other UI tabs.

## Tests added: 7 (nodes) + 11 (foundation) + 7 (dual) + 6 (sync) + 1 (contracts) + 2 (server) = 34 new; suite 161 passed.

## Commands executed
`pytest` (161 pass) · `idf.py build` (SUCCESS) · `esptool chip_id` (pre-flash MAC verify) · `idf.py -p /dev/ttyUSB0 flash` (exit 0, hashes verified) · boot-log reads · golden replay · UI smoke (`run_rfvision_ui.sh`) · privacy/secret scans (ZERO).

## Hardware validation results
- ESP32-B flashed with validated `csi_recv_router` (bootloader+app+partitions, hash-verified). App boots, runs, retries WiFi (`example_connect: disconnected 201` — correct with AP absent).
- ESP32-B single-node RF validation: DEFERRED — home AP `Nihaal` not visible at this location (laptop on VCET Lab Ch5). Cannot associate → no CSI flow possible here. NOT a failure; requires home-AP session.
- ESP32-A regression (golden `csi_golden_60s` replay through NEW code): EXACT — 4654 valid / 0 malformed / 1 gap ([121765]) / 62 tones / BSSID+channel stable; dup=0, ooo=0, `ts_host_ns` present.

## Synchronization results
State machine + estimator verified on fakes (UNSYNCED→SYNCING→SYNCED with documented criterion). Measured note: this host's `sleep()` pacing jitters ~3 ms, so the 2 ms default `SYNC_MAX_JITTER_NS` is tight — flagged tunable after real dual measurement. No live dual sync data yet (needs AP).

## UI verification
HTTP 200, all 8 markers, contract v2 live, `/api/v1/nodes` → honest standby (`available:false`, UNSYNCED, reason shown). Nodes card renders STANDBY, never fake data.

## Remaining limitations
B RF validation + live dual smoke + real sync-threshold calibration all require home-AP access. No localization/ML/imaging (out of scope, none added).

## Git: uncommitted (13 M, 5 ??), 441+/15-. No commit made — awaiting operator decision.
## Recommended next phase
Home-AP session: (1) B golden validation + manifest, (2) live dual soak + sync measurement, (3) commit/push, then zone-grid experiment design.
