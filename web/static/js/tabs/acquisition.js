/* Acquisition tab — source, stream, capture, live telemetry (system side).
   RF Vision native. Answers "is the instrument acquiring?": the physical
   data-source choice, stream start/stop, bounded diagnostic capture, and
   live session telemetry. Moved verbatim from the former experiments
   composition (same element IDs, same rendering, same API calls); the
   scientific provenance half stays in Research, never duplicated here.
   Diagnostic recording is bounded (≤30 s) and explicit only. */
import { api } from "../api.js";
import { pillFor, fetchErrors } from "../banner.js";

export const AcquisitionTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid grid-gap">
        <div class="card"><h3>Live session — telemetry</h3>
          <div class="kv" id="ex-live"></div></div>
        <div class="card"><h3>Data source (explicit choice)</h3>
          <div class="row">
            <select class="btn" id="ex-source">
              <option value="off">disconnected</option>
              <option value="fixture">offline fixture</option>
              <option value="simulated">simulated (mock)</option>
              <option value="live">live — /dev/ttyUSB0 @ 921600</option>
            </select>
            <button class="btn primary" id="ex-start">Start stream</button>
            <button class="btn" id="ex-stop">Stop</button>
          </div>
          <p class="state-note" id="ex-msg">Choose a source, then start. Fixture and
          simulated are never live. Live starts UNVERIFIED until the session gate passes.</p></div>
        <div class="card"><h3>Diagnostic capture (bounded)</h3>
          <div class="row">
            <button class="btn" id="ex-rec-start">Record 10 s</button>
            <button class="btn" id="ex-rec-stop">Stop + checksum</button>
          </div>
          <p class="state-note" id="ex-rec-msg">No automatic recording. Short
          diagnostics only (≤30 s), stored under research-data/, never committed.</p></div>
      </div>`;
    el.querySelector("#ex-start").addEventListener("click", () => this.apply(true));
    el.querySelector("#ex-stop").addEventListener("click", () => this.apply(false));
    el.querySelector("#ex-rec-start").addEventListener("click", () => this.record(true));
    el.querySelector("#ex-rec-stop").addEventListener("click", () => this.record(false));
    this.refresh();
    this.ctx.poll.acquire("acquisition", ["streamStatus", "live"],
      (view) => this.onPoll(view));
  },
  onHide() { this.ctx.poll.release("acquisition"); },
  onShow() {
    this.ctx.poll.acquire("acquisition", ["streamStatus", "live"],
      (view) => this.onPoll(view));
    this.refresh();
  },
  async apply(start) {
    const msg = this.el.querySelector("#ex-msg");
    const mode = this.el.querySelector("#ex-source").value;
    try {
      const res = await api.setSource(mode);
      if (res && res.source_state) this.ctx.store.setBaseState(res.source_state);
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
  async record(start) {
    const msg = this.el.querySelector("#ex-rec-msg");
    try {
      if (start) {
        const res = await api.recordStart(10);
        msg.textContent = `recording → ${res.path} (≤${res.max_seconds} s)`;
      } else {
        const res = await api.recordStop();
        const m = res.manifest;
        msg.textContent = m && m.path
          ? `saved ${m.bytes} B · sha256 ${m.sha256}` : "no recording was active";
      }
    } catch (e) {
      msg.textContent = `failed: ${e.message}`;
    }
    this.refresh();
  },
  onPoll(view) {
    this._stream = view.data.streamStatus || null;
    const live = view.data.live;
    this._live = live && live.available ? live : null;
    this._view = view;
    this.renderAll();
  },
  async refresh() {
    this.renderAll();
  },
  renderAll() {
    const stream = this._stream, live = this._live;
    const node = this.el.querySelector("#ex-live");
    const select = this.el.querySelector("#ex-source");
    if (stream && select && [...select.options].some((o) => o.value === stream.mode)) {
      select.value = stream.mode;  // reflect the ACTIVE source, not a wish
    }
    if (!node) return;
    node.innerHTML = live ? [
      ["session", live.session_id],
      ["board mac", live.board_mac],
      ["state", pillFor(live.source_state)],
      ["gate", live.gate.passed ? "VERIFIED" : `UNVERIFIED — ${live.gate.reasons.join("; ")}`],
      ["records", `${live.stream.valid} valid · ${live.stream.malformed} malformed`],
      ["raw capture", live.recording.path
        ? `${live.recording.active ? "recording" : "stopped"} · ${live.recording.bytes} B` : "idle (not recording)"],
      ["validation", "NOT_RUN — no human experiment in this phase"],
    ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("")
      : `<dt>live</dt><dd><span class="unknown">NO LIVE SESSION (select live source)</span></dd>`;
  },
};
