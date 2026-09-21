# Unity Project — scope for a later phase (foundation only)

This operation builds the Unity INTEGRATION FOUNDATION (message formats:
`unity/integration/MESSAGE_FORMATS.md`; event envelope:
`realtime/protocol/event_envelope.py`), not the 3D product.

Scheduled Unity phase (not started): 3D room matching `room_width/
room_length`, human avatar driven by `localization.update`, RF field
heatmap driven by `visualization/rf` data, digital-twin state sync via
`sensing.snapshot`, research dashboard + `xai.explanation` view.

Acceptance for that phase: Unity consumes ONLY the versioned envelope
(no ad-hoc serial parsing in C#); every rendered claim shows its
validation status from `docs/research/SCIENTIFIC_VALIDATION_STATUS.md`.
