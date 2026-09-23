/* RF Field tab — Three.js single-link scene + 2D room view.
   RF Vision native. Scene foundation (js/scene3d.js) + 2D room (js/viz2d.js).
   EXACTLY ONE LINK. Unknown geometry stays UNKNOWN. */
import { RfLinkScene } from "../scene3d.js";
import { drawRoom2d } from "../viz2d.js";
import { api } from "../api.js";

export const RfFieldTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card" style="grid-column: span 2">
          <h3>3D RF environment — one link (three.js r160, local)</h3>
          <div class="scene-wrap" id="rf-scene"></div>
          <p class="state-note">Drag to orbit · scroll to zoom. Field strip is an
          amplitude abstraction, not a propagation model. No bodies, no mesh.</p>
        </div>
        <div class="card"><h3>2D room view</h3>
          <canvas class="viz" id="rf-room"></canvas>
          <p class="state-note">Dashed outline = uncalibrated. Positions default to
          link ends until measured.</p></div>
      </div>`;
    this.scene = new RfLinkScene(el.querySelector("#rf-scene"));
    this._failed = false;
    this._hudExtra = "";
    try {
      this.scene.init();
    } catch (e) {
      this._failed = true;
      el.querySelector("#rf-scene").innerHTML =
        `<p class="state-note">3D unavailable (${e.message}). 2D view below remains.</p>`;
      console.error("scene init", e);
    }
    this.refreshCal();
    this._timer = setInterval(() => this.pollLive(), 2000);
    this.pollLive();
  },
  async refreshCal() {
    try {
      const cal = await api.calibration();
      this._widthM = cal.room_width_m;
    } catch {
      this._widthM = null;
    }
    this.paint();
  },
  onShow() {
    this.scene?.resize();
    if (!this._timer) {
      this._timer = setInterval(() => this.pollLive(), 2000);
      this.pollLive();
    }
    this.paint();
  },
  onHide() {
    if (this._timer) { clearInterval(this._timer); this._timer = null; }
  },
  async pollLive() {
    try {
      const live = await api.live();
      if (live && live.available) {
        const st = live.stream, sg = live.signal;
        this._hudExtra = `${live.source_state} · ` +
          `${st.rate_hz != null ? st.rate_hz.toFixed(1) + " Hz" : "rate ?"} · ` +
          `rssi ${sg.rssi_last != null ? sg.rssi_last : "?"} · ` +
          `seq ${st.last_seq != null ? st.last_seq : "?"}`;
      } else {
        this._hudExtra = "";
      }
    } catch {
      this._hudExtra = "";
    }
    this.paint();
  },
  onEvent(ev) {
    if (!ev || ev.type !== "sensing.snapshot") return;
    const p = ev.payload;
    this._amps = p.amplitudes || null;
    this._pos = (typeof p.position === "number") ? p.position : null;
    // Honest link-figure: the 3D marker follows measured/inferred state
    // only; presence_state rides the HUD, never a body mesh (none exists).
    this._showState = (p.presence_state && p.presence_state !== "UNKNOWN")
      ? `${p.presence_state} (RF-INFERRED, UNCALIBRATED)` : "";
    this.paint();
  },
  onState() { this.paint(); },
  paint() {
    const room = {
      widthM: this._widthM ?? null,
      lengthM: null,
      positionT: this._pos ?? null,
      uncertainty: null,
    };
    const canvas = this.el.querySelector("#rf-room");
    if (canvas) drawRoom2d(canvas, room);
    if (!this._failed) {
      const hud = [this._hudExtra, this._showState]
        .filter(Boolean).join(" · ");
      this.scene.setModel({
        widthM: this._widthM ?? null,
        amplitudes: this._amps ?? null,
        positionT: this._pos ?? null,
        uncertainty: null, // no validated uncertainty yet
        hudExtra: hud || null,
      });
    }
  },
  destroy() {
    this.scene?.destroy();
  },
};
