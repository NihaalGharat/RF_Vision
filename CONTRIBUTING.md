# Contributing to RF Vision

Research-grade contributions only. Read these first:

- `docs/research/SCIENTIFIC_VALIDATION_STATUS.md` — claim policy (binding)
- `docs/third_party/SOURCE_PROVENANCE.md` — where third-party code came from
- `THIRD_PARTY_NOTICES.md` — attribution requirements (never remove notices)

## Rules

1. **No new sensing/localization/XAI claims** without an experiment protocol
   in `experiments/protocols/`, session-split evaluation, and an entry in
   `docs/research/SCIENTIFIC_VALIDATION_STATUS.md`.
2. **Raw CSI is immutable.** Never commit raw captures to git; never modify
   authoritative raw files. Derived datasets carry source + transform +
   software version + config + checksum + timestamp.
3. **One implementation per capability.** Check the architecture doc before
   adding a second parser/filter/trainer — deduplication is project policy.
4. **Provenance on every third-party edit.** Modified upstream files keep
   their license headers and get a `CHANGES` note in SOURCE_PROVENANCE.md.
5. **License gate.** No GPL/copyleft, no unclear licenses, no
   view-only-licensed code (cf. csi-sensing exclusion). Ask before importing.
6. **Tests first for pipeline code.** Parser, validation, dsp, schema,
   protocol, and config changes need unit/integration coverage
   (`python3 -m pytest tests/ -q`). Synthetic fixtures preferred; real-CSI
   fixtures only as committed test vectors, never bulk data.
7. **No credentials, no secrets, no Wi-Fi passwords** in code, configs, or
   docs. Placeholders only (rotate any leaked value immediately).
8. **Hardware scope.** No flashing, no router changes, no live experiments
   unless an approved protocol exists. Foundation work is software-only.

## Style

- Python 3.10+, absolute package imports (`from csi.parser...`), no
  `sys.path` hacks, no flat-module imports.
- New modules: docstring with purpose + upstream source (or "RF Vision
  native") + validation status where relevant.
