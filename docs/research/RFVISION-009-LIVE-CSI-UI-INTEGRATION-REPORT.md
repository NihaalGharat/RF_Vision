# RFVISION-009 — Live CSI Provider + UI Visual Optimization Report

**Final status: PASS.**

Live serial CSI from the validated CURRENT receiver is connected to the
RF Vision web console, gated UNVERIFIED → VERIFIED, visualized with a
polished research-instrument UI, and verified end-to-end in a real
browser against REAL hardware. No sensing claims made or enabled.

## 1. Live provider implementation

`web/live_serial.py` (new) + `LiveProvider` in `web/source.py` (gate
replaced by binding; foundation types untouched).

- **Transport** (`SerialLineSource`): stdlib + POSIX `termios` only —
  no new dependency. Raw 8N1 `CLOCAL|CREAD` at 921600; opening never
  touches modem-control lines, so merely opening `/dev/ttyUSB0` cannot
  reset the validated receiver. Binary-safe: bytes split on LF, ASCII
  with replacement; overlong fragments (>64 KB, corruption) dropped and
  counted. Port opened ONCE per session, released on source switch /
  stream stop (`close()` idempotent; `ConsoleState.set_source` closes
  the previous provider).
- **Parsing**: every `CSI_DATA` line goes through the EXISTING strict
  `EspCsvAdapter` — zero rule changes. `PacketError` → malformed++ with
  reason + recent-example ring (last 5, truncated). Non-CSI lines (boot
  text, tails) counted separately, never classed as malformed; blank
  lines ignored. Nothing is fabricated; nothing is silently discarded.
- **Separation**: the session ingests EVERY line (lossless counting +
  optional lossless raw recording); `frames()` yields only latest-frame
  envelopes decimated to ~10 Hz, so visualization can never
  back-pressure capture.
- **Recording** (explicit only, never automatic): `start_recording` /
  `stop_recording`, bounded ≤30 s, every received line written,
  SHA-256 manifest on stop; the manifest survives session end so the
  checksum is never lost. Server: `POST /api/v1/live/record/start|stop`
  → `research-data/live-diag/` (gitignored). NOT exercised live in
  this operation (no raw dataset purpose); covered by unit test.
- **Envelopes**: `presence/movement UNKNOWN`, probs/position/`None`,
  `validated: False`, `phases: None` (phase stays gated by the
  amplitude-only pipeline decision), amplitudes from the validated
  `csi.parser.amplitude()` helper (62 tones), `source_state` = current
  gate state. Every frame validates via `contracts.validate_envelope`.

## 2. Serial configuration

`/dev/ttyUSB0` @ 921600 8N1, `read_timeout_s 0.5` (responsive stop),
expected BSSID `8c:53:c3:5b:e1:59`, expected channel 1, board MAC
`b0:3f:d3:70:20:3c`. `make_provider("live", port=, baud=,
expected_bssid=, expected_channel=, line_source=)` — `line_source`
injection keeps all automated tests hardware-free.

## 3. Validation gate (UNVERIFIED → VERIFIED)

- **Settle (automated C2 SOP)**: the validation window starts only
  after `settle_s` (2.0 s) of CURRENTLY clean streaming (valid records
  flowing, no active repeat run, trailing-3 s throughput within the
  baud cap). Pre-settle open-transient storms stay recorded
  (`pre_gate_storm`, `storm_epochs`) but do not poison the window.
- **Gate (~3 s)**: records present, measurable rate within [5, 220] Hz
  (ceiling raised 160 → 220 after genuine 156 Hz traffic observed;
  storms replay at thousands of lines/s), channel == {expected},
  BSSID == {expected}, windowed throughput possible, no NEW storm
  epoch inside the window, data fresh. Pass → `LIVE_VERIFIED`.
- **Demotion**: a new storm epoch or impossible throughput while
  VERIFIED demotes immediately with the cause in reasons. Failures
  stay `LIVE_UNVERIFIED` with reasons; transport death before any
  valid record → `DISCONNECTED` + diagnostic; death after data →
  frames stop → existing 3 s STALE override. No reconnect loops:
  one open per session; retry is an explicit user action (Stop/Start).

## 4. Live source-state behavior (observed)

- Session 1: storm inside gate window → correctly stayed
  `LIVE_UNVERIFIED` (714 valid but unverified — gate did its job).
- Sessions 2–3: pump/session race after rapid re-bind (no session
  attached). Answered with stop → wait → start discipline.
- Session 4 (`LIVE-b03fd370203c-1790027871`): settled, gate passed,
  **held `LIVE_VERIFIED` for 6.5 min** until deliberate stream stop.

## 5. Actual session statistics (final, live)

42,053 valid / 4 malformed / 2 non-CSI (99.99 % valid); rate 93.3 Hz
(windowed; observed 44–158 Hz across sessions — AP-traffic driven);
seq → 476,807 with 5 isolated gaps (missing logged, ≤32 kept);
Ch 1 single, BSSID `8c:53:c3:5b:e1:59` single; RSSI −56 last,
−55.88 mean, trend stable (drifted −52 → −56 over the session —
environment, same position); CSI len 128 → 62 tones, I/Q finite;
amplitude min/max/mean/std 0.00/50.16/20.68/14.35; transport
19,691,698 B @ ~50 kB/s, 0 overlong, no error; duplication:
0 consecutive, 0 epochs, no storm, throughput possible; parser
42,057 seen / 42,053 parsed / 4 rejected (examples retained).

## 6. UI changes (005 architecture kept, RuView never cloned)

- **Overview**: RF Vision hero (live pill + connection + rate),
  Sensor (model/MAC/serial/link/firmware), CSI (rate/valid/RSSI/
  channel/tones/seq+gaps), System (shown packets/malformed/frame
  age/contract), Research (UNCALIBRATED / NOT VALIDATED / NOT
  AVAILABLE / NO VALIDATED MODELS), Latest frame. 2 s polling +
  instant hero sync on store state.
- **Sensing**: signal-validity card (gate verdict + reasons, valid %,
  malformed, rate, freshness, duplication) — NEW; latest-frame
  amplitude line chart with axes + legend (new `drawLine`) — NEW;
  heatmap (40 rows), RSSI sparkline, packets/sequence (gaps, missing,
  lossless count); phase card explicitly GATED; presence/activity
  card headed NOT VALIDATED (no HUMAN DETECTED anywhere).
- **RF Field**: unchanged single link; scene HUD now carries live
  extras (`state · rate · rssi · seq`); no new nodes/geometry.
- **Hardware**: baseline + LIVE link state (port/baud/open/
  throughput/age) + diagnostics (channel/BSSID/len/tones/error,
  identity UNKNOWN with reason).
- **Localization**: explicit `NOT VALIDATED — framework only` row;
  unknowns stay UNKNOWN. **XAI**: NOT AVAILABLE + NO VALIDATED MODEL.
- **Experiments**: live-session card (id/MAC/state/gate/records/
  raw-capture/validation NOT_RUN) + source select (live enabled,
  reflects ACTIVE mode) + bounded diagnostic-record buttons.
- **Settings**: danger-zone text updated (no 003R block references).
- **Chrome**: banners updated (UNVERIFIED mentions session gate;
  DISCONNECTED drops the 003R reference).
- **CSS**: card header accent rule, dotted kv rows, bordered
  uppercase pills, `.ok/.warn-text/.err-text`, hero layout,
  focus-visible, button transitions, responsive + reduced-motion kept.
  Dark research-console aesthetic; no glow excess, no sci-fi.

## 7. Performance

~100–160 Hz ingest, 10 Hz WS fan-out, bounded deques (240 arrivals /
120 RSSI / 5 malformed-examples / 2048 byte-marks), per-frame work O(62
tones). Browser stayed responsive; screenshots show sub-second frame
ages. No render-every-packet path exists.

## 8. Browser verification

Headless Chrome (`--headless=new`, virtual-time budget) against the
LIVE streaming console, one shot per tab. 3D (three.js r160, local
vendor) renders headless with live HUD. One localization shot caught
a STALE banner under virtual-time WS starvation; server-side at that
moment: frame age 0.05 s, 158 Hz (artifact of the capture method, not
a console fault — documented; re-shot clean).

## 9. Screenshot locations (outside Git, /tmp/rfvision-ui-preview/)

`0-contact-sheet.png` (consolidated 7-tab montage),
`6-overview.png`, `2-sensing.png`, `3-rffield.png`,
`4-hardware.png`, `5-localization.png` (clean re-shot),
`4-xai.png`, `4-experiments.png`
(`1-overview.png`, `4-localization.png` superseded but retained).

## 10. Tests

`python3 -m pytest tests/ -q` → **128 passed** (107 preserved + 21
new). New `tests/unit/test_live_provider.py`: binding, exact
valid/malformed/non-CSI accounting, gap counting, gate promotion on
paced genuine stream, BSSID/channel rejection, storm blocks gate,
pass-then-demote, settle-promotes-despite-transient, disconnect
before/after data, stale flag, latest-frame decimation
(fewer envelopes than records, skipped seqs, non-decreasing),
bounded buffers, lossless recording + SHA manifest, envelope schema
(UNKNOWN/unvalidated/gated on EVERY frame), console wiring incl.
serial release on source switch. Updated: `test_web_contracts.py`
gate test → bind-unverified; `test_web_server.py` refusal test →
bind-unverified + `/api/v1/live` shape. Hardware-free via
`FakeLineSource` (+ callable pacing, disconnect injection) and the
genuine C1 50-line fixture.

## 11. Failures / warnings

1. First server launch ran with stale shell groups → `Permission
   denied` on `/dev/ttyUSB0`; honest DISCONNECTED + diagnostic shown.
   Relaunched under `sudo -n -g dialout` (group context only).
2. Gate window storm (session 1) → UNVERIFIED by design; settle logic
   added as a result (unit-covered).
3. Rate ceiling 160 → genuine 156 Hz traffic rejected; raised to 220
   with storm-rate justification (unit rates unaffected).
4. `ComplexWarning`-class noise: none in pipeline. `drawLine` uses
   `Math.min(...series)` (62 elements — safe).

## 12. Known limitations

- Validation is transport + signal only: no human sensing, no
  localization, no models, no XAI — all tabs say so.
- Rate/RSSI vary with AP traffic and environment (75 → 158 Hz
  across C2/live); gate tolerates, does not characterize.
- Storm root layer (bridge vs driver) still phenomenology-only.
- Recording endpoint live-untested (unit-tested only) — no raw was
  captured in this operation by design; C2 golden untouched.
- Headless screenshots under virtual time can show transient
  STALE/few-row heatmaps; live browser fills both.
- Termios reader is POSIX-only (bench host is Ubuntu; documented).

## 13. Next phase (separate approval, NOT started)

Controlled perturbation / presence-trial design, or `LiveProvider`
hardening (multi-session stats, longer soak). CSI-SENSE-001 remains
locked.

## 14. Commit

`0bfb241 feat: connect live CSI stream to RF Vision console` (plus this
hash-record follow-up per repo precedent). No raw, screenshots, caches,
credentials, or generated artifacts committed.
