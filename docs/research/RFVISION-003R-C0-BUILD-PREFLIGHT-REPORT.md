# RFVISION-003R-C0 — CSI Firmware Build Preflight Report

Operation: RFVISION-003R-C0 (build/flash preparation ONLY). Target board:
ESP32-D0WD-V3 Rev 3.1, MAC `b0:3f:d3:70:20:3c` (NEW board — never
relabelled as historical `f4:65:0b:56:0e:18`), 4 MB flash, CP2102
`/dev/ttyUSB0`.

**Final status: BUILD READY FOR FLASH.**

No flash/erase/write/reset of the ESP32 was performed. No router
changes. No CSI capture. No experiments. No architecture changes. No
credentials exist anywhere in this operation (placeholders only —
verified). No sudo was used; the entire toolchain lives in user space.

## 1. Toolchain installation / status

- Host: Ubuntu 26.04.1 LTS, kernel 7.0.0-31-generic, Python 3.14.4.
  Disk had 122 GB free; ample.
- Pre-existing state: NO `idf.py`, NO system cmake/ninja/git(https);
  only host python3 + a git without its https helper. Everything below
  was installed fresh by this operation.
- ESP-IDF installed at `~/esp/esp-idf` (outside the repo — toolchain,
  not project code): shallow clone (`--depth 1 --branch v5.4.4
  --recurse-submodules --shallow-submodules`), HEAD verified
  **`296b6eab9445fd720e71aecb961e2d3fbca9944`** — exact match to the
  validated baseline (peeled `refs/tags/v5.4.4^{}` confirms the tag
  resolves to this commit).
- Tools in `~/.espressif`: xtensa-esp-elf-gcc
  `esp-14.2.0_20260121` (14.2.0), cmake 3.30.2, ninja 1.12.1, esptool
  4.12.0 (in IDF venv), full IDF python env
  (`idf5.4_py3.14_env`, requirements.core installed).
- Workarounds required (all documented, none touch the project):
  1. gitroot git lacked its https helper → `GIT_EXEC_PATH` pointed at
     its own `lib/git-core`; then GitHub reachable, clone OK.
  2. `python3.14-venv` absent and apt needs a password → created the
     IDF venv with the PyPI `virtualenv` package (bundled pip, no
     ensurepip needed); `install.sh` detected and reused it (pip +
     curses checks passed) and installed all requirements itself.
  3. `install.sh` (even unfiltered) skipped cmake+ninja → installed via
     `idf_tools.py install cmake ninja` explicitly.

## 2/3. ESP-IDF version / ESP-CSI commit / target

- ESP-IDF v5.4.4 @ `296b6eab…` ✓ (see §1).
- ESP-CSI @ `8633d67152db2808f141cc1595970aa9cf406045`: commit verified
  to exist upstream; the vendored tree
  (`firmware/esp32/csi_recv_router/`) was diffed file-by-file against
  `git archive` of that commit's `examples/get-started/csi_recv_router`
  — **identical except our added `README_RFVISION.md`**. Verbatim
  provenance proven, not assumed. Neither commit was changed.
- Target: `esp32` (`idf.py set-target esp32`; `CONFIG_IDF_TARGET="esp32"`).

## 4/5. Configuration (Wi-Fi/CSI, credentials audit)

From `sdkconfig.defaults` + generated `sdkconfig` (gitignored, stays
local — never committed):
- `CONFIG_ESP32_WIFI_CSI_ENABLED=y`, console UART0 @
  `CONFIG_CONSOLE_UART_BAUDRATE=921600` (matches the 003-era validated
  capture baud), CPU 240 MHz, AMPDU TX/RX disabled, FreeRTOS 1 kHz,
  flash `dio / 40m / 2MB` header.
- App logic (`app_main.c`): ping-the-gateway stimulus
  (`interval = 1000/100` ms, target = gateway IP) + `CSI_DATA,…`
  schema in both legacy and extended-header forms — the schema the RF
  Vision `EspCsvAdapter` parses (paper-verified in B4).
- Managed deps from the Espressif registry: `esp_csi_gain_ctrl 0.1.5`
  (+ `cmake_utilities 0.5.3`), pinned in `dependencies.lock`.
- **Credentials: `CONFIG_EXAMPLE_WIFI_SSID="myssid"`,
  `CONFIG_EXAMPLE_WIFI_PASSWORD="mypassword"` — placeholders.** No real
  SSID/password exists in the repo, the build dir, or this report. Real
  credentials must be injected at flash-config time by the NEXT
  operation (via menuconfig, never committed).

## 6/7/8. Build result + binaries + SHA-256 + offsets

`idf.py build` → **SUCCESS `[1008/1008]`**, `Project commit: v5.4.4`.
App binary `0xb4b20` B with 29 % free in the 1 MB factory partition;
bootloader `0x65c0` B with 9 % free. (`git_describe` ran against the
repo history without tags — cosmetic only, build unaffected.)

| File | Size | SHA-256 | Flash offset |
|---|---|---|---|
| `build/bootloader/bootloader.bin` | 26,048 B | `63232ae348b0000277a0c686769dee9db5bc03139d41f534bc5499dfbeff8500` | `0x1000` |
| `build/partition_table/partition-table.bin` | 3,072 B | `7f00b6c042a89b15b0cac534f82ed988caf29278ff5700b0c511eb1b5bb7c820` | `0x8000` |
| `build/csi_recv_router.bin` | 740,128 B | `c61e978e4ec28dcd168ffeb3a2967adec7646ed6001184cfd40e3087f16adee9` | `0x10000` |

Offsets are authoritative per `build/flasher_args.json`
(`dio/2MB/40m`, `before default_reset, after hard_reset, stub true,
chip esp32`).

## 9. 4 MB compatibility — COMPATIBLE

Partition map: `nvs @0x9000 (24K) / phy_init @0xF000 (4K) /
factory @0x10000 (1 MB)`; highest used offset `0x110000` (1.06 MB) —
fits the 2 MB image header AND the 4 MB silicon with 2.94 MB spare.
The 2 MB header on a 4 MB chip is benign (upper flash simply unused).
Recommendation: flash these exact artifacts as-is (byte-exact validated
build); do NOT rebuild for a 4 MB header — it would change the
bootloader without benefit.

## 10. Exact flash plan for the next operation (NOT executed)

Preconditions: `/dev/ttyUSB0` present, no holders, CP2102 enumerated,
operator in `dialout` (persistent fix from B3 is in place); then inject
the real router SSID/password via `idf.py menuconfig`
(`Example Connection Configuration` — never commit, never print), and
run from `firmware/esp32/csi_recv_router/` with the IDF export active:

```
python -m esptool --chip esp32 -b 460800 --before default_reset --after hard_reset \
  write_flash --flash_mode dio --flash_size 2MB --flash_freq 40m \
  0x1000 build/bootloader/bootloader.bin \
  0x8000 build/partition_table/partition-table.bin \
  0x10000 build/csi_recv_router.bin
```

(equivalently `idf.py -p /dev/ttyUSB0 flash`, same `flasher_args.json`).
Post-flash (next op): expect readable boot + `CSI_DATA` at 921600;
record new-board MAC + build identity before any capture.

## 11/12. Risks + unresolved items

- Python 3.14 is newer than IDF v5.4.4's tested range — the build
  succeeded, but keep this in mind if any future IDF-side Python error
  appears; fix is `python3.14-venv` via apt (needs user password).
- Shallow IDF clone (no full history) — build-unaffecting; re-clone
  full if git archaeology inside IDF is ever needed.
- B-series serial garbage (~950 kB/s) never reproduced in B4 but never
  explained — first post-flash boot output must be inspected for
  readability before trusting any capture.
- `managed_components/` + `dependencies.lock` are untracked regenerable
  artifacts (recreated by any build); `build/` + `sdkconfig` are
  gitignored per repo `.gitignore` — the repo tree holds zero build
  residue in versioned files.
- Unresolved / deferred to the flash operation: real Wi-Fi credential
  injection; post-flash boot verification; 10 s CSI trial (Phase E).
  OTA partitions are absent (upstream example default: factory only) —
  future OTA updates would need a table change + rebuild; out of scope.
