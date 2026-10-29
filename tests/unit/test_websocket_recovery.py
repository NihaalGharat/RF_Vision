"""WS-1 — the browser client must recover after a long backend outage.

Runs the REAL websocket service through a Node driver with fake sockets and
timers. This reproduces the operator-visible failure where REST recovers but
the WebSocket stays disconnected forever after its retry budget expires.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
DRIVER = Path(__file__).with_name("websocket_recovery_driver.mjs")


def _node_bin():
    for cand in (
        os.environ.get("RFVISION_NODE_BIN"),
        shutil.which("node"),
        str(Path.home() / ".local" / "bin" / "node"),
        str(Path.home() / ".local" / "node-p3" / "bin" / "node"),
    ):
        if cand and Path(cand).exists():
            return cand
    return None


NODE = _node_bin()
needs_node = pytest.mark.skipif(
    NODE is None, reason="no Node.js runtime (RFVISION_NODE_BIN/PATH)"
)


@needs_node
def test_websocket_recovers_after_retry_budget():
    proc = subprocess.run(
        [NODE, str(DRIVER), str(REPO)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"driver failed: {proc.stderr[:2000]}"
    result = json.loads(proc.stdout)
    assert result["afterFailures"]["pendingTimers"] >= 1
    assert result["reconnected"] is True
    assert result["state"] == "connected"
