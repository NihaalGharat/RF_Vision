/* Phase 3 pytest driver: exercises the real spatial.js + pernode.js modules
   (imported by absolute path from argv) against batched JSON scenarios on
   stdin, prints one JSON line per scenario on stdout. Run with node only —
   no DOM, no build step. */
import { createRequire } from "module";

const base = process.argv[2];
const spatial = await import(`${base}/web/static/react/js/services/spatial.js`);
const pernode = await import(`${base}/web/static/react/js/services/pernode.js`);

let buf = "";
for await (const chunk of process.stdin) buf += chunk;
// Tagged non-finite revival: Python-side sends {"$num": "NaN"|"Infinity"|"-Infinity"}.
const revive = (v) => {
  if (Array.isArray(v)) return v.map(revive);
  if (v && typeof v === "object") {
    if (typeof v.$num === "string") {
      return v.$num === "NaN" ? NaN : (v.$num.startsWith("-") ? -Infinity : Infinity);
    }
    const o = {};
    for (const k of Object.keys(v)) o[k] = revive(v[k]);
    return o;
  }
  return v;
};
const scenarios = JSON.parse(buf).map(revive);

const out = [];
for (const sc of scenarios) {
  const r = { id: sc.id };
  try {
    if (sc.op === "zoneEvidence") {
      r.result = spatial.zoneEvidence(sc.dA, sc.dB);
    } else if (sc.op === "fieldSeq") {
      // Deterministic streak machine over a scripted observation sequence.
      let streak = spatial.emptyStreak();
      let last = null;
      for (const o of sc.seq) {
        last = spatial.updateField(streak, o);
        streak = last.streak;
      }
      r.result = { field: last.field, streak: last.streak, hold: last.hold };
    } else if (sc.op === "summary") {
      const last = spatial.updateField(spatial.emptyStreak(), sc.obs);
      r.result = { summary: spatial.fieldSummary(last.field), tier: last.field.evidenceTier };
    } else if (sc.op === "frameShape") {
      const last = spatial.updateField(spatial.emptyStreak(), sc.obs);
      const f = last.field;
      r.result = {
        keys: Object.keys(f).sort(),
        mode: f.mode, frame: f.coordinateFrame,
        hasXYZ: ("x" in f) || ("y" in f) || ("z" in f),
        hasMetres: JSON.stringify(f).toLowerCase().includes("metre") ||
          JSON.stringify(f).toLowerCase().includes("meter"),
        hasProb: "probability" in f,
      };
    } else if (sc.op === "holdBaseline") {
      // Real pernode EMA: persistent one-sided event vs common-mode drift.
      let slotA = { ...pernode.emptySlot(), amps: sc.baseA.slice(), baseline: sc.baseA.slice(), disturb: sc.baseA.map(() => 0), disturbMean: 0 };
      let slotB = { ...pernode.emptySlot(), amps: sc.baseB.slice(), baseline: sc.baseB.slice(), disturb: sc.baseB.map(() => 0), disturbMean: 0 };
      let streak = spatial.emptyStreak();
      let hold = false;
      const means = [];
      for (let i = 0; i < sc.frames; i++) {
        slotA = { ...slotA, amps: sc.eventA.slice() };
        slotB = { ...slotB, amps: sc.eventB.slice() };
        slotA = pernode.updateSlotDisturbance(slotA, pernode.BASELINE_ALPHA, hold);
        slotB = pernode.updateSlotDisturbance(slotB, pernode.BASELINE_ALPHA, hold);
        const u = spatial.updateField(streak, {
          dA: slotA.disturbMean, dB: slotB.disturbMean,
          freshA: true, freshB: true, now: i,
        });
        streak = u.streak;
        hold = u.hold;
        means.push([slotA.disturbMean, slotB.disturbMean, u.field.evidenceTier, u.hold]);
      }
      r.result = { means, finalTier: means[means.length - 1][2], everHold: means.some((m) => m[3]) };
    } else if (sc.op === "holdFreezes") {
      const slot = {
        ...pernode.emptySlot(), amps: sc.amps.slice(),
        baseline: sc.baseline.slice(),
        disturb: sc.amps.map(() => 0), disturbMean: 0,
      };
      const held = pernode.updateSlotDisturbance(slot, pernode.BASELINE_ALPHA, true);
      const free = pernode.updateSlotDisturbance(slot, pernode.BASELINE_ALPHA, false);
      r.result = {
        baselineFrozen: JSON.stringify(held.baseline) === JSON.stringify(sc.baseline),
        baselineMoved: JSON.stringify(free.baseline) !== JSON.stringify(sc.baseline),
        disturbFinite: held.disturb.every(Number.isFinite) && Number.isFinite(held.disturbMean),
      };
    } else {
      r.error = `unknown op ${sc.op}`;
    }
  } catch (e) {
    r.error = String((e && e.message) || e);
  }
  out.push(r);
}
console.log(JSON.stringify(out));
