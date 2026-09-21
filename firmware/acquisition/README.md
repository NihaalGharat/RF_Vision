# Acquisition notes (validated path)

Host side of the proven link: `csi/capture/serial_receiver.py`
(threaded reader + `RawSessionWriter` lossless CSV) or `tools/csi_record.py`
(headless raw recorder). Link params: `csi/transport/serial_config.py`
(921600 8N1, `/dev/ttyUSB0`, reconnect 2 s, offline after 3 s).

Firmware is NOT built from here (build in ESP-IDF v5.4.4 per
`firmware/esp32/csi_recv_router/README.md`); this directory documents the
host half. No flashing, no capture, and no live experiments are part of
foundation work.
