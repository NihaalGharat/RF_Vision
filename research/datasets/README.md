# Research datasets

Authoritative raw CSI is RESEARCH EVIDENCE, not source code: it lives
OUTSIDE git (external volume + backup), referenced by manifests carrying
path + SHA-256 + capture metadata per
`experiments/metadata/EXPERIMENT_METADATA_SCHEMA.md`.

Committed test vectors (tiny, synthetic or hand-picked golden lines) live
in `tests/fixtures/` — the ONLY CSI bytes in git. Never bulk-import raw
logs here. If a dataset must be versioned later, adopt Git LFS or
external storage first and document the decision here.
