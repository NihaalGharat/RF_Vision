# RFVISION-003R-B — Serial-Path Check Report

Operation: RFVISION-003R-B. No flash, no erase, no write, no reset
(esptool NOT used — its sync toggles reset lines), no firmware/router
changes, no 60 s capture, no experiments, no code modified. Plain
pyserial opens + timed reads only.

**STATUS: FAIL** — baud-independent fixed-pattern garbage at impossible
throughput persists; no readable UART output. **003R-C flash is NOT
ready** (a flash cannot be verified through a path that cannot carry
UART).

## 1. Board identity (NEW physical receiver — NOT the historical board)

- ESP32-D0WD-V3 rev 3.1, 40 MHz, 4 MB flash (per 003R-A esptool reads).
- MAC: `b0:3f:d3:70:20:3c` — labeled NEW receiver; historical validated
  board MAC `f4:65:0b:56:0e:18` does not match (003R-A §1.5).
- Firmware aboard: ESP-AT v2.3.0.0 (2022-05-20), proven by 003R-A flash
  reads — cannot emit CSI, but AT *should* emit readable text at 115200.
- Bridge: CP2102 s/n `0001` → `/dev/ttyUSB0` (`crw-rw-rw- root dialout`).

## 2. Cable/port tested

- **Steps 3–4 NOT PERFORMED — no physical access from this console.**
  USB topology is FROZEN since Sep 21 20:35:28: Bus 003 Port 005 Dev 006,
  cp210x driver, 12M full-speed (identical descriptors in 003R-A and now;
  zero re-enumerations in the kernel log). No cable swap, no second port,
  no hub change occurred or could be performed. This is now THE gating
  item (see §6).

## 3. USB/CP2102 status

- `lsusb -d 10c4:ea60 -v`: 10c4:ea60, "CP2102 USB to UART Bridge
  Controller", s/n 0001, bcdDevice 1.00 — HEALTHY enumeration.
- Port holders (`/proc` fd scan): NONE — port free, no contention.
- One transient empty `lsusb -d` output observed (immediately re-queried
  OK); apparmor snap-confinement noise around the querying process, not
  the device. Non-finding, recorded for completeness.

## 4. Serial results (steps 6–7)

4 s binary-safe captures, back-to-back, plain reads:

| Baud | Bytes | Rate | NL/CR | Distinct | Content |
|---|---|---|---|---|---|
| 115200 | 520,192 | 130,048 B/s | 0/0 | 2 (`00`:346,795 `80`:173,397) | `0080` repeat, no ASCII |
| 921600 | 520,192 | 130,048 B/s | 0/0 | 2 (identical counts) | **byte-identical file** |

- FAIL on all three criteria: output is NOT readable, NOT
  baud-dependent (bit-identical across an 8× baud change), and throughput
  is impossible (130 kB/s through a 115200-baud ≈11.5 kB/s line).
- Same anomaly CLASS as 003 (12-symbol family, ~951 kB/s) and 003R-A
  (00/80, ~134 kB/s): state-dependent alphabet, baud-independent,
  always super-line-rate. A UART transmitter cannot produce this; the
  bytes originate at/below the bridge-driver layer (stuck/break/framing
  artifact or bridge/host-driver fault — electrical root needs hands).
- Stored (volatile, outside git): `/tmp/rfv-003rb-115200.bin`,
  `/tmp/rfv-003rb-921600.bin`.

## 5. Logs/errors (step 5)

- `dmesg` direct read: `Operation not permitted` (confinement).
- `journalctl -k` (works): CP2102 attached cleanly Sep 21 20:35:28
  (`cp210x converter detected`, `now attached to ttyUSB0`) after a benign
  disconnect of the previous Dev 005 (a mouse receiver) — normal
  enumeration, not an error. **Zero USB errors, zero re-enumerations
  since.** The single `error|fail|disconnect` grep hit is that benign
  disconnect line.
- ModemManager probed `usb3/3-5` once (Sep 21 23:27, "not supported by
  any plugin", no claim) — residual non-interference note only.
- Verdict: USB transport layer is clean; the garbage appears above USB
  packet transport (UART framing/bridge/host-serial layer).

## 6. Verdict

- **FAIL.** The path cannot carry UART today: flashing `csi_recv_router`
  now would produce an unverifiable board (no readable boot text could be
  observed) and risk misattributing path garbage to the new firmware.
- **003R-C firmware flash: NOT READY.** Prerequisites, in order:
  1. USER (hands): move the board to a short, quality USB DATA cable on
     a direct motherboard port (no hub); confirm re-enumeration
     (`journalctl -k | grep cp210x` shows a new timestamp + device no.).
  2. 003R-B2 (my side, same read-only protocol): 4 s captures must show
     READABLE, BAUD-DEPENDENT text (AT `ready`/echoes at 115200) with
     plausible rates before any flash is approved.
  3. Only then: explicit 003R-C WRITE approval to flash pinned
     `csi_recv_router` (esp-csi `8633d671`).
- Open threads for the user: adjudicate the MAC mismatch (which unit is
  the true baseline board?); keep the historical `f4:65:0b…` unit out of
  the loop until identified.

Then STOP — awaiting (a) physical cable/port remediation + (b) explicit
003R-C approval. No further action taken.
