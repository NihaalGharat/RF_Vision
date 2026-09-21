/* Sensing tab — CSI stream status, RSSI, amplitude/phase, heatmap,
   packet statistics, presence/activity FIELDS (unvalidated).
   RF Vision native; viz via js/viz2d.js (dependency-free canvas). */
import { drawHeatmap, drawSparkline, drawBars } from "../viz2d.js";
import { pillFor } from "../banner.js";

const AMP_ROWS = 40;
const RSSI_N = 120;

export const SensingTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    this.amps = [];
    this.rssi = [];
    this._last = null;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Stream</h3><div class="kv" id="sn-stream"></div></div>
        <div class="card"><h3>Presence / activity (unvalidated fields)</h3>
          <canvas class="viz" id="sn-bars"></canvas>
          <p class="caveat">UI fields only until CSI-SENSE validation. Do not cite.</p></div>
        <div class="card"><h3>RSSI (dBm)</h3><canvas class="viz" id="sn-rssi"></canvas></div>
      </div>
      <div class="grid" style="margin-top:12px">
        <div class="card"><h3>Subcarrier amplitude heatmap (latest ${AMP_ROWS} frames)</h3>
          <canvas class="viz" id="sn-heat"></canvas></div>
        <div class="card"><h3>Packets</h3><div class="kv" id="sn-packets"></div></div>
      </div>`;
    this.renderStream();
    this.paint();
  },
  onState() { this.renderStream(); },
  onEvent(ev) {
    if (!ev || ev.type !== "sensing.snapshot") return;
    this._last = ev;
    const p = ev.payload;
    if (Array.isArray(p.amplitudes) && p.amplitudes.length) {
      this.amps.push(p.amplitudes);
      if (this.amps.length > AMP_ROWS) this.amps.shift();
    }
    if (typeof p.rssi === "number") {
      this.rssi.push(p.rssi);
      if (this.rssi.length > RSSI_N) this.rssi.shift();
    }
    this.paint();
  },
  onShow() { this.paint(); },
  canvas(id) { return this.el.querySelector(`#${id}`); },
  renderStream() {
    const snap = this.ctx.store.snapshot();
    const node = this.el.querySelector("#sn-stream");
    const ws = `ws: ${snap.wsState}`;
    node.innerHTML = [
      ["source", pillFor(snap.state)],
      ["transport", ws],
      ["frames buffered", this.amps.length],
      ["age", snap.ageMs === null ? "no frames" : `${(snap.ageMs / 1000).toFixed(1)} s`],
    ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    const pk = this.el.querySelector("#sn-packets");
    if (pk) {
      const ev = this._last;
      pk.innerHTML = [
        ["last seq", ev ? ev.seq : "—"],
        ["subcarriers", ev && ev.payload.amplitudes ? ev.payload.amplitudes.length : "—"],
        ["phase vector", ev && ev.payload.phases ? `${ev.payload.phases.length} (gated)` : "gated / absent"],
        ["validated", ev ? String(ev.payload.validated) : "—"],
      ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
  },
  paint() {
    drawHeatmap(this.canvas("sn-heat"), this.amps);
    drawSparkline(this.canvas("sn-rssi"), this.rssi, { label: "rssi" });
    const p = this._last ? this._last.payload : null;
    drawBars(this.canvas("sn-bars"), [
      { label: "presence_prob", value: p ? p.presence_prob : null },
      { label: "movement_prob", value: p ? p.movement_prob : null },
      { label: "confidence", value: p ? p.confidence : null },
    ]);
    this.renderStream();
  },
};
