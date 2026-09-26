# RFVISION-GLASS-INSTRUMENT-VISUAL-DESIGN-REPORT

Date: 2026-09-23. Branch `main`, base `51684bd`.
Phase: INSPECT → PROPOSAL. Status: **proposal pending approval — no code
changed, nothing committed, nothing pushed.**

## 1. Objective

Transform the RF Vision console into a futuristic, research-grade
glassmorphism instrument — futuristic, premium, technically sophisticated,
spatial, calm, precise, coherent, distinctly RF-oriented — without becoming
a generic SaaS/AI dashboard, gaming HUD, or neon overload. The result must
remain a usable scientific instrument: no information removed, no caveats
hidden, no scientific claims altered.

Control loop: INSPECT → DEFINE OBJECTIVE → IDENTIFY NECESSARY CHANGES →
PROPOSE → WAIT FOR APPROVAL → IMPLEMENT → TEST → VERIFY → CRITIQUE →
REVERIFY → STOP. This report covers work through PROPOSE.

## 2. Baseline inspection (read-only, completed)

- Tree: `main`, base `51684bd`; the only uncommitted diff is the prior
  nav/contrast fix (`web/static/css/app.css` +26/−1, `web/static/js/tabs.js`
  +7). No other drift.
- `web/static/css/tokens.css` (27 lines): dark console tokens, flat light
  scheme, Inter + JetBrains Mono stacks with system fallbacks.
- `web/static/css/app.css` (282 lines): topbar, source banners (5 states ×
  2 themes), tabs with collapse floor + styled scrollbar, cards, pills,
  hero triad, details/disclosure, dense tables, 44 px buttons with
  hover-gated press feedback, breakpoints 1100/1024/900/640,
  reduced-motion kill-all.
- All six areas inspected (Overview, Sensing, RF Field, Insights, Session,
  System + submodules): rendering is fully class-driven
  (`.grid/.card/.hero-*/.kv/.tbl/canvas.viz/.scene-wrap`), so a pure-CSS
  transformation is feasible with zero markup/JS changes.
- Canvases inherit theming for free: `viz2d.js` palette and `scene3d.js`
  background both derive from CSS variables. Only one form control exists
  (`select.btn` in `experiments.js`). The 3D scene (single link,
  theme-synced bg, HUD chip, reduced-motion + RAF pause) is intact.
- Observed problems (evidence, not taste): (1) near-flat sterile surfaces —
  `bg-0/1/2` are flat cool grays with uniform 1px borders; (2) shell layers
  (topbar/statusband/tabs) share `bg-1` and merge into one band;
  (3) uniform card weight buries the 3D RF scene, the instrument's
  centerpiece; (4) light theme has no depth system; (5) `panelIn` opacity
  animation fires on every tab switch, including keyboard switches.

## 3. Skill usage (all sources actually inspected)

- **Taste `redesign-existing-projects`** (SKILL.md, full): supplied the
  audit sequence and the "true glassmorphism" recipe adopted here —
  translucent surface + 1px inner border + inner shadow + tinted shadow
  (not `blur()` alone). Its single-accent and no-AI-gradient rules confirm
  keeping the lone teal.
- **Emil `emil-design-eng`** (SKILL.md, full): the animation decision
  framework justifies *removing* the per-tab-switch animation
  (high-frequency surface, keyboard must never animate) while keeping
  press/focus feedback. The existing `--ease-out`
  (`cubic-bezier(0.23, 1, 0.32, 1)`) already matches his recommended curve.
  Transform/opacity-only, ≤200 ms adopted.
- **Soft-skill `high-end-visual-design`** (SKILL.md, full): ethereal-glass
  archetype and blur-only-on-fixed-elements adopted. Its font-swap,
  floating-pill-nav, scroll-reveal, and double-whitespace mandates are
  explicitly **rejected** (offline instrument with no downloadable fonts;
  authoritative tab strip with collapse-fix history; polling dashboard;
  dense-instrument density requirement).
- **Impeccable** (repo overview + anti-pattern catalog + command reference
  inspected; skill body not fetched): anti-patterns (no purple gradients,
  no nested cards, no bounce easing, tinted darks) cross-checked — the
  baseline already complies except for depth/texture, which this proposal
  addresses. Its `audit → critique → polish` vocabulary shapes the
  post-implementation plan (§9 of the brief).

## 4. Proposal

### A. Visual language

- **Glass material (single recipe):** translucent surface (`color-mix` of
  `bg-1` toward transparent, ~72–82% opaque) + `backdrop-filter:
  blur(14–20px) saturate(1.2)` + 1px inner hairline (`inset 0 1px 0
  rgba(255,255,255,.06)` dark / `rgba(255,255,255,.7)` light) + teal-tinted
  shadow, never pure black.
- **Background:** deep teal-tinted charcoal (`#0b1114` family; current
  `#101417` shifts slightly cooler/darker) with two static radial ambient
  glows (teal 6–8% + faint cool blue, fixed, never animated). Light theme:
  pale cool mist with a soft radial teal wash. Grain via inline-SVG noise
  data-URI at ~3% on a fixed `body::before` — no assets, no network.
- **Accent:** single teal, unchanged (`#37c6d4` / `#14707a` light). No
  second hue, no purple/blue gradient. Status colors untouched.
- **Typography:** keep Inter + JetBrains Mono (offline constraint);
  hierarchy via scale/tracking only.
- **Radius/spacing/density:** existing tokens kept. Density stays dense —
  this is an instrument.

### B. Hierarchy

1. Primary: RF Field 3D scene + Overview hero triad (SYSTEM →
   OBSERVATION → CONFIDENCE). 2. Secondary: statusband, evidence,
   node-health, Sensing canvases. 3. Supporting: `details.detail`,
   Session/System sections, footer provenance. 4. Status/evidence (pills,
   banners, caveats, UNCALIBRATED labels) keeps full contrast above glass.

### C. Glass usage

- **Glass:** topbar (sticky), tab strip (translucent; active tab gets an
  illuminated hairline), hero cells, primary cards, statusband (subtle),
  `details.detail`, scene HUD + slim frame around (never over) the 3D
  viewport.
- **NOT glass:** canvas/viz interiors, tables and `.kv` rows, pills,
  banners, caveats, buttons, footer.

### D. Motion

Keep 160 ms press `scale(.97)` and focus transitions; keep or shorten hero
stagger. **Remove** `panelIn` on tab switch (tens of switches/day;
keyboard must never animate). Nothing continuous: no animated gradients,
no ambient drift. Reduced-motion full kill preserved. Existing `--ease-out`
throughout; transform/opacity only; ≤200 ms.

### E. RF identity

Depth = signal path: dark ambient field (environment) → luminous glass
viewports (field/observation) → mono tabular readouts
(evidence/inference). Link-line teal is the single "energy" hue, echoed
only in the active-tab indicator, hero top-edge, and HUD. No invented
symbology, no decorative waveforms, no glow readable as measurement.

### F. Responsive

Token-based glass scales across 1440/1280/1024/900/768/640/390/360:
1024 hero stacks full-width (collapse `min-height` floor untouched);
`backdrop-blur` eases to ~10 px on small screens for mobile GPU; tab strip
scroll + auto-scroll behavior byte-identical; effects via `box-shadow` /
pseudo-elements only, so zero layout impact and no new horizontal
overflow.

### G. Accessibility

Contrast re-measured post-implementation with the rendered-pair method
(both themes); glass behind text stays ≥72% opaque or gains a scrim so
pairs hold ≥4.5:1 — **accessibility wins every conflict**. Focus rings,
44 px targets, keyboard/hash/refresh behavior, and reduced-motion support
unchanged and re-verified.

## 5. Necessity (problem → evidence → minimum solution)

- Flat sterile surfaces → read in stylesheets, matches redesign audit →
  token-level glass + ambient background, no markup changes.
- Merged shell layers → all `bg-1` in source → translucent
  topbar/tabs/statusband with hairline separation.
- Buried 3D centerpiece → equal-weight cards observed → luminous viewport
  framing + hero emphasis, no restructuring.
- Gratuitous tab-switch animation → fires every switch incl. keyboard →
  remove; instant reads as faster.

## 6. Verification (planned, post-approval)

Browser matrix 1440→360 × dark/light; contrast re-measurement; backend
test suite; navigation hit-testing incl. tab-collapse regression;
perf/a11y/scientific-integrity passes; skill-informed critique; full
reverification after critique fixes. No backend, firmware, contract, or
scientific changes at any point.

## 7. Git

Branch `main`, base `51684bd`. This phase changed nothing: working tree
still only `M web/static/css/app.css`, `M web/static/js/tabs.js` (prior
fix, uncommitted). No commit, no push, no research notes modified — this
is a new file.

## 8. Approval gate — decision points

1. Glass coverage: shell + hero + cards (proposed) vs. shell-only?
2. Background: static radial ambient + faint grain (proposed) vs. flat
   tinted background?

Implementation begins only on explicit approval.

**END OF REPORT.**
