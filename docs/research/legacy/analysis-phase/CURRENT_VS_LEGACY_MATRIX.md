# RFVISION-006 — CURRENT vs LEGACY MATRIX

- Current (authoritative, baseline): `~/Desktop/RF Vision`
- Legacy (source archive): `~/Downloads/RF Vision Files-20260921T163602Z-1-001` (canonical inner `RF Vision Files/`)
- Priority rule applied: experimentally validated current baseline > current architecture > newer verified implementation > legacy > speculative/obsolete.
- Status values: ALREADY PRESENT / MISSING / SUPERSEDED / DUPLICATE / HISTORICAL ONLY / POTENTIALLY USEFUL.

## 0. Baseline facts used for comparison

- Current pins (from `docs/hardware/BASELINE.md` + `RFVISION-003` §4–5): ESP-CSI `8633d67152db2808f141cc1595970aa9cf406045`, ESP-IDF v5.4.4 `296b6eab9445fd720e71aecb961e2d3fbca9944`, `csi_recv_router`, 921600 8N1, HT20 `len=128` → 64 slots. Legacy pins IDENTICAL (see matrix row C1) — no conflict.
- Current validation posture (`docs/research/SCIENTIFIC_VALIDATION_STATUS.md`): acquisition VALIDATED (own external experiment), ALL sensing claims NOT YET VALIDATED, synthetic metrics never quotable. Legacy posture: CSI-VERIFY-001 PASS (external 2026-09-06 experiment), pilot INCONCLUSIVE N=1. Compatible — legacy does not contradict current claims register.
- Current live state (`docs/research/RFVISION-003-LIVE-CSI-GOLDEN-TEST-REPORT.md`): 60 s capture FAIL — 0 valid records, baud-independent 12-symbol stream at ~951 kB/s; golden fixture NOT created (refused to fabricate). Legacy R1 PASS capture is therefore the ONLY genuine-CSI evidence in the project family — increases its archival value, does NOT change the FAIL verdict (different date/hardware-state).
- Current tests: 68-test foundation suite (per `RFVISION-FOUNDATION-IMPLEMENTATION-REPORT.md` §13). Must stay green; no legacy code may break it.
- RuView: current `RFVISION-004-RUVIEW-AUDIT-REPORT.md` is controlling. Legacy contains ZERO RuView material (textual grep for `ruview|rUv|three.js|unity|gaussian` → no textual hits; binary `.npz/.png` byte-matches are false positives). No action.

## 1. Matrix

| Legacy Material | Current Equivalent | Status | Action | Reason |
|---|---|---|---|---|
| Plan `00_PROJECT/PLAN/CSI-SENSE-001_PLAN_v1.1.md` (v1.1, 753 L, `c72b2c4b`) — A–F protocol, gates, backup rule | `experiments/protocols/BASELINE_PROTOCOL.md` (23-line unexecuted template) | MISSING | MIGRATE (as `docs/research/legacy/CSI-SENSE-001_PLAN_v1.1.md`, sanitized) | Only executable human-protocol definition; template has no A–F detail. Historical, NOT an instruction to run (human experiments remain forbidden without new approval). |
| `01_HARDWARE/hardware_identity.json` (`f35a5223`) — exact ESP32/router/host/Live identities | `docs/hardware/BASELINE.md` (pins only) | MISSING (detail) | MIGRATE (as `docs/hardware/legacy/CSI-SENSE-001_hardware_identity.json`, sanitized; summarize deltas into `BASELINE.md` provenance note only) | Recovers BIOS `JMCN48WW`, flash `0x68:0x4016`, bridge by-id, gateway, signal, Live volatility, untouched-NVMe attestation. Mark HISTORICAL / PRE-UBUNTU-transition where host-specific. |
| `02_FIRMWARE/firmware_versions.json` (`0b286912`) — IDF/CSI commits, build SHAs `ce23861e`/`7d7cf518`, flash transcript | `docs/hardware/BASELINE.md` + `firmware/esp32/csi_recv_router/` source | ALREADY PRESENT (pins) + MISSING (transcript) | MIGRATE transcript-only (sanitized; password line REDACTED) | Pins match exactly — confirms baseline, no change. Build/flash transcript is unique provenance. NEVER overwrite firmware source. |
| `02_FIRMWARE/capture_config.json` (`edcfbf00`) — baud, send-freq 100, A–F durations, validity gates | `config/default.yaml` + `experiments/metadata/EXPERIMENT_METADATA_SCHEMA.md` (generic, no A–F values) | POTENTIALLY USEFUL | MIGRATE as historical reference doc; DO NOT merge into `default.yaml` | Gate thresholds (≤1 % missing, ≤0.5 % malformed, >500 ms gap, ch1 ≥99 %) are the only machine-readable validity definition. Current defaults win on conflict. |
| Raw R1 `CSI_RAW_70s...log` (`51d47ce…`, 3.57 MB) — VERIFY PASS | NOTHING in repo (correct); external `~/RFVision-Research-Data/rfvision-003/csi_raw_60s.bin` (`c64e5a00…`, 57 MB, FAIL capture) | MISSING (external evidence) | MIGRATE-EXTERNAL to `~/RFVision-Research-Data/legacy-csi-verify-001/` + manifest; NEVER into git | Only genuine-CSI PASS evidence; distinct hash from the FAIL capture. Raw-immutable rule. |
| Raw R2 trial_01 (`4734dcf…`, 14.3 MB) + sidecars (`capture_meta`, `capture_stdout`, `events`, `validate`, `.sha256`) | NOTHING | MISSING (external evidence) | MIGRATE-EXTERNAL (raw) + MIGRATE sidecar JSONs as docs | N=1 INCONCLUSIVE pilot — evidence, not a claim. Sidecars are KB-scale and safe for docs. |
| Raw R3 smoke (`ce04708…`, 0.5 MB) + sidecars | NOTHING | MISSING (external evidence) | Same as R2 | Pre-pilot smoke evidence. |
| `04_EVENTS_METADATA/events/events_trial01.jsonl` — A→F timeline | Schema only (`EXPERIMENT_METADATA_SCHEMA.md`) | MISSING | MIGRATE (docs) | Only ground-truth sidecar; required to interpret R2. |
| `room_geometry.json` (NULL placeholder) | Schema only | HISTORICAL ONLY | MIGRATE (as gap record) | Documents an UNFULFILLED measurement — prevents false claims that geometry is known. |
| `study_metadata.json`, `environment_trial01.json` (UNKNOWNs + 0.55 m height), `trial_01_metadata.json`, `smoke_test_metadata.json`, `capture_meta_*.json`, `validate_*.json` | Schema only | MISSING / HISTORICAL ONLY | MIGRATE (docs) | Methodology + negative-space record. Environment UNKNOWNs must stay UNKNOWN (no invention). |
| Derived `05_ANALYSIS/trial_01/*` (parsed/features/baseline/PCA/figures, ~55 MB) + `smoke_test/*` | NOTHING (current `dsp/`, `ai/` have no pilot artifacts; `research/datasets/README.md` forbids bulk in git) | HISTORICAL ONLY | ARCHIVE-EXTERNAL (one copy + manifest); migrate ONLY small JSON metas into docs | Reproducible from raw+tools; large; git-forbidden. |
| Phase-B-era `CSI_SENSE_001/ANALYSIS/{stats,figures}` + `SOURCE_PROJECT/...` equivalents | NOTHING | SUPERSEDED | ARCHIVE (reference; deduplicate) | Superseded by `05_ANALYSIS` trial_01 set. |
| `07_REPORTS/CSI-VERIFY-001_FINAL_REPORT.md` + `PHASE1_APPROVAL_GATE.md` | `SCIENTIFIC_VALIDATION_STATUS.md` (policy) + `RFVISION-003` (contrasting FAIL) | MISSING | MIGRATE (sanitized — password lines redacted) | Foundational PASS evidence the current tree cites but does not contain. |
| `07_REPORTS/PHASE_B_IMPLEMENTATION_REPORT.md` | NOTHING | MISSING | MIGRATE | Host-tooling PASS record (no human experiment). |
| `07_REPORTS/PHASE_C_READINESS_REPORT.md` | `BASELINE_PROTOCOL.md` (template) | MISSING | MIGRATE | Prerequisite logic (geometry/env/backup) the template lacks. |
| `07_REPORTS/PHASE_C_PILOT_REPORT.md` (INCONCLUSIVE) | NOTHING | MISSING | MIGRATE | Negative result — scientifically valuable; pins scope (no localization/ML/3D claim). |
| `07_REPORTS/PERSISTENT_BACKUP_GATE_REPORT.md` | NOTHING | POTENTIALLY USEFUL | MIGRATE (with backup tool) | Operational-safety precedent. |
| `07_REPORTS/FINAL-FOLDER-AUDIT-001.md` + `FINAL-ARCHIVE-AUDIT-002.md` | `RFVISION-REPO-FOUNDATION-001-ANALYSIS-ARCHIVE.md` (different scope) | HISTORICAL ONLY | MIGRATE one copy each | Provenance of the archive itself (volatility, dups, boot-gap, Nano note). |
| `08_CHECKSUMS_MANIFESTS/SHA256SUMS.txt` + `PATH_PROVENANCE.md` | `research/datasets/README.md` (policy only) | POTENTIALLY USEFUL | MIGRATE excerpt (hashes of migrated items + Live-path note) | Checksum discipline + `/home/ubuntu` Live-path explanation. |
| `BACKUP_MANIFEST.md` / `BACKUP_COMPLETE.md` / `BACKUP_BEFORE_REBOOT.md` (Live-staging narrative) | NOTHING | HISTORICAL ONLY | ARCHIVE (condense into migration provenance; no verbatim bulk) | Stale Live-USB/Google-Drive narrative; keep facts, drop staging instructions. |
| `README.md` (archive index, 47 L) | `README.md` (current) | SUPERSEDED | ARCHIVE (cite style only) | Current README is authority; Live-upload narrative stale. |
| `06_TOOLS/csi_capture/capture_csi_sense.py` | `tools/csi_record.py` + `csi/capture/serial_receiver.py` | SUPERSEDED | REFERENCE ONLY | Current recorder + receiver are tested; legacy adds timed-phase logic only as future idea. |
| `06_TOOLS/csi_capture/event_logger.py` | `realtime/protocol/event_envelope.py` | SUPERSEDED | REFERENCE ONLY | Current envelope is the contract; legacy sync-tolerance note is citable. |
| `06_TOOLS/csi_capture/validate_raw.py` | `csi/validation/validators.py` (generic) | POTENTIALLY USEFUL | ADAPT-candidate (thresholds → test vectors/docs) | Only place with field-validated gate values; port as data, not code copy. |
| `06_TOOLS/csi_capture/backup_verify.py` | NOTHING | POTENTIALLY USEFUL | REFERENCE ONLY (future `tools/` item) | Unique safety tooling; no current counterpart. Not active code now. |
| `06_TOOLS/csi_analysis/parse_csi.py` (regex + glued `finditer`, validated on real data) | `csi/parser/esp_csv_adapter.py` (csv-based, tested) + `csi/parser/csi_parser.py` (JSON model) | SUPERSEDED (as code) / POTENTIALLY USEFUL (as technique) | REFERENCE ONLY | Wire-format families differ (legacy 24-group regex vs current 25-col adapter incl. smoothing/not_sounding). Do NOT replace adapter. Document glued-fragment handling; add regression test ONLY if a gap is proven. |
| `06_TOOLS/csi_analysis/features.py` | `dsp/preprocessing/preprocessing.py` + `dsp/features/feature_extraction.py` | SUPERSEDED | REJECT (cite only) | Current chain is tested (incl. bug-regression tests); legacy is untested in this tree. |
| `06_TOOLS/csi_analysis/baseline_model.py` (μ/σ/cov + walk covariate) | `ai/training/baseline_model.py` (DIFFERENT concept — ML baseline) | POTENTIALLY USEFUL | REFERENCE ONLY | Name collision noted — must never be confused. No current statistical-baseline counterpart. |
| `06_TOOLS/csi_analysis/pca_spectrogram.py` | NOTHING | POTENTIALLY USEFUL | REFERENCE ONLY | No current PCA/STFT counterpart. |
| `06_TOOLS/csi_analysis/statistical_tests.py` (Q1–Q6 FDR effect-size) | NOTHING | POTENTIALLY USEFUL | REFERENCE ONLY (candidate for future `experiments/analysis/`) | Only significance-testing method in either tree. |
| `06_TOOLS/csi_analysis/temporal_plots.py` | `visualization/dashboard/`, `visualization/rf/` | SUPERSEDED | REFERENCE ONLY | Current viz is RuView-pattern native; legacy plots are pilot-specific. |
| `csi_analysis/analysis_config.json` | `config/default.yaml` | SUPERSEDED | ARCHIVE | Params citable in provenance; defaults win. |
| All `SOURCE_PROJECT/`, `99_ARCHIVE/SOURCE_PROJECT_mirror_20260906/`, `CSI_VERIFY_001/`, `CSI_SENSE_001/`, `99_ARCHIVE/historical_duplicates/`, `99_ARCHIVE/obsolete_phase_b_files/`, root dup copies | (mirrors of above) | DUPLICATE / SUPERSEDED / HISTORICAL ONLY | DO NOT MIGRATE (record hash equality; DELETE-class after verification) | 150+ files verified byte-identical to canonical copies. |
| RuView / Unity / three.js / XAI / ML weights / papers / citations | `docs/research/RFVISION-004*`, `docs/architecture/RUVIEW_TO_RFVISION_COMPONENT_MAP.md`, `web/static/vendor/three.module.js`, `ai/*`, `docs/third_party/bib/` | ALREADY PRESENT (current) / ABSENT (legacy) | NO ACTION | Legacy has none of these; current audit remains controlling. No duplicate-doc risk. |
| Third-party code/licenses in legacy | `THIRD_PARTY_NOTICES.md` + `docs/third_party/SOURCE_PROVENANCE.md` | ALREADY PRESENT (current) / ABSENT (legacy) | NO ACTION | No third-party content found in legacy; no notices update needed. |
| Credentials: Wi-Fi password plaintext in `firmware_versions.json` + VERIFY report | NOTHING (current repo clean — 0 hits) | MISSING (correctly) | DO NOT MIGRATE value; record detection in `docs/security/LEGACY_CREDENTIAL_AUDIT.md` (REDACTED) | Secret must never enter git. Recommend rotation (see migration plan §5). |
| Router BSSID/MAC, ESP32 MAC, SSID, gateway (reproducibility IDs) | Partially in `BASELINE.md` | ALREADY PRESENT (pins) | MIGRATE with IDs intact (policy: retained for reproducibility, per legacy README §Security) | Not secrets; needed to interpret captures. |

## 2. Conflict resolutions (version rule applied)

1. **Firmware pins agree** (IDF `296b6eab`, CSI `8633d671`, `ce23861e`/`7d7cf518`) — no conflict; legacy corroborates `BASELINE.md`. Action: cite legacy as corroborating evidence, change nothing.
2. **Parser families differ** — current `EspCsvAdapter` (tested, 25-col) wins over legacy regex parser (validated 2026-09-06 but untested here). Action: REFERENCE ONLY, no replacement.
3. **DSP/feature chain** — current Human-Sensing-derived `dsp/` (tested) wins over legacy `features.py`. Action: REJECT.
4. **Protocol** — legacy v1.1 (executed once, N=1) vs current template (unexecuted). No contradiction; legacy is historical detail, template stays the forward process. Action: archive legacy as reference, do not promote it to active protocol.
5. **Pilot verdict vs any future claim** — legacy INCONCLUSIVE N=1 must never be quoted as detection/localization proof. Current `SCIENTIFIC_VALIDATION_STATUS.md` (zero validated sensing claims) remains binding. Action: migrate pilot report with its INCONCLUSIVE label intact.
6. **RFVISION-003 FAIL vs legacy PASS** — different captures, different dates/states; both stand. Action: preserve both; do not let legacy PASS override the current FAIL remediation path (003R).

## 3. Raw-data disposition (immutable rule)

- R1/R2/R3 do NOT exist in the current repo or in `~/RFVision-Research-Data/` (which holds only the RFVISION-003 FAIL capture). No SHA collision, no duplicate copy — all three are UNIQUE and must be preserved EXTERNALLY.
- Proposed external home (pending approval): `~/RFVision-Research-Data/legacy-csi-verify-001/` (R1) and `~/RFVision-Research-Data/legacy-csi-sense-001/{raw/trial_01,raw/smoke_test,derived/}` (R2/R3 + one derived copy). Git receives ONLY manifests (path + SHA-256 + size + provenance), never bytes.
- Derived `.npz/.csv` (~55 MB + ~1 MB per copy) are reproducible; ONE external copy suffices. Git receives only small JSON metas + figure-manifest references.

## 4. Code disposition (no-duplication rule)

- ZERO legacy `.py` files qualify for direct MIGRATE into the active tree. Best case is ADAPT-candidate (`validate_raw.py` thresholds → test vectors) and REFERENCE ONLY for the rest. Rationale per file is in the matrix above; the governing facts are: (a) current equivalents are tested and integrated, (b) legacy tools target a different (older-named) layout and the JSON-vs-CSV model split, (c) `python3 -m pytest tests/ -q` must stay green.
