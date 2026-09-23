/* Insights tab — revamp consolidation (Localization + XAI, re-homed).
   Composition, not rewrite: the two section modules render unchanged into
   wrappers; lifecycle calls fan out. Every row, caveat, and honesty label
   from the old tabs is preserved verbatim. */
import { LocalizationTab } from "./localization.js";
import { XaiTab } from "./xai.js";

function fanOut(subs, method, arg) {
  for (const sub of subs) {
    if (sub[method]) {
      try { sub[method](arg); } catch (e) { console.error(e); }
    }
  }
}

export const InsightsTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <h2 class="tab-section">Localization — 1-D link framework (NOT VALIDATED)</h2>
      <div id="ins-loc"></div>
      <h2 class="tab-section">XAI — explanation status (NOT AVAILABLE)</h2>
      <div id="ins-xai"></div>`;
    this.subs = [LocalizationTab, XaiTab];
    LocalizationTab.init(el.querySelector("#ins-loc"), ctx);
    XaiTab.init(el.querySelector("#ins-xai"), ctx);
  },
  onShow() { fanOut(this.subs, "onShow"); },
  onHide() { fanOut(this.subs, "onHide"); },
  onEvent(ev) { fanOut(this.subs, "onEvent", ev); },
  onState(snap) { fanOut(this.subs, "onState", snap); },
};
