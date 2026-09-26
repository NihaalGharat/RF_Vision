/* Shared REST polling scheduler — RF Vision native (revamp Phase 2).
   Replaces duplicated per-tab 2 s timers with one scheduler: tabs declare
   which endpoints they need while visible; the scheduler polls the union at
   the same 2 s cadence and fans results out. Same endpoints, same cadence,
   same freshness semantics — fewer requests, no timer drift. STALE and
   source semantics stay in store.js / the backend; this layer only moves
   bytes on a timer. */
import { CONSOLE } from "./config.js";
import { api } from "./api.js";

const FETCHERS = {
  status: () => api.status(),
  experiment: () => api.experiment(),
  live: () => api.live(),
  nodes: () => api.nodes(),
  streamStatus: () => api.streamStatus(),
  network: () => api.network(),
  rfReadiness: () => api.rfReadiness(),
};

const CADENCE_MS = 2000;

export class PollScheduler {
  constructor() {
    this.subs = new Map(); // id -> {endpoints:[], cb}
    this.cache = {}; // endpoint -> {data, error, at}
    this._timer = null;
  }

  // Register interest; performs an immediate refresh for the new union.
  acquire(id, endpoints, cb) {
    this.subs.set(id, { endpoints: [...endpoints], cb });
    this._ensure();
    this.refresh();
    return () => this.release(id);
  }

  release(id) {
    this.subs.delete(id);
    if (this.subs.size === 0 && this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  _ensure() {
    if (!this._timer) {
      this._timer = setInterval(() => this.refresh(), CADENCE_MS);
    }
  }

  _union() {
    const set = new Set();
    for (const { endpoints } of this.subs.values()) {
      for (const e of endpoints) if (FETCHERS[e]) set.add(e);
    }
    return [...set];
  }

  async refresh() {
    if (this.subs.size === 0) return;
    const at = Date.now();
    const results = await Promise.all(this._union().map(async (name) => {
      try {
        return [name, { data: await FETCHERS[name](), error: null, at, okAt: at }];
      } catch (err) {
        const prev = this.cache[name];
        return [name, {
          data: prev ? prev.data : null,
          error: String(err && err.message || err),
          at,
          okAt: prev ? prev.okAt : null, // last-good timestamp survives failures
        }];
      }
    }));
    for (const [name, entry] of results) this.cache[name] = entry;
    for (const { endpoints, cb } of this.subs.values()) {
      const view = { at, data: {}, errors: {}, okAt: {} };
      for (const e of endpoints) {
        const entry = this.cache[e];
        if (entry) {
          view.data[e] = entry.data;
          if (entry.error) view.errors[e] = entry.error;
          view.okAt[e] = entry.okAt;
        }
      }
      try { cb(view); } catch (err) { console.error("poll subscriber", err); }
    }
  }
}
