# RFVISION-011 Presence Pilot v1.0 — E1 Re-run Final Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, unmodified)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`
**Phase scope:** E1 re-run only, under fresh run ID. No E2, no P1, no analysis,
no modification, no commit, no push.
**Authorizing change:** Option B recording-cap fix (human-approved):
`web/source.py:225` `REC_MAX_SECONDS` 30.0 → 120.0; plus 2 unit tests in
`tests/unit/test_live_provider.py` (163/163 suite green pre-run).
**Report date (UTC):** 2026-09-23

## 1. Execution record

1. Created fresh run dir `research-data/rfvision-011-presence/trials/R11P-01R/`;
   verified both `/dev/ttyUSB0` + `/dev/ttyUSB1` present and the R11P-01R
   paths Git-ignored (`research-data/.gitignore:4:*`) before capture.
2. Ran **E1 re-run (R11P-01R)** with the validated stack
   (`web/dual_node.DualNodeSession`, unchanged): 15.087 s warm-up (pumped,
   discarded) + 60.589 s clean window, 2026-09-23T07:31:10+00:00 →
   2026-09-23T07:32:10+00:00. Recording armed before warm-up spanned the
   full ~75.7 s session — the 120 s cap held, no auto-stop.
3. Room empty, human out of the Router→ESP path, setup untouched, no
   disturbance or anomaly observed at the room level.
4. Validated at live-counter level (warm-up-subtracted) and at preserved-file
   level with the stack parser; SHA-256 independently re-verified.
5. **E1 re-run FAILED §K** (Node A board silent) → E2 NOT started. STOP.
   No repair, reset, reflash, replug, filter, retry, truncation, or discard.

## 2. Identity note (not a setup change)

Node identity follows USB by-path + board MAC (`csi/transport/nodes.py`):
`esp32-a` (usb-0:5.4, `b0:3f:d3:70:20:3c`) resolved to `/dev/ttyUSB1`,
`esp32-b` (usb-0:1, `04:b2:47:20:1a:dc`) to `/dev/ttyUSB0` this boot.
`ttyUSBn` numbering differs across boots by design; topology is unchanged.

## 3. E1 re-run results (R11P-01R) — §K FAIL

Clean-window counts are live counters minus the warm-up snapshot
(A base 0/0/4, B base 1382/0/1 valid/malformed/non-CSI).

| Check | Node A (`b0:3f…20:3c`) | Node B (`04:b2…1a:dc`) | §K |
|---|---|---|---|
| Clean valid / malformed | **0 / 0** (valid-pct undefined) | 6306 / 0 (100.0%) | **FAIL** (need ≥5000/node, ≥99%) |
| Clean gaps / dups / ooo | 0 / 0 / 0 (on zero records) | 0 / 0 / 0 | PASS (live) / PASS (file: A 0/0/0, B 0/0/0) |
| Duration | 60.589 s wall (shared window) | 60.589 s wall | PASS (60 ± 2 s) |
| 62 tones + finite I/Q | none (no records) | file: unanimous 62, 0 non-finite/bad of 7686 | **FAIL** (A) |
| RSSI live mean / file mean | — / — | −58.89 / −58.21 (file span −63…−52) | **FAIL** (A) |
| BSSID / channel | — (no records) | unanimous `8c:53:c3:5b:e1:59` / 1 | **FAIL** (A) |
| Host-ts / source state | age None / LIVE_UNVERIFIED, gate never evaluated | 0.0012 s fresh, not stale / LIVE_VERIFIED, gate passed, no storm | **FAIL** (A) |
| Sync | 0 offset observations | ready (jitter 168675 ns ≤ 2 ms) | **FAIL** (session UNSYNCED 52/52) |

## 4. Anomaly characterization (evidence, not repair)

Node A emitted zero `CSI_DATA` over the full 75.7 s session — only 25
non-CSI binary-garbage lines (35–64 KB LF-delimited chunks of control bytes,
no CSI framing). Its preserved file (466662 bytes) holds the same 25 chunks;
text-mode iteration over-splits embedded control bytes into 120 fragments,
so the live count (25) is authoritative. Node B opened with one 32 KB `&`
settle-transient line (counted, `pre_gate_storm: false`, gate passed) then
7686 clean valid records.

## 5. Evidence inventory (all Git-ignored, SHAs independently verified)

- Raw A: `research-data/rfvision-011-presence/trials/R11P-01R/R11P-01R_node-a_raw.bin`
  SHA-256 `d9ec9357203cac942135a6b877b837ac18c961470a59fc181de6fddf9df06073`
- Raw B: `research-data/rfvision-011-presence/trials/R11P-01R/R11P-01R_node-b_raw.bin`
  SHA-256 `ac4a9d63b1e3bfd3720659accea53b444c12fe492a83b4a0e1978dd5b11a91d4`
- Sidecar (valid JSON, verdict FAIL):
  `research-data/rfvision-011-presence/trials/R11P-01R/R11P-01R_sidecar.json`
- Full session telemetry:
  `research-data/rfvision-011-presence/trials/R11P-01R/R11P-01R_capture_stats.json`
- Scripts (tooling, not data): `/tmp/opencode/r11p_rerun.py`,
  `/tmp/opencode/r11p_revalidate.py`
- Quarantine intact: `research-data/rfvision-011-presence/trials/R11P-01/`
  still holds exactly its 4 original files, unmodified, NOT reused.

Tracked tree shows only the 2 pre-authorized Option B modifications
(`web/source.py`, `tests/unit/test_live_provider.py`); nothing else modified,
committed, or pushed.

## 6. Verdict

```text
E1_RERUN_FAIL — node A board (b0:3f:d3:70:20:3c, usb-0:5.4) emitted zero CSI_DATA over the full session (25 non-CSI garbage lines only); session UNSYNCED; §K count/validity/identity/sync gates fail
```

## 7. Decision required (human)

The blocker is a silent Node A board (hardware/runtime), not tooling or
protocol. Next step needs human authorization — e.g. inspect/re-seat/recover
board A, then authorize a further E1 attempt. No further capture, E2, or
recovery action was taken unilaterally.
