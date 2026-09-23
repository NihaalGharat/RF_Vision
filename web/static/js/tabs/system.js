/* System tab — technical console: is the instrument functioning?
   Composition, not rewrite: Acquisition (source, stream, capture,
   live telemetry), Hardware (baseline, link, node registry, transport
   diagnostics, calibration/sync), Models (reserved), and Settings
   render unchanged into wrappers; lifecycle calls fan out. Scientific
   interpretation lives under Research, never duplicated here. */
import { AcquisitionTab } from "./acquisition.js";
import { HardwareTab } from "./hardware.js";
import { ModelsTab } from "./models.js";
import { SettingsTab } from "./settings.js";

function fanOut(subs, method, arg) {
  for (const sub of subs) {
    if (sub[method]) {
      try { sub[method](arg); } catch (e) { console.error(e); }
    }
  }
}

export const SystemTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <h2 class="tab-section">Acquisition — source, stream, capture</h2>
      <div id="sys-acq"></div>
      <h2 class="tab-section">Hardware — baseline + link health</h2>
      <div id="sys-hw"></div>
      <h2 class="tab-section">Models — reserved until validated</h2>
      <div id="sys-models"></div>
      <h2 class="tab-section">Console settings</h2>
      <div id="sys-settings"></div>`;
    this.subs = [AcquisitionTab, HardwareTab, ModelsTab, SettingsTab];
    AcquisitionTab.init(el.querySelector("#sys-acq"), ctx);
    HardwareTab.init(el.querySelector("#sys-hw"), ctx);
    ModelsTab.init(el.querySelector("#sys-models"), ctx);
    SettingsTab.init(el.querySelector("#sys-settings"), ctx);
  },
  onShow() { fanOut(this.subs, "onShow"); },
  onHide() { fanOut(this.subs, "onHide"); },
  onEvent(ev) { fanOut(this.subs, "onEvent", ev); },
  onState(snap) { fanOut(this.subs, "onState", snap); },
};
