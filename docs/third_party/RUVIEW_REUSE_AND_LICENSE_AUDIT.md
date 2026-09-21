# RuView Reuse & License Audit (RFVISION-004)

Upstream: https://github.com/ruvnet/RuView — snapshot = `main` tarball
downloaded 2026-09-21 (61 MB; commit hash not recorded by tarball — pin an
exact commit before any extraction). Audit is static (no tests executed).
No upstream code copied into RF Vision during this operation.

## 1. Root license

- `LICENSE:1-21`: MIT, `Copyright (c) 2024 rUv`, standard MIT text.
- Declared `license = "MIT"` in root `pyproject.toml:10`.
- Obligation on reuse: retain the `Copyright (c) 2024 rUv` notice +
  permission text in every copy / substantial portion.

## 2. License variants inside the repo (all permissive)

- `v2/` Rust workspace: `MIT OR Apache-2.0` (`v2/Cargo.toml:152`,
  inherited by ~40 crates); `homecore-*` crates MIT-only.
- `wifi-veil/` + `firmware/privshield/`: dual `MIT OR Apache-2.0`
  (`wifi-veil/LICENSE-APACHE`, `wifi-veil/LICENSE-MIT`).
- `tools/ruview-cli/package.json:31`: Apache-2.0 (private/unpublished).
- Per-file headers mostly `SPDX-License-Identifier: MIT`.
- Separate MIT texts with other holders: `references/LICENSE`,
  `ui/pose-fusion/pkg/ruvector-attention/LICENSE`,
  `harness/{ruview,homecore}/LICENSE`, `wifi-veil/harness/LICENSE`.

## 3. Copyleft check

- Python/JS/Rust dependency manifests: NO GPL/AGPL dependency found.
- One touchpoint: FeitCSI (GPL, KuskoSoft) used as an EXTERNAL tool only
  (`v2/crates/wifi-densepose-mat/src/integration/feitcsi.rs:6-8`,
  ADR-292) — parser reads its output files/streams, no linking. Keep that
  boundary if ever used; legal review before distributing.
- False positive: `ui/mobile/package-lock.json` line with
  `(BSD-3-Clause OR GPL-2.0)` is a dual-licensed transitive dep (GPL
  optional), not a GPL-only dep.

## 4. Third-party UI libraries (licenses NOT vendored — verify upstream)

- three.js: r128 UMD via cdnjs (legacy pages/examples), 0.160.0 modules
  via unpkg (`ui/viz.html`, `ui/observatory.html`), r165 + 0.165.0/0.183.2
  npm (mobile). Upstream three.js is MIT (inferred, not stated in repo).
- `stats.js@0.17.0` (unpkg), fflate (FBX support), Lit 3.2.1 (BSD-3),
  Lucide icons (ISC), Victory Native (MIT), Expo/React-Native-SVG (MIT),
  MediaPipe + TF.js (Apache-2.0) — all inferred from upstream, none with
  license text in the snapshot. Retain notices when bundling.
- No vendored font files (Google Fonts Inter + JetBrains Mono fetched at
  runtime; normally OFL 1.1 — preserve OFL if self-hosted).
- No `node_modules`, no vendored JS libs in `ui/` — CDN + npm only.

## 5. Do NOT reuse without extra clearance

- `vendor/*`: EMPTY in snapshot (uninitialized git submodules:
  ruvector, midstream, rvcsi, rufield, metaharness, ruv-neural,
  ruview-swarm, worldgraph, RuForecast). Audit each upstream repo at a
  pinned commit before relying on it.
- `assets/*` (26 MB: zips, PNG/GIF): no license grant (`assets/README.txt`
  is a device spec). Treat as all-rights-reserved.
- `examples/three.js/assets/X Bot.fbx`: Mixamo, intentionally NOT
  redistributed — end-user download only (proprietary Adobe/Mixamo terms).
- Model weights: `v2/.../cog-{pose-estimation,person-count}/cog/artifacts/*`
  (KB-scale), `*.rvf`, `huggingface.co/ruvnet/wifi-densepose-pretrained`
  and `-mmfi-pose`: NO weight license found anywhere. Treat as
  proprietary/unlicensed — do NOT reuse.
- FeitCSI binary itself (GPL): external-tool use only, never bundle.

## 6. Verdict for RF Vision

- MAY reuse with MIT/Apache attribution: `ui/` web UI source (minus
  Google-Fonts fetch if offline), `examples/three.js` demos 01–03
  (helpers/cinematic/skinned — no FBX), `v2/*` Rust crates,
  `wifi-veil/*`, Python client code (`python/wifi_densepose/client/`).
- MUST NOT take: `vendor/*` (unaudited), `assets/*`, `X Bot.fbx`,
  any weights/checkpoints, FeitCSI binary.
- RF Vision caution: `requirements-gui.txt` currently isolates PyQt6
  (GPL/commercial). Any RuView-derived web UI (MIT three.js etc.) must
  stay license-separated from the PyQt6 path; do not mix GPL and
  MIT-licensed UI code in one deliverable without a licensing decision.
- Before extraction (next operation): pin the exact upstream commit,
  re-verify `vendor/*` contents at that commit, and record everything in
  `docs/third_party/SOURCE_PROVENANCE.md` per the 002 pattern.
