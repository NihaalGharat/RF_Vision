/* Charts — teammate chart treatment (ProgressRing / ProgressBars) as
   dependency-free SVG/DOM, driven only by real RFVISION values.
   No mock data: null/unknown input renders an explicit NO DATA state. */
import { h } from "./h.js";

let _gid = 0;

export function Ring({ value, label, sublabel, size, from, via, to, glow }) {
  const s = size || 104;
  const stroke = 9;
  const v = value == null ? null : Math.max(0, Math.min(100, value));
  const r = (s - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = v == null ? 0 : c * (1 - v / 100);
  const gid = `rvring${(_gid += 1)}`;
  const c0 = from || "#38bdf8";
  const c1 = via || "#6366f1";
  const c2 = to || "#8b5cf6";
  return h("div", { style: { position: "relative", flexShrink: 0, width: `${s}px`, height: `${s}px` } },
    h("svg", { width: s, height: s, viewBox: `0 0 ${s} ${s}`, "aria-hidden": "true" },
      h("defs", null,
        h("linearGradient", { id: `${gid}-ring` },
          h("stop", { offset: "0%", stopColor: c0 }),
          h("stop", { offset: "50%", stopColor: c1 }),
          h("stop", { offset: "100%", stopColor: c2 }))),
      h("circle", { cx: s / 2, cy: s / 2, r, fill: "none", stroke: "rgba(80,140,220,0.14)", strokeWidth: stroke }),
      v == null ? null : h("circle", {
        cx: s / 2, cy: s / 2, r, fill: "none", stroke: `url(#${gid}-ring)`,
        strokeWidth: stroke, strokeLinecap: "round",
        strokeDasharray: c.toFixed(1), strokeDashoffset: offset.toFixed(1),
        transform: `rotate(-90 ${s / 2} ${s / 2})`,
        style: { filter: `drop-shadow(0 0 6px ${glow || "rgba(59,130,246,0.55)"})` },
      })),
    h("div", {
      style: {
        position: "absolute", inset: 0, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", textAlign: "center",
      },
    },
      h("span", { style: { fontSize: "20px", fontWeight: 700, letterSpacing: "-0.02em", color: "#fff" } },
        v == null ? "—" : (label != null ? label : `${Math.round(v)}%`)),
      sublabel ? h("span", { style: { marginTop: "2px", maxWidth: "82px", fontSize: "9px", fontWeight: 500, color: "var(--rv-muted)" } }, sublabel) : null));
}

export function Bars({ rows }) {
  return h("div", { className: "rfreact-bars" },
    (rows || []).map((row, i) => {
      const v = row.value == null ? null : Math.max(0, Math.min(100, row.value));
      return h("div", { className: "rfreact-bar", key: row.label || i },
        h("span", { className: "rfreact-barlabel" }, row.label),
        h("div", { className: "rfreact-bartrack" },
          v == null ? null : h("div", {
            className: "rfreact-barfill",
            style: Object.assign({ width: `${v}%` }, row.color ? { background: row.color } : null),
          })),
        h("span", { className: "rfreact-barval" }, v == null ? "NO DATA" : `${Math.round(v)}%`));
    }));
}
