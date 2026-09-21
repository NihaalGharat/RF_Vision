/* Source-state store — RF Vision native (mandatory transparency layer).
   Adapted concept from RuView's provenance + data-source-banner discipline
   (dd02efe2): every frame carries provenance; STALE is computed on a
   freshness timeout; subscribers re-render on change. RF Vision states are
   our own six tokens (see web/contracts.py); LIVE_VERIFIED is currently
   unreachable by backend gate (003R), which the store surfaces honestly. */
import { CONSOLE } from "./config.js";

export const STATES = [
  "LIVE_VERIFIED", "LIVE_UNVERIFIED", "OFFLINE_FIXTURE",
  "SIMULATED", "STALE", "DISCONNECTED",
];

export class SourceStore {
  constructor() {
    this.state = "DISCONNECTED";
    this.lastEventTs = 0;
    this.lastEvent = null;
    this.wsState = "disconnected";
    this.subs = [];
    this._timer = setInterval(() => this._tick(), 500);
  }

  subscribe(cb) {
    this.subs.push(cb);
    cb(this.snapshot());
  }

  snapshot() {
    return {
      state: this.state,
      wsState: this.wsState,
      lastEvent: this.lastEvent,
      ageMs: this.lastEventTs ? Date.now() - this.lastEventTs : null,
    };
  }

  _notify() {
    const snap = this.snapshot();
    for (const cb of this.subs) {
      try { cb(snap); } catch (err) { console.error("store subscriber", err); }
    }
  }

  setBaseState(state) {
    if (!STATES.includes(state)) return;
    if (state !== "STALE") {
      this.state = state;
      this._notify();
    }
  }

  setWsState(wsState) {
    this.wsState = wsState;
    if ((wsState === "disconnected" || wsState === "reconnecting") &&
        this.state !== "DISCONNECTED") {
      // Transport loss never masquerades as data: freeze into STALE only
      // if we had frames, else DISCONNECTED is set by the app layer.
    }
    this._notify();
  }

  ingest(event) {
    if (!event || typeof event !== "object") return;
    const payload = event.payload || {};
    const declared = payload.source_state;
    if (declared && STATES.includes(declared) && declared !== "STALE") {
      this.state = declared;
    }
    this.lastEventTs = Date.now();
    this.lastEvent = event;
    this._notify();
  }

  markDisconnected() {
    this.state = "DISCONNECTED";
    this.lastEvent = null;
    this.lastEventTs = 0;
    this._notify();
  }

  _tick() {
    if (this.lastEventTs &&
        ["LIVE_VERIFIED", "LIVE_UNVERIFIED", "OFFLINE_FIXTURE", "SIMULATED"]
          .includes(this.state) &&
        Date.now() - this.lastEventTs > CONSOLE.STALE_AFTER_MS) {
      this.state = "STALE";
      this._notify();
    }
  }
}
