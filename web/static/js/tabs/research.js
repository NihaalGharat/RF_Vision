/* Research tab — scientific workspace: what does the RF evidence mean?
   Composition, not rewrite: Localization (estimate + uncertainty),
   XAI (status + feature importance + latest evidence), and the experiment
   provenance section modules render unchanged into wrappers; the
   validation-state block is static markup moved from the Overview
   disclosures (same literals, same honesty labels). Engineering content
   (node registry, calibration/sync, acquisition controls, telemetry,
   hardware) lives under System, never duplicated here. Lifecycle calls
   fan out. */
import { LocalizationTab } from "./localization.js";
import { XaiTab } from "./xai.js";
import { ExperimentsTab } from "./experiments.js";

function fanOut(subs, method, arg) {
  for (const sub of subs) {
    if (sub[method]) {
      try { sub[method](arg); } catch (e) { console.error(e); }
    }
  }
}

export const ResearchTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <h2 class="tab-section">Localization — 1-D link framework (NOT VALIDATED)</h2>
      <div id="res-loc"></div>
      <h2 class="tab-section">XAI — explanation status (NOT AVAILABLE)</h2>
      <div id="res-xai"></div>
      <h2 class="tab-section">Experiment — session provenance &amp; evidence</h2>
      <div id="res-exp"></div>
      <h2 class="tab-section">Validation state — known vs unknown</h2>
      <div class="grid"><div class="card"><h3>Validation state</h3>
        <div class="kv">
          <dt>calibration</dt><dd><span class="unknown">UNCALIBRATED</span></dd>
          <dt>localization</dt><dd><span class="unknown">NOT VALIDATED</span></dd>
          <dt>xai</dt><dd><span class="unknown">NOT AVAILABLE</span></dd>
          <dt>models</dt><dd><span class="unknown">NO VALIDATED MODELS</span></dd>
        </div></div></div>`;
    this.subs = [LocalizationTab, XaiTab, ExperimentsTab];
    LocalizationTab.init(el.querySelector("#res-loc"), ctx);
    XaiTab.init(el.querySelector("#res-xai"), ctx);
    ExperimentsTab.init(el.querySelector("#res-exp"), ctx);
  },
  onShow() { fanOut(this.subs, "onShow"); },
  onHide() { fanOut(this.subs, "onHide"); },
  onEvent(ev) { fanOut(this.subs, "onEvent", ev); },
  onState(snap) { fanOut(this.subs, "onState", snap); },
};
