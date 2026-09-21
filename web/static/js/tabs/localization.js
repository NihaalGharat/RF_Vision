/* Localization tab — 1-D link framework only.
   RF Vision native. Coordinate system, node registry, calibration status,
   position + uncertainty, sync state. 2-D/3-D reserved, never claimed. */
import { api } from "../api.js";
import { pillFor, fmtUnknown } from "../banner.js";
import { drawBars } from "../viz2d.js";

export const LocalizationTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Estimate (link-1d)</h3><div class="kv" id="lc-est"></div>
          <p class="caveat">1-D link-relative only. No 2-D/3-D claim exists.</p></div>
        <div class="card"><h3>Uncertainty</h3><canvas class="viz" id="lc-bars"></canvas></div>
        <div class="card"><h3>Node registry</h3><div class="kv" id="lc-nodes"></div></div>
        <div class="card"><h3>Calibration / sync</h3><div class="kv" id="lc-cal"></div></div>
      </div>`;
    this.refresh();
  },
  onShow() { this.refresh(); },
  onEvent(ev) {
    if (ev && ev.type === "sensing.snapshot") {
      const p = ev.payload;
      this._pos = (typeof p.position === "number") ? p.position : null;
      this._posM = (typeof p.position_m === "number") ? p.position_m : null;
      this.renderEst();
    }
  },
  async refresh() {
    try {
      const [loc, cal] = await Promise.all([api.localization(), api.calibration()]);
      this._loc = loc;
      this._cal = cal;
    } catch {
      this._loc = null;
      this._cal = null;
    }
    this.renderAll();
  },
  kv(id, rows) {
    this.el.querySelector(`#${id}`).innerHTML =
      rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
  renderAll() {
    const loc = this._loc, cal = this._cal;
    this.kv("lc-nodes", (loc ? loc.nodes : []).map((n) =>
      [n.id, `${n.role} · pos: ${n.position_m === null ? "UNKNOWN" : `${n.position_m} m`}`]));
    if (!loc || !loc.nodes.length) {
      this.kv("lc-nodes", [["nodes", `<span class="unknown">UNREACHABLE / UNKNOWN</span>`]]);
    }
    this.kv("lc-cal", [
      ["calibration", cal ? cal.status : "UNKNOWN"],
      ["room width", cal ? fmtUnknown(cal.room_width_m, (v) => `${v} m`) : "UNKNOWN"],
      ["sync", loc ? loc.sync : "UNKNOWN"],
      ["frame", loc ? loc.frame : "UNKNOWN"],
    ]);
    this.renderEst();
  },
  renderEst() {
    const snap = this.ctx.store.snapshot();
    this.kv("lc-est", [
      ["source", pillFor(snap.state)],
      ["position t", fmtUnknown(this._pos, (v) => v.toFixed(3))],
      ["position (m)", fmtUnknown(this._posM, (v) => v.toFixed(2))],
      ["uncertainty", `<span class="unknown">UNKNOWN (no validated estimator)</span>`],
    ]);
    drawBars(this.el.querySelector("#lc-bars"), [
      { label: "position t", value: this._pos ?? null, color: "#e0a63c" },
      { label: "uncertainty", value: null },
    ]);
  },
};
