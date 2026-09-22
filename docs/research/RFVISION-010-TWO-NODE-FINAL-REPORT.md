# RF VISION — TWO-NODE SENSING FOUNDATION: FINAL REPORT
**Operation:** RFVISION-010 (implementation) + RFVISION-010-VALIDATION (home-AP hardware validation)
**Date:** 2026-09-22 · **Site:** home lab · **Author:** operator + assistant (implementation), assistant-executed validation
**Decision:** GO — approved for commit (not committed, not pushed)
**Supersedes/merges:** `RFVISION-010-TWO-NODE-SENSING-FOUNDATION-REPORT.md`, `RFVISION-010-HOME-AP-VALIDATION-REPORT.md`

---

## 1. Objective
Extend the validated single-node ESP32 CSI receiver into a controlled two-node
sensing foundation (coarse-localization research prerequisite): stable node
identity, host-side ingress timing, stream-quality accounting, host-side temporal
alignment (NOT hardware clock sync), minimal honest UI telemetry — then prove it
works with real concurrent CSI streams on the home AP.

## 2. Hardware baseline (measured, esptool-verified)
| Node | Board MAC | USB by-path | Device | Firmware |
|------|-----------|-------------|--------|----------|
| esp32-a | `b0:3f:d3:70:20:3c` | `usb-0:1`→ corrected to **`usb-0:5.4`** | `/dev/ttyUSB0` | `csi_recv_router` |
| esp32-b | `04:b2:47:20:1a:dc` | `usb-0:5.4`→ corrected to **`usb-0:1`** | `/dev/ttyUSB1` | `csi_recv_router` |

Both boards: ESP32-D0WD-V3 rev 3.1, 4 MB flash, CP2102 s/n 0001 (identical silicon).
Firmware binary sha256 `0a49073799e9fd52788437772008706633c90e40886756762ad3df84b5ec49dd`
(740144 B; source unmodified; rebuild reproduces the hash).
Home AP measured live: SSID `Nihaal`, BSSID `8c:53:c3:5b:e1:59`, channel 1 (2412 MHz),
signal 84. Both nodes associated to the same AP/BSSID/channel.

## 3. Implementation delivered (13 modified + 5 new files, +441/−15, additive only)
- `csi/transport/nodes.py` (NEW) — `NodeIdentity` table (by-path + verified MAC), strict/by-path resolution with MAC-verified fallback.
- `csi/parser/csi_parser.py`, `csi/parser/esp_csv_adapter.py` — `ts_host_ns` host-ingress stamp threaded through (dataclass tail field + passthrough; parse semantics unchanged).
- `csi/capture/serial_receiver.py` — ingress stamp + `ts_host_ns` CSV column for new captures.
- `web/live_serial.py`, `web/source.py` — `last_line_rx_ns`, threaded `_ingest(rx_ns)`, duplicate/out-of-order counters; single-node gate/parse semantics untouched.
- `localization/synchronization/sync.py` — `ClockOffsetEstimator` gains `n/jitter/drift_per_sample/stable()`; offset math untouched.
- `web/dual_node.py` (NEW) — `NodeProvider` + `DualNodeSession` (per-node pump threads, deterministic fan-in queue, documented SYNCED criterion, honest `esp_to_host_latency_us=None`).
- `web/contracts.py` (v1→v2, v1 builders byte-identical), `web/server.py` (`GET /api/v1/nodes` + session holder, other routes untouched), `web/static/js/api.js`, `web/static/js/tabs/overview.js` (Nodes card, standby-honest).
- Tests: 3 new modules (`test_nodes`, `test_dual_foundation`, `test_dual_node`) + extensions; **34 new tests**.
- Untouched: firmware source, bootloader/partitions, `sdkconfig.defaults`, sensing/presence, XAI, models, CI, SECURITY/CITATION, published history, all other UI tabs. No localization/ML/imaging added.

## 4. Validation: ESP32-B single-node gate — PASS
62.77 s golden (`research-data/rfvision-010b/`, SHA `4632c4be…`):
6280 valid / 1 malformed / 99.984% @ 100.05 Hz · 62 tones · 0 seq gaps (30033–36312 contiguous) ·
dup/ooo 0 · RSSI −52…−47 · BSSID/channel stable. 30 s repro confirmed (3003 @ 100.1 Hz, 0 gaps).
Observation: 1–3% run-varying print-fragment lines rejected by the strict parser; all RF frames
accounted; likely host USB-serial drain timing.

## 5. Validation: concurrent dual-node soak — PASS
120 s through the real `DualNodeSession` code path:
A 11459 valid @ 95.5 Hz (0 malf, 1 five-frame gap, dup/ooo 0, LIVE_VERIFIED);
B 12004 valid @ 100.0 Hz (2 malf, 1 five-frame gap, dup/ooo 0, LIVE_VERIFIED).
Independent lean concurrent raw dumps (`research-data/rfvision-010dual/`): A 5143/0, B 6055/0,
zero gaps/dup/ooo. Soak loss ≈0.04% attributed to host processing/drain timing — no acquisition failure.

## 6. Validation: synchronization — PASS, threshold KEPT
SYNCED at all 24 samples (5 s cadence); zero transitions; zero desync periods.
Jitter A 105k–888k ns (mean 233k), B 197k–442k ns (mean 323k) — sub-ms throughout, max 0.89 ms
vs the 2 ms default: suitable with margin. The synthetic 3 ms sleep-jitter concern did NOT
reproduce on real data. No threshold change. Host-side mapping only; ESP clocks never claimed synced.

## 7. Validation: live UI — PASS
`GET /api/v1/nodes` against the live dual session: available=true, SYNCED, both nodes with real
rate/valid%/RSSI/dup/ooo/gaps/jitter/offset/channel/BSSID/tones; zero empty fields; zero simulated
values. Overview tab polls the endpoint with honest standby fallback. Standalone smoke: HTTP 200,
all 8 markers, standby state honest (UNSYNCED + reason).

## 8. Regression — all PASS
`pytest` 161 passed · `idf.py build` SUCCESS · ESP32-A golden replay EXACT
(4654/0/1-gap/[121765]/62/0/0) · privacy scan 0 hits · secret scan 0 hits.

## 9. Evidence index (raws Git-ignored, SHA-256 manifested)
- `research-data/rfvision-010b/` — golden bin + `.sha256`, `capture_metadata.json`, `validation.json`, `manifest.json`
- `research-data/rfvision-010dual/` — `dual_60s_{a,b}.bin` + `.sha256`, `validation.json`, `dual_soak_120s_stats.json` (24-sample series + final stats), `manifest.json`
- Prior records: `/tmp/rfvision-022/` … `/tmp/rfvision-026/` (publication), `/tmp/rfvision-two-node/`, `/tmp/rfvision-dualsync/`, `/tmp/rfvision-dual-impl/`

## 10. Problems & limitations
1. Port↔board mapping swapped vs lab config — corrected with operator approval (by-path swap + pinning tests; suite re-greened).
2. Run-varying 0–3% print fragmentation on B; zero sequence loss; cause undetermined (likely host drain timing).
3. One 5-frame burst gap per node in the 120 s soak (0.04%); lean readers lossless.
4. No localization/ML/imaging (out of scope, none added or claimed).

## 11. Decision — GO
A healthy · B reproduces the single-node baseline · concurrent streams sustained 120 s ·
no unexplained acquisition failures · sync measurable and honest · UI real-data verified ·
regression/privacy/secret green. **The implementation is approved for commit.**
Commit/push deliberately NOT performed (awaiting operator action).

## 12. Recommended next steps
1. Commit + push the validated tree. 2. Zone-grid experiment design (static anchor geometry,
   controlled human-presence protocol, per-zone capture manifests). 3. Long-duration soak with
   rx-timestamped logging to localize the burst-gap/fragmentation source. 4. Only then consider
   presence-feature research — still no localization/ML claims until measured.
