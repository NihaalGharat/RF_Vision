# RFVISION-010 COMMIT & PUSH RECORD (2026-09-22)

## Commit
- SHA: `d1f12a51954964161cacde6c9d4f9d40ec1f25e0`, branch `main`, parent `bc80bbf`
- Message: `feat: add validated two-node CSI acquisition foundation` (+ validation body)
- Scope: 21 files (+1450/−15) — 13 modified, 8 new (nodes.py, dual_node.py,
  3 test modules, 3 RFVISION-010 reports). No firmware/parser/threshold/UI-behavior
  changes beyond the validated set. No history rewrite, no amend.

## Pre-commit gates (all PASS)
- Tree contained only intended RFVISION-010 changes; raw captures Git-ignored (verified).
- Privacy scan 0 hits; secret scan 0 hits; no workflow/AI-prompt/personal data staged.
- pytest 161 passed; `idf.py build` SUCCESS (binary hash `0a490737…` unchanged);
  ESP32-A golden replay EXACT (4654/0/1-gap/[121765]/62/0/0).

## Push
- `git push origin main:main` → fast-forward `bc80bbf..d1f12a5`, no force.
- Remote verified: `origin main = d1f12a5`, local/remote in sync, tree clean.

## Validation it certifies (GO basis)
- B single-node: 6280 valid @ 100 Hz, 0 gaps. Dual 120 s soak: A 11459 @ 95.5 Hz,
  B 12004 @ 100 Hz, SYNCED throughout, sub-ms jitter, 2 ms threshold kept.
- UI serves real dual data; standby honest. Known limits documented, not fixed:
  0–3% print fragmentation, occasional 5-frame soak gaps.

## Optimal next move
Controlled zone-grid experiment design + data-collection protocol (planned phase):
fix two anchor nodes at measured room coordinates, define a marked floor grid,
collect per-zone static captures (empty-room baseline + controlled human presence
at known cells) with manifests, then quantify per-link CSI perturbation vs zone
before any localization/ML claim. Prerequisite sequencing: (1) protocol doc for
approval, (2) empty-room baseline captures, (3) zoned presence captures,
(4) statistical separability analysis — features/models only if step 4 shows signal.
Rationale: the foundation is validated but has zero evidence of spatial
discriminability; measurement must precede modeling or all later claims are void.
Also deferred: rx-timestamped logging to localize the burst-gap source (small
instrumentation addition, propose alongside the protocol).
