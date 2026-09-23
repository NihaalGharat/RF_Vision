/* Overview tab — RF Vision / Sensor / CSI / System / Research.
   RF Vision native. Every value is read live from the backend; anything
   unavailable renders UNKNOWN, never invented. */
import { api } from "../api.js";
import { pillFor, fmtUnknown } from "../banner.js";

const num = (v, f) => fmtUnknown(v, f);

export const OverviewTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    this._last = null;
    el.innerHTML = `
      <div class="grid">
        <div class="card card-hero"><h3>RF Vision</h3>
          <div class="hero-state" id="ov-hero">…</div>
          <div class="kv" id="ov-sys"></div></div>
        <div class="card"><h3>Sensor — ESP32 receiver</h3>
          <div class="kv" id="ov-sensor"></div></div>
        <div class="card"><h3>CSI — live signal</h3>
          <div class="kv" id="ov-csi"></div></div>
        <div class="card"><h3>System — backend / stream</h3>
          <div class="kv" id="ov-backend"></div></div>
        <div class="card"><h3>Research — validation state</h3>
          <div class="kv" id="ov-research"></div>
          <p class="caveat">Calibration, localization and XAI are not
          validated. Telemetry above is transport + signal only.</p></div>
        <div class="card"><h3>Latest frame</h3>
          <div class="kv" id="ov-frame"></div></div>
        <div class="card"><h3>Nodes — two-node telemetry</h3>
          <div class="kv" id="ov-sync"></div>
          <div class="kv" id="ov-node-a"></div>
          <div class="kv" id="ov-node-b"></div>
          <p class="caveat">Localization not validated: zones stay
          AWAITING VALIDATED LOCALIZATION DATA.</p></div>
      </div>`;
    this.refresh();
    this._timer = setInterval(() => this.refresh(), 2000);
  },
  onHide() { if (this._timer) { clearInterval(this._timer); this._timer = null; } },
  onShow() {
    if (!this._timer) this._timer = setInterval(() => this.refresh(), 2000);
    this.refresh();
  },
  onState() { this.renderHero(); this.renderFrame(); },
  onEvent(ev) {
    if (ev && ev.type === "sensing.snapshot") {
      this._last = ev;
      this.renderFrame();
    }
  },
  kv(id, rows) {
    const node = this.el.querySelector(`#${id}`);
    if (node) {
      node.innerHTML = rows.map(([k, v]) =>
        `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
  },
  async refresh() {
    let status = null, exp = null, live = null, nodes = null;
    try {
      [status, exp] = await Promise.all([api.status(), api.experiment()]);
    } catch { /* unreachable backend */ }
    try {
      live = await api.live();
    } catch { live = null; }
    try {
      nodes = await api.nodes();
    } catch { nodes = null; }
    this._status = status;
    this._exp = exp;
    this._live = live && live.available ? live : null;
    this._nodes = nodes && nodes.available ? nodes : null;
    this.renderAll();
  },
  renderHero() {
    const snap = this.ctx.store.snapshot();
    const s = this._status;
    const hero = this.el.querySelector("#ov-hero");
    if (hero) {
      hero.innerHTML = `${pillFor(snap.state)}
        <span class="hero-sub">${s ? s.connection : "UNKNOWN"} · ` +
        `${s && s.csi_rate != null ? `${s.csi_rate.toFixed(1)} Hz` : "rate UNKNOWN"}</span>`;
    }
    this.kv("ov-sys", [[
      "source", pillFor(snap.state),
    ]]);
  },
  renderAll() {
    const s = this._status, e = this._exp, L = this._live;
    this.renderHero();
    this.kv("ov-sys", [
      ["backend", s ? "reachable" : `<span class="unknown">UNREACHABLE</span>`],
      ["connection", s ? s.connection : "UNKNOWN"],
      ["stream", e ? e.session_id : "UNKNOWN"],
      ["validation", e ? e.validation : "UNKNOWN"],
    ]);
    const hw = e ? e.hardware : null;
    this.kv("ov-sensor", [
      ["sensor", hw ? (hw.receiver || hw.esp32) : "UNKNOWN"],
      ["mac", hw ? (hw.receiver_mac || "UNKNOWN") : "UNKNOWN"],
      ["serial", hw ? (hw.serial || hw.transport || "UNKNOWN") : "UNKNOWN"],
      ["link", L ? (L.transport.open ? "serial open" : "serial closed") : "UNKNOWN"],
      ["firmware", e ? `${e.firmware.name} · esp-csi ${e.firmware.esp_csi_commit.slice(0, 8)}` : "UNKNOWN"],
    ]);
    this.kv("ov-csi", L ? [
      ["record rate", num(L.stream.rate_hz, (v) => `${v.toFixed(1)} Hz`)],
      ["valid", num(L.stream.valid_pct, (v) => `${v.toFixed(2)} %`)],
      ["rssi", L.signal.rssi_last != null
        ? `${L.signal.rssi_last} dBm (${L.signal.rssi_trend || "trend ?"})` : "UNKNOWN"],
      ["channel", L.signal.channel != null ? `CH ${L.signal.channel}` : "UNKNOWN"],
      ["tones", num(L.signal.tones, (v) => `${v} subcarriers`)],
      ["seq", L.stream.last_seq != null
        ? `${L.stream.last_seq} · ${L.stream.gaps} gap(s)` : "UNKNOWN"],
    ] : [
      ["record rate", "UNKNOWN"], ["valid", "UNKNOWN"], ["rssi", "UNKNOWN"],
      ["channel", "UNKNOWN"], ["tones", "UNKNOWN"], ["seq", "UNKNOWN"],
    ]);
    this.kv("ov-backend", [
      ["packets (shown)", s ? s.packets : "UNKNOWN"],
      ["malformed", s ? s.malformed : "UNKNOWN"],
      ["frame age", s && s.last_frame_age_s != null
        ? `${s.last_frame_age_s.toFixed(1)} s${s.stale ? " — STALE" : ""}` : "no frames"],
      ["contract", e ? `v${e.software.contract}` : "UNKNOWN"],
      ["console", e ? `web ${e.software.rfvision_web}` : "UNKNOWN"],
    ]);
    this.kv("ov-research", [
      ["calibration", `<span class="unknown">UNCALIBRATED</span>`],
      ["localization", `<span class="unknown">NOT VALIDATED</span>`],
      ["xai", `<span class="unknown">NOT AVAILABLE</span>`],
      ["models", `<span class="unknown">NO VALIDATED MODELS</span>`],
    ]);
    this.renderNodes();
    this.renderFrame();
  },
  renderNodes() {
    const N = this._nodes;
    if (!N) {
      const standby = `<span class="unknown">STANDBY (dual session not started)</span>`;
      this.kv("ov-sync", [["sync", standby]]);
      this.kv("ov-node-a", [["node A", standby]]);
      this.kv("ov-node-b", [["node B", standby]]);
      return;
    }
    this.kv("ov-sync", [["sync state", N.sync_state]]);
    const byId = {};
    for (const n of (N.nodes || [])) byId[n.node_id] = n;
    for (const [slot, id] of [["ov-node-a", "esp32-a"], ["ov-node-b", "esp32-b"]]) {
      const n = byId[id];
      if (!n) {
        this.kv(slot, [[id, `<span class="unknown">NO DATA</span>`]]);
        continue;
      }
      const us = (v) => (v != null ? `${(v / 1000).toFixed(1)} ms` : "UNKNOWN");
      const bad = n.connection === "DEGRADED" || n.connection === "DISCONNECTED";
      const stateCell = bad
        ? `<span class="err-text">${n.connection} — DEGRADED MODE</span>`
        : n.connection;
      this.kv(slot, [
        ["state", stateCell],
        ["rate", num(n.csi_rate, (v) => `${v.toFixed(1)} Hz`)],
        ["valid", n.valid_pct != null ? `${n.valid_pct.toFixed(2)} % (${n.valid})` : "UNKNOWN"],
        ["rssi", n.rssi != null ? `${n.rssi} dBm` : "UNKNOWN"],
        ["seq gaps / dup / ooo", `${n.gaps} / ${n.duplicates} / ${n.out_of_order}`],
        ["channel / bssid", `${n.channel != null ? "CH " + n.channel : "?"} · ${n.bssid || "?"}`],
        ["tones", n.tones != null ? `${n.tones}` : "UNKNOWN"],
        ["sync offset / jitter", `${us(n.sync_offset_ns)} / ${us(n.sync_jitter_ns)}`],
        ["pipe (host)", n.host_pipeline_us_mean != null
          ? `${n.host_pipeline_us_mean.toFixed(0)} µs mean` : "UNKNOWN"],
      ]);
    }
  },
  renderFrame() {
    const ev = this._last;
    const snap = this.ctx.store.snapshot();
    if (!ev) {
      this.kv("ov-frame", [["state", `no frames yet (${snap.state})`]]);
      return;
    }
    const p = ev.payload;
    this.kv("ov-frame", [
      ["source", pillFor(p.source_state || snap.state)],
      ["seq", ev.seq],
      ["rssi (dBm)", num(p.rssi, (v) => v.toFixed(0))],
      ["tones", Array.isArray(p.amplitudes) ? p.amplitudes.length : "UNKNOWN"],
      ["presence", `${p.presence} <span class="state-note">(NOT VALIDATED)</span>`],
      ["showcase", p.presence_state && p.presence_state !== "UNKNOWN"
        ? `${p.presence_state} · RF-evidence ` +
          `${p.rf_evidence_confidence != null
            ? (p.rf_evidence_confidence * 100).toFixed(0) + " %"
            : "none"} ` +
          `<span class="state-note">(UNCALIBRATED, ` +
          `${p.provenance || "?"}, ${p.node_mode || "?"})</span>`
        : "no inference attached"],
    ]);
  },
};
