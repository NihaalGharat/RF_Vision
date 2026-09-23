/* Sensing tab — REAL CSI telemetry only.
   RF Vision native; viz via js/viz2d.js (dependency-free canvas).
   No human-presence, position, or activity claims exist here: presence /
   activity cards are explicitly NOT VALIDATED until CSI-SENSE. Phase is
   gated by the amplitude-only pipeline decision and labelled as such. */
import { drawHeatmap, drawSparkline, drawBars, drawLine, placeholder } from "../viz2d.js";
import { api } from "../api.js";
import { pillFor, fmtUnknown } from "../banner.js";

const AMP_ROWS = 40;
const RSSI_N = 120;

export const SensingTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    this.amps = [];
    this.rssi = [];
    this._last = null;
    this._live = null;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Signal validity — live gate</h3>
          <div class="kv" id="sn-valid"></div></div>
        <div class="card"><h3>Subcarrier amplitude — latest frame</h3>
          <canvas class="viz" id="sn-amp"></canvas></div>
        <div class="card"><h3>RSSI (dBm)</h3>
          <canvas class="viz" id="sn-rssi"></canvas></div>
      </div>
      <div class="grid" style="margin-top:12px">
        <div class="card" style="grid-column: span 2">
          <h3>Subcarrier amplitude heatmap (latest ${AMP_ROWS} frames)</h3>
          <canvas class="viz" id="sn-heat"></canvas></div>
        <div class="card"><h3>Packets / sequence</h3>
          <div class="kv" id="sn-packets"></div></div>
      </div>
      <div class="grid" style="margin-top:12px">
        <div class="card"><h3>Phase stream — gated</h3>
          <canvas class="viz" id="sn-phase"></canvas>
          <p class="state-note">Amplitude-only pipeline: phase is not
          consumed until validated. Displayed as GATED, never synthesized.</p></div>
        <div class="card"><h3>Presence / activity — NOT VALIDATED</h3>
          <canvas class="viz" id="sn-bars"></canvas>
          <div class="kv" id="sn-showcase"></div>
          <p class="caveat">NOT VALIDATED — no human-presence claim, no
          activity classification. UI fields only; do not cite. RF Evidence
          Confidence below is UNCALIBRATED product state, never a
          probability.</p></div>
      </div>
      <div class="grid" style="margin-top:12px">
        <div class="card" style="grid-column: span 2">
          <h3>1-D trajectory — RF-inferred position trail</h3>
          <canvas class="viz" id="sn-trail"></canvas>
          <p class="state-note">Recent RF-inferred link positions, oldest
          first. Empty = none available (no models, or nobody detected).
          NOT VALIDATED — do not cite.</p></div>
      </div>`;
    this.paint();
    this._timer = setInterval(() => this.pollLive(), 2000);
    this.pollLive();
  },
  onHide() { if (this._timer) { clearInterval(this._timer); this._timer = null; } },
  onShow() {
    if (!this._timer) this._timer = setInterval(() => this.pollLive(), 2000);
    this.paint();
  },
  onState() { this.renderValidity(); },
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
    if (Array.isArray(p.trail) && p.trail.length) {
      this._trail = p.trail.slice(-60);
    }
    this.paint();
  },
  async pollLive() {
    try {
      const live = await api.live();
      this._live = live && live.available ? live : null;
    } catch { this._live = null; }
    this.renderValidity();
  },
  canvas(id) { return this.el.querySelector(`#${id}`); },
  renderValidity() {
    const snap = this.ctx.store.snapshot();
    const L = this._live;
    const rows = [["source", pillFor(snap.state)]];
    if (L) {
      const st = L.stream, g = L.gate, dup = L.duplication;
      rows.push(
        ["gate", g.passed ? `<span class="ok">VERIFIED</span>`
          : `<span class="warn-text">UNVERIFIED — ${g.reasons.join("; ")}</span>`],
        ["valid", st.valid_pct != null ? `${st.valid_pct.toFixed(2)} %` : "UNKNOWN"],
        ["malformed", `${st.malformed}`],
        ["rate", st.rate_hz != null ? `${st.rate_hz.toFixed(1)} Hz` : "UNKNOWN"],
        ["freshness", st.last_update_age_s != null
          ? `${st.last_update_age_s.toFixed(1)} s ago${st.stale ? " — STALE" : ""}` : "no data"],
        ["duplication", dup.storm ? `<span class="err-text">STORM SIGNATURE</span>`
          : dup.impossible_throughput ? `<span class="err-text">IMPOSSIBLE THROUGHPUT</span>` : "none"],
      );
    } else {
      rows.push(["session", `<span class="unknown">NO LIVE SESSION</span>`]);
    }
    const node = this.el.querySelector("#sn-valid");
    if (node) {
      node.innerHTML = rows.map(([k, v]) =>
        `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
    const pk = this.el.querySelector("#sn-packets");
    if (pk) {
      const ev = this._last;
      const seqRows = ev ? [
        ["last seq", ev.seq],
        ["subcarriers", ev.payload.amplitudes ? ev.payload.amplitudes.length : "—"],
        ["validated", String(ev.payload.validated)],
      ] : [["packets", "none yet"]];
      if (L) {
        seqRows.push(["gaps", `${L.stream.gaps}`],
          ["missing", L.stream.missing.length ? L.stream.missing.join(", ") : "none"],
          ["records (lossless)", `${L.stream.valid}`]);
      }
      pk.innerHTML = seqRows.map(([k, v]) =>
        `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
  },
  paint() {
    drawHeatmap(this.canvas("sn-heat"), this.amps);
    drawSparkline(this.canvas("sn-rssi"), this.rssi, { label: "rssi" });
    const p = this._last ? this._last.payload : null;
    drawLine(this.canvas("sn-amp"),
      p && Array.isArray(p.amplitudes) ? p.amplitudes : null,
      { label: "amplitude", color: "#37c6d4" });
    placeholder(this.canvas("sn-phase"), "PHASE GATED — AMPLITUDE ONLY");
    drawBars(this.canvas("sn-bars"), [
      { label: "presence_prob", value: p ? p.presence_prob : null },
      { label: "movement_prob", value: p ? p.movement_prob : null },
      { label: "confidence", value: p ? p.confidence : null },
      { label: "rf_evidence", value: p ? (p.rf_evidence_confidence ?? null) : null },
    ]);
    drawSparkline(this.canvas("sn-trail"), this._trail || null,
      { label: "link position t" });
    const sc = this.el.querySelector("#sn-showcase");
    if (sc) {
      const rows = p ? [
        ["state", p.presence_state ?? "UNKNOWN"],
        ["rf evidence", p.rf_evidence_confidence != null
          ? `${(p.rf_evidence_confidence * 100).toFixed(0)} % ` +
            `<span class="state-note">(UNCALIBRATED)</span>` : "none"],
        ["provenance", p.provenance ?? "UNKNOWN"],
        ["nodes", p.node_mode ?? "UNKNOWN"],
      ] : [["state", "no frames yet"]];
      sc.innerHTML = rows.map(([k, v]) =>
        `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
    this.renderValidity();
  },
};
