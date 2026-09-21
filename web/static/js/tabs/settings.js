/* Settings tab — console preferences (no sensing semantics).
   RF Vision native: theme, stream cadence display, reduced-motion note,
   danger-zone documentation (actions this console will NOT take). */
import { api } from "../api.js";

export const SettingsTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Appearance</h3>
          <div class="row">
            <button class="btn" id="set-theme">Toggle light / dark</button>
          </div>
          <p class="state-note">Honors <code>prefers-reduced-motion</code> for the 3D scene.</p></div>
        <div class="card"><h3>Backend</h3><div class="kv" id="set-back"></div></div>
        <div class="card"><h3>Out of scope for this console</h3>
          <div class="kv">
            <dt>flash / erase / reset</dt><dd>never</dd>
            <dt>router changes</dt><dd>never</dd>
            <dt>live capture</dt><dd>diagnostic only (≤30 s, explicit, via Experiments)</dd>
            <dt>human experiments</dt><dd>not in this phase</dd>
            <dt>model training</dt><dd>not in this phase</dd>
          </div></div>
      </div>`;
    el.querySelector("#set-theme").addEventListener("click", () => {
      const root = document.documentElement;
      const next = root.dataset.theme === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try { localStorage.setItem("rfvision-theme", next); } catch { /* private mode */ }
    });
    try {
      const saved = localStorage.getItem("rfvision-theme");
      if (saved === "light" || saved === "dark") document.documentElement.dataset.theme = saved;
    } catch { /* private mode */ }
    this.refresh();
  },
  onShow() { this.refresh(); },
  async refresh() {
    let h = null;
    try {
      h = await api.health();
    } catch { /* unreachable */ }
    this.el.querySelector("#set-back").innerHTML = h
      ? `<dt>health</dt><dd>${h.status} · contract v${h.contract}</dd>
         <dt>uptime</dt><dd>${Math.round(h.uptime_s)} s</dd>
         <dt>source</dt><dd>${h.source} · ${h.source_state}</dd>`
      : `<dt>backend</dt><dd><span class="unknown">UNREACHABLE</span></dd>`;
  },
};
