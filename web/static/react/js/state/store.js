/* Domain stores — one tiny pub/sub store per state domain.
   Explicitly NOT one giant global object. Visualization state (vizStore)
   is separate from physical system state by construction. */
const R = window.React;

function createStore(initial) {
  let state = initial;
  const listeners = new Set();
  return {
    get() { return state; },
    set(patch) {
      state = { ...state, ...patch };
      listeners.forEach((cb) => { try { cb(state); } catch (e) { console.error("store cb", e); } });
    },
    subscribe(cb) {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
  };
}

function useStore(store) {
  const [snap, setSnap] = R.useState(() => store.get());
  R.useEffect(() => store.subscribe(setSnap), [store]);
  return snap;
}

// Backend / WebSocket / contract / app status.
export const systemStore = createStore({
  health: null, healthError: null, contract: null, version: null,
  wsState: "disconnected",
});
// OFF / LIVE / FIXTURE / SIMULATION + freshness + validity.
export const sourceStore = createStore({
  source: "OFF", sourceState: "DISCONNECTED",
  running: false, mode: "off",
  lastEvent: null, lastEventTs: 0,
});
// Network + nodes + provisioning + RF READY + sync.
export const hardwareStore = createStore({
  network: null, networkError: null,
  readiness: null, readinessError: null,
  nodes: null, nodesError: null,
  provResult: null,
});
// CSI / RSSI / packets / sequence / validity / current frame / evidence.
export const sensingStore = createStore({
  live: null, liveError: null, status: null,
  frameCount: 0,
});
// Session / protocol / validation / analysis / provenance.
export const researchStore = createStore({
  experiment: null, experimentError: null,
  recording: null, recordMsg: null,
});
// Visualization-only: render pause, view reset token. Never hardware.
export const vizStore = createStore({ paused: false, viewToken: 0 });

export { useStore };
