# RF Vision Architecture

Pipeline (single link, validated acquisition → native extensions):

```
ESP32-D0WD-V3 (csi_recv_router, ESP-IDF v5.4.4)
  │  ping 10 ms → Xiaomi Router 4C → CSI callback → CSI_DATA @921600 8N1
  ▼
firmware/esp32 + csi/capture (SerialReceiver, RawSessionWriter) + tools/csi_record
  │  + csi/transport (serial constants) + firmware/protocols (wire spec)
  ▼
csi/parser (CsiSample) ← csi/parser/esp_csv_adapter (CSI_DATA text → sample)
  ▼
csi/validation (plausibility ranges, warnings not rejections)
  ▼
dsp/preprocessing (rx_state/first-word/cwb/HT gates → Hampel → EMA/MA → opt. LP)
  ├─ dsp/amplitude (canonical amplitude entry point, 54-valid-subcarrier mask)
  └─ dsp/phase (gated OFF by default — per-packet offset, needs validation)
  ▼
dsp/features (sliding 64/stride 8 → deterministic 180-d vector + names)
  ▼
sensing/ (motion heuristic → presence KNN/RF/MLP → PresenceSmoother → state)
  ├─ presence / motion / activity (movement-derived labels, no trained classifier)
  └─ state (SystemState snapshot for GUI/Unity)
  ▼
localization/ (calibration → geometry [0,1]→m → position_1d → tracking filter)
  │  + synchronization (clock-offset helpers; multi-node = scheduled work)
  ▼
ai/ (datasets session-split → training → inference API → evaluation → xai)
  ▼
realtime/ (streaming re-export → live_app → protocol event envelope v1)
  ▼
visualization/dashboard (Qt room+status+debug) · visualization/rf (field viewer)
  · digital_twin (interface) · unity/ (message formats; scenes = scheduled work)
```

Cross-cutting: `config/` (central YAML), `experiments/` (protocols, metadata
schema, overrides), `research/` (manifests/reports/publication, no raw data).

## Subsystem maturity

| Subsystem | Source | Maturity | Limits |
|---|---|---|---|
| firmware/esp32 | esp-csi (verbatim) | VALIDATED acquisition | single-ESP router mode only |
| csi/capture+parser+validation | Human-Sensing + native adapter | integrated, 68 tests | adapter is new code (synthetic-tested; needs live-CSI golden test) |
| dsp/* | Human-Sensing + fixes | integrated, tested | amplitude-only default; phase gated |
| sensing/* | Human-Sensing, split | integrated, tested | activity = heuristic; no trained classifier |
| localization/* | Human-Sensing + native | seed only | 1-D link; 2-D/3-D + sync scheduled |
| ai/datasets+training+evaluation | Human-Sensing | smoke-tested (train→eval runs) | no real dataset yet; torch optional |
| ai/xai | native | interface + importances | NOT a validated explanation method |
| realtime/protocol | native | envelope v1, tested | single-node; MQTT/WS bridge scheduled |
| visualization/dashboard | Human-Sensing | code integrated | PyQt6 untested headless (needs GUI env) |
| digital_twin / unity scenes | — | interface specs only | scheduled work |
| experiments/ | native | framework only | no protocol executed |

## Key decisions (from RFVISION-REPO-FOUNDATION-001 audit)

1. One firmware (esp-csi router mode; HEAD == validated commit — zero drift).
2. One parser (Human-Sensing strict JSON) + one native adapter (ESP-CSV).
3. One filter chain, one 180-d feature contract, one trainer.
4. csi-sensing: zero code (restrictive license). CSI-Tool firmware: excluded.
5. `signal/` → `dsp/` (stdlib shadowing). No duplicate implementations.
