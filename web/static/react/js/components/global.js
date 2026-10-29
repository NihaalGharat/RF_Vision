/* Global shell components — teammate visual system, RFVISION data.
   Read-only status: nothing here changes acquisition state. Buttons that DO
   change state live in features/* with explicit action semantics.
   Icons are inline stroke SVGs (lucide-style geometry, no dependency). */
import { h, kv, unknown, useClock } from "../h.js";

const R = window.React;

function svgPaths(name) {
  switch (name) {
    case "radio": return [
      h("circle", { cx: "12", cy: "12", r: "2" }),
      h("path", { d: "M4.9 19.1a10 10 0 0 1 0-14.2" }),
      h("path", { d: "M7.8 16.2a6 6 0 0 1 0-8.4" }),
      h("path", { d: "M16.2 7.8a6 6 0 0 1 0 8.4" }),
      h("path", { d: "M19.1 4.9a10 10 0 0 1 0 14.2" }),
    ];
    case "trending": return [
      h("polyline", { points: "22 7 13.5 15.5 8.5 10.5 2 17" }),
      h("polyline", { points: "16 7 22 7 22 13" }),
    ];
    case "flask": return [
      h("path", { d: "M10 2v7.5a2 2 0 0 1-.2.9L4.7 20.5a1 1 0 0 0 .9 1.5h12.8a1 1 0 0 0 .9-1.5L14.2 10.4a2 2 0 0 1-.2-.9V2" }),
      h("path", { d: "M8.5 2h7" }),
      h("path", { d: "M7 16h10" }),
    ];
    case "cpu": return [
      h("rect", { x: "4", y: "4", width: "16", height: "16", rx: "2" }),
      h("rect", { x: "9", y: "9", width: "6", height: "6" }),
      h("path", { d: "M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2" }),
    ];
    case "sliders": return [
      h("line", { x1: "21", x2: "14", y1: "4", y2: "4" }),
      h("line", { x1: "10", x2: "3", y1: "4", y2: "4" }),
      h("line", { x1: "21", x2: "12", y1: "12", y2: "12" }),
      h("line", { x1: "8", x2: "3", y1: "12", y2: "12" }),
      h("line", { x1: "21", x2: "16", y1: "20", y2: "20" }),
      h("line", { x1: "12", x2: "3", y1: "20", y2: "20" }),
      h("line", { x1: "14", x2: "14", y1: "2", y2: "6" }),
      h("line", { x1: "8", x2: "8", y1: "10", y2: "14" }),
      h("line", { x1: "16", x2: "16", y1: "18", y2: "22" }),
    ];
    case "sun": return [
      h("circle", { cx: "12", cy: "12", r: "4" }),
      h("path", { d: "M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" }),
    ];
    case "moon": return [h("path", { d: "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" })];
    case "chevron": return [h("polyline", { points: "9 18 15 12 9 6" })];
    case "back": return [
      h("line", { x1: "19", x2: "5", y1: "12", y2: "12" }),
      h("polyline", { points: "12 19 5 12 12 5" }),
    ];
    default: return [h("circle", { cx: "12", cy: "12", r: "4" })];
  }
}

export function Icon({ name, size, strokeWidth }) {
  return h("svg", {
    viewBox: "0 0 24 24", fill: "none", stroke: "currentColor",
    strokeWidth: strokeWidth || 1.9, strokeLinecap: "round", strokeLinejoin: "round",
    width: size || 18, height: size || 18, "aria-hidden": "true",
  }, svgPaths(name));
}

// Source pill — teammate ModePill treatment, RFVISION source truth.
// LIVE green / SIMULATION amber / FIXTURE violet / OFF muted / STALE amber.
const PILL_META = {
  LIVE: { color: "#34d399", bg: "rgba(52,211,153,0.12)" },
  SIMULATION: { color: "#fbbf24", bg: "rgba(251,191,36,0.12)" },
  FIXTURE: { color: "#a78bfa", bg: "rgba(167,139,250,0.12)" },
  OFF: { color: "#5c7190", bg: "rgba(92,113,144,0.12)" },
};

export function ModePill({ source, stale, dual }) {
  const dualMeta = dual && dual.tone === "live"
    ? { color: "#34d399", bg: "rgba(52,211,153,0.12)" }
    : { color: "#fbbf24", bg: "rgba(251,191,36,0.12)" };
  const key = stale ? "SIMULATION" : (PILL_META[source] ? source : "OFF");
  const meta = dual && dual.label
    ? dualMeta
    : stale
      ? { color: "#fbbf24", bg: "rgba(251,191,36,0.12)" }
      : PILL_META[key];
  const label = dual && dual.label
    ? dual.label
    : stale ? `STALE ${source}` : source;
  const title = dual && dual.label
    ? `dual-session status · ${dual.live}/${dual.expected} live · sync ${dual.sync}`
    : "active data source (backend provider mode)";
  return h("span", {
    className: "rfreact-pill", title,
    style: { color: meta.color, borderColor: `${meta.color}55`, background: meta.bg },
  },
    h("span", { className: "dot", style: { background: meta.color, boxShadow: `0 0 6px ${meta.color}` } }),
    label);
}

// CONNECTED / DISCONNECTED derived from real WS + backend reachability.
export function ConnDot({ wsState, backendUp }) {
  const up = backendUp && wsState === "connected";
  const color = up ? "#34d399" : "#f87171";
  const label = !backendUp ? "DISCONNECTED (backend unreachable)"
    : wsState === "connected" ? "CONNECTED (backend + WebSocket)"
      : `DISCONNECTED (ws ${wsState})`;
  return h("span", {
    className: "rfreact-conndot", title: label,
    style: { background: color, boxShadow: `0 0 6px ${color}` },
  });
}

// RF READY / NOT READY rendered ONLY from GET /api/v1/rf_readiness.
export function RfReadyBadge({ readiness, error }) {
  if (error || !readiness) {
    return h("span", { className: "rfreact-badge off", title: String(error || "no readiness read") }, "RF READY: UNKNOWN");
  }
  const ok = readiness.rf_ready === true;
  return h("span", {
    className: `rfreact-badge ${ok ? "ready" : "notready"}`,
    title: readiness.reason || readiness.state || "",
  }, ok ? "RF READY" : `NOT READY (${readiness.state || "?"})`);
}

export function ThemeToggle() {
  const [theme, setTheme] = R.useState(() => document.documentElement.dataset.theme || "dark");
  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try { localStorage.setItem("rfvision-theme", next); } catch { /* private mode */ }
    setTheme(next);
  };
  R.useEffect(() => {
    try {
      const saved = localStorage.getItem("rfvision-theme");
      if ((saved === "light" || saved === "dark") && saved !== theme) {
        document.documentElement.dataset.theme = saved;
        setTheme(saved);
      }
    } catch { /* private mode */ }
  }, []);
  return h("button", {
    className: `rfreact-iconbtn${theme === "dark" ? "" : " on"}`,
    onClick: toggle, title: `Theme: ${theme} (toggle light / dark)`,
    "aria-label": `Theme: ${theme}. Activate to switch theme.`,
  }, h(Icon, { name: theme === "dark" ? "moon" : "sun", size: 17 }));
}

// Page header — teammate PageHeader: eyebrow + title left, actions right.
export function PageHeader({ eyebrow, title, back, actions }) {
  return h("div", { className: "rfreact-pagehead" },
    h("div", { className: "rfreact-pagetitle" },
      back ? h("button", {
        className: "rfreact-backbtn", title: "Go back", "aria-label": "Go back",
        onClick: () => window.history.back(),
      }, h(Icon, { name: "back", size: 15 })) : null,
      h("div", null,
        h("p", { className: "rfreact-eyebrow" }, eyebrow || "RF Vision"),
        h("h1", { className: "rfreact-title" }, title))),
    actions ? h("div", { className: "rfreact-headactions" }, actions) : null);
}

// Global fetch-error row with Retry (read-only refresh, never reconfigures).
export function ErrorRow({ error, onRetry, what }) {
  if (!error) return null;
  return h("p", { className: "rfreact-err" },
    `${what || "fetch"} failed: ${error} `,
    h("button", { className: "rfreact-btn", onClick: onRetry, type: "button" }, "Retry"));
}

// Card — teammate BaseCard: label + title + actions header, body, footer.
export function Card({ label, title, actions, footer, bodyClassName, children }) {
  return h("article", { className: "rfreact-card" },
    (label || title || actions)
      ? h("header", { className: "rfreact-cardhead" },
        h("div", { className: "rfreact-cardheadtxt" },
          label ? h("p", { className: "rfreact-card-label" }, label) : null,
          title ? h("h3", { className: "rfreact-card-title" }, title) : null),
        actions ? h("div", { className: "rfreact-cardactions" }, actions) : null)
      : null,
    h("div", { className: `rfreact-cardbody${bodyClassName ? ` ${bodyClassName}` : ""}` }, children),
    footer ? h("footer", { className: "rfreact-card-foot" }, footer) : null);
}

export function Clock() {
  const clock = useClock();
  return h("span", { className: "rfreact-clock" }, clock);
}

export { kv, unknown };
