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
    try {
      this.scene.init();
    } catch (e) {
      this._failed = true;
      el.querySelector("#rf-scene").innerHTML =
        `<p class="state-note">3D unavailable (${e.message}). 2D view below remains.</p>`;
      console.error("scene init", e);
    }
    this.refreshCal();
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
    this.paint();
  },
  onHide() { /* scene keeps rendering; cheap single link */ },
  onEvent(ev) {
    if (!ev || ev.type !== "sensing.snapshot") return;
    const p = ev.payload;
    this._amps = p.amplitudes || null;
    this._pos = (typeof p.position === "number") ? p.position : null;
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
      this.scene.setModel({
        widthM: this._widthM ?? null,
        amplitudes: this._amps ?? null,
        positionT: this._pos ?? null,
        uncertainty: null, // no validated uncertainty yet
      });
    }
  },
  destroy() {
    this.scene?.destroy();
  },
};
