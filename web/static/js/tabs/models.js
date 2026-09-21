/* Models tab — RESERVED until validated.
   RF Vision native. The nav button is disabled; this module explains why so
   a deep-linked or re-enabled tab can never imply a trained model exists. */

export const ModelsTab = {
  init(el) {
    el.innerHTML = `
      <div class="grid">
        <div class="card"><h3>Model registry — reserved</h3>
          <div class="kv">
            <dt>status</dt><dd><span class="unknown">NO VALIDATED MODELS</span></dd>
            <dt>policy</dt><dd>no training on real data until CSI-SENSE validation</dd>
            <dt>baselines</dt><dd>KNN / RF / NN definitions exist in ai/ (untrained)</dd>
          </div>
          <p class="caveat">The console runs heuristic UI fields only. This tab
          unlocks after an independently validated training run.</p></div>
      </div>`;
  },
};
