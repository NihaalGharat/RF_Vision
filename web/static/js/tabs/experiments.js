/* Experiments tab — session provenance + source/stream controls.
   RF Vision native. Prepares CSI-SENSE-001 bookkeeping (session, config,
   hardware, firmware, software, geometry, raw-data ref, checksum,
   validation). Runs nothing. Stream/source controls live here because
   choosing a data source IS an experiment decision. */
import { api } from "../api.js";
import { pillFor } from "../banner.js";

export const ExperimentsTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card" style="grid-column: span 2">
          <h3>Active session provenance</h3><div class="kv" id="ex-prov"></div></div>
        <div class="card"><h3>Data source (explicit choice)</h3>
          <div class="row">
            <select class="btn" id="ex-source">
              <option value="off">disconnected</option>
              <option value="fixture">offline fixture</option>
              <option value="simulated">simulated (mock)</option>
              <option value="live" disabled>live — blocked by 003R</option>
            </select>
            <button class="btn primary" id="ex-start">Start stream</button>
            <button class="btn" id="ex-stop">Stop</button>
          </div>
          <p class="state-note" id="ex-msg">Choose a source, then start. Fixture and
          simulated are never live.</p></div>
      </div>`;
    el.querySelector("#ex-start").addEventListener("click", () => this.apply(true));
    el.querySelector("#ex-stop").addEventListener("click", () => this.apply(false));
    this.refresh();
  },
  onShow() { this.refresh(); },
  async apply(start) {
    const msg = this.el.querySelector("#ex-msg");
    const mode = this.el.querySelector("#ex-source").value;
    try {
      await api.setSource(mode);
      this.ctx.store.setBaseState(
        mode === "off" ? "DISCONNECTED" : mode === "fixture" ? "OFFLINE_FIXTURE" : "SIMULATED");
      if (start) {
        await api.streamStart();
        this.ctx.ws.send({ command: "stream:start" });
      } else {
        await api.streamStop();
      }
      msg.textContent = `source=${mode}, stream=${start ? "started" : "stopped"}.`;
    } catch (e) {
      msg.textContent = `failed: ${e.message}`;
    }
    this.refresh();
  },
  async refresh() {
    let exp = null, stream = null;
    try {
      [exp, stream] = await Promise.all([api.experiment(), api.streamStatus()]);
    } catch { /* unreachable backend */ }
    const node = this.el.querySelector("#ex-prov");
    if (!exp) {
      node.innerHTML = `<dt>session</dt><dd><span class="unknown">BACKEND UNREACHABLE</span></dd>`;
      return;
    }
    const g = exp.geometry || {};
    node.innerHTML = [
      ["session", exp.session_id],
      ["source", pillFor(this.ctx.store.snapshot().state)],
      ["stream", stream ? `${stream.mode} · running=${stream.running}` : "UNKNOWN"],
      ["software", JSON.stringify(exp.software)],
      ["hardware", `${exp.hardware.esp32} · ${exp.hardware.router} · ${exp.hardware.band} · ${exp.hardware.transport}`],
      ["firmware", `${exp.firmware.name} · esp-csi ${exp.firmware.esp_csi_commit.slice(0, 8)} · identity ${exp.firmware.identity}`],
      ["geometry", `room ${g.room_width_m ?? "UNKNOWN"} × ${g.room_length_m ?? "UNKNOWN"} (${g.status})`],
      ["raw data", exp.raw_ref ? JSON.stringify(exp.raw_ref) : "none — no capture this session"],
      ["validation", exp.validation],
    ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
};
