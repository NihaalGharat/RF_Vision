# Traffic-generator reference (NOT the default path)

Upstream: ESP32-WiFi-CSI-Human-Sensing `firmware/esp32_ap/` (MIT),
verbatim. A softAP beacon source (`CSI_SENSOR`, HT20, UDP echo :8765) for
the OPTIONAL two-board Arduino experiments only.

The validated default remains `firmware/esp32/csi_recv_router/` (single
ESP32 + Xiaomi router + ESP-IDF v5.4.4). Building this `.ino` requires the
Arduino-ESP32 core and an explicit experimental decision — never a silent
replacement. Rotate the `CSI_SENSOR`/`change_this` placeholders on first
use; no credentials are committed.
