# RF visualization

- `csi_viewer_reference.html` — Espressif's dependency-free Web Serial
  viewer (Apache-2.0, verbatim): open in Chromium/Edge, select the ESP32
  port @ 921600, live amplitude/phase/IQ. Header + subcarrier color tables
  here are the reference for the native RF tab.
- Native heatmap tab (time × carrier, studied from the csi-sensing GUI
  pattern) is scheduled work in `visualization/dashboard/`; interface
  contract: `docs/architecture/RFVISION_DATA_SCHEMA.md`.
