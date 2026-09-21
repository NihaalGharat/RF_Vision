# RFVISION-003 — Live-CSI Golden Test Report

Operation: RFVISION-003 (development/validation phase, NOT a sensing experiment).
Date: 2026-09-21 UTC. No human subjects, no human data, no model training
on real data, no localization evaluation, no Unity work, no flashing, no
router changes, no resets.

**RFVISION-003 STATUS: FAIL** (driven by the live-CSI path; all other
phases PASS — see phase table).

| Phase | Result |
|---|---|
| 0 Repository safety | PASS |
| 1 GitHub remote (inspected + proposal; creation DEFERRED by user) | PASS (deferred) |
| 2 Software reproducibility + `requirements.lock` | PASS |
| 3 Live CSI golden capture (60 s, byte-preserved) | FAIL (anomalous stream, 0 valid records) |
| 4 Golden fixture `tests/fixtures/live_csi/` | FAIL (blocked — no valid records; NOT fabricated) |
| 5 GUI bring-up (offscreen + real display) | PASS 6/6 |
| 6 Calibration/geometry dry-run, no humans | PASS 5/5 |
| 7–9 Report, evidence policy, quality gate, commit | PASS (this file) |

## 1. Environment

- Host: Lenovo IdeaPad Gaming 3 15IAH7, Ubuntu 26.04.1 LTS, kernel
  7.0.0-31-generic, Python 3.14.4, pip 26.2.1 (user-site).
- `python3 -m venv` unavailable (no ensurepip; `python3.14-venv` not
  installed; apt NOT used — no system modification). Isolated env not
  possible; documented GUI deps installed with
  `python3 -m pip install --user --break-system-packages PyQt6 matplotlib`
  (additions to `~/.local` only; no OS package touched).
- No gcc, no ESP-IDF toolchain in this env (recorded; firmware build/flash
  impossible here — consistent with the no-flash constraint).
- `sudo` requires interactive password; unattended execution could not escalate
  (see §13 F1).

## 2. Hardware

- USB-serial bridge: Silicon Labs CP2102 (VID:PID `10c4:ea60`, serial
  `0001`) → `/dev/ttyUSB0`. Matches baseline bridge expectation.
- ESP32 chip identity (D0WD-V3 rev 3.1): NOT independently verified —
  no esptool installed, and reading chip ID via boot-log capture would
  require a reset (forbidden). Identity evidence is limited to the USB
  bridge + node presence.
- Router: unmodified; association/path NOT verified (no valid frames to
  inspect; no router-side access attempted).

## 3. Firmware

- On-board firmware identity: UNKNOWN. Read-back, verification, re-flash,
  and reset-to-observe-bootlog are all outside the allowed actions, so the
  assumption "board runs `firmware/esp32/csi_recv_router/` @ `8633d671`"
  could NOT be confirmed. This is central to the Phase 3 verdict.
- Repo firmware copy untouched (git clean, §9 gate).

## 4. Software versions

Frozen in `requirements.lock` (repo root; install via
`python3 -m pip install -r requirements.lock`):
base+dev validated by tests/ — pyserial 3.5, numpy 2.5.3, scipy 1.18.1,
pandas 3.0.6, scikit-learn 1.9.1, matplotlib 3.11.2, PyYAML 6.0.3,
joblib 1.6.0, pytest 9.1.1 (+ pinned transitives);
gui — PyQt6 6.11.0 (Qt 6.11.2, sip 13.12.0), bring-up validated;
ml — torch NOT INSTALLED (KNN/RF baselines only).
Baseline pins retained: ESP-CSI `8633d67152db2808f141cc1595970aa9cf406045`,
ESP-IDF v5.4.4 (`296b6eab9445fd720e71aecb961e2d3fbca9944`, toolchain absent).

## 5. Capture conditions

- ONE passive 60.03 s capture, `/dev/ttyUSB0` @ 921600 8N1, firmware-side
  ping trigger assumed (host transmitted nothing; serial opened read-only).
- Binary-safe recorder (`/tmp/rfvision_capture.py`): bytes only, no
  parsing/decoding/line-splitting during recording (counter only).
- Pre-checks: node present, 124 GB disk free, raw dir outside git (§8).
  Serial `EACCES` (user not in `dialout`) resolved by the USER running
  `sudo chmod 666 /dev/ttyUSB0` (session-only; resets on replug).

## 6. Raw capture location

`~/RFVision-Research-Data/rfvision-003/csi_raw_60s.bin`
(external to git; 57,081,856 bytes). Independent 5 s `stty`+`dd` probe:
`/tmp/rate_probe.bin` (4,867,269 B) — same anomaly, discarded after analysis.

## 7. Raw SHA-256

`c64e5a00292f5fe886dd5d65dea0b61c301a65d1736c424a70a7accaf8f352df`
(file unmodified since recording; do NOT modify).

## 8. Validation results — FAIL

| Check | Result | Expected (CSI-VERIFY-001 / BASELINE.md) |
|---|---|---|
| Total bytes / duration | 57,081,856 B / 60.03 s (**950,880 B/s**) | ≤ 92,160 B/s @ 921600 8N1 |
| Text lines (`\n` / `\r`) | **0 / 0** | ~100 records/s |
| `CSI_DATA` markers | **0** | every record |
| Distinct byte values (57 MB) | **12** (`0,12,96,112,124,126,128,140,142,224,252,255`) | full int8 range |
| ASCII-decodable | NO (`0x8c` at offset 6) | ASCII `CSI_DATA,…` text |
| Boot/ROM markers (`ets `, `rst:`, `0xE9`) | none | n/a (app firmware expected) |
| Baud-dependence (115200/460800/1.5M/3M probes) | **identical stream at all bauds** | framing changes with baud |
| Valid records | **0** | ~6,000 |
| Sequence continuity / channel / BSSID / RSSI / rate / I/Q / amplitude / phase | N/A (no records) | ch 1, HT20 len 128 |

Interpretation (engineering, not a claim): a baud-independent 12-symbol
fixed-pattern stream at ~10× the UART line cap cannot be ESP32 UART
output sampled at 921600 8N1 — the configured baud has zero effect on
the received bytes, which is impossible for genuine serial traffic. The
plugged board is NOT emitting the validated `csi_recv_router` output.
Unverified hypotheses (need physical access): wrong firmware on board,
ESP32 held in reset/boot-loop with bridge artifact, faulty cable/levels,
or wrong board. Deliberately NOT investigated further: all discriminating
actions (reset, re-flash, read-back, cable swap) are outside this
operation's authority.

## 9. Adapter results — 0 parsed (correct rejection)

`EspCsvAdapter` against the capture: `lines_seen=0, parsed=0,
rejected_total=0` — head-1KB fails ASCII decode before parsing; no input
reaches `parse_esp_csv_line`. The adapter's strictness is confirmed (it
does not hallucinate samples from garbage); there is simply nothing valid
to adapt. No adapter code changed.

## 10. Golden fixture details — NOT CREATED (blocked)

`tests/fixtures/live_csi/` does NOT exist, by decision: a "golden"
fixture must derive from genuine live CSI, and zero valid records were
captured. Fabricating one from synthetic data under a live name would be
a provenance fraud. Unblocks on RFVISION-003R re-capture.

## 11. GUI results — PASS

Bring-up harness `/tmp/rfvision_gui_bringup.py` (heuristic engine,
stub receiver with the real polled interface, 70 synthetic samples):
6/6 — imports (Qt 6.11.2, mpl available), config load
(serial `auto`/921600), engine init (heuristic, models None), window
starts + visible, data flows (presence `EMPTY`), screenshot
`/tmp/rfvision-003-gui-bringup.png` (external). Repeated on the real
display (`DISPLAY=:0`, xcb, window visible, clean 1 s run).
Exact start command (from repo root):
`PYTHONPATH=. python3 realtime/server/live_app.py --port /dev/ttyUSB0`
Findings (warnings, no redesign): entry point requires `PYTHONPATH=.`
(pre-existing import quirk); missing-port behavior is resilient (receiver
retries in background, GUI still starts, link shown offline).

## 12. Calibration dry-run results — PASS

Harness `/tmp/rfvision_calib_dryrun.py`, config defaults only: 5/5 —
geometry 5-point round-trip + clamp, `room_width<=0` raises, sync median
offset exact with 1-outlier rejection + reset, calibration config
(`movement.auto_threshold_from_calibration=true`,
`data/processed/calibration.json`) resolves + serializes. Harness bug
found and fixed (nested keys need `get_nested`, not `resolve_path` —
repo API correct). GAP recorded: no node-registry module exists (nodes
implicit via config/MAC) — native work. ALL physical geometry
(router/ESP32 positions, room size, orientations): UNKNOWN, none invented.

## 13. Failures

- F1 serial `EACCES` (user not in `dialout`; the test session could not sudo):
  resolved via user-executed `sudo chmod 666` (session-only).
- F2 anomalous serial stream (§8): UNRESOLVED — stop condition
  "raw CSI capture malformed beyond expected limits" triggered; live-CSI
  path halted, no improvisation (no reset/flash/cable/router action).
- F3 golden fixture blocked by F2 (deferred, not fabricated).
- F4 ESP32 chip + firmware + router-association identity unverifiable
  within the no-reset/no-flash/no-router-access constraints.

## 14. Warnings

W1 rate paradox (~951 kB/s at 921600 baud) documented as evidence, not
explained away. W2/W3 user-site installs + `--break-system-packages`
(documented deps only; venv impossible — no ensurepip, apt unused).
W4 torch absent (ML baseline scope only). W5 no gcc/IDF toolchain.
W6 permanent serial fix (`usermod -aG dialout` + re-login) still pending
with the user. W7 `live_app.py` needs `PYTHONPATH=.`.

## 15. Known limitations

Single 60 s sample; one USB port/cable tried; no crosstalk check with a
second host; GUI exercised with synthetic (not live) samples; dry-run
uses config defaults; report evidence (screenshot, probes) in `/tmp`
(volatile) — raw capture + this report are the durable record.

## 16. Git commit

- Phase commit: `1ff91e4` ("rfvision-003: reproducibility baseline,
  GUI/dry-run PASS; live-CSI golden test FAILs (anomalous serial stream,
  0 valid records)"), recorded here in the follow-up commit (002 pattern).
- The prescribed message "feat: validate live CSI foundation…" was NOT
  used — it would misrepresent a FAILED golden test.

## 17. Next phase recommendation

RFVISION-003R (remediation, needs user + physical access): permanent
`dialout` membership; read-only `esptool chip_id`/`flash_id` (no
write); confirm which firmware is on the board (read-only `verify`/image
info — decide explicitly, still no flashing); try a second cable/port;
confirm the Xiaomi path associates; re-run the 60 s golden test; on PASS,
mint `tests/fixtures/live_csi/` + re-run adapter acceptance. Then:
GitHub remote creation (proposal §18, user-deferred), `requirements.lock`
freeze re-check, calibration with measured geometry (CSI-SENSE-001 track,
still NOT started). No sensing claims until live adapter acceptance passes.

## 18. GitHub remote — Phase 1 (user-deferred)

`git remote -v` empty (verified). Proposal recorded, NOT executed:
private repo `rf-vision` on the user's account (private: pre-publication,
zero validated claims); `main` + `rfvision-00X-<topic>` branches with
`rfvision-00X` tags; push `main` as-is after 003R; LFS only for >1 MB
fixtures (`tests/fixtures/**`); raw captures NEVER in git
(`~/RFVision-Research-Data/`, SHA-256 manifests in-repo). No credentials
in the repo (none added). Awaiting explicit user approval to create/push.
