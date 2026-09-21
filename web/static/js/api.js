/* REST client — RF Vision native.
   Adapted pattern from RuView services/api.service.js (dd02efe2):
   thin get/post helpers with uniform error mapping. No auth yet
   (single-user bench console; Bearer hook reserved). */
import { apiUrl } from "./config.js";

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
    res = await fetch(apiUrl(path), opts);
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

export const api = {
  get: (path) => request("GET", path),
  post: (path, body) => request("POST", path, body),
  health: () => request("GET", "/api/v1/health"),
  status: () => request("GET", "/api/v1/status"),
  latest: () => request("GET", "/api/v1/sensing/latest"),
  telemetry: () => request("GET", "/api/v1/telemetry"),
  streamStatus: () => request("GET", "/api/v1/stream/status"),
  streamStart: () => request("POST", "/api/v1/stream/start"),
  streamStop: () => request("POST", "/api/v1/stream/stop"),
  setSource: (mode, path) => request("POST", "/api/v1/source", path ? { mode, path } : { mode }),
  experiment: () => request("GET", "/api/v1/experiment"),
  calibration: () => request("GET", "/api/v1/calibration"),
  localization: () => request("GET", "/api/v1/localization"),
  xai: () => request("GET", "/api/v1/xai"),
};
