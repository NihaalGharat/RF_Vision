# Legacy Tool Reference (CSI-SENSE-001, HISTORICAL / PRE-UBUNTU)

> **RFVISION-006 legacy migration — HISTORICAL / PRE-UBUNTU.**
> Legacy source: `RF Vision Files/06_TOOLS/` · Migrated 2026-09-21 ·
> See `docs/research/LEGACY-MIGRATION-PROVENANCE.md`.

Status: **REFERENCE ONLY — not active code.** The 11 legacy Python tools below
were validated against real 2026-09-06 captures on Ubuntu Live, but they target
the legacy directory layout and pre-date the current tested stack. Do NOT copy
them into `csi/`, `dsp/`, `tools/`, or `experiments/` without a dedicated work
item, review, and tests. Full byte-identical scripts live OUTSIDE git at
`~/RFVision-Research-Data/legacy-csi-sense-001/tools-reference/`.

## Why this file exists

The current stack (`csi/parser/esp_csv_adapter.py`, `dsp/*`, `tools/csi_record.py`,
`csi/validation/validators.py`, `realtime/protocol/event_envelope.py`) is tested
and integrated. The legacy tools below are preserved as citable technique notes
for future `experiments/analysis/` work — nothing more.

## Capture tools (`tools-reference/csi_capture/`)

| Script (SHA-256 prefix) | Lines | What it does | Current counterpart | Verdict |
|---|---|---|---|---|
| `capture_csi_sense.py` (`8b6d2bd8…`) | 264 | pyserial 921600 `read(4096)→wb`, timed A–F phase capture | `tools/csi_record.py` + `csi/capture/serial_receiver.py` | REFERENCE ONLY (timed-phase idea only) |
| `event_logger.py` (`0048fd78…`) | 262 | wall_clock_ns + chip_seq sidecar sync, 100 ms tolerance | `realtime/protocol/event_envelope.py` | REFERENCE ONLY |
| `validate_raw.py` (`0c490399…`) | 227 | Post-capture gates: missing ≤1 %, malformed ≤0.5 %, no gap >500 ms, ch1 ≥99 %, BSSID stable ≥99 %, `len 128` ≥99 % | `csi/validation/validators.py` (generic) | ADAPT-CANDIDATE (thresholds → future test vectors, never blind copy) |
| `backup_verify.py` (`b201c94b…`) | 373 | Persistent-backup gate: refuses `/cow/tmp/tmpfs/overlay`, SHA round-trip write test, ≥5 GB free, per-trial copy+verify | NONE | REFERENCE ONLY (unique safety design; see backup-gate report in this directory) |

## Analysis tools (`tools-reference/csi_analysis/`)

| Script (SHA-256 prefix) | Lines | What it does | Current counterpart | Verdict |
|---|---|---|---|---|
| `parse_csi.py` (`e95d91a2…`) | 304 | 24-group `CSI_DATA` regex + `re.finditer` glued-fragment handling; proven on real data (14 malformed / 0.195 % glued) | `csi/parser/esp_csv_adapter.py` (25-col `csv`-based, tested) | REFERENCE ONLY — do NOT replace the adapter (wire models differ; adapter additionally parses `smoothing`/`not_sounding`) |
| `features.py` (`1bae77bc…`) | 230 | amplitude `sqrt(I²+Q²)`, phase `atan2` detrended | `dsp/preprocessing/` + `dsp/features/` | REJECT (current chain tested incl. bug-regression) |
| `baseline_model.py` (`a820523e…`) | 288 | μ/σ/cov deviation model + walking-speed covariate | NONE (name collision with `ai/training/baseline_model.py`, a DIFFERENT ML-baseline concept — never confuse) | REFERENCE ONLY |
| `pca_spectrogram.py` (`65164d45…`) | 321 | PCA on baseline + STFT 2 s window, 90 % overlap | NONE | REFERENCE ONLY |
| `statistical_tests.py` (`a43b116e…`) | 376 | Q1–Q6 distribution-dependent tests, FDR correction, effect sizes | NONE (only significance-testing method in either tree) | REFERENCE ONLY (candidate for future `experiments/analysis/`) |
| `temporal_plots.py` (`14a1beaa…`) | 335 | A/C/D/F overlay plots + events + speed | `visualization/dashboard/`, `visualization/rf/` | REFERENCE ONLY |
| `analysis_config.json` (`39a68729…`) | — | Parser/feature/PCA/plot parameters | `config/default.yaml` | ARCHIVE (params cited in provenance; defaults win) |

## License note

No third-party headers found in these scripts (scanned for
`license|copyright|SPDX|MIT|Apache|GPL` — prose mentions only). Treated as
original RF Vision legacy code under the project MIT license. If
`validate_raw.py` thresholds are ever adapted, attribute as
`RF Vision legacy (CSI-SENSE-001, 2026-09-06, pre-Ubuntu archive)`.
No `THIRD_PARTY_NOTICES.md` change required.
