/* Health polling + provenance footer — RF Vision native.
   Adapted pattern from RuView services/health.service.js (dd02efe2):
   periodic GET with subscriber fan-out. Ours polls /api/v1/health and
   pushes the declared source_state into the store. */
import { CONSOLE } from "./config.js";
import { api } from "./api.js";

export class HealthMonitor {
  constructor(store) {
    this.store = store;
    this.last = null;
    this._timer = null;
  }

  start() {
    this.poll();
    this._timer = setInterval(() => this.poll(), CONSOLE.HEALTH_POLL_MS);
  }

  stop() {
    if (this._timer) { clearInterval(this._timer); this._timer = null; }
  }

  async poll() {
    try {
      const data = await api.health();
      this.last = { ok: true, data };
      if (data.source_state && data.source_state !== "STALE") {
        // STALE is computed client-side from frame freshness; the server
        // hint only promotes non-stale base states.
        this.store.setBaseState(data.source_state);
      }
      document.getElementById("contract-version").textContent =
        `contract v${data.contract ?? "?"}`;
      document.getElementById("provenance-line").textContent =
        `provenance: ${data.source} · ${data.source_state} · web v${data.version} · up ${Math.round(data.uptime_s)}s`;
    } catch (err) {
      this.last = { ok: false, error: String(err) };
      document.getElementById("provenance-line").textContent =
        "provenance: console unreachable";
    }
  }
}
