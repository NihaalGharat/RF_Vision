/* Experiments tab — live session provenance + evidence (research side).
   RF Vision native. Shows the ACTIVE live session (id, board, firmware,
   start, state, counts, raw-capture state, validation): the scientific
   record of what produced the current evidence. Engineering controls
   (data-source choice, stream start/stop, diagnostic capture) and live
   acquisition telemetry live in the System acquisition surface, never
   duplicated here. Never starts a CSI-SENSE human experiment. */
import { pillFor, fetchErrors } from "../banner.js";

export const ExperimentsTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid grid-gap">
        <div class="card">
          <h3>Active session provenance</h3><div class="kv" id="ex-prov"></div></div>
      </div>`;
    this.refresh();
    this.ctx.poll.acquire("experiments", ["experiment", "streamStatus"],
      (view) => this.onPoll(view));
  },
  onHide() { this.ctx.poll.release("experiments"); },
  onShow() {
    this.ctx.poll.acquire("experiments", ["experiment", "streamStatus"],
      (view) => this.onPoll(view));
    this.refresh();
  },
  onPoll(view) {
    this._exp = view.data.experiment || null;
    this._stream = view.data.streamStatus || null;
    this._view = view;
    this.renderAll();
  },
  async refresh() {
    this.renderAll();
  },
  renderAll() {
    const exp = this._exp, stream = this._stream;
    const prov = this.el.querySelector("#ex-prov");
    if (!prov) return;
    if (!exp) {
      prov.innerHTML = `<dt>session</dt><dd><span class="unknown">BACKEND UNREACHABLE</span></dd>`;
      return;
    }
    const g = exp.geometry || {};
    const errs = this._view ? fetchErrors(this._view) : "";
    prov.innerHTML = errs + [
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
