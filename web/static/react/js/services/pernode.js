/* Per-node live-stream routing + signal-derived disturbance helpers.
   Pure functions only: no DOM, no React, no imports. Presentation logic for
   the Visualize 3D signal field — never acquisition, never inference.
   - nodeKey(): maps the existing WS envelope top-level node_id
     ("esp32-a"/"esp32-b", tagged by the dual-session pump, passed through
     byte-identical) to a visualization slot "A"/"B". Anything else → null,
     so single-source frames without node_id keep the legacy single-strip
     behavior instead of being mislabeled.
   - routeSnapshot(): folds one sensing.snapshot envelope into per-node
     slots immutably: an A frame returns a new A slot and the UNTOUCHED B
     slot object (and vice versa), so A frames cannot overwrite B state.
   - updateBaseline()/deviation(): a short-term visualization baseline
     (per-tone exponential moving average) and measured signal deviation
     (|current − baseline|, normalized). Presentation emphasis only: no
     detection threshold, no classifier, no person/object claim. */

export const NODE_SLOTS = ["A", "B"];

// Temporal smoothing constant for the visualization baseline (per ingested
// frame). Presentation only — not a scientific threshold, makes no decision.
export const BASELINE_ALPHA = 0.05;

export function nodeKey(nodeId) {
  if (nodeId === "esp32-a") return "A";
  if (nodeId === "esp32-b") return "B";
  return null;
}

export function emptySlot() {
  return {
    amps: null, rssi: null, seq: null, ts: null,
    baseline: null, disturb: null, disturbMean: null,
  };
}

export function emptySlots() {
  return { A: emptySlot(), B: emptySlot() };
}

function validAmps(amps) {
  return Array.isArray(amps) && amps.length &&
    amps.every((v) => typeof v === "number" && Number.isFinite(v))
    ? amps.slice() : null;
}

// Immutable routing: returns {slots, routed} where slots reuses the
// untouched sibling object by reference. Routed slot carries fresh
// amps/rssi/seq/ts; baseline/disturbance update in updateSlotDisturbance.
export function routeSnapshot(slots, event) {
  const key = event && nodeKey(event.node_id);
  if (!key) return { slots, routed: null };
  const q = (event && event.payload) || {};
  const amps = validAmps(q.amplitudes);
  const rssi = (typeof q.rssi === "number" && Number.isFinite(q.rssi)) ? q.rssi : null;
  const seq = (typeof event.seq === "number" && Number.isFinite(event.seq)) ? event.seq : null;
  const ts = (typeof event.ts === "number" && Number.isFinite(event.ts)) ? event.ts : null;
  if (amps === null && rssi === null && seq === null) return { slots, routed: null };
  const prev = slots[key] || emptySlot();
  const next = {
    amps: amps !== null ? amps : prev.amps,
    rssi: rssi !== null ? rssi : prev.rssi,
    seq: seq !== null ? seq : prev.seq,
    ts: ts !== null ? ts : prev.ts,
    baseline: prev.baseline, disturb: prev.disturb, disturbMean: prev.disturbMean,
  };
  const out = key === "A"
    ? { A: next, B: slots.B }
    : { A: slots.A, B: next };
  return { slots: out, routed: key };
}

// Fold the slot's current amps into its baseline, then measure deviation.
// First frame seeds the baseline (copy) with zero disturbance — a baseline
// needs history before "change" is meaningful.
// Phase 3: hold=true freezes the baseline (deviation is still re-measured
// against it) so a held directional RF event is not absorbed as environment.
// The hold decision comes from the spatial-evidence streak state — never a
// magnitude threshold. hold=false (default) keeps byte-identical behavior.
export function updateSlotDisturbance(slot, alpha = BASELINE_ALPHA, hold = false) {
  if (!slot || !slot.amps || !slot.amps.length) return slot;
  if (!slot.baseline || slot.baseline.length !== slot.amps.length) {
    return { ...slot, baseline: slot.amps.slice(), disturb: slot.amps.map(() => 0), disturbMean: 0 };
  }
  if (hold === true) {
    return { ...slot, ...deviation(slot.amps, slot.baseline) };
  }
  const a = (typeof alpha === "number" && alpha > 0 && alpha < 1) ? alpha : BASELINE_ALPHA;
  const baseline = slot.amps.map((v, i) => slot.baseline[i] + a * (v - slot.baseline[i]));
  return { ...slot, baseline, ...deviation(slot.amps, baseline) };
}

export function deviation(amps, baseline) {
  if (!amps || !amps.length || !baseline || baseline.length !== amps.length) {
    return { disturb: null, disturbMean: null };
  }
  let lo = Infinity, hi = -Infinity;
  for (const v of amps) { if (v < lo) lo = v; if (v > hi) hi = v; }
  const span = (hi > lo) ? (hi - lo) : 1;
  const disturb = amps.map((v, i) => Math.abs(v - baseline[i]) / span);
  let mean = 0;
  for (const d of disturb) mean += d;
  mean /= disturb.length;
  return { disturb, disturbMean: mean };
}

// Phase 2: pure false-colour thermal mapping for the live RF disturbance
// overlay. Maps normalized measured signal change t in [0,1] to an RGB
// triple in [0,1]: cool blue/cyan (low) → green/yellow (moderate) →
// orange/red (high). Continuous interpolation between fixed palette
// anchors — the anchors are VISUAL ENCODING ONLY, not detection/presence/
// scientific thresholds; they make no decision and carry no significance.
// Deterministic, finite for every input; non-finite input maps to the cool
// end (no data → no warmth). Never touches acquisition or inference.
const THERMAL_STOPS = [
  [0.00, 0.15, 0.55], // deep blue
  [0.00, 0.55, 0.85], // cyan
  [0.10, 0.70, 0.45], // green
  [0.95, 0.85, 0.20], // yellow
  [0.95, 0.45, 0.10], // orange
  [0.95, 0.08, 0.08], // red
];

export function thermalColor(t) {
  let v = (typeof t === "number") ? t : NaN;
  if (!Number.isFinite(v)) v = 0;
  v = Math.max(0, Math.min(1, v));
  const segs = THERMAL_STOPS.length - 1;
  const x = v * segs;
  const i = Math.min(segs - 1, Math.floor(x));
  const f = x - i;
  const a = THERMAL_STOPS[i], b = THERMAL_STOPS[i + 1];
  return [
    a[0] + (b[0] - a[0]) * f,
    a[1] + (b[1] - a[1]) * f,
    a[2] + (b[2] - a[2]) * f,
  ];
}
