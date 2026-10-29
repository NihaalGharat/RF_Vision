# Changelog

All notable changes to the RF Vision foundation are recorded here.
Format: `YYYY-MM-DD — summary`.

## 2026-10-30 — Pre-demo stabilization checkpoint

- Fixed the recording-finalization race with a narrow re-entrant lock around
  recording start, write, auto-stop, checksum, and manifest publication.
  Regression coverage now compares metadata bytes/SHA against the raw files.
- WebSocket reconnect-budget exhaustion is corrected with indefinite capped
  backoff; Live uses the actual WebSocket service state.
- Preserved the verified dual-ESP32 CSI to Live/Visualize baseline and the
  conservative dual-node presentation. Reference View remains illustrative.
- Consolidated the scientific boundary: acquisition and live measured A/B
  delivery verified; relative RF activity observed; human-presence association
  exploratory; detection/tracking/coordinates/pose/obstacle/localization/
  reconstruction not validated.
- Recorded two audio-guided `Nihaal` human-presence trials and the VCET
  reference trial correction (`11,027` A / `11,559` B vectors; former
  `9,071`/`9,517` values were cumulative counters).
- Added the operator demo runbook and updated setup/status documentation.
- Verification: **325 passed** Python regression, 12 focused recorder/WebSocket
  tests, 13/13 offline browser checks, compile and diff checks clean. No new
  hardware trial and no new live-hardware acceptance claim.

## 2026-10-26 — Host truthfulness and live-visualization checkpoint

- Checkpointed host RF readiness/freshness truthfulness: stale data can no
  longer satisfy RF READY or SYNCED, and stale dual-node status maps to
  DEGRADED with DISCONNECTED precedence.
- Checkpointed dashboard/frontend progress: explicit node-health
  classification, corrected legacy-console routing text, and per-node React
  RF visualization (A/B routing, room backdrop, false-colour disturbance
  overlay, and approximate evidence tiers, all labelled unvalidated).
- Added focused Python/Node coverage; fresh full suite `278 passed`.
- The uncommitted P1-like firmware lifecycle candidate in `app_main.c` is NOT
  part of this checkpoint, remains unvalidated, and received no hardware test
  or build. No validated sensing claim was added.

## 2026-09-21 — Integrated research foundation (RFVISION-FOUNDATION-002)

- Initialized single authoritative repository (`~/Desktop/RF Vision`, `main`).
- Vendored validated acquisition firmware `csi_recv_router` (esp-csi @
  `8633d671`, Apache-2.0) untouched; pinned build files retained.
- Integrated Human-Sensing Python chain @ `d978e103` (MIT) across
  `csi/`, `dsp/`, `sensing/`, `localization/`, `ai/`, `realtime/`,
  `visualization/`, `config/` with import standardization.
- Fixes on import: serial double-callback/write duplication removed;
  preprocessor double `accepted` increment removed; first-word key renamed
  to `trim_first_word_invalid` (legacy alias kept); `expect_length` wired
  as acceptance telemetry; scaler double-reshape cleaned; sensing engine
  split into presence/motion/activity/state modules (identical math).
- New native code: ESP-CSV→CsiSample adapter, validators, capture helpers,
  transport constants, event envelope protocol, geometry/1-D/sync, XAI
  foundation, headless recorder, synthetic generators.
- `signal/` renamed to `dsp/` (stdlib `signal` shadowing breaks
  joblib/pytest — documented in `dsp/README.md`).
- 68 tests green (unit + integration + train→evaluate smoke on synthetic).
- Docs: architecture, data schema, validation status, dependencies,
  hardware baseline, provenance, wire formats, experiment framework,
  Unity message formats. csi-sensing excluded (license); CSI-Tool
  firmware excluded (obsolete).
