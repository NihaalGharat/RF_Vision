/* Localization tab — 1-D link framework only.
   RF Vision native. Coordinate system, node registry, calibration status,
   position + uncertainty, sync state. 2-D/3-D reserved, never claimed. */
import { api } from "../api.js";
import { pillFor, fmtUnknown } from "../banner.js";
import { drawBars, describe } from "../viz2d.js";

export const LocalizationTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Estimate (link-1d)</h3><div class="kv" id="lc-est"></div>
          <p class="sub-label">Uncertainty</p>
          <canvas class="viz" id="lc-bars" role="img" aria-label="Position and uncertainty bars. No validated estimator."></canvas>
          <p class="caveat">1-D link-relative only. No 2-D/3-D claim exists.</p></div>
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
      this._loc = await api.localization();
    } catch {
      this._loc = null;
    }
    this.renderEst();
  },
  kv(id, rows) {
    this.el.querySelector(`#${id}`).innerHTML =
      rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
  renderEst() {
    const snap = this.ctx.store.snapshot();
    this.kv("lc-est", [
      ["localization", `<span class="unknown">NOT VALIDATED — framework only, no estimator</span>`],
      ["source", pillFor(snap.state)],
      ["position t", fmtUnknown(this._pos, (v) => v.toFixed(3))],
      ["position (m)", fmtUnknown(this._posM, (v) => v.toFixed(2))],
      ["uncertainty", `<span class="unknown">UNKNOWN (no validated estimator)</span>`],
    ]);
    drawBars(this.el.querySelector("#lc-bars"), [
      { label: "position t", value: this._pos ?? null },
      { label: "uncertainty", value: null },
    ]);
    describe(this.el.querySelector("#lc-bars"), this._pos != null
      ? `Position t=${this._pos.toFixed(3)}, NOT VALIDATED, uncertainty unknown.`
      : "Position and uncertainty bars. No validated estimator.");
  },
};
