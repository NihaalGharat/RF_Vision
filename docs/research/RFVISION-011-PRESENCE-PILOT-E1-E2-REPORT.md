# RFVISION-011 Presence Pilot v1.0 — E1+E2 Phase Final Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, unmodified)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`, tracked tree clean
**Phase scope:** E1 + E2 (empty-room PRE) only. No P1, no analysis, no commit, no push.
**Report date (UTC):** 2026-09-23

## 1. Execution record

1. Reviewed capture stack (`web/dual_node.py`, `web/source.py` recording API,
   `csi/parser` validators). Wrote trial capture script (15 s warm-up pumped and
   discarded, 60 s clean window recorded, 1 Hz sync sampling) and offline file
   validator using the same stack parser as the live path.
2. Ran **E1 (R11P-01)**: 15.01 s warm-up + 60.033 s live clean window,
   2026-09-22T20:44:38.205+00:00 → 2026-09-22T20:45:38.238+00:00.
   Setup untouched between all steps; room empty; no disturbance or anomaly.
3. Validated E1 at live-counter level and at preserved-file level; SHA-256
   independently re-verified with `sha256sum`.
4. **E1 FAILED §K** (truncated raw) → per the execute order (validate E1 before
   starting E2), **E2 was not started**. Stopped. Nothing repaired, filtered,
   retried, or discarded.

## 2. E1 results (R11P-01, E1 Empty PRE) — §K FAIL

| Check | Node A (`b0:3f:d3:70:20:3c`, `usb-0:5.4`) | Node B (`04:b2:47:20:1a:dc`, `usb-0:1`) | §K |
|---|---|---|---|
| Live valid / malformed | 6173 / 0 (100.0%) | 5786 / 0 (100.0%) | PASS |
| Live gaps / dups / ooo | 0 / 0 / 0 | 0 / 0 / 0 | PASS |
| 62 tones + IQ finite (live and file) | 62 unanimous / all finite | 62 unanimous / all finite | PASS |
| RSSI live mean / file mean (min…max) | −57.95 / −58.41 (−63…−56) | −61.31 / −59.31 (−66…−56) | present |
| BSSID / channel | `8c:53:c3:5b:e1:59` unanimous / 1 | unanimous / 1 | PASS |
| Host-ts fresh / source state | 0.0016 s, not stale / LIVE_VERIFIED, gate passed | 0.1311 s, not stale / LIVE_VERIFIED, gate passed | PASS |
| Sync | SYNCED 60/60 samples (100%), final SYNCED | — | PASS |
| Storm / impossible throughput | none / false | none / false | PASS |
| **Preserved raw span** | **~30 s, 3354 records** | **~30 s, 2882 records** | **FAIL — requires 60 ± 2 s and ≥ 5000 records/node** |

File-level parse used the validated stack parser (`EspCsvAdapter.handle_line` +
`amplitude()`, mirroring the live path exactly): A 3354 parsed / 0 malformed,
B 2882 / 0, seq gaps/dups/ooo 0/0/0 both, MACs unanimous, channels unanimous,
IQ finite A 3354/3354, B 2882/2882.

## 3. E2 status (R11P-02) — NOT RUN

No data, no files, no setup change. No E1-vs-E2 comparison is possible.

## 4. Root cause of block

The app's hard recording cap `REC_MAX_SECONDS = 30.0` (`web/source.py:225`,
clamped by `min()` at `:533`) auto-stopped both raw recordings mid-window via
the `_record_raw` bounded auto-stop path. The live RF/hardware path stayed fully
healthy for the whole 60 s — this is a **recording-artifact failure, not a
signal failure**. Extending the cap requires modifying acquisition code, which
the execute order forbids; re-running under an altered procedure would be an
unauthorized retry. Both were declined unilaterally.

## 5. Evidence inventory (all Git-ignored, SHAs independently verified)

- Raw A: `research-data/rfvision-011-presence/trials/R11P-01/R11P-01_node-a_raw.bin`
  SHA-256 `f56a4857d9320a237a6a8092c71747ce175b6b6b358096668ada1fd30fe7b100`
- Raw B: `research-data/rfvision-011-presence/trials/R11P-01/R11P-01_node-b_raw.bin`
  SHA-256 `02936a0a327b220e51275b4ef687b6d4987c910b3ac5852a2a2d38c4b4bce05a`
- Sidecar (verdict FAIL, cause documented):
  `research-data/rfvision-011-presence/trials/R11P-01/R11P-01_sidecar.json`
- Full session telemetry:
  `research-data/rfvision-011-presence/trials/R11P-01/R11P-01_capture_stats.json`
- Scripts (tooling, not data): `/tmp/opencode/r11p_capture.py`, `/tmp/opencode/r11p_validate.py`

The truncated R11P-01 files are quarantined as evidence and are **not** a valid
trial; E1 must be re-run from scratch under an authorized fix and can never reuse
these files.

## 6. Verdict

```text
E1_E2_BLOCKED — E1 raw truncated at 30.0 s by app REC_MAX_SECONDS cap; fails §K duration/count gates; E2 not started
```

## 7. Decision required (human)

- **Option A:** Authorize a recording-procedure amendment (e.g. segmented capture)
  via protocol update, then re-run E1.
- **Option B:** Authorize raising/extending the 30 s recording cap in acquisition
  code, then re-run E1.
