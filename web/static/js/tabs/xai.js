/* XAI tab — explanation interface foundation.
   RF Vision native. Renders NOT AVAILABLE until a validated explanation
   exists; when available, scores render WITH the mandatory caveat.
   SHAP/LIME output is never fabricated. */
import { api } from "../api.js";
import { drawBars } from "../viz2d.js";

export const XaiTab = {
  init(el, ctx) {
    this.el = el;
    this.ctx = ctx;
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Explanation status</h3><div class="kv" id="xai-status"></div></div>
        <div class="card"><h3>Feature importance</h3><canvas class="viz" id="xai-bars"></canvas>
          <p class="caveat" id="xai-caveat" hidden></p></div>
      </div>`;
    this.refresh();
  },
  onShow() { this.refresh(); },
  async refresh() {
    let data = null;
    try {
      data = await api.xai();
    } catch {
      data = null;
    }
    this._data = data;
    this.render();
  },
  render() {
    const d = this._data;
    const status = this.el.querySelector("#xai-status");
    const caveat = this.el.querySelector("#xai-caveat");
    const bars = this.el.querySelector("#xai-bars");
    if (!d) {
      status.innerHTML = `<dt>xai</dt><dd><span class="unknown">UNREACHABLE</span></dd>`;
      drawBars(bars, []);
      caveat.hidden = true;
      return;
    }
    if (!d.available) {
      status.innerHTML =
        `<dt>explanation</dt><dd><span class="unknown">NOT AVAILABLE</span></dd>` +
        `<dt>reason</dt><dd>no validated model, no validated explanation</dd>`;
      drawBars(bars, []);
      caveat.hidden = true;
      return;
    }
    status.innerHTML =
      `<dt>method</dt><dd>${d.method}</dd>` +
      `<dt>provenance</dt><dd>model + dataset recorded at train time</dd>`;
    const scores = d.scores || {};
    const top = (d.top_k || []).slice(0, 12);
    const max = Math.max(0.0001, ...Object.values(scores));
    drawBars(bars, top.map((k) => ({
      label: k, value: (scores[k] ?? 0) / max, color: "#a678e8",
    })));
    caveat.hidden = false;
    caveat.textContent = `Caveat (mandatory): ${d.caveats} Scores are comparative, never causal.`;
  },
};
