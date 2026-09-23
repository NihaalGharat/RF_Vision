/* System tab — revamp consolidation (Models + Settings, re-homed).
   Composition, not rewrite. The Models section keeps its RESERVED /
   NO VALIDATED MODELS messaging verbatim; the disabled-nav-button guard is
   replaced by the section's own explanation (deep-link safe). */
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
      <h2 class="tab-section">Models — reserved until validated</h2>
      <div id="sys-models"></div>
      <h2 class="tab-section">Console settings</h2>
      <div id="sys-settings"></div>`;
    this.subs = [ModelsTab, SettingsTab];
    ModelsTab.init(el.querySelector("#sys-models"), ctx);
    SettingsTab.init(el.querySelector("#sys-settings"), ctx);
  },
  onShow() { fanOut(this.subs, "onShow"); },
  onHide() { fanOut(this.subs, "onHide"); },
  onEvent(ev) { fanOut(this.subs, "onEvent", ev); },
  onState(snap) { fanOut(this.subs, "onState", snap); },
};
