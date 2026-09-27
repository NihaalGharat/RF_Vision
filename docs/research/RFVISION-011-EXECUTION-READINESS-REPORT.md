# RFVISION-011 — Execution Readiness Report

**Phase:** Controlled Spatial Discriminability Pilot — pre-execution readiness
**Protocol:** `RFVISION-011-PROTOCOL-v1.3.md` (FINAL, frozen, authoritative)
**Baseline commit:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`
**Report date (UTC):** 2026-09-22
**Status:** CONDITIONAL READY — blocked on human gates, not on the system

No experimental data collected. No firmware/AP/USB/config change. No ML,
localization, imaging, or UI work. No commit, no push.

---

## 1. Repository audit (read-only)

```text
Baseline commit: d1f12a51954964161cacde6c9d4f9d40ec1f25e0
Current commit:  d1f12a51954964161cacde6c9d4f9d40ec1f25e0 (identical)
Branch:          main
Working tree:    tracked files clean (git diff empty); 2 untracked docs only
```

RFVISION-010 foundation intact — all files present:

- `csi/transport/nodes.py`, `web/dual_node.py` (DualNodeSession)
- `localization/synchronization/sync.py` (host-side sync states only)
- `csi/capture/serial_receiver.py`, `csi/parser/csi_parser.py`,
  `csi/parser/esp_csv_adapter.py`, `web/live_serial.py`, `web/source.py`
- `research-data/README.md`, `research-data/MANIFEST.md`

RFVISION-011 v1.3 FINAL present: `docs/research/RFVISION-011-PROTOCOL-v1.3.md`
(264 lines; freeze anchors verified on disk — final H1 wording, `baseline_ref`,
separation-ratio definition, B3-no-C, E5/E6 never-retroactive).

Tooling confirmed: dual-node acquisition, §K validation logic
(`web/source.py`, `web/contracts.py`, `web/server.py`), synchronization,
raw-capture handling. `research-data/*` Git-ignored except MANIFEST/README;
prior evidence dirs (`rfvision-010b/`, `rfvision-010dual/`) present and ignored.
Safeguards: `SECURITY.md` no-secrets policy, CI workflow
`.github/workflows/ci.yml`, report archive `docs/research/` intact.

## 2. Hardware / acquisition readiness (verified live, nothing configured or flashed)

| Item | Expected | Observed | Verdict |
|---|---|---|---|
| Node A port | `/dev/ttyUSB0` via `usb-0:5.4` | by-path `usb-0:5.4` → `ttyUSB0` | MATCH |
| Node B port | `/dev/ttyUSB1` via `usb-0:1` | by-path `usb-0:1` → `ttyUSB1` | MATCH |
| Node A stream | live CSI-shaped I/Q @921600 baud | 246 framed lines / ~117 KB in 5 s probe | ALIVE |
| Node B stream | live CSI-shaped I/Q @921600 baud | 502 framed lines / ~241 KB in 5 s probe | ALIVE |
| Firmware SHA | `0a490737…dd` | exact match on `csi_recv_router.bin` | MATCH |
| AP | Nihaal / `8c:53:c3:5b:e1:59` / ch1 / 2412 MHz | live scan: same, signal 85 | MATCH |

The 5 s serial probe was a non-recorded liveness check only (bytes counted,
nothing persisted, ports closed). Line counts ≠ record counts (multi-line
framing); true rates, 62-tone completeness, on-device MACs, and AP association
are verified during execution under protocol §§D/K.

## 3. Blockers / discrepancies

No hard blockers. Zero discrepancies vs the validated baseline. Three soft gaps:

1. On-device MAC identity not re-queried (deferred to human pre-session §D check).
2. `research-data/rfvision-011/` does not exist yet (check only; nothing created).
3. No `trial_order.csv` writer tooling found (§5 orders generated in-memory only).

## 4. Required human actions

1. Physical setup + geometry (tape measure, floor grid, photos outside Git); fill §6 worksheets.
2. Pre-session §D verification: on-device MACs, firmware identity, AP/BSSID/channel,
   then ≥60 s healthy dual-acquisition check. Abort on any mismatch.
3. Approve research-data layout (protocol §J) and randomization (§5); authorize
   `mkdir -p research-data/rfvision-011/trials research-data/rfvision-011/analysis`
   plus `geometry.json` and `trial_order.csv` before E1.
4. Participant/environment control (§6C) with single-participant + electronics-ban confirmation.
5. Explicit GO before E1 (per-trial §K validation and STOP-on-flag rules apply throughout).

## 5. Randomization preview (Fisher–Yates, seeds recorded, not yet persisted)

```text
B1  seed=11011  order=Z6,Z5,Z4,Z1,Z2,Z3
B2  seed=11012  order=Z6,Z4,Z3,Z5,Z1,Z2
B3  seed=11013  order=Z3,Z6,Z1,Z4,Z5,Z2
```

Session order: PRE(E1,E2) → B1 → E3 → B2 → E4 → B3 → POST(E5,E6).
Baselines: B1→mean(E1+E2); B2→E3; B3→E4; E5+E6 drift-only, never retroactive.
C: B1→E3, B2→E4, B3→none. Every occupied trial records `baseline_ref`.

## 6. Execution checklist + worksheets

Room — X: ____ Y: ____ Z: ____ Origin: ____ A(x,y,z): ____ B(x,y,z): ____
AP(x,y,z≈): ____ Separation: ____ Heights: A ____ B ____ Orientation: ____
Obstacles: ____ Env (door/window/fan/AC/outsiders/RF events): ____ Photos (outside Git): ____

Zones (3×2, centers ≥1.0 m apart; STOP if room cannot fit — no invented alternative):

| Zone | Center X | Center Y | Size | Dist→A | Dist→B |
|---|---|---|---|---|---|
| Z1–Z6 | | | | | |

Participant: posture ____ facing ____ clothing ____ devices cleared ____
operator phone parked at ____.

Per trial (24 total; 15 s warm-up + 60 s clean + 5 s margins; cue-gated):
confirm ID/condition/zone/participant/A/B/AP → capture → immediate §K validation
(totals, valid %, rate, gaps, dups, ooo, malformed, monotonicity, 62 tones,
finite IQ, RSSI, BSSID/channel, node + firmware identity, sync) → metadata +
SHA-256 + anomaly log. FLAG if gaps>10 or valid%<99. Failed trials repeat only
on human decision, never automatically.

STOP on: wrong ESP32/MAC/firmware/AP/channel, moved node/geometry, unhealthy
acquisition, sync failure, second person, unexpected software behavior, protocol
ambiguity, or any uncovered decision — emit EXECUTION BLOCK and await human ruling.

## 7. Verdict

**CONDITIONAL READY.** All system-side checks pass. Awaiting human gates (§4)
and explicit GO before the 24-trial experiment.
