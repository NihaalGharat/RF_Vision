# Test fixtures

- `golden_esp_csv_line.txt` — one well-formed classic `CSI_DATA` line
  (seed 7, deterministic via `tests/synthetic/synth.py`).
- `golden_json_line.txt` — one well-formed `#CSI {JSON}` line (seed 7).
- `malformed_lines.txt` — negative cases (short columns, bad JSON).

Regenerate with `tests/synthetic/synth.py`. These tiny vectors are the
ONLY CSI bytes committed to git (see `research/datasets/README.md`).
