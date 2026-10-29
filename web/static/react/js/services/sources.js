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

// Dual session is a separate authoritative state from the legacy
// single-source provider. GET /api/v1/nodes is the only source of truth;
// this projection never fabricates a single-source provider or changes
// /api/v1/status or /api/v1/stream/status. Null means "no dual session";
// callers then keep the existing single-source OFF/LIVE/FIXTURE/SIMULATION
// behavior unchanged.
export function dualProjection(nodes) {
  if (!nodes || nodes.available !== true) return null;
  const entries = Array.isArray(nodes.nodes) ? nodes.nodes : [];
  const expected = Math.max(
    2,
    (nodes.session && Array.isArray(nodes.session.nodes) && nodes.session.nodes.length) || 0,
  );
  const live = entries.filter((n) => n
    && n.source_state === "LIVE_VERIFIED"
    && Number(n.valid) > 0
    && n.connection !== "DEGRADED"
    && n.connection !== "DISCONNECTED").length;
  const stale = entries.some((n) => n && n.source_state === "STALE");
  const down = entries.some((n) => n && (
    n.source_state === "DISCONNECTED"
    || n.connection === "DISCONNECTED"
    || n.connection === "DEGRADED"
  ));
  const base = {
    available: true,
    sync: nodes.sync_state || "UNSYNCED",
    live,
    expected,
  };
  if (stale) return { ...base, state: "STALE", label: "DUAL STALE", tone: "warn" };
  if (down) return { ...base, state: "DEGRADED", label: "DUAL DEGRADED", tone: "warn" };
  if (entries.length < expected || live < expected) {
    return { ...base, state: "STARTING", label: "DUAL STARTING", tone: "warn" };
  }
  if (nodes.sync_state === "SYNCED") {
    return { ...base, state: "SYNCED", label: "DUAL LIVE / SYNCED", tone: "live" };
  }
  return {
    ...base,
    state: "SYNCING",
    label: `DUAL LIVE / ${nodes.sync_state || "SYNCING"}`,
    tone: "warn",
  };
}

// Compare one node's observed BSSID/channel with the laptop's active
// network. Missing provenance is UNKNOWN, never a silent match. BSSID and
// channel are the authoritative fields already exposed by the existing APIs.
export function networkMatch(network, node) {
  const targetBssid = String(network && network.bssid || "").trim().toLowerCase();
  const targetChannel = network && network.channel;
  const nodeBssid = String(node && node.bssid || "").trim().toLowerCase();
  const nodeChannel = node && node.channel;
  if (!targetBssid || targetChannel == null) {
    return {
      state: "UNKNOWN", label: "NETWORK UNKNOWN",
      reason: "laptop BSSID/channel unavailable",
    };
  }
  if (!nodeBssid) {
    return {
      state: "UNKNOWN", label: "NETWORK UNKNOWN",
      reason: "node BSSID not reported",
    };
  }
  if (nodeBssid !== targetBssid) {
    return {
      state: "MISMATCH", label: "NETWORK MISMATCH",
      reason: `node ${nodeBssid} ≠ laptop ${targetBssid}`,
    };
  }
  if (nodeChannel == null) {
    return {
      state: "UNKNOWN", label: "NETWORK UNKNOWN",
      reason: "node channel not reported",
    };
  }
  if (Number(nodeChannel) !== Number(targetChannel)) {
    return {
      state: "MISMATCH", label: "NETWORK MISMATCH",
      reason: `node channel ${nodeChannel} ≠ laptop channel ${targetChannel}`,
    };
  }
  return {
    state: "MATCH", label: "NETWORK MATCH",
    reason: `BSSID ${targetBssid} · channel ${targetChannel}`,
  };
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
