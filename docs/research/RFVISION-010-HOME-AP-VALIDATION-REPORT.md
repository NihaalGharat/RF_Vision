# RFVISION-010 HOME-AP HARDWARE VALIDATION REPORT (2026-09-22)

## 1. ESP32-A identity/result
- MAC `b0:3f:d3:70:20:3c` (esptool-verified), by-path `usb-0:5.4` → `/dev/ttyUSB0`.
- Running `csi_recv_router`, associated to home AP, streaming. HEALTHY.

## 2. ESP32-B identity/result
- MAC `04:b2:47:20:1a:dc` (esptool-verified), by-path `usb-0:1` → `/dev/ttyUSB1`.
- Running `csi_recv_router`, associated to home AP, streaming. HEALTHY.
- Mapping note: boards were on swapped ports vs the lab-written config; operator
  approved updating the canonical by-paths to measured reality (see §11).

## 3. ESP32-B single-node statistics (62.77 s golden, `research-data/rfvision-010b/`)
- 6280 valid / 1 malformed / 192 non-CSI frags / 99.984% @ 100.05 Hz.
- 62 tones, 0 seq gaps (seq 30033–36312 contiguous), 0 dup, 0 ooo.
- RSSI −52…−47 (mean −49.7); BSSID `8c:53:c3:5b:e1:59` + channel 1 stable.
- 30 s repro: 3003 valid @ 100.1 Hz, 0 malf, 29 frags, 0 gaps — reproducible.
- GATE: PASS. Fragment observation: 1–3% run-varying print-fragment lines rejected
  by the strict parser; all RF frames accounted; likely host USB-serial drain timing.

## 4. Dual-node concurrent statistics (120 s `DualNodeSession` soak, real code path)
- A: 11459 valid @ 95.5 Hz, 0 malf, 36 non-CSI, 1 gap ([43594–43598]), dup/ooo 0, LIVE_VERIFIED.
- B: 12004 valid @ 100.0 Hz, 2 malf, 3 non-CSI, 1 gap ([50895–50899]), dup/ooo 0, LIVE_VERIFIED.
- Concurrent lean raw dumps (60 s, `research-data/rfvision-010dual/`): A 5143/0,
  B 6055/0, zero gaps/dup/ooo — zero-loss baseline exists; soak loss (~0.04% +
  rare frags) attributed to host processing/drain timing under full-pipeline load.

## 5. Synchronization measurements (host-side mapping only; ESP clocks NOT synced)
- State SYNCED at all 24 samples (5 s cadence); zero transitions; zero desync periods.
- Jitter A: 105k–888k ns (mean 233k); B: 197k–442k ns (mean 323k). Sub-ms throughout.
- Offset ranges recorded (A 876.6e9→905.2e9, B 739.7e9→743.1e9 ns); drift/sample
  A 167 ns, B 1566 ns. `host_time − esp_time` never used as latency; ESP→host
  latency reported None everywhere.

## 6. Current threshold assessment
- Default (≥64 obs AND jitter ≤ 2 ms): SUITABLE on real data — max observed jitter
  0.89 ms < 2 ms with margin. The synthetic 3 ms sleep-jitter concern did NOT
  reproduce. NO CHANGE made or recommended.

## 7. UI verification
- Live dual session → `GET /api/v1/nodes`: available=true, SYNCED, both nodes with
  real rate/valid%/RSSI/dup/ooo/gaps/jitter/offset/channel/BSSID/tones; no empty fields.
- Overview `overview.js` polls `api.nodes()` into ov-sync/ov-node-a/ov-node-b
  (runtime-rendered; standby fallback on fetch failure). No simulated values anywhere.
- Standalone smoke: HTTP 200, all 8 markers, honest standby (UNSYNCED + reason).

## 8. Evidence/manifest locations (all Git-ignored raws + SHA-256)
- `research-data/rfvision-010b/`: golden bin + .sha256 (4632c4be…), capture_metadata.json, validation.json, manifest.json.
- `research-data/rfvision-010dual/`: dual_60s_{a,b}.bin + .sha256, validation.json, dual_soak_120s_stats.json (24-sample series + final stats), manifest.json.
- Firmware identity: rebuilt `csi_recv_router.bin` sha256 0a490737… (740144 B; source unmodified).

## 9. Regression results
- `pytest`: 161 passed. `idf.py build`: SUCCESS (binary hash unchanged).
- ESP32-A golden replay through current code: EXACT (4654/0/1-gap/[121765]/62/0/0).
- UI smoke + privacy scan (0 hits) + secret scan (0 hits): PASS.

## 10. Problems discovered
- (a) Port↔board mapping swapped vs lab config — corrected with approval (§11).
- (b) Run-varying 0–3% print-fragment lines on B; zero seq loss; cause undetermined (likely host drain timing).
- (c) One 5-frame burst gap per node in the 120 s soak (0.04%); lean readers show zero loss — host-side contention under full-pipeline load, no acquisition failure.

## 11. Code changes necessary
- YES — minimal, approved, validation-required: swapped canonical by-paths in
  `csi/transport/nodes.py` (A→usb-0:5.4, B→usb-0:1) + updated the three pinning
  unit tests (`test_nodes.py`, `test_dual_foundation.py`). No firmware, parser,
  threshold, or UI-logic changes. Suite re-greened (161 passed) after the fix.

## 12. Decision: GO
A healthy; B reproduces the single-node baseline; concurrent streams sustained
120 s; no unexplained acquisition failures; sync metrics measurable and honest;
UI shows real data with honest standby; regression/privacy/secret all pass.
Ready to commit the current implementation. NOT pushed (per instructions).
