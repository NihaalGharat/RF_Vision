# RFVISION-SPATIAL-INSTRUMENT-UI-TRANSFORMATION-REPORT

Date: 2026-09-23. Branch `main`, base `51684bd`.
Task: minimal premium spatial UI transformation — fewer surfaces,
stronger hierarchy, 4 primary destinations + secondary System, spatial
composition (§FINAL REPORT). Status: **IMPLEMENTED + VERIFIED +
UNCOMMITTED. No commit, no push.**

Scope decisions (confirmed before implementation): merge to 4 primary
destinations + secondary System; refined horizontal strip (no sidebar);
no live RF preview on Overview (a second Three.js scene is
expensive/invasive; RF Field stays the centerpiece tab). No reference
image was attached to the task; principles were translated from the
brief's text.

## 1. Decision

**PASS** — one minimal correction applied mid-pass (System open-state
indicator on the topbar control) and reverified. Human visual delta
gate passes: 4-destination rail with index ordinals, secondary System
gear, 38 px display values, consolidated Sensing, atmospheric depth —
immediately distinct from the baseline screenshots.

## 2. Changes

- **Routes 6 → 4 + secondary.** New `web/static/js/tabs/research.js`
  composes Localization + XAI + Experiments + Hardware via the
  codebase's established fanOut composition pattern (section headers
  verbatim, every row/caveat/honesty label preserved). Superseded
  `tabs/insights.js` and `tabs/session.js` shims deleted.
  `web/static/index.html` nav/panels rewired (Overview, Sensing,
  RF Field, Research + aria-labelled System panel). `web/static/js/app.js`
  registers research + system. `web/static/js/tabs.js` redirect map
  remapped (localization/xai/insights/experiments/hardware/session →
  research; models/settings → system) — re-homing, no dead deep links.
- **System secondary access.** Topbar gear control (bespoke inline SVG
  cog, 15 px, 1.5 px stroke; full 44 px target; keyboard-focusable;
  visible "System" text owns the accessible name) switches to the
  System panel via the existing `switchTo`; hash `#system`/`#models`/
  `#settings` keep working. An `onChange` subscription carries a
  `data-open` orientation cue styled in the active-tab language.
- **Sensing 8 cards → 5, 4 grids → 3.** One dominant CSI surface
  (heatmap + amplitude/RSSI row; "latest 40 frames" preserved as a
  state-note) plus one compact acquisition block (validity + packets
  under sub-labels). Phase (gated), presence (NOT VALIDATED), and
  trajectory cards byte-identical. All nine element IDs preserved;
  paint code untouched.
- **Spatial composition, CSS-only.** Static vignette + enlarged
  asymmetric ambient field (frozen, tonal, never data-like); display
  values 38 px desktop / 28 px ≤640 px; mono index ordinals on rail
  tabs (accent when active); `.viz-row` / `.sub-label` layout
  primitives for the consolidated surfaces.

## 3. Necessity (one line per change)

- Route merge removes top-level fragmentation with the codebase's own
  composition pattern instead of new architecture.
- Secondary System demotes settings prominence without a drawer
  framework or router rewrite.
- Sensing merge yields one measurement surface + one acquisition
  surface, matching the brief's workspace model.
- Vignette, display type, and rail indices supply the spatial/premium
  delta that micro-polish passes could not.
- Open-state cue closes the orientation gap the demotion itself
  created (rail shows no selection inside secondary space).

## 4. Verification

- Backend suite: 196/196 pass (twice). Zero console/JS errors in
  every browser session.
- Routing: all 13 hashes resolve to the correct visible panel (6
  legacy → research/system); sys-btn real pointer click → system +
  `#system`; open-state sets on entry and clears on return; trusted
  key events cycle overview → sensing → research → rffield with
  Home/End correct.
- Responsive: 8 widths (1440→360) dark + light spot-checks — strip
  height 52–53 px, no page overflow, real-click hit-testing of all
  tabs at 360/390, hash reload persistence, reduced-motion kills
  transitions, sticky topbar blur, 3D scene + HUD intact.
- Screenshots reviewed (12): 1440/390 dark/light Overview,
  consolidated Sensing, RF Field centerpiece, 4-section Research,
  secondary System, open-state crops.
- Accessibility: open-state pair measured on rendered pixels — 9.77
  dark / 4.99 light (≥ 4.5); no other text surface altered; keyboard,
  focus-visible rings, 44 px targets, ARIA names, reduced motion
  preserved; pseudo-element content never carries information.
- Performance: no animations or transitions added; blur confined to
  the existing recipe; no new paint loops; scheduler, RAF pause, and
  250 ms canvas decimation untouched.

## 5. Scientific integrity

Presentation + shell/template re-homing only. No change to CSI
acquisition, parsing, synchronization, inference, localization, XAI,
confidence semantics, contracts, REST, WebSocket, firmware, research
protocols, data, models, thresholds, experimental evidence, RF
interpretation, or Three.js scene meaning. All caveats and
UNCALIBRATED / UNKNOWN / NOT VALIDATED / GATED states render
verbatim; disconnected stays disconnected; no fabricated waves,
bodies, fields, or measurements.

## 6. Git

Branch `main`, base `51684bd`. Modified: `web/static/css/app.css`,
`web/static/index.html`, `web/static/js/app.js`,
`web/static/js/tabs.js` (prior auto-scroll fix preserved verbatim),
`web/static/js/tabs/sensing.js` (init template only). Deleted:
`web/static/js/tabs/insights.js`, `web/static/js/tabs/session.js`
(superseded shims). New untracked: `web/static/js/tabs/research.js`.
Pre-existing research docs untouched. Nothing staged, no secrets, no
artifacts, no backend/firmware/dependency changes. **NOT COMMITTED /
NOT PUSHED.**

## 7. Issues

Three verification-harness artifacts, none product defects: synthetic
`KeyboardEvent` dispatched on `document` bypasses the tablist
listener (re-proven with trusted CDP input); `var`-statement evaluate
returns undefined in the harness (expression-form probes used);
synthetic-mouse hover stuck across same-document fragment navigations
in one long session plus one transient white-canvas capture (fresh
loads + pixel readback confirmed correct dark rendering). No
reference image was supplied with the task. A real touch-device smoke
pass is recommended where available — headless Chrome cannot cover it.

**END OF REPORT.**
