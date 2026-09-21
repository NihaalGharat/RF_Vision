# Digital twin — interface definition (scheduled work)

The twin consumes versioned events ONLY (`realtime/protocol/`):
`sensing.snapshot` (avatar state), `localization.update` (track),
`xai.explanation` (overlay), `system.status` (link health). Canonical
payloads: `docs/architecture/RFVISION_DATA_SCHEMA.md`; Unity contract:
`unity/integration/MESSAGE_FORMATS.md`.

No twin implementation exists in this foundation. When built, the twin
must render validation status alongside every claim (see claim policy)
and must never parse serial data directly.
