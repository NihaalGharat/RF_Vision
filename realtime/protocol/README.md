# Realtime protocol (single-node v1 + multi-node hook)

Implemented: `realtime/protocol/event_envelope.py` — versioned JSON
envelope (`schema: 1`), five event types, stdlib-only, unit-tested.

Scheduled: transport binding (serial bridge → MQTT/WebSocket broker),
multi-node envelope (studied pattern: grouped `{CSI_DATA}` + per-node
queues + shared window arrays — see
`docs/third_party/CSI_SENSING_STUDY_NOTES.md`), NTP-disciplined sync with
`localization/synchronization`. Serial-first, bridge later; the envelope
is transport-agnostic by design.
