# RFVISION-011 — Node A Read-Only Diagnosis Final Report

**Protocol:** `RFVISION-011-PRESENCE-PILOT-v1.0.md` (FROZEN, unmodified)
**Baseline:** `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`
**Phase scope:** read-only / minimum-intervention diagnosis of Node A only,
after the failed E1 re-run (R11P-01R). No E1/E2/P1, no firmware change, no
reflash, no AP change, no baud/config change, no evidence modification,
no retry, Node B untouched except one passive read, no commit, no push.
**Trigger:** R11P-01R Node A emitted 0 CSI_DATA over ~75.7 s (25 non-CSI
binary-garbage chunks); Node B fully healthy (6306 clean valid, gate passed).
**Report date (UTC):** 2026-09-23

## 1. Node A identity confirmation

- `/dev/ttyUSB1` eFuse MAC: **`b0:3f:d3:70:20:3c`** — matches frozen Node A.
- `/dev/ttyUSB0` eFuse MAC: `04:b2:47:20:1a:dc` — Node B. No swap, no impostor.
- Transparency note: `esptool read_mac` (same read-only check used in all
  prior validations) performs an RTS hard-reset on open — both boards were
  reset by this step. No firmware, configuration, or evidence was modified.

## 2. USB topology / device mapping

- `/dev/serial/by-path`: `pci-…-usb-0:5.4 … → ../../ttyUSB1` (Node A),
  `pci-…-usb-0:1 … → ../../ttyUSB0` (Node B). Topology matches the frozen
  record; only kernel `ttyUSBn` numbering differs across boots (by design —
  identity follows by-path + board MAC per `csi/transport/nodes.py`).
- Both bridges: `10c4:ea60 Silicon Labs CP210x`, driver `cp210x`, USB serial
  `0001`/`0001` (identical, as documented — serials unusable for identity).
- Enumeration complete and unambiguous; both serial endpoints open cleanly
  with zero transport errors. No replug was needed to resolve identity.

## 3. Kernel/USB findings

- `dmesg` **unavailable** (`read kernel buffer failed: Operation not
  permitted` — container restriction). No kernel evidence for or against
  disconnects, resets, framing or I/O errors. Recorded as a limitation,
  not as "no errors".
- No other kernel-side signal was reachable; USB health is attested by
  stable by-path enumeration + error-free opens only.

## 4. Serial observation findings (existing 921600 config, passive reads)

All observations used the validated `SerialLineSource` (read-only: never
writes to the port) with scratch in `/tmp` only — never `research-data`.

- **Node A, first 8 s open** (immediately post-RTS-reset): 811 `CSI_DATA`
  (~101 Hz) + 70 ASCII tail fragments (`-8]"\r\n`) + 0 binary, 0 blank.
  Expected BSSID `8c:53:c3:5b:e1:59`, consecutive seqs (2754/2755/2756),
  RSSI −56…−57. Fragments = post-reset boot transient.
- **Node A, second 10 s open** (steady state): per-second CSI 99–150 with
  **0 other / 0 binary** (after 75 open-transient blanks in s+0). Replay
  through the real stack parser (`EspCsvAdapter.handle_line`, live-path
  semantics, no line reassembly): **1216 valid / 1 malformed / 0 non-CSI =
  99.92%**, gaps/dups/ooo **0/0/0**.
- Node A currently produces the expected application/CSI stream — not ROM
  output, not a boot loop, not garbage.

## 5. Comparison with Node B

- Node B (one 8 s passive read; configuration untouched): 859 `CSI_DATA`
  (~107 Hz), consecutive seqs (5501/5502/5503), RSSI −62, 1 binary settle
  line — matching its E1 re-run health and its single non-CSI line there.
- Post-recovery Node A now matches Node B's healthy signature (rate,
  framing, BSSID, sequence continuity).

## 6. Failed-E1 evidence still relevant (R11P-01R, untouched)

- Node A session totals: 0 valid / 0 malformed / 25 non-CSI; clean-window:
  0 valid, 21 non-CSI garbage lines; gate never evaluated; 0 sync
  observations → session UNSYNCED.
- Preserved file (466662 bytes, SHA-256
  `d9ec9357203cac942135a6b877b837ac18c961470a59fc181de6fddf9df06073`):
  25 LF-delimited binary-garbage chunks, 35–64 KB each (`\x0c`/`\x0e`
  control bytes, no CSI framing). A board that enumerates cleanly but emits
  huge unframed binary blobs is a crashed/stuck runtime UART state — not a
  dead board, broken cable, or wrong device.

## 7. Classification: B — ESP32 runtime/boot-state issue (confidence HIGH)

- For B: USB path and identity fully healthy; pre-reset output was unframed
  runtime garbage; post-reset output is correct application CSI at the
  expected rate passing the real parser at 99.92%; prior valid acquisitions
  prove the hardware/firmware combination works.
- Against A (USB/enumeration): enumeration stable and unambiguous.
- Against C (firmware/application state): firmware runs and frames correctly
  post-reset — reflash would fix nothing. **Reflash NOT warranted.**
- Against D (serial-path/configuration): baud/config never changed, and the
  identical configuration now yields clean data.
- Against E (hardware fault): no fault signature survives the reset.

## 8. Recommended next action (single)

Physically reseat + power-cycle Node A (an RTS reset is not a full
power-cycle; only a power-cycle rules out a marginal-power brownout as the
crash cause), then human GO for a fresh E1 attempt. No recovery action was
taken beyond the resets implicit in the read-only identity check; E1 was
not retried.

## 9. Verdict

```text
NODE_A_DIAGNOSIS_COMPLETE — PHYSICAL RESEAT/POWER-CYCLE RECOMMENDED
```
