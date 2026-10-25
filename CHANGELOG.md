# Changelog

All notable changes to the RF Vision foundation are recorded here.
Format: `YYYY-MM-DD — summary`.

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
