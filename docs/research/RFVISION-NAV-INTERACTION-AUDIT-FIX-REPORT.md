# RF VISION — INTERACTION & NAVIGATION UX: AUDIT + MINIMAL FIX REPORT

**Status: IMPLEMENTED + VERIFIED, UNCOMMITTED (awaiting authorization).**
**Method: INSPECT → REPRODUCE → DIAGNOSE → DECIDE → SMALLEST CHANGE →
TEST → VERIFY → ARCHITECTURE → SCIENTIFIC-INTEGRITY → REGRESSION → REVERIFY.**
**Base: `main` @ `51684bd`. Date: 2026-09-23.**

---

## 1. Diagnosis

Reproduced against the real served UI (headless Chrome via CDP at
1280 / 900 / 768 / 640 / ~390 px: load, click each tab, scroll, hash-load,
refresh, keyboard, viewport changes).

- **The scrollbar is the symptom, not the bug.** `overflow-x` stays `auto`
  through every selection; no JS touches overflow, nav width, or scroll
  position; a user-set `scrollLeft` survives tab clicks. The "disappearing"
  affordance is platform overlay-scrollbar behavior plus an unstyled scroll
  container with no persistent affordance of its own.
- **The real defect: the selected tab is never scrolled into view.**
  Measured at ~390 px: clicking System leaves it clipped at (429,502) in a
  470 px container with `scrollLeft=0`; hash-loading `#system` (including
  refresh) leaves the *active* tab half-hidden. Overflow exists only below
  ~500 px (at 640+ all six tabs fit), but there the failure is total: no
  cue, active tab hidden.
- **Keyboard path was already sound:** arrow/Home/End handling, exact
  `aria-selected`, focus tracking the active tab, native focus scrolling.
  No change required.

## 2. Interaction audit

**Interactive surfaces (all genuine, all correctly afforded — cursor,
hover, focus-visible, active/pressed, disabled, keyboard where applicable;
nothing broken, nothing removed):** 6 tabs, 4 experiment buttons, source
select, theme toggle, Retry linklikes, `<details>` summaries, skip link.
3D scene communicates "Drag to orbit · scroll to zoom" in adjacent text.
Hash routing, old-hash redirects, refresh persistence all verified working.

**Misleading / non-interactive surfaces:** exactly one violation —
`.tbl tbody tr:hover td` highlighted informational, non-clickable rows
(false clickability cue). `cursor: pointer` exists only on genuinely
interactive elements. Hero cells, pills, status band, kv lists, canvases
imply no interaction. No dead controls found.

## 3. Changes (2 files, +14/−1)

1. **`web/static/js/tabs.js`** — `switchTo` calls
   `btn.scrollIntoView({ block: "nearest", inline: "nearest" })`.
   Purpose: active tab always visible after click / hash / load.
   Minimum: `nearest` is a no-op when already visible (desktop
   `scrollLeft` stays 0, measured); `block:"nearest"` cannot scroll the
   page; keyboard path unaffected; no buttons, listeners, or layout change.
2. **`web/static/css/app.css`** — thin styled scrollbar on `.tabs`
   (`scrollbar-width`, `scrollbar-color`, webkit thumb, all token-driven).
   Purpose: persistent affordance where the platform shows scrollbars;
   harmless where it doesn't (clipped-tab edge + auto-scroll cover
   discovery there).
3. **`web/static/css/app.css`** — deleted the row-hover rule, left an
   explanatory note. Purpose: informational rows must not look clickable.

Rejected as failing the necessity test: scroll buttons / edge gradients
(scroll listeners, decorative risk), `scrollbar-gutter` (shifts layout at
all widths), smooth scrolling (gratuitous motion), active-state redesign
(already unmistakable), any framework or structural change.

## 4. Verification

- **Navigation:** 390 px click-System → fully visible (402,475 in 475);
  click-Overview scrolls back; hash-load `#system` → visible; 1280 px zero
  movement across selections; keyboard arrows + focus + `aria-selected`
  correct; full loop re-run after review — PASS.
- **Backend:** 196/196 pass, twice (post-change and post-review).
- **Responsive:** fix verified <500 px; 640–1440 need no overflow handling
  (measured fit); 44 px targets; focus visible throughout.
- **Architecture:** frontend-only, 2 files, no store/scheduler/routing/
  contract/backend/firmware changes.
- **Scientific integrity:** no data, inference, confidence, localization,
  state, or semantics changed.
- **Regression:** all preserved interactions re-verified intact; `git diff`
  proves only the 2 UI files touched.

## 5. Git

- Branch `main`, base `51684bd`. Working tree: `M web/static/css/app.css`,
  `M web/static/js/tabs.js`; 25 pre-existing untracked research notes left
  alone. **No commit created — awaiting explicit authorization.**
- Ephemeral verification server (`web.server --port 18380`) may still be
  running; the sandbox blocks process termination from this side. Safe to
  ignore or kill the listener on 18380.

## 6. Remaining issues

None found within scope. No improvements invented. A browser smoke pass on
a real device (overlay scrollbars, touch) is recommended where available —
this environment has only headless Chrome.

---

## 7. Follow-up phase (2026-09-23): collapsed tab strip + light contrast

Two reported residuals were re-verified against the served UI (headless
Chrome via CDP, 1280/900/360 px, both themes) before any code was touched.

### 7.1 Tab strip collapse (Sensing/Session untappable)

- **Issue:** real taps on Sensing/Session missed. Synthetic `.click()`
  always worked (it bypasses hit-testing), which is why §4 verified green
  while the symptom survived for real users.
- **Root cause:** not tab width, JS timing, or hash routing (all eliminated
  by measurement: `scrollIntoView` fires correctly, `overflow-x`/scroll
  position never change, zero console errors). The `.tabs` strip itself
  collapses to 9 px height while the 44 px tab buttons overflow inside it;
  later panel content paints over them, so real taps land on panel cards.
  Trigger isolated bidirectionally: it occurs exactly when the page carries
  a vertical scrollbar (breakpoint precisely at the 1024 px query where the
  hero stacks and page height jumps 657→868 px; forcing a tall page at
  1280 px reproduces it, hiding panels at 900 px cures it). Pre-existing
  since the revamp (confirmed on stashed baseline `51684bd`).
- **Change:** `web/static/css/app.css` — one line,
  `.tabs { min-height: calc(44px + var(--space-2)); }`, flooring the strip
  at exactly its natural healthy height (52 px + border = 53 px, identical
  when healthy, hence a no-op there). Rejected: `overflow`/`align-items`/
  `display` probes (measured: still 9 px), markup restructure, scroll
  buttons (wrong problem). The §3 `scrollIntoView` is kept — complementary
  (scroll position), not redundant (container height).
- **Verification:** strip 52–53 px at all widths; every on-screen tab
  hit-tests SELF; click/hash-load/reload/keyboard leave all six tabs fully
  visible at 360 px; 1280 px zero-movement; screenshots confirm.

### 7.2 Light-mode contrast

- **Issue:** unreadable text in light mode. Every rendered light-theme
  text/background pair was audited in-browser (computed styles, correct
  alpha blending). All body/UI text already passes (6.2–13.7:1). Exactly
  three failures: brand-mark "RF" glyphs (1.95–3.12), primary-button hover
  text (3.12), 3D HUD chip (1.15 — effectively invisible).
- **Change:** `web/static/css/app.css` — three light-scoped declarations
  only (`.brand-mark{color:#fff}`,
  `button.btn.primary:hover{color:#fff}`,
  `.scene-hud{color:#e8f6f8; background:rgba(6,25,28,.78)}`). No palette
  change, no redesign; dark-mode computed values verified unchanged.
- **Verification:** fixed pairs now 5.79 / 5.79 / 8.38 (≥ 4.5:1); dark and
  light screenshots confirm readability.

### 7.3 Phase totals

- Diff: 2 files, +26/−1 (`app.css`, `tabs.js`), frontend-only. No
  store/contract/API/backend/firmware/data changes; no scientific or
  behavioral change. 196/196 backend tests pass (post-change and
  post-review). **STOPPED before commit — nothing committed, nothing
  pushed.**

**END OF REPORT.**
