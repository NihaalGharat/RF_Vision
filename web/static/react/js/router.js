/* Hash router — 5 Phase-1 destinations.
   Hash routing (not history API) so refresh and deep links work with the
   existing stdlib server unchanged: no per-route server fallback needed.
   Legacy-console hashes redirect to their new home (no dead deep links). */
import { h } from "./h.js";
import { Icon } from "./components/global.js";

const R = window.React;

export const ROUTES = [
  { id: "live", path: "#/live", label: "Live Sensing", icon: "radio" },
  { id: "visualize", path: "#/visualize", label: "Visualize", icon: "trending" },
  { id: "research", path: "#/research", label: "Research", icon: "flask" },
  { id: "hardware", path: "#/hardware", label: "Hardware", icon: "cpu" },
  { id: "system", path: "#/system", label: "System", icon: "sliders" },
];

const LEGACY_REDIRECT = {
  overview: "live", sensing: "live",
  rffield: "visualize",
  research: "research", localization: "research", xai: "research",
  insights: "research", experiments: "research", session: "research",
  hardware: "hardware", system: "system",
  models: "system", settings: "system",
};

export function parseRoute(hash) {
  const clean = (hash || "").replace(/^#\/?/, "").split("?")[0];
  if (ROUTES.some((r) => r.id === clean)) return clean;
  if (LEGACY_REDIRECT[clean]) return LEGACY_REDIRECT[clean];
  return "live";
}

export function navigate(id) {
  if (location.hash !== `#/${id}`) location.hash = `#/${id}`;
}

export function useRoute() {
  const [route, setRoute] = R.useState(() => parseRoute(location.hash));
  R.useEffect(() => {
    // Normalize legacy/unknown hashes to the canonical route once on boot
    // (replaceState fires no hashchange, so no loop). Deep links keep working.
    const canonical = `#/${parseRoute(location.hash)}`;
    if (location.hash !== canonical) history.replaceState(null, "", canonical);
    const onChange = () => setRoute(parseRoute(location.hash));
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export function Nav({ current }) {
  return h("nav", { className: "rfreact-railnav", "aria-label": "Console destinations" },
    ROUTES.map((r) => h("a", {
      key: r.id, href: r.path, title: r.label, "aria-label": r.label,
      "aria-current": current === r.id ? "page" : undefined,
    }, h(Icon, { name: r.icon, size: 18 }))));
}
