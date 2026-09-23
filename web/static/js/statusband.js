/* Persistent status band — RF Vision native (revamp Phase 3).
   The 5-second answer, visible from every tab. READ-ONLY view over the
   existing SourceStore: no independent state engine. Values come from the
   store snapshot (state, freshness) and the latest ingested event payload
   (observation, confidence, node mode), with UNKNOWN fallbacks for absent
   fields — including pre-v3 fixture envelopes. */
import { pillFor } from "./banner.js";

function fmtAge(ageMs) {
  if (ageMs === null || ageMs === undefined) return "no frames";
  if (ageMs < 1000) return "live";
  return `${(ageMs / 1000).toFixed(0)} s ago`;
}

export function bindStatusBand(store) {
  const el = {
    state: document.getElementById("sb-state"),
    obs: document.getElementById("sb-obs"),
    conf: document.getElementById("sb-conf"),
    nodes: document.getElementById("sb-nodes"),
    fresh: document.getElementById("sb-fresh"),
  };

  function render() {
    const snap = store.snapshot();
    const p = (snap.lastEvent && snap.lastEvent.payload) || {};
    el.state.innerHTML = pillFor(snap.state);
    el.obs.textContent = p.presence_state ?? "UNKNOWN";
    el.conf.textContent = p.rf_evidence_confidence != null
      ? `${p.rf_evidence_confidence.toFixed(2)} UNCALIBRATED`
      : "none (UNCALIBRATED)";
    el.nodes.textContent = p.node_mode ?? "UNKNOWN";
    el.fresh.textContent = fmtAge(snap.ageMs);
  }

  store.subscribe(render);
  // Freshness text drifts between store notifications; refresh the one span
  // on a cheap 1 s tick (same cadence as the header clock).
  setInterval(() => {
    const snap = store.snapshot();
    el.fresh.textContent = fmtAge(snap.ageMs);
  }, 1000);
}
