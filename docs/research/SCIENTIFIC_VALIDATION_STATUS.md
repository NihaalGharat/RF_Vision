# Scientific Validation Status (binding policy)

Rule: **IMPLEMENTED ≠ EXPERIMENTALLY VALIDATED ≠ CLAIMED.**
RF Vision inherits no validated sensing result from any upstream repository.

## Current verdict

- Real dual-ESP32 CSI acquisition: **VERIFIED**.
- Live measured A/B visualization: **VERIFIED** (engineering evidence, not a
  sensing claim).
- Reference-relative RF activity: **OBSERVED**.
- Human-presence association: **EXPLORATORY**.
- Validated presence/activity classifier: **NOT AVAILABLE**.
- Human coordinates, trajectories, pose: **NOT VALIDATED**.
- Controlled inanimate obstacle detection: **NOT VALIDATED**.
- Obstacle localization/geometry: **NOT VALIDATED**.
- Reference View waves and room: **ILLUSTRATIVE**.
- Audio dispatch and phase schedule: **not proof of physical action timing**.

Residual-energy ratios are never detector accuracy, confidence, or probability.

## Verified acquisition and visualization

- Real dual ESP32 CSI on the verified `VCET Lab` session, channel 6. Exact
  network identifiers are kept in operator-local evidence, not public docs.
- Both receivers reached `LIVE_VERIFIED`, `SYNCED`, and `RF_READY`; the backend
  reported the full network/node/CSI/sync chain.
- Real browser delivery: Live Sensing and Visualization received independent
  A/B frames; no synthetic substitution.
- WebSocket permanent-reconnect exhaustion was reproduced, fixed with
  indefinite capped backoff, and regression-tested. Live now reports the actual
  WebSocket service state.
- The accepted live baseline had `323 passed`; the current build has `325
  passed`, including recorder-finalization coverage. Offline browser smoke is
  `13/13` across the five React routes. These are engineering checks, not a new
  live-hardware sensing validation.
- The five React routes (`Live`, `Visualize`, `Hardware`, `Research`, `System`)
  are present and browser-tested. The legacy console remains at `/legacy`.
- Separate historical sessions used different networks and channels; their
  observations must not be merged.

## Claim register

| Capability | Upstream claim | In RF Vision | Status |
|---|---|---|---|
| CSI acquisition (D0WD-V3 + 4C + csi_recv_router) | esp-csi bring-up | vendored verbatim | VALIDATED (own experiment, external to repos) |
| Presence detection | Human-Sensing pipeline | integrated | NOT YET VALIDATED |
| Movement detection | heuristic + calibration | integrated | NOT YET VALIDATED |
| 1-D position | KNN/RF/MLP + tracker | integrated | NOT YET VALIDATED |
| Activity recognition | none trained (labels only) | heuristic labels | NOT YET VALIDATED (no classifier) |
| 2-D/3-D localization | D (“device-free”, no model) | not implemented | NOT YET VALIDATED |
| csi-sensing zones/activities | CNN/Transformer/SVM | not included | NOT VERIFIED (weights absent, license-blocked) |
| XAI explanations | none anywhere | interface only | NOT YET VALIDATED |
| Realtime rates/latency | viewers/demos | integrated | NOT YET VALIDATED (measure on hardware) |
| Synthetic-data metrics | “learn almost perfectly by design” | tests only | NEVER QUOTABLE AS EVIDENCE |

## VCET reference analysis

Trial `WT-20261029T121111Z` (historical VCET Lab session on channel 11; not the
later channel-6 session):

- Raw parse: **11,027 A** and **11,559 B** CSI vectors, 54 tones with 50 usable
  per node (four consistently zero amplitude slots).
- The older `9,071`/`9,517` values in `trial_meta.json` are cumulative source
  counters captured at trial start, **not trial frame totals**.
- ReferenceTracker-compatible A/B amplitude vectors were available for
  in-session analysis.
- In-session empty-baseline interior: 1,605 A / 1,704 B vectors; held-out
  second half showed no disturbed tones; median reference-relative energy was
  A `0.283` / B `0.419`, gain `0.975` / `0.992`.
- Phase-associated reference-relative energy (medians): stand-still A `4.03` /
  B `22.87`; move A `0.70` / B `7.35`; post-exit A `0.20` / B `0.48`. These are
  interval-associated RF changes, not proof of the planned action and not
  obstacle detection.
- Missing obstacle ground truth, exact geometry, frozen protocol, and
  same-network repeatability. Other complete trials use different networks or
  pathological references and are not interchangeable evidence.

## Nihaal human-presence experiments

Primary: `WT-20261029T194753Z`. Supplementary: `WT-20261029T193657Z`.
Network: home-lab 2.4 GHz session, channel 1; exact identifiers are not
published.

Conditions: solo operator; audio guidance confirmed audible; fan OFF and
furniture unchanged (operator-reported); human stood approximately between the
receivers. Exact spatial geometry and action timestamps are unknown.

Findings:

- Both trials showed directional increases in reference-relative CSI residuals
  during planned stationary-presence intervals.
- ESP32-B baseline was comparatively stable.
- ESP32-A showed reference drift and/or near-zero-scale sensitivity.
- Quantitative repeatability was not established.
- Phase timing remained approximate.
- No validated human-presence detector was produced.

The supplementary trial’s original `trial_meta.json` reported ESP32-B
`bytes=0` / `sha256=null` although its raw file was nonempty. The original raw
file, metadata, checksums, and append-only correction manifest are preserved;
no historical value was silently repaired.

## Scientific limitations

- Real CSI acquisition and live measured A/B visualization are verified
  engineering capabilities; they are not evidence of a validated sensing
  model.
- Relative RF activity is observed; human-presence association remains
  exploratory.
- No validated presence/activity classifier, human coordinates, trajectories,
  pose, controlled inanimate obstacle detection, obstacle localization, or
  obstacle geometry exists.
- Reference View room and waves are illustrative, not measured geometry.
- Audio dispatch and phase markers do not prove physical action timing.
- Do not convert residual-energy ratios into detector accuracy or confidence
  probabilities.
- Obstacle reconstruction and new sensing features are deferred until after the
  demonstration.

## Deferred research tasks

1. Host-monotonic CSI receipt and audio/phase event timing.
2. Trial/session/network/tone-layout provenance.
3. Robust reference-scale and baseline-quality checks.
4. Investigation of live 62-tone versus offline 54-tone terminology.
5. Controlled repeat human-presence experiments with sham/null controls.
6. Controlled physical-object placement/removal experiments.
7. Trial-level validation with held-out data.
8. Spatial observability assessment.
9. Optional experimental RF Change Analysis view.
10. Obstacle geometry only after independent spatial validation.

These are dependency-ordered: timing/provenance and reference quality precede
repeat trials; held-out validation precedes any detector or spatial claim;
obstacle geometry comes last.

## Evidence availability

Detailed evidence bundles, live logs, screenshots, and analysis outputs are
retained locally and intentionally not published because they contain
environment-specific diagnostics and identifiers. Raw CSI remains in its
original Git-ignored `research-data/` locations. Local retention is not an
independent off-device backup. Do not infer validation from an unpublishable
local artifact.
