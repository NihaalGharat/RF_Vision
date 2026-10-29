/* API service — the single React-side abstraction over the existing backend.
   Components must NOT scatter raw fetch() calls; feature hooks/state call
   through this module. Endpoint semantics are the backend's (contracts v3 +
   RFVISION-012); awkward shapes are adapted here, never in components. */

export class ApiError extends Error {
  constructor(status, message) {
    super(`API ${status}: ${message}`);
    this.status = status;
  }
}

async function request(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  let res;
  try {
    res = await fetch(path, opts);
  } catch (err) {
    throw new ApiError(0, `unreachable (${err.message})`);
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    throw new ApiError(res.status, "non-JSON response");
  }
  if (!res.ok) {
    throw new ApiError(res.status, data.error || res.statusText);
  }
  return data;
}

const get = (path) => request("GET", path);
const post = (path, body) => request("POST", path, body);

export const api = {
  // System / provenance
  health: () => get("/api/v1/health"),
  status: () => get("/api/v1/status"),
  // Acquisition / source
  streamStatus: () => get("/api/v1/stream/status"),
  streamStart: () => post("/api/v1/stream/start"),
  streamStop: () => post("/api/v1/stream/stop"),
  setSource: (mode, extra) => post("/api/v1/source", { mode, ...(extra || {}) }),
  // Hardware / RFVISION-012
  network: () => get("/api/v1/network"),
  provision: (ssid, password, nodes) => post("/api/v1/network/provision", { ssid, password, ...(nodes ? { nodes } : {}) }),
  inspectNodes: (nodes) => post("/api/v1/network/inspect", { ...(nodes ? { nodes } : {}) }),
  dualStart: () => post("/api/v1/dual/start"),
  dualStop: () => post("/api/v1/dual/stop"),
  rfReadiness: () => get("/api/v1/rf_readiness"),
  nodes: () => get("/api/v1/nodes"),
  live: () => get("/api/v1/live"),
  // RF Vision pipeline (dual only; engineering/demonstration state)
  vision: () => get("/api/v1/vision"),
  // Research
  experiment: () => get("/api/v1/experiment"),
  recordStart: (maxSeconds) => post("/api/v1/live/record/start", { max_seconds: maxSeconds }),
  recordStop: () => post("/api/v1/live/record/stop"),
  trialCurrent: () => get("/api/v1/trials/current"),
  trialStart: (audioEnabled) => post("/api/v1/trials/start", { audio_enabled: !!audioEnabled }),
  trialStop: (reason) => post("/api/v1/trials/stop", { reason }),
  // Deferred-phase reads (exposed for later phases; not polled in Phase 1)
  calibration: () => get("/api/v1/calibration"),
  localization: () => get("/api/v1/localization"),
  xai: () => get("/api/v1/xai"),
  sensingLatest: () => get("/api/v1/sensing/latest"),
  telemetry: () => get("/api/v1/telemetry"),
};
