"""Pytest bootstrap: put the project root on ``sys.path``.

RF Vision uses a flat research layout (``csi/``, ``signal/``, ... at the
root), so tests import absolute package paths like ``csi.parser``. This
conftest makes that work regardless of the invocation directory.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
