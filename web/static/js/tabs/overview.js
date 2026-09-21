/* Overview tab — system/sensor/backend/source status + latest state.
   RF Vision native. Unknown values render UNKNOWN, never invented. */
import { api } from "../api.js";
import { pillFor, fmtUnknown } from "../banner.js";

export const OverviewTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>System status</h3><div class="kv" id="ov-sys">
          <dt>loading…</dt></div></div>
        <div class="card"><h3>Latest sensing state</h3><div class="kv" id="ov-sense">
          <dt>loading…</dt></div>
          <p class="caveat">Presence/activity are unvalidated UI fields — not conclusions.</p></div>
        <div class="card"><h3>Session / validation</h3><div class="kv" id="ov-exp">
          <dt>loading…</dt></div></div>
        <div class="card"><h3>RF link</h3><div class="kv" id="ov-link">
          <dt>loading…</dt></div></div>
      </div>`;
    this.refresh();
  },
  onShow() { this.refresh(); },
  onState() { this.renderSense(); },
  onEvent(ev) {
    if (ev && ev.type === "sensing.snapshot") {
      this._last = ev;
      this.renderSense();
    }
  },
  async refresh() {
    try {
      const [status, exp] = await Promise.all([api.status(), api.experiment()]);
      this._status = status;
      this._exp = exp;
    } catch (e) {
      this._status = null;
      this._exp = null;
    }
    this.renderAll();
  },
  kv(id, rows) {
    const node = this.el.querySelector(`#${id}`);
    node.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
  renderAll() {
    const s = this._status, e = this._exp;
    const snap = this.ctx.store.snapshot();
    this.kv("ov-sys", [
      ["source", pillFor(snap.state)],
      ["backend", s ? "reachable" : `<span class="unknown">UNREACHABLE</span>`],
      ["connection", s ? s.connection : "UNKNOWN"],
      ["packets", s ? s.packets : "UNKNOWN"],
      ["malformed", s ? s.malformed : "UNKNOWN"],
      ["stale", s ? String(s.stale) : "UNKNOWN"],
    ]);
    this.kv("ov-exp", [
      ["session", e ? e.session_id : "UNKNOWN"],
      ["validation", e ? e.validation : "UNKNOWN"],
      ["raw data", e && e.raw_ref ? JSON.stringify(e.raw_ref) : "none (no capture this session)"],
      ["web console", e ? e.software.rfvision_web : "UNKNOWN"],
    ]);
    this.kv("ov-link", [
      ["path", "Xiaomi AP → ESP32 → USB serial → console"],
      ["firmware identity", e ? e.firmware.identity : "UNKNOWN"],
      ["csi rate (Hz)", s ? fmtUnknown(s.csi_rate, (v) => v.toFixed(1)) : "UNKNOWN"],
      ["model", s ? s.model : "UNKNOWN"],
    ]);
    this.renderSense();
  },
  renderSense() {
    const ev = this._last;
    const snap = this.ctx.store.snapshot();
    if (!ev) {
      this.kv("ov-sense", [["state", `no frames yet (${snap.state})`]]);
      return;
    }
    const p = ev.payload;
    this.kv("ov-sense", [
      ["source", pillFor(p.source_state || snap.state)],
      ["presence", `${p.presence} <span class="state-note">(unvalidated)</span>`],
      ["movement", `${p.movement} <span class="state-note">(unvalidated)</span>`],
      ["rssi (dBm)", fmtUnknown(p.rssi, (v) => v.toFixed(1))],
      ["seq", ev.seq],
    ]);
  },
};
