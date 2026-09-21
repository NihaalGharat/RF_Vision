# Wire protocol notes

Firmware emits `CSI_DATA` text (classic 25-col; C5/C6 15-col variant
exists upstream but is out of scope for the D0WD-V3 baseline). Full column
spec + the three legacy/alternative formats: `csi/formats/WIRE_FORMATS.md`.
Host parsing: `csi/parser/esp_csv_adapter.py` → `CsiSample`; validation:
`csi/validation/validators.py`. Multi-node envelopes (MQTT grouping
pattern, studied from csi-sensing) belong to `realtime/protocol/` when
that package is built — serial-first, bridge later.
