# Vendored frontend dependencies — RF Vision React console (Phase 1)

Verbatim upstream builds, unmodified. Loaded locally; no CDN at runtime.

## React 18.3.1 — MIT License

- Files: `vendor/react.production.min.js` (10,751 bytes),
  `vendor/react-dom.production.min.js` (131,835 bytes)
- Source: https://unpkg.com/react@18.3.1/umd/react.production.min.js
  and https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js
- Owner: Facebook, Inc. and its affiliates (Copyright (c) Facebook, Inc.
  and its affiliates — see license header inside each file)
- License: MIT (license header preserved at the top of each vendored file)
- Reason vendored: the RF Vision bench console is local-only with no
  Node/npm toolchain (see `tools/run_rfvision_ui.sh`); React 18 is the last
  React line shipping UMD builds consumable without a bundler.
- Modifications: none.

Why UMD + no build: no JSX, no bundler — components use
`React.createElement` via the `h()` helper in `js/h.js`, loaded as native
ES modules exactly like the legacy console.
