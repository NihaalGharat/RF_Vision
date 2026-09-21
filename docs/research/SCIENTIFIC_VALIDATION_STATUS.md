# Scientific Validation Status (binding policy)

Rule: **IMPLEMENTED ≠ EXPERIMENTALLY VALIDATED ≠ CLAIMED.**
RF Vision inherits no result from any upstream repository.

## Claim register

| Capability | Upstream claim | In RF Vision | Status |
|---|---|---|---|
| CSI acquisition (D0WD-V3 + 4C + csi_recv_router) | esp-csi bring-up | vendored verbatim | VALIDATED (own experiment, external to repos) |
| Presence detection | Human-Sensing pipeline | integrated | NOT YET VALIDATED |
| Movement detection | heuristic + calibration | integrated | NOT YET VALIDATED |
| 1-D position | KNN/RF/MLP + tracker | integrated | NOT YET VALIDATED |
| Activity recognition | none trained (labels only) | heuristic labels | NOT YET VALIDATED (no classifier) |
| 2-D/3-D localization | D ("device-free", no model) | not implemented | NOT YET VALIDATED |
| csi-sensing zones/activities | CNN/Transformer/SVM | not included | NOT VERIFIED (weights absent, license-blocked) |
| XAI explanations | none anywhere | interface only | NOT YET VALIDATED |
| Realtime rates/latency | viewers/demos | integrated | NOT YET VALIDATED (measure on hardware) |
| Synthetic-data metrics | "learn almost perfectly by design" | tests only | NEVER quotable as evidence |

## Validation requirements (before any claim)

1. Approved protocol in `experiments/protocols/` (calibration, ground
   truth, environment, geometry, subjects).
2. Session-split evaluation minimum; cross-session/cross-environment
   reporting required (CSI drift is the known hard problem).
3. Derived datasets registered with source + transform + software version
   + config + checksum + timestamp. Raw data immutable, outside git.
4. Phase features need a dedicated gate (amplitude-only is the default).
5. No inherited numbers in docs, slides, drafts, or papers — ever.

## Currently: zero validated sensing claims

The 68-test suite validates **plumbing** (parsing, math, contracts,
train→evaluate mechanics on synthetic data). Synthetic metrics
(100% F1 on separable blobs) prove the harness runs — nothing more.
