/* Hardware tab — validated baseline + ACTUAL live link health.
   RF Vision native. Baseline values come from the backend (constants gated
   by docs/hardware/BASELINE.md); link health comes from /api/v1/live.
   Anything unverified renders UNKNOWN. */
import { pillFor, fetchErrors } from "../banner.js";

export const HardwareTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Receiver — validated baseline</h3>
          <div class="kv" id="hw-base"></div></div>
        <div class="card"><h3>Link state — live</h3>
          <div class="kv" id="hw-link"></div></div>
        <div class="card"><h3>Transport diagnostics</h3>
          <div class="kv" id="hw-diag"></div>
          <p class="state-note">Firmware identity stays UNKNOWN until a
          read-back is possible without reset. No flash / erase / reset is
          ever initiated from this console.</p></div>
      </div>`;
    this.refresh();
    this.ctx.poll.acquire("hardware", ["experiment", "live"],
      (view) => this.onPoll(view));
  },
  onHide() { this.ctx.poll.release("hardware"); },
  onShow() {
    this.ctx.poll.acquire("hardware", ["experiment", "live"],
      (view) => this.onPoll(view));
    this.refresh();
  },
  onPoll(view) {
    this._exp = view.data.experiment || null;
    const live = view.data.live;
    this._live = live && live.available ? live : null;
    this._view = view;
    this.renderAll();
  },
  onState() { this.renderLink(); },
  async refresh() {
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
        ["receiver", h.receiver || h.esp32],
        ["mac", h.receiver_mac || "UNKNOWN"],
        ["flash", `${h.flash_mb} MB`],
        ["csi stack", h.csi_stack],
        ["router", h.router],
        ["band", h.band],
        ["firmware", `${f.name} (esp-csi ${f.esp_csi_commit.slice(0, 8)})`],
        ["esp-idf", f.esp_idf],
        ["cp2102", "USB-UART bridge → /dev/ttyUSB0"],
      ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
    this.renderLink();
  },
  renderLink() {
    const snap = this.ctx.store.snapshot();
    const L = this._live;
    const link = [
      ["source", pillFor(snap.state)],
      ["serial", L ? `${L.port} @ ${L.baud} 8N1` : `<span class="unknown">UNKNOWN (no live session)</span>`],
      ["transport", L ? (L.transport.open ? "open" : "closed") : "UNKNOWN"],
      ["throughput", L && L.transport.bytes_per_s != null
        ? `${(L.transport.bytes_per_s / 1000).toFixed(1)} kB/s` : "UNKNOWN"],
      ["last packet", snap.ageMs === null ? "none this session" : `${(snap.ageMs / 1000).toFixed(1)} s ago`],
    ];
    this.el.querySelector("#hw-link").innerHTML =
      link.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    const diag = L ? [
      ["channel", L.signal.channel != null ? `CH ${L.signal.channel}` : "UNKNOWN"],
      ["bssid", L.signal.bssid || "UNKNOWN"],
      ["csi length", L.signal.csi_len != null ? L.signal.csi_len : "UNKNOWN"],
      ["tones", L.signal.tones != null ? L.signal.tones : "UNKNOWN"],
      ["transport error", L.transport.error || "none"],
      ["firmware identity", (this._exp ? this._exp.firmware.identity : "UNKNOWN")],
    ] : [["diagnostics", `<span class="unknown">NO LIVE SESSION</span>`]];
    if (this._view) {
      const errs = fetchErrors(this._view, ["experiment", "live"]);
      if (errs) diag.push(["poll", errs]);
    }
    this.el.querySelector("#hw-diag").innerHTML =
      diag.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
  },
};
