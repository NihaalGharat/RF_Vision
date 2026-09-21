"""RF Vision web-interface package (RFVISION-005).

Stdlib-only HTTP + WebSocket console backend (``web/server.py``) serving
the dependency-free frontend in ``web/static/``. Data enters exclusively
through ``web/source.py`` providers and leaves through ``web/contracts.py``
payloads — UI components never touch serial parsing.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
