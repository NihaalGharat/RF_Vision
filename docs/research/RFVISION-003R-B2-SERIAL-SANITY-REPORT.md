# RFVISION-003R-B2 — Serial Sanity Report

Operation: RFVISION-003R-B2. No esptool, no reset, no flash/erase/write,
no firmware/router changes, no CSI capture, no experiments, no code
modified. Read-only inspection only — the planned 4 s captures could NOT
be executed (permission block, §4).

**STATUS: INCONCLUSIVE (BLOCKED)** — neither PASS nor FAIL criteria can
be evaluated yet. The physical move itself verified clean; one
user-side command unblocks the retest. **003R-C NOT READY.**

## 1–4. Enumeration / port / holders / kernel log — all HEALTHY

- CP2102 re-enumerated on the NEW port: `usb 3-2`, s/n 0001, driver
  cp210x, clean attach Sep 22 00:48:49 (`converter detected`, `now
  attached to ttyUSB0`). Old identity (Bus 003 Port 005 Dev 006) is gone;
  new identity Port 002 Dev 005. **The user's physical move is confirmed
  in the kernel log.**
- `/dev/ttyUSB0` exists, fresh timestamp 00:48, holders: NONE (port free).
- USB errors on the new port: ZERO (targeted grep over `journalctl -k`;
  `dmesg` direct still denied by confinement, journal path used as in B).
- Board identity unchanged: ESP32-D0WD-V3 rev 3.1, MAC
  `b0:3f:d3:70:20:3c` (NEW receiver, not the historical
  `f4:65:0b:56:0e:18` board), ESP-AT v2.3.0.0 aboard.

## 5–9. Captures — NOT EXECUTED (blocker)

- Re-enumeration reset the device node to `crw-rw---- root dialout`,
  wiping the session-only `chmod 666` from the 003 era. Operator
  `nihaal-gharat` is NOT in `dialout` → `PermissionError: [Errno 13]` on
  open at 115200. Bytes/s, newline/ASCII presence, and baud-dependence
  are therefore UNMEASURED — no PASS/FAIL verdict on the UART stream is
  possible, and inventing one would be fabrication.
- I deliberately did NOT change the permission myself: device access
  policy is the user's call (precedent: user ran the 003-era chmod via
  sudo explicitly).

## Verdict

- **INCONCLUSIVE — 003R-C NOT READY.**
- Remaining issue is NOT the cable/port anymore (that half is verified
  good: clean enumeration, zero errors) but **serial-port permission**:
  user, please run ONE of (a) `sudo chmod 666 /dev/ttyUSB0` (session-only,
  must repeat after every replug) or (b) `sudo usermod -aG dialout
  nihaal-gharat` + re-login (persistent, recommended), then tell me to run
  003R-B3: the same 4 s 115200/921600 read-only comparison. Note the
  replug power-cycled the board, so any AT boot text is long gone — B3
  will judge purely on readability / baud-dependence / plausible rate.
- No other action taken. Then STOP — awaiting (a) the permission fix +
  (b) explicit 003R-C WRITE approval, separately.
