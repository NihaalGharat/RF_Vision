/* RF Vision console config — endpoint + URL builders.
   Adapted pattern from RuView config/api.config.js (dd02efe2):
   central constants, same-origin URL building, no hard-coded hosts. */
export const CONSOLE = {
  CONTRACT_VERSION: 1,
  STALE_AFTER_MS: 3000,
  HEALTH_POLL_MS: 5000,
  WS_RECONNECT_DELAYS_MS: [1000, 2000, 4000, 8000, 16000, 30000],
  WS_MAX_ATTEMPTS: 10,
};

export function apiUrl(path) {
  return path.startsWith("/") ? path : `/${path}`;
}

export function wsUrl(path = "/ws/sensing") {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}${path}`;
}

export const SOURCE_META = {
  LIVE_VERIFIED: { pill: "pill-live", conn: "conn-live", banner: null },
  LIVE_UNVERIFIED: {
    pill: "pill-unverified", conn: "conn-warn",
    banner: "UNVERIFIED LIVE SOURCE — ~3 s session gate not yet passed; frames are not validated",
  },
  OFFLINE_FIXTURE: {
    pill: "pill-sim", conn: "conn-sim",
    banner: "OFFLINE FIXTURE — recorded data, not live. Never sensing evidence.",
  },
  SIMULATED: {
    pill: "pill-sim", conn: "conn-sim",
    banner: "SIMULATED — synthetic frames for UI development only. Never evidence.",
  },
  STALE: {
    pill: "pill-stale", conn: "conn-stale",
    banner: "STALE — no frames within 3 s. Last values shown, do not act on them.",
  },
  DISCONNECTED: {
    pill: "pill-off", conn: "conn-offline",
    banner: "DISCONNECTED — no data source selected.",
  },
};
