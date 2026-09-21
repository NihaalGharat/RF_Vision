# Three.js Version Pin (RFVISION-005)

- Version: **r160** (`REVISION = '160'`), MIT License
  (© 2010–2023 Three.js Authors, SPDX-License-Identifier: MIT —
  header retained in the vendored file).
- Files (vendored, no CDN, no npm):
  - `web/static/vendor/three.module.js` (1,272,972 bytes, `three@0.160.0`
    build target, fetched from unpkg 2026-09-21)
  - `web/static/vendor/OrbitControls.js` (29,868 bytes, matching
    `three@0.160.0` `examples/jsm/controls/`, fetched from unpkg
    2026-09-21)
- Import map (`web/static/index.html`): `"three"` →
  `/static/vendor/three.module.js`, `"three/addons/"` → `/static/vendor/`.
- Exactly ONE version is used. RuView's fragmentation (r128 UMD +
  0.160.0 importmap + r165 + npm 0.183.2 across pages) is explicitly
  rejected as the anti-pattern. Upgrading means replacing both vendored
  files together and re-running `tests/integration/test_web_server.py`
  (which asserts `REVISION = '160'`) plus a headless render check.
