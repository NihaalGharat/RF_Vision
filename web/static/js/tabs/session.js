/* Session tab — revamp consolidation (Experiments + Hardware, re-homed).
   Composition, not rewrite: section modules render unchanged into wrappers;
   lifecycle calls fan out, including shared-scheduler acquire/release. */
import { ExperimentsTab } from "./experiments.js";
import { HardwareTab } from "./hardware.js";

function fanOut(subs, method, arg) {
  for (const sub of subs) {
    if (sub[method]) {
      try { sub[method](arg); } catch (e) { console.error(e); }
    }
  }
}

export const SessionTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <h2 class="tab-section">Experiment control — source, stream, capture</h2>
      <div id="ses-exp"></div>
      <h2 class="tab-section">Hardware — baseline + link health</h2>
      <div id="ses-hw"></div>`;
    this.subs = [ExperimentsTab, HardwareTab];
    ExperimentsTab.init(el.querySelector("#ses-exp"), ctx);
    HardwareTab.init(el.querySelector("#ses-hw"), ctx);
  },
  onShow() { fanOut(this.subs, "onShow"); },
  onHide() { fanOut(this.subs, "onHide"); },
  onEvent(ev) { fanOut(this.subs, "onEvent", ev); },
  onState(snap) { fanOut(this.subs, "onState", snap); },
};
