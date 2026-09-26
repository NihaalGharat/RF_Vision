/* Hardware tab — validated baseline + ACTUAL live link health.
   RF Vision native. Baseline values come from the backend (constants gated
   by docs/hardware/BASELINE.md); link health comes from /api/v1/live.
   Anything unverified renders UNKNOWN. */
import { api } from "../api.js";
import { pillFor, fmtUnknown, fetchErrors } from "../banner.js";

export const HardwareTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    this._prov = null;
    this._ssidTouched = false;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Receiver — validated baseline</h3>
          <div class="kv" id="hw-base"></div></div>
        <div class="card"><h3>Link state — live</h3>
          <div class="kv" id="hw-link"></div></div>
        <div class="card"><h3>Node registry</h3><div class="kv" id="lc-nodes"></div></div>
        <div class="card"><h3>RF network — provision</h3>
          <div class="kv" id="hw-rfnet"></div>
          <div class="row">
            <input class="input" id="rf-ssid" type="text" placeholder="SSID"
              autocomplete="off" aria-label="Wi-Fi SSID" />
            <input class="input" id="rf-pass" type="password" placeholder="password"
              autocomplete="off" aria-label="Wi-Fi password" />
            <button class="btn primary" id="rf-connect">CONNECT RF NODES</button>
          </div>
          <p class="state-note" id="rf-msg">Provision targets the detected
          network. The password travels only in the provisioning POST body —
          never displayed, logged, or stored.</p></div>
        <div class="card"><h3>Dual-node session</h3>
          <div class="kv" id="hw-dual"></div>
          <div class="row">
            <button class="btn primary" id="dual-start">START DUAL SESSION</button>
            <button class="btn" id="dual-stop">STOP</button>
          </div>
          <p class="state-note" id="dual-msg">Starts backend dual-node CSI
          acquisition (ESP32-A + ESP32-B, both required). Refuses while the
          single live source runs.</p></div>
        <details class="detail"><summary>Transport diagnostics</summary>
          <div class="detail-body"><div class="kv" id="hw-diag"></div>
          <p class="state-note">Firmware identity stays UNKNOWN until a
          read-back is possible without reset. No flash / erase / reset is
          ever initiated from this console.</p></div></details>
        <details class="detail"><summary>Calibration / sync</summary>
          <div class="detail-body"><div class="kv" id="lc-cal"></div></div></details>
      </div>`;
    el.querySelector("#rf-connect").addEventListener("click", () => this.connect());
    el.querySelector("#dual-start").addEventListener("click", () => this.dual(true));
    el.querySelector("#dual-stop").addEventListener("click", () => this.dual(false));
    el.querySelector("#rf-ssid").addEventListener("input", () => { this._ssidTouched = true; });
    this.refresh();
    this.ctx.poll.acquire("hardware", ["experiment", "live", "network", "nodes", "rfReadiness"],
      (view) => this.onPoll(view));
  },
  onHide() { this.ctx.poll.release("hardware"); },
  onShow() {
    this.ctx.poll.acquire("hardware", ["experiment", "live", "network", "nodes", "rfReadiness"],
      (view) => this.onPoll(view));
    this.refresh();
  },
  onPoll(view) {
    this._exp = view.data.experiment || null;
    const live = view.data.live;
    this._live = live && live.available ? live : null;
    this._net = view.data.network || null;
    const nodes = view.data.nodes;
    this._nodes = nodes || null;
    this._rfr = view.data.rfReadiness || null;
    this._view = view;
    this.renderAll();
  },
  onState() { this.renderLink(); },
  async refresh() {
    try {
      const [loc, cal] = await Promise.all([api.localization(), api.calibration()]);
      this._loc = loc;
      this._cal = cal;
    } catch {
      this._loc = null;
      this._cal = null;
    }
    this.renderAll();
  },
  // Backend values can carry attacker-controlled AP names — escape HTML.
  esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  },
  async connect() {
    const msg = this.el.querySelector("#rf-msg");
    const btn = this.el.querySelector("#rf-connect");
    const ssidEl = this.el.querySelector("#rf-ssid");
    const passEl = this.el.querySelector("#rf-pass");
    const ssid = (ssidEl.value || "").trim();
    const password = passEl.value || "";
    passEl.value = ""; // never retained in the DOM
    if (!ssid || !password) {
      msg.textContent = "SSID and password are required. The password travels only in the provisioning POST body.";
      return;
    }
    btn.disabled = true;
    msg.textContent = `provisioning ${ssid} … (backend state drives the display below)`;
    try {
      // Single call into the existing RFVISION-012 backend; the response
      // carries the truthful per-node states — never invented here.
      this._prov = await api.provision(ssid, password);
      msg.textContent = `${this._prov.state} — ${this._prov.reason || ""}`.trim();
    } catch (e) {
      this._prov = null;
      msg.textContent = `failed: ${e.message}`;
    }
    btn.disabled = false;
    this.renderAll();
  },
  async dual(start) {
    const msg = this.el.querySelector("#dual-msg");
    const btn = this.el.querySelector(start ? "#dual-start" : "#dual-stop");
    btn.disabled = true;
    msg.textContent = start ? "starting dual session …" : "stopping dual session …";
    try {
      // Single call into the backend; the response + polled /api/v1/nodes
      // carry the truthful session state — never invented here.
      const res = start ? await api.dualStart() : await api.dualStop();
      msg.textContent = `${res.running ? "RUNNING" : "STOPPED"} — ${res.reason || res.note || ""}`.trim();
    } catch (e) {
      msg.textContent = `failed: ${e.message}`;
    }
    btn.disabled = false;
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
    this.renderNodes();
    this.renderDual();
    this.renderRfnet();
  },
  renderDual() {
    const box = this.el.querySelector("#hw-dual");
    if (!box) return;
    const d = this._nodes;
    const rows = [];
    if (!d) {
      rows.push(["session", `<span class="unknown">BACKEND UNREACHABLE</span>`]);
    } else if (!d.available) {
      rows.push(["session", `<span class="unknown">STANDBY (dual session not started)</span>`]);
      if (d.reason) rows.push(["detail", this.esc(d.reason)]);
    } else {
      // Dual session state is rendered ONLY from the backend payload.
      rows.push(["session", pillFor(d.sync_state || "UNKNOWN")]);
      for (const n of (d.nodes || [])) {
        rows.push([`node ${this.esc(n.node_id)}`,
          `${this.esc(n.connection || "?")} · ${this.esc(n.source_state || "?")} · ` +
          `${n.csi_rate != null ? `${Number(n.csi_rate).toFixed(1)} Hz` : "rate ?"} · ` +
          `${n.valid != null ? `${n.valid} valid` : "count ?"} · ` +
          `${n.malformed != null ? `${n.malformed} malformed` : ""} · ` +
          `sync obs ${n.sync_observations != null ? n.sync_observations : "?"}`.trim()]);
      }
      if (d.session && d.session.elapsed_s != null) {
        rows.push(["elapsed", `${Number(d.session.elapsed_s).toFixed(0)} s`]);
      }
    }
    box.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    if (this._view) {
      const errs = fetchErrors(this._view, ["nodes"]);
      if (errs) box.innerHTML += errs;
    }
  },
  renderRfnet() {
    const box = this.el.querySelector("#hw-rfnet");
    if (!box) return;
    const net = this._net;
    const rfr = this._rfr;
    // Prefill the SSID from detection until the user types their own.
    const ssidEl = this.el.querySelector("#rf-ssid");
    if (ssidEl && !this._ssidTouched && net && net.network && net.network.ssid && !ssidEl.value) {
      ssidEl.value = net.network.ssid;
    }
    const rows = [];
    if (!net) {
      rows.push(["network", `<span class="unknown">BACKEND UNREACHABLE</span>`]);
    } else {
      const n = net.network || {};
      rows.push(["network", pillFor(net.state || "UNKNOWN")]);
      rows.push(["ssid", net.state === "NETWORK_DETECTED" ? this.esc(n.ssid) : `<span class="unknown">—</span>`]);
      rows.push(["bssid / ch", net.state === "NETWORK_DETECTED"
        ? `${this.esc(n.bssid || "?")} · ch ${n.channel != null ? n.channel : "?"} · ${this.esc(n.band || "")}` : `<span class="unknown">—</span>`]);
      if (net.reason) rows.push(["detail", this.esc(net.reason)]);
    }
    if (rfr) {
      // RF READY is rendered ONLY from backend readiness — never set here.
      rows.push(["readiness", pillFor(rfr.rf_ready ? "RF_READY" : (rfr.state || "UNKNOWN"))]);
      if (rfr.reason) rows.push(["readiness detail", this.esc(rfr.reason)]);
    } else {
      rows.push(["readiness", `<span class="unknown">BACKEND UNREACHABLE</span>`]);
    }
    // Last provisioning attempt, verbatim backend per-node states.
    if (this._prov && Array.isArray(this._prov.nodes)) {
      for (const nd of this._prov.nodes) {
        rows.push([`node ${this.esc(nd.node_id)}`, `${this.esc(nd.state)}${nd.reason ? ` — ${this.esc(nd.reason)}` : ""}`]);
      }
    }
    box.innerHTML = rows.map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    if (this._view) {
      const errs = fetchErrors(this._view, ["network", "rfReadiness"]);
      if (errs) box.innerHTML += errs;
    }
  },
  renderNodes() {
    const loc = this._loc, cal = this._cal;
    const nodes = this.el.querySelector("#lc-nodes");
    if (nodes) {
      nodes.innerHTML = (loc && loc.nodes.length ? loc.nodes.map((n) =>
        [n.id, `${n.role} · pos: ${n.position_m === null ? "UNKNOWN" : `${n.position_m} m`}`])
        : [["nodes", `<span class="unknown">UNREACHABLE / UNKNOWN</span>`]])
        .map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
    const calEl = this.el.querySelector("#lc-cal");
    if (calEl) {
      calEl.innerHTML = [
        ["calibration", cal ? cal.status : "UNKNOWN"],
        ["room width", cal ? fmtUnknown(cal.room_width_m, (v) => `${v} m`) : "UNKNOWN"],
        ["sync", loc ? loc.sync : "UNKNOWN"],
        ["frame", loc ? loc.frame : "UNKNOWN"],
      ].map(([k, v]) => `<dt>${k}</dt><dd>${v}</dd>`).join("");
    }
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
