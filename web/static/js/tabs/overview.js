/* Overview tab — revamp Phase 4: SYSTEM → OBSERVATION → CONFIDENCE →
   EVIDENCE → NODE HEALTH → DETAIL.
   Every fact from the old equal-weight card wall is preserved, re-homed into
   the hero (primary), evidence + node table (secondary), or <details>
   sections (detail). Nothing deleted. Anything unavailable renders UNKNOWN. */
import { pillFor, fmtUnknown, fetchErrors } from "../banner.js";

const num = (v, f) => fmtUnknown(v, f);

export const OverviewTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    this._last = null;
    el.innerHTML = `
      <div class="hero-grid" id="ov-hero">
        <div class="hero-cell" id="ov-hero-sys"></div>
        <div class="hero-cell" id="ov-hero-obs"></div>
        <div class="hero-cell" id="ov-hero-conf"></div>
      </div>
      <div class="grid grid-gap">
        <div class="card"><h3>RF evidence — latest</h3>
          <div class="kv" id="ov-evidence"></div></div>
        <div class="card"><h3>Node health</h3>
          <div id="ov-nodes"></div>
          <p class="caveat">Localization not validated: zones stay
          AWAITING VALIDATED LOCALIZATION DATA.</p></div>
      </div>
      <div class="grid grid-gap" id="ov-detail">
        <details class="detail"><summary>Sensor — ESP32 receiver</summary>
          <div class="detail-body"><div class="kv" id="ov-sensor"></div></div></details>
        <details class="detail"><summary>CSI — live signal</summary>
          <div class="detail-body"><div class="kv" id="ov-csi"></div></div></details>
        <details class="detail"><summary>System — backend / stream</summary>
          <div class="detail-body"><div class="kv" id="ov-backend"></div>
          <div id="ov-errors"></div></div></details>
        <details class="detail"><summary>Research — validation state</summary>
          <div class="detail-body"><div class="kv" id="ov-research"></div>
          <p class="caveat">Calibration, localization and XAI are not
          validated. Telemetry above is transport + signal only.</p></div></details>
        <details class="detail"><summary>Latest frame</summary>
          <div class="detail-body"><div class="kv" id="ov-frame"></div></div></details>
      </div>`;
    this.ctx.poll.acquire("overview", ["status", "experiment", "live", "nodes"],
      (view) => this.onPoll(view));
  },
  onHide() { this.ctx.poll.release("overview"); },
  onShow() {
    this.ctx.poll.acquire("overview", ["status", "experiment", "live", "nodes"],
      (view) => this.onPoll(view));
    this.renderAll();
  },
  onState() { this.renderHero(); },
  onEvent(ev) {
    if (ev && ev.type === "sensing.snapshot") {
      this._last = ev;
      this.renderHero();
      this.renderEvidence();
      this.renderFrame();
    }
  },
  onPoll(view) {
    const d = view.data;
    this._status = d.status || null;
    this._exp = d.experiment || null;
    this._live = d.live && d.live.available ? d.live : null;
    this._nodes = d.nodes && d.nodes.available ? d.nodes : null;
    this._view = view;
    this.renderAll();
  },
  kv(id, rows) {
    const node = this.el.querySelector(`#${id}`);
    if (node) {
      node.innerHTML = rows.map(([k, v]) =>
        `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
  },
  setHtml(id, html) {
    const node = this.el.querySelector(`#${id}`);
    if (node) node.innerHTML = html;
  },
  nodeSummary() {
    const N = this._nodes;
    if (!N) return "STANDBY (dual session not started)";
    const nodes = N.nodes || [];
    const down = nodes.filter((n) =>
      n.connection === "DEGRADED" || n.connection === "DISCONNECTED").length;
    const tag = down ? ` — ${down} DEGRADED` : "";
    return `${nodes.length} node(s) · sync ${N.sync_state}${tag}`;
  },
  renderHero() {
    const snap = this.ctx.store.snapshot();
    const s = this._status;
    const ev = this._last;
    const p = ev ? ev.payload : null;
    const alert = snap.state === "DISCONNECTED" ? " hero-alert"
      : (snap.state === "STALE" ? " hero-warn" : "");
    this.setHtml("ov-hero-sys",
      `<div class="hero-label">System state</div>` +
      `<div class="hero-value hero-small">${snap.state}</div>` +
      `<div class="hero-note hero-sub">${pillFor(snap.state)} ` +
      `${s ? s.connection : "UNKNOWN"} · ` +
      `${s && s.csi_rate != null ? `${s.csi_rate.toFixed(1)} Hz` : "rate UNKNOWN"}<br>` +
      `${this.nodeSummary()}</div>`);
    const obs = p && p.presence_state && p.presence_state !== "UNKNOWN"
      ? p.presence_state : "—";
    this.setHtml("ov-hero-obs",
      `<div class="hero-label">Observation</div>` +
      `<div class="hero-value${obs.length > 10 ? " hero-small" : ""}">${obs}</div>` +
      `<div class="hero-note hero-sub">${p ? `${p.presence} / ${p.movement}` : "no frames yet"}` +
      ` <span class="state-note">(NOT VALIDATED)</span></div>`);
    const conf = p && p.rf_evidence_confidence != null
      ? p.rf_evidence_confidence.toFixed(2) : "none";
    this.setHtml("ov-hero-conf",
      `<div class="hero-label">RF Evidence Confidence</div>` +
      `<div class="hero-value">${conf}</div>` +
      `<div class="hero-note hero-sub"><span class="state-note">UNCALIBRATED — ` +
      `never a probability · ${p ? `${p.provenance ?? "?"} / ${p.node_mode ?? "?"}` : "no frames yet"}</span></div>`);
    const hero = this.el.querySelector("#ov-hero");
    if (hero) hero.className = `hero-grid${alert}`;
  },
  renderEvidence() {
    const ev = this._last;
    if (!ev) {
      this.kv("ov-evidence", [["state", "no frames yet"]]);
      return;
    }
    const p = ev.payload;
    this.kv("ov-evidence", [
      ["showcase", p.presence_state && p.presence_state !== "UNKNOWN"
        ? `${p.presence_state} · RF-evidence ` +
          `${p.rf_evidence_confidence != null
            ? p.rf_evidence_confidence.toFixed(2) : "none"} ` +
          `<span class="state-note">(UNCALIBRATED, ` +
          `${p.provenance || "?"}, ${p.node_mode || "?"})</span>`
        : "no inference attached"],
      ["evidence", p.evidence_statement || "none yet"],
    ]);
  },
  renderNodes() {
    const N = this._nodes;
    if (!N) {
      const standby = `<span class="unknown">STANDBY (dual session not started)</span>`;
      this.setHtml("ov-nodes",
        `<dl class="kv"><dt>sync</dt><dd>${standby}</dd></dl>`);
      return;
    }
    const us = (v) => (v != null ? `${(v / 1000).toFixed(1)} ms` : "?");
    const rows = (N.nodes || []).map((n) => {
      const bad = n.connection === "DEGRADED" || n.connection === "DISCONNECTED";
      const state = bad
        ? `<span class="err-text">${n.connection} — DEGRADED MODE</span>` : n.connection;
      return `<tr><td>${n.node_id}</td><td>${state}</td>` +
        `<td>${num(n.csi_rate, (v) => `${v.toFixed(1)} Hz`)}</td>` +
        `<td>${n.valid_pct != null ? `${n.valid_pct.toFixed(2)} % (${n.valid})` : "UNKNOWN"}</td>` +
        `<td>${n.rssi != null ? `${n.rssi} dBm` : "UNKNOWN"}</td>` +
        `<td>${n.gaps} / ${n.duplicates} / ${n.out_of_order}</td>` +
        `<td>${n.channel != null ? "CH " + n.channel : "?"} · ${n.bssid || "?"}</td>` +
        `<td>${n.tones != null ? `${n.tones}` : "UNKNOWN"}</td>` +
        `<td>${us(n.sync_offset_ns)} / ${us(n.sync_jitter_ns)}</td>` +
        `<td>${n.host_pipeline_us_mean != null ? `${n.host_pipeline_us_mean.toFixed(0)} µs` : "UNKNOWN"}</td></tr>`;
    }).join("");
    this.setHtml("ov-nodes",
      `<div class="tbl-wrap"><table class="tbl">` +
      `<caption>sync ${N.sync_state} — all fields, no sampling</caption>` +
      `<thead><tr><th scope="col">node</th><th scope="col">state</th>` +
      `<th scope="col">rate</th><th scope="col">valid</th><th scope="col">rssi</th>` +
      `<th scope="col">gaps/dup/ooo</th><th scope="col">ch · bssid</th>` +
      `<th scope="col">tones</th><th scope="col">sync off/jit</th>` +
      `<th scope="col">pipe</th></tr></thead><tbody>${rows}</tbody></table></div>`);
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
    ]);
  },
  renderAll() {
    const s = this._status, e = this._exp, L = this._live;
    this.renderHero();
    this.renderEvidence();
    this.renderNodes();
    this.renderFrame();
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
      ["backend", s ? "reachable" : `<span class="unknown">UNREACHABLE</span>`],
      ["connection", s ? s.connection : "UNKNOWN"],
      ["stream", e ? e.session_id : "UNKNOWN"],
      ["validation", e ? e.validation : "UNKNOWN"],
      ["packets (shown)", s ? s.packets : "UNKNOWN"],
      ["malformed", s ? s.malformed : "UNKNOWN"],
      ["frame age", s && s.last_frame_age_s != null
        ? `${s.last_frame_age_s.toFixed(1)} s${s.stale ? " — STALE" : ""}` : "no frames"],
      ["contract", e ? `v${e.software.contract}` : "UNKNOWN"],
      ["console", e ? `web ${e.software.rfvision_web}` : "UNKNOWN"],
    ]);
    this.setHtml("ov-errors", this._view ? fetchErrors(this._view) : "");
    this.kv("ov-research", [
      ["calibration", `<span class="unknown">UNCALIBRATED</span>`],
      ["localization", `<span class="unknown">NOT VALIDATED</span>`],
      ["xai", `<span class="unknown">NOT AVAILABLE</span>`],
      ["models", `<span class="unknown">NO VALIDATED MODELS</span>`],
    ]);
  },
};
