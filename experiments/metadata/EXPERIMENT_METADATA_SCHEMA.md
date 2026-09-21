# Experiment Metadata Schema (v1)

Every experiment directory (outside git — see `research/datasets/`) ships
an `experiment.json` with these fields. `experiments/analysis/` tooling
must refuse to score runs with missing fields.

| Field | Meaning |
|---|---|
| `experiment_id` | e.g. `CSI-SENSE-002` (unique, chronological) |
| `date_utc` | ISO-8601 start |
| `hardware` | router model, ESP32 variant/rev, USB path, room |
| `firmware` | repo + commit + example + sdkconfig checksum |
| `software` | RF Vision commit + `requirements-*.txt` checksums |
| `configuration` | config YAML checksum + overrides |
| `environment` | room dims, furniture, interference notes, photos ref |
| `geometry` | node positions (metres), link line, ground-truth marks |
| `subjects` | count + scripted positions per session |
| `protocol` | file in `experiments/protocols/` + version |
| `raw_data_ref` | immutable raw path + SHA-256 per file |
| `derived_data_ref` | transform + params + SHA-256 per artifact |
| `model_version` | `model_manifest.json` checksum (or `heuristic`) |
| `analysis_version` | scoring code commit |
| `checksum` | SHA-256 of this file (self-integrity) |
