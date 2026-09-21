# Wire Formats

## A. Validated baseline — esp-csi `csi_recv_router` (classic ESP32, 25 cols)

```
CSI_DATA,seq,mac,rssi,rate,sig_mode,mcs,bandwidth,smoothing,not_sounding,
aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,channel,
secondary_channel,local_timestamp,ant,sig_len,rx_state,len,
first_word_invalid,"[I0,R0,I1,R1,...]"
```

- `ets_printf` @ 921600 8N1. I/Q: even index = Imag(Q), odd = Real(I),
  signed int8, gain-compensated in firmware. HT20: `len=128` (64 slots).
- Quirk: header says `rx_format`, value is `sig_mode` (cosmetic).
- Parser: `csi/parser/esp_csv_adapter.py` (csv-split + JSON payload).

## B. Human-Sensing 2-board firmware — `#CSI {JSON}` @ 921600

Fields: `timestamp,seq,rssi,channel,secondary_channel,sig_mode,mcs,cwb,
rate,aggregation,stbc,fec_coding,sgi,noise_floor,ampdu_cnt,sig_len,
rx_state,ant,timestamp_wifi,mac,first_word_invalid,csi_len,csi:[int8…]`.
Parser: `csi/parser/csi_parser.py`. Status: reference alt-transport; the
proven path stays format A (adapter bridges A→`CsiSample`).

## C. ESP32-CSI-Tool legacy — 26-col `CSI_DATA,role,…,len,[b0 b1 …]`

Space-separated bracketed bytes, `len` 128 (LLTF) or 384 (merged LTF),
extra `role/real_time_set/real_timestamp` columns. Predates IDF-v5
`rx_ctrl`; **incompatible**, kept as `docs/reference/example_csi.csv`
specimen only. Note: its demo parser swaps I/Q labels (amplitude
unaffected, phase mirrored) — do not port that parser.

## D. csi-sensing MQTT grouping — `{CSI_DATA,…}` regex over broker payloads

Transport + subcarrier assumptions (192/114, amplitude-only `/15`) differ;
documented for study only (`docs/third_party/CSI_SENSING_STUDY_NOTES.md`).

## Ruling

Canonical parser: B's strict validator. Mandatory companion: adapter A.
No silent conversions: adapter + preprocessor expose
`rejected_total/rejection_reasons` and `length_unexpected` counters.
