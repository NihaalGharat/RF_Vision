/* Phase 3 — approximate spatial RF evidence layer (pure functions only).
   No DOM, no React, no imports. Deterministic presentation logic for the
   APPROXIMATE RF EVIDENCE FIELD — never acquisition, never inference beyond
   the coarse engineering zones below, never calibration.
   - APPROX_FRAME: the ONLY coordinate frame implemented here. A tag, not a
     measurement: conceptually normalized x,y in [0,1], with NO room-dimension
     field, NO metre conversion, NO x/y/z physical coordinates anywhere in
     this module. A value such as 0.52 stays 0.52 — conversion to metres is
     structurally impossible (there is nothing to convert with).
   - zoneEvidence(): folds the two existing per-node disturbMean values into
     three deterministic relative evidence scores (NEAR-A / BETWEEN / NEAR-B).
     CANDIDATE SPATIAL EVIDENCE — REQUIRES RFVISION-011 VALIDATION. The
     differential direction is the only node-anchored signal a two-node link
     provides; the resulting zones are approximate evidence regions anchored
     to the approximate node arrangement, NOT surveyed physical coordinates,
     NOT validated localization. Tone index never enters this module.
   - updateField(): tier + persistence state machine. RF_ACTIVITY while change
     exists without usable direction; RF_ESTIMATE only for a held directional
     leader across consecutive evaluations; NO_LIVE when no fresh node.
     LOCALIZED is never emitted — no code path produces it.
   - hold: baseline-protection flag for the existing EMA baseline (see
     updateSlotDisturbance hold). Held only while a directional (NEAR-A /
     NEAR-B) leader persists across consecutive evaluations, so an active
     event is not absorbed as baseline while genuine common-mode drift
     (BETWEEN leader) still adapts. STREAK_HOLD/STREAK_ESTIMATE are temporal
     presentation-stability counts, not detection thresholds and not spatial
     thresholds: they assert nothing about the world, only that a presented
     claim/protection persists across evaluations instead of flickering. */

export const APPROX_FRAME = Object.freeze({ tag: "APPROX_NORMALIZED" });

export const ZONE_KEYS = ["nearA", "nearB", "between"];

export const ZONE_LABEL = { nearA: "NEAR-A", nearB: "NEAR-B", between: "BETWEEN" };

// Consecutive-evaluation counts for presentation stability (see header).
export const STREAK_HOLD = 2;
export const STREAK_ESTIMATE = 3;

function clean(v) {
  return (typeof v === "number" && Number.isFinite(v) && v > 0) ? v : 0;
}

function clamp01(v) {
  if (!Number.isFinite(v)) return 0;
  return Math.max(0, Math.min(1, v));
}

// Deterministic leader among zone scores. Exact ties (measure-zero) break
// toward the directional zones in fixed order — documented, no threshold.
function pickLeader(zones) {
  let best = null;
  for (const k of ["nearA", "nearB", "between"]) {
    if (best === null || zones[k] > zones[best]) best = k;
  }
  return best;
}

export function zoneEvidence(dA, dB) {
  const a = clean(dA), b = clean(dB);
  const total = a + b;
  if (!(total > 0)) {
    return {
      zones: { nearA: 0, nearB: 0, between: 0 },
      leader: null, total: 0,
    };
  }
  const sA = clamp01(a / total), sB = clamp01(b / total);
  const zones = {
    nearA: sA,
    nearB: sB,
    // Balanced two-node response reads as BETWEEN; a one-sided response
    // drives it toward 0. Relative evidence only — never a position.
    between: clamp01(1 - Math.abs(sA - sB)),
  };
  return { zones, leader: pickLeader(zones), total };
}

export function emptyStreak() {
  return { zone: null, count: 0 };
}

function isDirectional(leader) {
  return leader === "nearA" || leader === "nearB";
}

// Pure state machine. streak: previous {zone, count} (pass emptyStreak()
// after placement/source change to invalidate the old arrangement).
// obs: {dA, dB, freshA, freshB, now} — freshness is caller-owned (existing
// STALE rule); `now` is caller-provided so output stays deterministic.
// Returns {field, streak, hold}.
export function updateField(streak, obs) {
  const prev = (streak && typeof streak.count === "number") ? streak : emptyStreak();
  const o = obs || {};
  const freshA = o.freshA === true, freshB = o.freshB === true;
  const now = (typeof o.now === "number" && Number.isFinite(o.now)) ? o.now : null;

  const sourceNodes = [];
  if (freshA) sourceNodes.push("A");
  if (freshB) sourceNodes.push("B");

  let zones = { nearA: 0, nearB: 0, between: 0 };
  let leader = null;
  let tier = "RF_ACTIVITY";
  let stale = true;

  if (!freshA && !freshB) {
    tier = "NO_LIVE";
  } else if (freshA && freshB) {
    stale = false;
    const ev = zoneEvidence(o.dA, o.dB);
    zones = ev.zones;
    leader = ev.leader; // null while quiet (total == 0)
  } else {
    // One healthy node: activity evidence only. No differential exists, so
    // none is fabricated — zones stay zero, staleness stays flagged.
    stale = true;
  }

  let next = emptyStreak();
  if (leader !== null && leader === prev.zone) {
    next = { zone: leader, count: prev.count + 1 };
  } else if (leader !== null) {
    next = { zone: leader, count: 1 };
  }

  // A held DIRECTIONAL leader promotes activity to an approximate estimate.
  // BETWEEN leaders, quiet, single-node, and stale inputs can never promote.
  if (tier === "RF_ACTIVITY" && !stale && isDirectional(leader) &&
      next.count >= STREAK_ESTIMATE) {
    tier = "RF_ESTIMATE";
  }

  // Baseline protection: while a directional leader holds across consecutive
  // evaluations, the EMA baseline must not absorb the event. Released the
  // moment direction is lost — drift (common-mode/BETWEEN) always adapts.
  const hold = !stale && isDirectional(leader) && next.count >= STREAK_HOLD;

  const uncertainty = tier === "RF_ESTIMATE"
    ? "APPROXIMATE · ZONE-SCALE · PLACEMENT UNMEASURED"
    : (tier === "RF_ACTIVITY" ? "NO SPATIAL CLAIM" : "NO DATA");

  return {
    field: {
      mode: "APPROXIMATE",
      coordinateFrame: APPROX_FRAME.tag,
      evidenceTier: tier,
      zones, leader, uncertainty, sourceNodes,
      timestamp: now, stale,
    },
    streak: next,
    hold,
  };
}

// One-line HUD/aria summary with honest semantics baked into the wording.
export function fieldSummary(field) {
  if (!field) return "NO LIVE RF DATA";
  if (field.evidenceTier === "RF_ESTIMATE" && field.leader) {
    return `APPROXIMATE RF EVIDENCE · RF ESTIMATE · ${ZONE_LABEL[field.leader]} (candidate — NOT VALIDATED · NOT CALIBRATED)`;
  }
  if (field.evidenceTier === "RF_ACTIVITY") {
    return "APPROXIMATE RF EVIDENCE · RF ACTIVITY (change without direction — NO LOCATION CLAIM)";
  }
  return "NO LIVE RF DATA";
}
