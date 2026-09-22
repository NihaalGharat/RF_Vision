#!/usr/bin/env bash
# RF Vision web console launcher (RFVISION-011).
# Starts the existing stdlib console (web/server.py) on 127.0.0.1:8130.
# Local-only. No Node/npm. No architecture changes.
set -u

PORT="${1:-8130}"

case "$PORT" in
    -h|--help|help)
        echo "Usage: ./tools/run_rfvision_ui.sh [port]"
        echo "Starts the RF Vision web console (local-only) on 127.0.0.1:<port> (default 8130)."
        echo "Env: RFVISION_PYTHON=/path/to/python3 to override the interpreter."
        exit 0
        ;;
esac

# Resolve repository root robustly (script lives in <root>/tools/).
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

if [ ! -f "$REPO_ROOT/web/server.py" ]; then
    echo "ERROR: cannot find web/server.py under $REPO_ROOT" >&2
    exit 1
fi

# Fail cleanly if the port is already occupied (do not start duplicates).
if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") >/dev/null 2>&1; then
    exec 3>&- 3<&-
    echo "RF Vision UI is already running at http://127.0.0.1:$PORT/"
    echo "Refusing to start a duplicate server."
    exit 0
fi

# Deterministic RF Vision interpreter (RFVISION-012).
# The repo has no venv: dependencies live in the system Python's user
# site (~/.local/lib/python3.14/site-packages). A bare `python3` is
# PATH-dependent and resolves to the ESP-IDF virtualenv in any shell
# where export.sh ran — that env has no numpy. Pin system Python so
# the launcher is immune to IDF PATH shadowing. Override with
# RFVISION_PYTHON=/path/to/python3 if ever needed.
PY="${RFVISION_PYTHON:-/usr/bin/python3}"

if [ ! -x "$PY" ]; then
    echo "ERROR: RF Vision Python not found/executable: $PY" >&2
    echo "Set RFVISION_PYTHON to a Python 3 with the requirements-base.txt stack." >&2
    exit 1
fi

# Fail fast with a clear message if the dependency stack is missing
# (do not let the server die later with a bare ModuleNotFoundError).
if ! "$PY" -c "import numpy" 2>/dev/null; then
    echo "ERROR: $PY cannot import numpy." >&2
    echo "Install the stack: $PY -m pip install -r \"$REPO_ROOT/requirements-base.txt\"" >&2
    exit 1
fi

cd -- "$REPO_ROOT" || exit 1

echo "RF Vision Python: $PY"
echo "RF Vision UI starting..."
echo "URL: http://127.0.0.1:$PORT/"
echo "RF Vision UI: http://127.0.0.1:$PORT/"
exec "$PY" -u -m web.server --port "$PORT"
