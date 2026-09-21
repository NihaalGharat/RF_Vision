# Validated acquisition firmware — RF Vision provenance note

Upstream: Espressif esp-csi @ `8633d67152db2808f141cc1595970aa9cf406045`
(master, 2026-04-22), Apache-2.0. Directory vendored verbatim
(`firmware/esp32/csi_recv_router/` mirrors the upstream
`examples/get-started/csi_recv_router/` layout exactly).

Policy: this is the PROVEN acquisition path (ESP32-D0WD-V3 + Xiaomi Mi
Router 4C + ESP-IDF v5.4.4 + Ubuntu USB serial). Do NOT modify or replace
it because an alternative implementation exists elsewhere. Any alternative
firmware is an experimental candidate with its own migration plan — never
a silent replacement. See `docs/hardware/BASELINE.md`.
