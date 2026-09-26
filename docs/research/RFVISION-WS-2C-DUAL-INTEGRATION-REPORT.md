# RFVISION WS-2C — DUAL-SESSION APP INTEGRATION REPORT

- **Date:** 2026-09-26 (UTC). Repo `main` @ `1711c9e`.
- **Baseline:** status 61, tracked diff 8 files `+495/-4`, full suite 241 passed.
- **After:** status 62 (the +1 is tracked `tests/integration/test_web_server.py`
  newly modified), full suite 248 passed. No new repo files; /tmp clean;
  no server proc; both serial ports free.

## Decision

```text
WS-2C — VERIFIED PASS
```

## Gap found
`DUAL` was attachable only in-process (tests). Production HTTP had no way to
create/attach/stop a `DualNodeSession`, so SYNC → RF READY was unreachable
through the real app (WS-2B finding). Minimum fix: expose the existing
session lifecycle; reuse `DualNodeSession` unchanged.

## Changes (all attributable to this objective)
- `web/server.py` — import `DualNodeSession`; `_dual_lock` + new factory seam
  `_DUAL_SESSION_FACTORY` (alongside the pre-existing `set_dual_session`
  test attachment); `dual_start()`/`dual_stop()`; `POST /api/v1/dual/start`
  and `POST /api/v1/dual/stop`; 409 guards (dual-start while single-live
  streams; provision while dual runs; live-source HTTP+WS while dual runs);
  `ValueError`→`RuntimeError` on fail-fast resolution; stop-on-start-failure;
  detach-guaranteed stop; docstring. Purely additive (zero `-` lines).
- `web/static/js/api.js` — `dualStart`/`dualStop` client calls.
- `web/static/js/tabs/hardware.js` — Dual-node session card (START/STOP +
  verbatim backend state via existing `nodes` poll key; RF READY rendered
  from backend only, never computed).
- `web/static/react/js/services/api.js`, `web/static/react/js/features/hardware.js`
  — same minimal control in the React mirror (inside pre-existing untracked dir).
- `tests/integration/test_web_server.py` — `DualSessionRouteTests` (7 tests,
  stub factory, no hardware): start/attach + nodes reflection + registry MACs,
  duplicate 409, stop/detach + idempotence, streaming guard, missing-board
  409 with nothing attached, provision-while-dual 409, live-while-dual 409.

Pre-existing work correctly NOT claimed: firmware `app_main.c`, `web/network.py`,
`csi/transport/*`, React scaffold, `scheduler.js`, `app.css`, THIRD_PARTY
(all dated 2026-09-25 / in WS-2C baseline).

## Verification
```text
Tests: 248 passed (241 baseline + 7 new); route file 20/20; dual-node unit 7/7.
DualNodeSession: reused unmodified (git diff web/dual_node.py empty).
ESP32-A: PROVISIONED (prior creds persist) → dual CSI ACTIVE → SYNCED.
  LIVE_VERIFIED, 458 valid / 0 malformed, board_mac b0:3f:d3:70:20:3c @ ttyUSB1,
  ch1 + expected BSSID, sync obs 458. (Rates vary with AP traffic.)
ESP32-B: same path → SYNCED. LIVE_VERIFIED, 1378 valid / 0 malformed,
  board_mac 04:b2:47:20:1a:dc @ ttyUSB0, sync obs 1378.
  (Dual-path MACs are registry-measured per node — the WS-2B single-live
  default-MAC caveat does not apply; by-path map confirmed correct live.)
Synchronization: SYNCED (criterion ≥64 obs + jitter ≤2 ms both nodes) at t+10 s.
RF READY: true — "full chain verified: network valid + compatible, both nodes
  identified + reachable, CSI on expected network, acquisition healthy, sync SYNCED".
Simulation/Fixture: untouched; source truth preserved (LIVE/SIMULATED/FIXTURE/OFF/STALE
  unchanged; no sim/fixture data in the live path).
STOP/Cleanup: dual/stop → standby, ports released; server stopped; 8130 free.
UI: both consoles serve with dual controls (HTTP 200, control present).
```

## Second Verification
Independent pass: routes/guards/backend-only rendering/no second acquisition or
sync path/no node masquerade all CONFIRMED; file tests 20/20 re-run.
Verdict was `FINDINGS REQUIRED CORRECTION` on claims/scope (not behavior):
(1) "only test hook" wording — corrected above; (2) pre-existing vs new
attribution — corrected with mtimes + baseline; (3) fixture/sim-while-dual
unblocked — deliberate non-change (necessity rule: no serial conflict, source
truth preserved, blocking would restrict pre-existing diagnostics);
(4) `dual_stop` exception path — practically unreachable (`stop()` guards each
close, `join` has timeout) with detach guaranteed by `finally`; no change per
necessity rule; (5) full-suite 248 is first-pass evidence, second pass covered
the route file. No code changes required; affected verification re-run: 27 passed.

```text
Second verification: AGREES (after corrections above; no code change needed)
```

## Diff Integrity
```text
Unrelated changes: NONE (my hunks purely additive; 4 deletions pre-existing)
Firmware changes: NONE
Research changes: NONE
Protocol changes: NONE
Secrets introduced: NONE (no credential handling in this task)
New files: NONE
```

## Remaining Limitation
None for the objective. Observed (not failures): A/B valid-rate asymmetry
follows AP traffic; `duplication.storm` single epoch symmetric at startup.

## Commit
```text
NOT AUTHORIZED
```

## Push
```text
NOT AUTHORIZED
```

**STOP.**

## WS-2C Final Acceptance Audit (2026-09-27 UTC)
- Full suite: 248 passed. Route file: 20/20. Second verification: AGREES (7/7).
- Live acceptance via app: dual/start 200 (A ttyUSB1, B ttyUSB0, expected BSSID/ch);
  t+12s B LIVE_VERIFIED, A SYNCING (slow verify); t+42s BOTH SYNCED +
  LIVE_VERIFIED (A 1395 valid/1 malformed 88.8Hz b0:3f:d3:70:20:3c;
  B 2095 valid/1 malformed 149.9Hz 04:b2:47:20:1a:dc; BSSID+ch1 both),
  sync SYNCED, RF READY true (full chain).
- Live guards: provision→409, live-source→409, duplicate start→409.
- STOP: 200, nodes standby, rf_ready false, ports free, no server proc.
- Decision: WS-2C FINAL ACCEPTANCE — VERIFIED PASS.
