# RF VISION — UI REVAMP: PHASE 0 REPORT (READ-ONLY AUDIT + REDESIGN PROPOSAL)

**Status: PROPOSAL ONLY. Nothing modified, installed, committed, or pushed during Phase 0.**
**Method: INSPECT → ANALYZE → DECIDE → PROPOSE → SELF-VERIFY → STOP.**
**Date: 2026-09-23. Post-P1 state, contract v3, commits `f73d49d` (P0) + `2f2a227` (P1).**

Reconciliation note: the post-P1 UI Revamp Readiness Note matches the
repository, with three corrections applied in favor of the implementation —
(1) there are **9 tabs incl. disabled Models**; (2) `CONSOLE.CONTRACT_VERSION`
in `web/static/js/config.js` is stale (`1`, display-only; backend serves `3`
via `/api/v1/health`); (3) server-side STALE applies **only while streaming**
(verified live: stop stream + 3.6 s → health still `OFFLINE_FIXTURE`; STALE
after stop is client-synthesized via the 3 s freshness timer).

Inspection limits (stated, not hidden): no browser automation exists in this
environment, so there are **no screenshots**; visual inspection was done via
source audit + served HTML shell (HTTP 200, 9 tabs, banner node present) +
live endpoint behavior (fixture source selected, stream started, snapshot /
nodes / xai / live / status payloads read, stop-stream stale transition
observed). The Watermelon `capitalio-dashboard.json` URL returns **404**
(registry path invalid or unpublished); principles below are drawn from the
reachable Watermelon catalog pages and changelog, the taste-skill
`redesign-skill`, Kowalski's design-engineering skill, and Impeccable — each
passed through the necessity filter, not copied.

---

## A. Executive design direction

**An instrument panel, not a dashboard.** One persistent status band answers
the six 5-second questions (running? nodes healthy? observing? activity?
confidence? degraded/stale/simulated?) from every tab; Overview becomes a
three-layer read — *state → evidence → detail* — where the top layer is five
facts and everything else is progressively disclosed; secondary tabs keep
100% of research function behind calmer, denser, consistently-tokenized
surfaces. No new dependencies, no framework migration, no backend change, no
new visual metaphor beyond the honest single-link RF figure.

## B. Current UI audit (evidence, not adjectives)

**What works and must survive:** the banner + dot + pill provenance system
(`web/static/js/banner.js`, `config.js:21-43`) is honest and complete;
`viz2d.js` null→placeholder discipline is exemplary; the Models-locked and
PHASE GATED placeholders are correct policy UI; the 60-line `index.html`
shell with hash deep-linking is the right skeleton.

**Problems:**

1. **Cognitive load** — Overview renders ~35 facts across 7 equal-weight
   cards (`web/static/js/tabs/overview.js:14-37`); Sensing stacks 6 canvases
   + 3 KVs (`sensing.js:21-57`). No primary/secondary step: every `h3` is an
   identical 11 px uppercase label (`css/app.css:71-80`).
2. **Duplication** — rssi/rate/gaps on Overview ≈ Sensing ≈ Hardware;
   presence/confidence on Overview ≈ Sensing ≈ RFField HUD ≈ XAI;
   firmware/commit in three tabs; room-width UNKNOWN in four tabs.
3. **Status gaps** — `LIVE_VERIFIED` has no banner rule (renders as *absence*
   of banner, `app.css:38-42`); `OFFLINE_FIXTURE` and `SIMULATED` share one
   color (`app.css:39-40`); critical caveats are the smallest text on screen
   (11–12 px).
4. **Inconsistent visuals** — canvas code hard-codes dark colors, so the
   light theme shows dark islands (`viz2d.js:19` fills `#1a2126`
   unconditionally); light tokens omit all status colors (`tokens.css:22-27`
   overrides bg/ink/accent/line only); `drawBars` value colors vary per tab
   with no legend; `.badge` CSS plus `TabManager.setBadge`,
   `api.telemetry`, `api.latest`, and `HealthMonitor.subscribe` are dead
   surface (zero callers/subscribers).
5. **Motion/perf** — an infinite `requestAnimationFrame` runs even when RF
   Field is hidden (`scene3d.js:200-209`; `onHide` clears only the poll
   timer); five concurrent 2 s pollers plus 5 s health plus 0.5 s STALE tick;
   `prefers-reduced-motion` kills CSS (`app.css:144-146`) but not
   canvas/polling updates.
6. **Empty/error asymmetry** — fetch failures are swallowed
   (`overview.js:64`, `sensing.js:89`, `experiments.js:94,97`), leaving stale
   numbers with no timestamp; XAI's empty state is a blank 32 px strip
   (`viz2d.js:82` has no empty guard); Localization never re-polls after
   navigation.

## C. Information architecture — CURRENT → PROPOSED

No function deleted; merges only where content is near-duplicate or
mostly-empty. All cards/sections survive inside their new home, collapsed or
re-ordered.

| Current | Proposed | Rationale |
|---|---|---|
| Overview (7-card wall) | **Overview** (hero band + evidence + disclosed detail) | §D below; fixes B.1 |
| Sensing (signal detail) | **Sensing** (unchanged scope, restyled, deduplicated) | Signal detail is a core researcher need; keep |
| RF Field (3D+2D) | **RF Field** (unchanged scope) | Keep; only honest spatial surface |
| Localization (mostly UNKNOWN) + XAI (NOT AVAILABLE + 1 sentence) | **Insights** (localization estimate + uncertainty + XAI evidence, all states preserved) | Two sparse interpretation surfaces become one; fixes nav sprawl without removing a single row |
| Experiments (ops) + Hardware (ops) | **Session** (source control + recording + transport diagnostics + baseline) | Both are operations; overlap (firmware/commit/serial) collapses naturally |
| Models (locked) + Settings (theme/backend/scope) | **System** (registry status + appearance + backend + scope) | Both are meta; lock messaging preserved verbatim |
| — | Persistent **status band** in shell (state pill, observation, confidence, node mode, freshness) | The 5-second answer, visible from every tab |

Result: 9 tabs → **6: Overview · Sensing · RF Field · Insights · Session ·
System**. Hash deep-links keep working (`tabs.js` untouched); old hashes for
merged tabs redirect to the merged tab's section anchor.

## D. Overview wireframe

```text
┌ STATUS BAND (all tabs) ─────────────────────────────────────┐
│ ● LIVE_UNVERIFIED · DETECTED · RF-ev 0.42 UNCALIBRATED ·     │
│   DUAL · frame 0.3s ago                            [contract] │
├ HERO ───────────────────────────────────────────────────────┤
│  SYSTEM            │  OBSERVATION        │  CONFIDENCE        │
│  LIVE_UNVERIFIED   │  DETECTED           │  0.42              │
│  2/2 nodes SYNCED  │  (NOT VALIDATED)    │  UNCALIBRATED,     │
│                    │  MOTION: STATIC     │  never probability │
├ EVIDENCE ───────────────────────────────────────────────────┤
│  [RF field strip / link figure — small]  │ Node health table │
│  evidence: "…" (factual sentence)        │ A: LIVE 141Hz …   │
│                                          │ B: LIVE 128Hz …   │
├ DETAIL (disclosed: <details>/collapsed sections) ───────────┤
│  ▸ Sensor · CSI · Backend · Research · Latest frame · Sync  │
└─────────────────────────────────────────────────────────────┘
```

Prominence order: system state > observation > confidence > node health >
visualization > evidence sentence > everything else collapsed.
Degraded/stale/disconnected/simulated states **replace** the hero values in
place (same layout, err/warn styling) — never a separate screen the user must
discover.

## E. Design system (extend `tokens.css`, never a competing system)

- **Typography:** keep the dependency-free stacks; add a type scale
  (`--text-display 28/34`, `--text-h 15/20` semibold, `--text-body 13/20`,
  `--text-data 12` mono tabular, `--text-note 12`),
  `font-variant-numeric: tabular-nums` on all telemetry,
  `text-wrap: balance` on headings, sentence case for headers. Existing 11 px
  uppercase card labels are load-bearing visual language — keep them, fix
  their size to a 12 px minimum.
- **Colors:** keep the hue system; fix the light theme by overriding
  `--ok/--warn/--sim/--err/--stale/--ink-1` (currently missing);
  desaturate `--warn` below 80%; distinguish FIXTURE vs SIMULATED banner
  tints; add a quiet `LIVE_VERIFIED` rule (thin accent underline, not
  invisibility).
- **Surfaces/spacing/radii:** keep `--space-*` / `--radius-*`; add
  `--space-7: 48px`; hero uses `radius-m`, inner elements `radius-s`; shadows
  tinted to background hue.
- **Semantic states:** one mapping table (state → dot + pill + banner + hero
  treatment) sourced in `config.js` + CSS; canvas helpers read CSS variables
  via `getComputedStyle` so the light theme stops producing dark islands.
- **Charts/empty/loading/error/focus:** `drawBars` empty-array guard
  ("NO DATA"); skeleton shimmer for first-load cards (opacity only); inline
  error rows with retry + last-good timestamp (fixes swallowed-fetch
  staleness); `:focus-visible` on all interactives; skip-link; 44 px minimum
  touch targets on source/record controls.

## F. Component strategy

- **KEEP:** banner/dot/pill system, `store.js` provenance + STALE logic,
  `viz2d.js` placeholder discipline, `scene3d.js` link-figure model,
  Models-lock and PHASE GATED messaging verbatim, hash routing, WS+REST
  split.
- **REDESIGN:** Overview (→ §D), status band (new shell element fed by the
  existing store), card header scale, light theme, buttons/press states,
  tables (sticky header, tabular numerals, row hover), empty/error/loading
  states.
- **CONSOLIDATE:** Localization+XAI → Insights; Experiments+Hardware →
  Session; Models+Settings → System; five 2 s pollers → one shared 2 s
  scheduler with per-tab subscriptions (fixes drift + request spam; same
  endpoints, same cadence).
- **REMOVE FROM DEFAULT VIEW (not delete):** per-tab duplicate KVs (single
  source per fact, others link), dead surface (`api.telemetry`/`latest`
  stubs, `setBadge`, unused subscribe), inline `margin-top:12px` styles →
  tokens.
- **NEW:** status band component; shared poller; `<details>`-based
  disclosure sections; degraded-mode banner treatment; canvas text-fallback
  summaries (`role="img"` + `aria-label` + adjacent sr-only values).
- Watermelon principles adopted (filtered): clear status presentation,
  information-dense tables, consistent card composition, responsive preview
  discipline. Watermelon components **not** adopted: anything React / shadcn /
  Tailwind (see §G-tech) — principles only, zero code.

## G. Motion strategy (Kowalski frequency rule: 10 Hz telemetry never animates per-frame)

| Item | Verdict | Rationale |
|---|---|---|
| Button press `scale(0.97)`, 100–160 ms ease-out | ADD | Missing feedback; cheapest aliveness |
| Tab switch: opacity-only fade ≤180 ms ease-out | ADD | Prevents "broken" feeling on lazy init; no layout transform |
| Hero value change: opacity crossfade 200 ms | ADD | Crossfade only on *state* change, never per frame |
| Overview card entry stagger 30–50 ms | ADD | Decorative, once per tab visit; interaction never blocked |
| Infinite 3D RAF while hidden | REMOVE (pause on `onHide`) | Pure waste; biggest reduced-motion violation |
| Heatmap/strip full redraw per WS frame | REDUCE (redraw at most 4 Hz, latest frame wins) | Jank source; zero data loss (decimation, not sampling) |
| `prefers-reduced-motion` | REDESIGN (extend to JS: stop stagger, crossfades, strip animation; keep opacity comprehension aids) | Current CSS-only handling is incomplete |
| Animation libraries (GSAP/Motion/etc.) | REJECTED | No spring/gesture need exists; WAAPI + transitions cover the four additions |

Easing tokens: `--ease-out: cubic-bezier(0.23,1,0.32,1)`; never `ease-in`
for UI; never `transition: all`.

**Technology necessity verdict (§4):** no framework migration. The vanilla
stack demonstrably covers every need (1728 non-vendor lines, clean module
split, lazy tabs, working WS/REST). React/Next/Tailwind/shadcn/chart or
animation libraries would add migration cost and regression risk against zero
demonstrated capability gap. Rejected with reasons, not by preference.

## H. Responsive strategy

Targets: 1500 px (current max) → laptop 1280 → small desktop 1024 → tablet
768. Hero container 1500 → 1160 (readability; tables keep full width).
≥1024: full layout, hero 3-column. 900–1024: hero stacks to 1 column
(state→observation→confidence order preserved), node table keeps columns,
tabs scroll-x (already works). ≤640: already single column, plus scene
height 420→260, status band wraps to two lines with freshness always visible,
tables become stacked label/value rows. RF visualization strip scales by
width (already fluid); 3D keeps orbit but disables damping on
touch/reduced-motion. Nothing is deleted at any width — detail sections
collapse, never vanish.

## I. Accessibility strategy (built-in, not a patch)

Skip-link; tablist with `aria-controls`, `tabindex` management, arrow-key
navigation; every canvas gets `role="img"` + dynamic `aria-label` +
visually-hidden value summary (screen readers currently get zero); status
never color-only (text labels already exist — extend to the 3D strip with a
textual legend); fix light-theme contrast (`ink-2` on white fails — darken
to pass 4.5:1); raise critical notes to 12 px minimum; banner `aria-live`
extended to hero state changes (polite, state-changes only, not per-frame);
`@media (hover:hover)` gates hover motion; touch targets ≥44 px on controls.

## J. Technical implementation plan (small, independently verifiable phases)

1. **Tokens** — extend `tokens.css` (§E), fix light theme; verify both
   themes render, zero JS touched.
2. **Shared poller + dead-code removal** — one 2 s scheduler; remove
   `telemetry`/`latest` stubs, `setBadge`, unused subscribe; verify request
   count drops, all tabs still update.
3. **Shell** — status band + 6-tab nav + skip-link + tablist ARIA; verify the
   5-second questions, old-hash redirects, keyboard nav.
4. **Overview** — hero + evidence + disclosed detail per §D; verify every
   current Overview fact still reachable.
5. **Tab consolidation** — Insights / Session / System merges; verify
   row-for-row content parity checklist.
6. **RF visualization honesty pass** — CSS-variable canvas colors, `drawBars`
   empty guard, text fallbacks, HUD label preservation; verify light theme +
   screen-reader summary.
7. **Responsive** — breakpoints + scene height + stacked tables; verify at
   1280/1024/768/390 widths.
8. **Motion** — four additions + RAF pause + 4 Hz redraw cap + reduced-motion
   JS; verify with animation inspector, hidden-tab CPU ≈ idle.
9. **Accessibility sweep** — contrast, focus, live regions, touch targets;
   verify by keyboard-only run + contrast check.
10. **Visual QA + regression verification** — full suite green, contract v3
    payloads unchanged, fixture-missing-keys fallback re-verified,
    degraded/stale/disconnected/simulated states walked live,
    firmware/parsers/sync untouched confirmation.

## K. Risk register

| Risk | Mitigation |
|---|---|
| Tab merges hide research function (UX) | Row-for-row parity checklist in phase 5; nothing deleted, only re-homed |
| Shared poller changes update timing (regression) | Same endpoints + same 2 s cadence; STALE thresholds (`3.0 s` × 3 layers) untouched |
| Canvas theming breaks readability (visual) | Contrast-check both themes; placeholders keep explicit text, never color-only |
| Status band + hero disagree (integrity) | Single source: both read `store.snapshot()`; no independent state |
| Confidence rendered as probability (integrity — critical) | UNCALIBRATED tag is part of the component, not a prop; raw 0–1, never bare %; review gate in phase 10 |
| Fixture missing v3 keys crashes new components (technical) | `??` fallback discipline + explicit fixture-mode test pass in phase 10 |
| 3D changes imply new capability (integrity) | Link-figure model frozen; dressing only; HUD honesty strings verbatim |
| Scope creep into backend (scope) | Hard rule: any value not renderable from contract v3 + REST/WS becomes an UNKNOWN display; no contract edits |
| Poll-heavy tabs regress perf (performance) | 4 Hz canvas cap, paused hidden RAF, single scheduler; profile in phase 8 |

## L. Approval gates (explicit)

Owner approval required before implementation for: **(1)** the 9→6 tab merge
(fallback if rejected: Overview-only revamp); **(2)** the shared poller
replacing per-tab timers; **(3)** the font decision (default: refine the
in-place system stack, zero new assets — versus a vendored font);
**(4)** any content rewording beyond casing/spacing (honesty strings stay
verbatim by default). Everything else is ordinary design execution within
this proposal. No framework migration is recommended or requested.

---

## Self-verification (§21 loop, executed)

- **UX:** every major change traces to a §B item with file:line evidence;
  merges preserve all rows; the 5-second test is answerable from the band.
  PASS.
- **Visual:** extends existing tokens; bans purple gradients, glassmorphism,
  and card-soup explicitly; light theme fixed rather than reimagined. PASS.
- **Technical feasibility:** all changes are CSS + tab JS + shell HTML;
  `store`/`tabs`/`api`/`ws` logic untouched except the additive scheduler;
  Three.js scene model frozen. PASS.
- **Performance:** net-negative load (fewer pollers, paused RAF, capped
  redraws); no new libraries. PASS.
- **Accessibility:** §I items are phased deliverables with verification
  steps, not aspirations. PASS.
- **Scientific integrity:** honesty labels verbatim; confidence never
  probability; UNKNOWN stays UNKNOWN; fixture fallback explicit; no backend
  change possible by construction. PASS.
- **Necessity/scope:** each item answers "what problem, what evidence,
  minimum change"; React/Tailwind/shadcn/chart/animation libraries rejected
  with reasons; the proposal is simpler (6 tabs, one scheduler, one token
  source), not merely different. PASS.

```text
DESIGN PROPOSAL → UX → VISUAL → TECHNICAL → PERFORMANCE →
ACCESSIBILITY → SCIENTIFIC-INTEGRITY → NECESSITY/SCOPE → PASS → REPORT
```

**END OF PHASE 0 REPORT. Implementation is separately authorized as
RF VISION — UI REVAMP IMPLEMENTATION.**
