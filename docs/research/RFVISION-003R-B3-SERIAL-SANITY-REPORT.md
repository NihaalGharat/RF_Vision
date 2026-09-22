# RFVISION-003R-B3 — Serial Sanity Re-run Report (B2 unblocked)

Operation: RFVISION-003R-B3 (B2 rerun after the user's permission fix).
No esptool, no reset, no flash/erase/write, no firmware/router changes,
no CSI capture, no experiments, no code modified. Timed pyserial reads
only. `sudo -n -g dialout` was used SOLELY as a group context to open
the port for reading (user is in `dialout` per `/etc/group`; my shell
carried stale groups) — nothing was modified.

**STATUS: FAIL** — new cable + new port did NOT fix the path.
**003R-C NOT READY.**

## 1–4. Enumeration / port / holders / kernel — HEALTHY

- CP2102 s/n 0001 re-enumerated AGAIN Sep 22 00:54:35, now `usb 3-1`
  (Port 001 Dev 006; prior B2 state was Port 002 Dev 005) — the user moved
  ports between B2 and B3. Clean attach, zero USB errors.
- `/dev/ttyUSB0` (`crw-rw---- root dialout`), holders: NONE.
- Permission path: node still 660, operator now in `dialout` (persistent
  fix confirmed via `getent group dialout`); session shells need re-login
  to inherit it — operational note, not a defect.

## 5–9. Captures — FAIL on every criterion

4 s binary-safe captures, back-to-back:

| Baud | Bytes | Rate | Line cap | NL/CR | Distinct | Readable? |
|---|---|---|---|---|---|---|
| 115200 | 3,801,088 | 950,272 B/s | ~11,500 B/s (**82× over**) | 0/0 | 12 | NO |
| 921600 | 3,796,992 | 949,248 B/s | ~115,200 B/s (**8× over**) | 0/0 | 12 | NO |

- Rates are effectively IDENTICAL (950 vs 949 kB/s) across an 8× baud
  change — baud-independent throughput, physically impossible for a UART
  transmitter. (Files differ byte-wise this time, but share the family:
  12 symbols, zero newlines, ~950 kB/s — the exact signature of the
  original 003 capture, ~951 kB/s / 12 symbols.)
- No AT text: the board was power-cycled by two replugs and never once
  printed readable boot text (`ready` expected at 115200) in any session.
- Stored (volatile): `/tmp/rfv-003rb3-115200.bin` (`6b0b5e…`),
  `/tmp/rfv-003rb3-921600.bin` (`cfe938…`).

## Verdict

- **FAIL — 003R-C NOT READY.** The cable/port hypothesis is now
  EXCLUDED: two ports + known-good data cable (enumeration proves data
  lines) + zero USB errors, yet identical impossible garbage. Remaining
  suspects, in order: (1) the devkit board itself (CP2102 bridge or ESP32
  TX/firmware state — AT never speaks even at boot); (2) host-side USB
  serial driver delivering bulk garbage for an unclocked line; (3) cable
  still suspect only if "known-good" was never validated for data.
- Next physical steps for the user (pick any): try a USB2 vs USB3 port
  / different machine; re-validate the cable carries data on another
  device; try a SECOND ESP32 board (also answers the open MAC-mismatch
  question: `b0:3f:d3:70:20:3c` vs historical `f4:65:0b:56:0e:18`).
- Then STOP — awaiting remediation + explicit 003R-C WRITE approval.
