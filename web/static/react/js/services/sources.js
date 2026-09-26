/* Source-of-truth model — OFF / LIVE / FIXTURE / SIMULATION.
   Maps the backend provider modes + contract source states onto the four
   Phase-1 source tokens. Rules enforced here (not in components):
   - LIVE renders only real backend acquisition frames.
   - SIMULATION renders only the backend simulated provider, always badged.
   - FIXTURE renders only backend fixture replay, always badged.
   - OFF renders nothing; stale frames are never presented as current.
   STALE_AFTER_MS mirrors the legacy console (3 s). */

export const SOURCES = ["OFF", "LIVE", "FIXTURE", "SIMULATION"];
export const STALE_AFTER_MS = 3000;

// Backend provider mode → Phase-1 source token.
export function sourceFromMode(mode) {
  switch (mode) {
    case "live": return "LIVE";
    case "fixture": return "FIXTURE";
    case "simulated": return "SIMULATION";
    default: return "OFF";
  }
}

export function badgeClass(source, stale) {
  if (stale) return "warn";
  switch (source) {
    case "LIVE": return "live";
    case "SIMULATION":
    case "FIXTURE": return "sim";
    default: return "off";
  }
}

// A frame is current only when its source is active and its age is fresh.
// Stale LIVE data must never render as current LIVE data.
export function frameFreshness(source, ageMs) {
  if (source === "OFF") return { current: false, stale: false, label: "no source" };
  if (ageMs === null || ageMs === undefined) return { current: false, stale: false, label: "no frames" };
  if (ageMs > STALE_AFTER_MS) return { current: false, stale: true, label: `STALE — ${(ageMs / 1000).toFixed(0)} s ago` };
  return { current: true, stale: false, label: ageMs < 1000 ? "live" : `${(ageMs / 1000).toFixed(0)} s ago` };
}
