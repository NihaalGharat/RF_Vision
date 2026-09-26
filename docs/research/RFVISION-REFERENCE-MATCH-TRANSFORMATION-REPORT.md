# RFVISION-REFERENCE-MATCH-TRANSFORMATION-REPORT

Date: 2026-09-23. Branch `main`, base `51684bd`.
Task: final UI transformation — reference-match + information
simplification against the supplied reference image (icon rail,
2-column instrument composition, decluttered hierarchy). Status:
**IMPLEMENTED + VERIFIED + UNCOMMITTED. No commit, no push.**

Scope decisions (confirmed before implementation): vertical icon rail
(4 destinations + System gear + theme toggle, collapses to a
horizontal strip below 901 px); no new visualizations (no ring/bar
meters — hierarchy carried by composition, type, and spacing);
Overview keeps its readout triad with merged secondary surfaces;
no live RF preview (a second Three.js scene is expensive/invasive).

## 1. Pre-implementation clustering diagnosis

1. Overview "RF evidence — latest" state row duplicated the hero
   confidence cell — same fact in two permanent containers.
2. Statusband triple-carries hero facts — justified as the every-tab
   answer; retained.
3. Overview evidence + node-health cards answered the same
   "supporting detail?" question — merged into one surface.
4. Sensing was already consolidated; RF Field's 3D-dominant
   asymmetry was already correct.
5. Research diagnostic cards (Calibration/sync, Transport
   diagnostics) were LEVEL-3 technical detail renting permanent
   grid space — converted to progressive disclosure.
6. Overview's five detail rows and secondary System placement were
   already correct — retained.
7. Reference delta: left icon rail vs top strip.
8. Reference delta: 2-column asymmetric grid + display header + air
   vs uniform auto-fit density.
9. Reference delta: ambient depth vs flat dark (teal identity kept;
   steel-blue depth only, no second-hue glow).
10. Ring meters declined — type/scale/air carry the hierarchy with
    zero fabrication risk.

## 2. Final information architecture

- Rail: Overview, Sensing, RF Field, Research + secondary System
  gear + theme toggle (icon + label, 44 px targets, same router and
  keyboard map; horizontal strip below 901 px).
- Overview: hero triad + one merged "RF evidence · node health"
  surface + five disclosures.
- Sensing: one dominant CSI surface + one compact acquisition block
  + gated / not-validated / trajectory surfaces (5 total).
- Research: four labeled sections, 12 cards + 2 disclosures.
- System: Models + Settings, secondary, hash-addressable.

## 3. Exact files changed

- `web/static/index.html` — rail nav with six bespoke inline SVGs
  (home, waveform, node, flask, gear, moon), sys/theme cluster.
- `web/static/css/app.css` — rail grid shell, icon-button geometry,
  display type, vignette, consolidated layouts.
- `web/static/js/app.js` — research registration, sys wiring +
  open-state cue, rail theme toggle + boot-apply of saved theme.
- `web/static/js/tabs.js` — redirect remap (prior auto-scroll fix
  preserved verbatim).
- `web/static/js/tabs/research.js` — new composite (Localization +
  XAI + Experiments + Hardware, fanOut pattern).
- `web/static/js/tabs/overview.js` — merged secondary surface.
- `web/static/js/tabs/sensing.js` — init template only.
- `web/static/js/tabs/localization.js`, `web/static/js/tabs/hardware.js`
  — cards converted to native disclosures.
- Deleted: `web/static/js/tabs/insights.js`,
  `web/static/js/tabs/session.js` (superseded shims).

## 4. What was merged

Insights + Session workspaces into Research; Overview evidence +
node health into one surface; validity + packets acquisition block
(retained from prior pass). All element IDs and render logic
preserved; paint code untouched.

## 5. Progressive disclosure

Calibration/sync and Transport diagnostics → native `<details>`
(mouse click and Space verified; same interaction as the five
pre-existing Overview disclosures). Capture controls stay
interactive; nothing actionable was disclosed away.

## 6. Removed as redundant

Only the duplicated evidence-state row (absorbed into the merged
surface) and the two superseded composition shims. Zero information
loss — every section/value mapped and verified present.

## 7. Intentionally preserved

All render/paint logic, poll acquisition keys, honesty labels,
caveats, UNCALIBRATED / UNKNOWN / NOT VALIDATED / GATED states,
experiment provenance and controls, theme preference key, hash and
deep-link coverage for all eight legacy routes, scheduler and canvas
performance architecture.

## 8. Reference-match changes

Left icon rail with bottom secondary cluster; two-column asymmetric
card grids; 38 px display readout values (28 px small screens);
mono micro-labels and index ordinals; hairline glass with corner
ticks; static atmospheric depth; single teal accent; bespoke
stroke-icon family. Recognizably the same visual language with RF
Vision content throughout.

## 9. Test results

Backend suite 196/196 (three runs across the task). No backend,
contract, firmware, or data changes.

## 10. Browser verification results

All 13 hashes resolve to the correct panel (6 legacy re-homed);
sys-btn real-click → System + hash; open-state sets/clears;
trusted-keyboard 4-tab cycle with Home/End; rail geometry (92 px,
full height, content offset); disclosures open via mouse/Space;
theme toggle flips + persists; hash reload persistence; zero
console/JS errors; 20+ screenshots reviewed across Overview,
Sensing, RF Field, Research, System, both themes.

## 11. Responsive/accessibility/performance results

Widths 1500/1440/1280/1024/900/768/640/390/360: rail above 901 px,
strip below; no page overflow anywhere; 44 px targets including
rail buttons; keyboard, focus-visible rings, ARIA names, canvas
summaries preserved; reduced-motion kills all transitions; contrast
holds (worst new pairs: sub-labels 4.92/4.93, light sys-open 4.99
measured on rendered pixels). No animations, loops, scenes, or
polling added.

## 12. Scientific-integrity verification

Presentation + template re-homing only. No change to acquisition,
parsing, synchronization, inference, localization, XAI, confidence
semantics, contracts, protocols, data, models, thresholds,
firmware, or Three.js meaning. Disconnected stays disconnected;
nothing fabricated — no waves, bodies, fields, probabilities, or
results beyond what the system reports.

## 13. Remaining visual mismatches

None structural. Two genuine defects found and fixed during the
pass: banner row inflating to viewport height in the rail grid
(fixed with explicit grid rows) and this report's verification
methodology notes below. Minor note: wrapped rail separators on
390 px rows read as a ledger — clean, out of scope to restructure.

## 14. Commit confirmation

Nothing staged, nothing committed, nothing amended, rebased, or
pushed. Pre-existing research docs untouched (this new report file
excepted). No secrets, artifacts, or dependency changes.
**NOT COMMITTED / NOT PUSHED. STOP.**

### Verification-methodology notes (harness artifacts, not defects)

- The CDP harness window is 757 px tall, not 900 — rail correctly
  fills 100vh; thresholds must use `innerHeight`.
- Long single-session loops bleed `dataset.theme` into the cached
  canvas palette and leave stuck `:hover` from synthetic mouse —
  fresh browser sessions per theme/state were used for all
  evidentiary captures.
- Synthetic `KeyboardEvent` on `document` bypasses the tablist
  listener; trusted CDP key input used instead.

**END OF REPORT.**
