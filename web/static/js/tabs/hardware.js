/* Hardware tab — validated baseline display + live link state.
   RF Vision native. Baseline values come from the backend (constants gated
   by docs/hardware/BASELINE.md); anything unverified renders UNKNOWN. */
import { api } from "../api.js";
import { pillFor } from "../banner.js";

export const HardwareTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Validated baseline (unchanged)</h3><div class="kv" id="hw-base"></div></div>
        <div class="card"><h3>Link state</h3><div class="kv" id="hw-link"></div>
          <p class="state-note">Firmware identity is UNKNOWN until a read-back
          is possible without reset (blocked in this phase).</p></div>
      </div>`;
    this.refresh();
  },
  onShow() { this.refresh(); },
  onState() { this.renderLink(); },
  async refresh() {
    try {
      this._exp = await api.experiment();
    } catch {
      this._exp = null;
    }
    this.renderAll();
  },
  renderAll() {
    const e = this._exp;
    const base = this.el.querySelector("#hw-base");
    if (!e) {
      base.innerHTML = `<dt>baseline</dt><dd><span class="unknown">BACKEND UNREACHABLE</span></dd>`;
    } else {
      const h = e.hardware, f = e.firmware;
      base.innerHTML = [
        ["esp32", h.esp32], ["flash", `${h.flash_mb} MB`],
        ["csi stack", h.csi_stack], ["router", h.router],
        ["band", h.band], ["transport", h.transport],
        ["firmware", `${f.name} (esp-csi ${f.esp_csi_commit.slice(0, 8)})`],
        ["esp-idf", f.esp_idf],
      ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
    this.renderLink();
  },
  renderLink() {
    const snap = this.ctx.store.snapshot();
    const e = this._exp;
    this.el.querySelector("#hw-link").innerHTML = [
      ["source", pillFor(snap.state)],
      ["serial", `<span class="unknown">UNKNOWN (no live probe this phase)</span>`],
      ["firmware identity", e ? e.firmware.identity : "UNKNOWN"],
      ["last packet", snap.ageMs === null ? "none this session" : `${(snap.ageMs / 1000).toFixed(1)} s ago`],
      ["capture state", snap.state === "DISCONNECTED" ? "idle — live blocked by 003R" : snap.state],
    ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
};
