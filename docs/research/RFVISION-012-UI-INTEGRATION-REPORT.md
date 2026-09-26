# RFVISION-012 — UI INTEGRATION REPORT: `CONNECT RF NODES`

- **Date:** 2026-09-25 (UTC)
- **Task:** UI integration only (backend + firmware already implemented and hardware-verified)
- **Status:** PASS

---

## 1. Necessity gate

No equivalent control existed (searched `web/static` for connect/provision/RF-ready UI: none). The only required capability — initiate provisioning and observe truthful state — was missing. Implementation justified; nothing redesigned.

## 2. Changes (4 UI files, +108/−4 lines)

- `web/static/js/tabs/hardware.js` — new "RF network — provision" card in the existing System → Hardware destination: network/readiness kv rows (backend states verbatim, HTML-escaped), SSID + password inputs, `CONNECT RF NODES` (`btn primary`), progress note. Poll keys extended with `network`/`rfReadiness`; SSID prefilled from detection until user-typed; password cleared from DOM after submit; per-node POST-response states rendered, never invented; RF READY only from backend readiness.
- `web/static/js/api.js` — `network()`, `provision(ssid, password)`, `rfReadiness()` on the existing thin REST client.
- `web/static/js/scheduler.js` — matching poll fetchers (existing 2 s cadence, no new timers).
- `web/static/css/app.css` — `input.input` mirroring `.btn` tokens (no input style existed).
- No backend, firmware, contract (`CONTRACT_VERSION` 3), threshold, navigation, framework, or research changes. No duplicated provisioning logic.

## 3. Verification

- Automated: **241 passed** (backend untouched; no new tests — UI is a thin caller of tested endpoints).
- Runtime (headless Chrome + CDP, live server): card renders on System tab; button enabled; SSID prefilled `Nihaal`; `type=password`; `NETWORK_DETECTED` facts + honest `NODE_MISSING` shown; empty-submit guard (no backend call); wrong-password click → truthful `PROVISIONING_FAILED` with verbatim per-node states, readiness stays non-ready; password cleared and absent from DOM.
- Second: post-reload button enabled with default note (in-memory provision state correctly resets), no stale RF READY, backend/UI agree (`rf_ready` false both), password field empty.
- Hardware restored: test wrong-creds NVS-erased; both nodes streaming CSI on Nihaal; ports free; server stopped; /tmp probes removed.

## 4. Safety

- Password only in POST body; never displayed, logged, persisted, or URL-embedded; diff secret-scan clean (code-shape hits only).
- Research protocols/data, sync policy, acquisition, firmware: untouched.

## 5. Diff (final)

- `web/static/js/tabs/hardware.js` (+94/−4), `web/static/js/api.js` (+4), `web/static/js/scheduler.js` (+2), `web/static/css/app.css` (+8) — plus the 2 prior RFVISION-012 backend files. No commit, no push.

---

*End of report.*
