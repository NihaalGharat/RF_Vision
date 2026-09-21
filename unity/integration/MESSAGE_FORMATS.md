# Unity Integration — Message Formats (foundation)

Unity side implements against the versioned JSON event envelope
(`realtime/protocol/event_envelope.py`, schema v1). Transport binding
(serial bridge → MQTT/WebSocket) is scheduled work; THESE formats are the
contract both sides code to.

## `sensing.snapshot` payload

```json
{"presence": "PERSON", "presence_prob": 0.87,
 "movement": "MOVING", "movement_prob": 0.72,
 "position": 0.42, "position_m": 2.1, "confidence": 0.87}
```
`position`/`position_m` null when EMPTY or model-free.

## `localization.update` payload

```json
{"position": 0.42, "position_m": 2.1, "raw": 0.45,
 "frame": "link-1d", "room_width_m": 5.0}
```
`frame` is `"link-1d"` until 2-D/3-D schemas are defined (reserved).

## `xai.explanation` payload

`{"method": "rf_impurity"|"permutation", "caveats": "...",
"scores": {"sub_mean_12": 0.03, ...}, "top_k": [...]}` — comparative,
never causal; Unity must render the caveat wherever scores are shown.

## `system.status` / `system.log`

```json
{"connection": "ONLINE", "csi_rate": 98.5, "packets": 1204,
 "malformed": 3, "latency_ms": 4.2, "model": "knn"}
```

## Unity project scope (this operation: foundation only)

`unity/project/` defines scope and acceptance for a LATER phase: 3D room,
human avatar, RF field + localization overlays, twin state sync, research
dashboard, XAI view. No scenes, assets, or packages are created here.
