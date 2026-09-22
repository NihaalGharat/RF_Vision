# RF Vision Development Environment (RFVISION-011)

Ubuntu 26.04.1 LTS, kernel 7.0.0-31-generic, x86_64.
Login user is in the `dialout` and `sudo` groups (serial + admin access).

## Python

- `python3` = Python 3.14.4 (`/usr/bin/python3`), pip 26.2.1
- RF stack (verified): numpy, scipy, pandas, matplotlib, scikit-learn,
  pytest, pyserial, websockets (`requirements-base.txt`)
- Future ML (torch/captum/OpenCV) not installed; not required by the
  current console
- Confirmed RF Vision interpreter: `/usr/bin/python3` with user-site
  packages (`~/.local/lib/python3.14/site-packages`). No venv.
  `tools/run_rfvision_ui.sh` pins this interpreter (override:
  `RFVISION_PYTHON=...`) and intentionally ignores the ESP-IDF
  virtualenv even when `export.sh` shadows `python3` on PATH.

## Git

- Git 2.53.0, user-local at `$HOME/.local/gitroot/usr/bin/git`
- `~/.bashrc` prepends that directory to `PATH` (idempotent block,
  tagged RFVISION-011), so `git` works in a normal interactive shell
- Local repo identity configured (`git config --local`); global
  identity intentionally unset

## GitHub CLI + authentication

- `gh` installed from the official GitHub CLI apt repository
- Auth method: **GitHub CLI + HTTPS credential helper**
  (`gh auth login --web --git-protocol https`, then `gh auth setup-git`)
- No tokens, passwords, or SSH keys are stored in chat, docs, or git

## Git remote

- Remote `origin`: `https://github.com/OWNER/REPO.git`
  (exact value recorded in `/tmp/rfvision-011-setup-report.md`;
  HTTPS only, never SSH)
- Read-only verification: `git ls-remote origin HEAD`
- Workflow: `git status --short --branch`, `git pull --ff-only`,
  `git push` (never `--force`, never rebase `main`)

## ESP-IDF v5.4.4 (pinned, validated baseline)

- `$HOME/esp/esp-idf` @ `296b6eab9445fd720e71aecab961e2d3fbca9944`
  (`git describe` → `v5.4.4`). Do NOT upgrade.
- Host build deps (apt): git wget flex bison gperf ccache gcc g++
  make cmake ninja-build python3 python3-pip python3-venv libffi-dev
  libssl-dev dfu-util libusb-1.0-0 pkg-config
- `~/.bashrc` sources `$HOME/esp/esp-idf/export.sh` (idempotent,
  tagged RFVISION-011); fresh shell gives `IDF_PATH=.../esp/esp-idf`,
  `idf.py --version` → `ESP-IDF v5.4.4`
- Xtensa toolchain: `~/.espressif/tools/xtensa-esp-elf/
  esp-14.2.0_20260121/.../xtensa-esp32-elf-gcc` (crosstool-NG 14.2.0);
  bundled cmake 3.30.2, ninja 1.12.1
- Firmware project: `firmware/esp32/csi_recv_router/`
  (`idf.py build` only; NEVER `flash`/`erase-flash` without a
  separate explicit approval; build outputs are git-ignored)

## Browser

- Google Chrome 153 (primary). No extensions required.

## RF Vision web UI (local-only)

- Architecture (unchanged, RFVISION-009): Python stdlib `http.server`
  + hand-rolled WebSocket + vendored Three.js r160. No React/Next/
  FastAPI/Node/Electron/Docker.
- Binds **127.0.0.1 only**, port **8130**. Never `0.0.0.0`/LAN/public
  without separate approval.
- Launch from the repository root: `./tools/run_rfvision_ui.sh [port]`
- URL: `http://127.0.0.1:8130/` (also `http://localhost:8130/`)
- Health check: `python3 -c "import urllib.request;
  print(urllib.request.urlopen(
  'http://127.0.0.1:8130/', timeout=10).status)"` → `200`
- Tests: `python3 -m pytest tests/ -q` (baseline: 128 passed)

## Secrets policy

`.gitignore` excludes `.env`, `*password*`, `*secret*`, `*token*`,
`*.pem`, raw data (`data/`, `*.csv`, `*.bin`), firmware build outputs,
and research binaries. RFVISION-009 screenshots stay out of git
(`/tmp` only; currently unavailable after reboot — INCONCLUSIVE).
