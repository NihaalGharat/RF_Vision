# csi-sensing Study Notes (research notes — NO code reused)

Source: thkimKETI/csi-sensing @ `898f7f33` (KETI, custom view-only license).
Everything below is a factual design summary in our own words to inform
native RF Vision work. Copy nothing; thresholds/weights are not ours.

## Architecture facts (for `realtime/protocol` multi-node design)

- 1–2× ESP32-S3 → external MQTT broker → grouped payloads
  (`group_mac, group_ntp_millis, data_format, group_count` + concatenated
  `{CSI_DATA,…}` frames, regex-extracted per message).
- Multiprocessing: 1 MQTT subscriber + N per-node processors + 1 inference
  process + PyQt5 GUI; shared `180×114` double arrays + locks; ~1 Hz gated
  inference with threaded location/activity heads.

## Model shapes (for `ai/training` NN design)

- Window: 180 packets × 114 amplitudes (slices of a 192-amp vector).
- `TinyCSINet` (location): Conv2d(E→8, k3p1) + ReLU + AdaptiveAvgPool(10,10)
  + Dropout(0.25) + FC(800→classes).
- `TinyTransformerNet` (activity): Linear(180·114→128) + 1×
  TransformerEncoder(d128, 4 heads, ff256, dropout 0.25) + FC(128→classes).
- SVM fallback on flattened windows (20520/41040-d). Labels observed:
  location far/near (1-D) or left/right (2-D); activity Exercise/Sit/Stand/
  Walk + `EMPTY` heuristic (10-s mean foreground < 0.03).

## GUI pattern (for `visualization/rf` heatmap tab)

- 8 heatmaps (per-port raw viridis 0–1 + foreground coolwarm −1…1,
  time × carrier), Raw/Butterworth toggle, start/stop acquisition gate.

## Caveats (binding)

- Weights absent (Drive links); `1D_csi_sensing_svm.py` is corrupt machine
  code; NN scripts hardcode `cuda`; serial code dead; no training code, no
  splits, no metrics in repo. Validity rests on cited papers (CSI-Chain
  KSII TIIS 2026; ICSPIS 2024; BDCAT 2023), not on this repo. Any native
  re-implementation must be validated independently (see claim policy).
