# RF Vision Canonical Data Schema (v1)

All downstream consumers (features → sensing → localization → ai →
realtime → Unity) use these representations. Raw wire formats are
documented in `csi/formats/WIRE_FORMATS.md`; adapters convert wire →
canonical. **Never alter validated raw CSI; adapt at the boundary.**

## CsiPacket (canonical sample = `CsiSample`)

| Field | Type | Meaning |
|---|---|---|
| `ts_esp32_us` / `ts_wifi_us` | int (µs) | firmware clocks (wrap; see sync) |
| `ts_local` | float (s) | host `time.time()` at reception |
| `seq` | int | receiver-side monotonic counter |
| `rssi` | int (dBm) | `rx_ctrl.rssi`, plausible range [-110, 30] |
| `channel` / `secondary_channel` | int | primary 1–14 (2.4 GHz); secondary 0/1/2 |
| `sig_mode` / `mcs` / `cwb` | int | 0=11bg,1=HT,3=VHT; MCS; 0=20 MHz,1=40 MHz |
| `rate, aggregation, stbc, fec_coding, sgi` | int | PHY flags (preserved, mostly unused) |
| `noise_floor, ampdu_cnt, sig_len, rx_state, ant` | int | `rx_state` 0 = clean |
| `mac` | str | source BSSID/sender |
| `first_word_invalid` | bool | trim first 4 bytes when true |
| `csi` | int8 array | (real, imag) pairs per subcarrier slot |

Derived: complex slots `real + j·imag` (`dsp`), amplitude `|·|`
(`dsp/amplitude`), phase `atan2` (`dsp/phase`, gated),
valid-subcarrier mask `(0–26, 32–58)` → 54 amplitudes.

## FeatureVector

180 floats + names + `timestamp` + `window_samples` (64/stride 8):
per-subcarrier mean/std/mean|diff| (162) + aggregate (5) + temporal (4) +
spectral bands (4) + RSSI (3) + movement descriptors (2). Contract tested
in `tests/unit/test_features.py`. `rssi` (raw) is metadata, never a feature.

## SensingResult (`SystemState`)

`connection` ONLINE/OFFLINE · `presence_label` PERSON/EMPTY/UNKNOWN +
`presence_probability` · `movement_label` MOVING/STATIC/UNKNOWN +
`movement_probability` · `position_raw`/`position_filtered` in [0,1] +
`confidence` · `csi_rate` · `latency_ms` · `packets`/`malformed` ·
`model_name` (`"none (heuristic)"` when untrained) · `last_update`.

## LocalizationResult

`{"position": [0,1], "position_m": metres from node A, "raw": model output}`
via `localization/positioning`. Metric mapping uses `room_width`
(A–B separation). 2-D/3-D schemas are reserved, not defined.

## XaiResult (`xai.explanation` payload)

`{"method", "caveats", "scores": {feature: score}}` — method is
`rf_impurity` or `permutation`; scores are comparative, never causal.

## RealtimeEvent (envelope v1)

`{"schema": 1, "type", "ts", "source", "seq", "payload"}`; types:
`sensing.snapshot`, `localization.update`, `xai.explanation`,
`system.status`, `system.log`. See `unity/integration/MESSAGE_FORMATS.md`.
