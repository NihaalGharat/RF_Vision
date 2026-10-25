const TONES = Object.freeze({
  SYNCED: "healthy",
  LIVE: "healthy",
  SYNCING: "degraded",
  DEGRADED: "degraded",
  DISCONNECTED: "unavailable",
  STANDBY: "unavailable",
});

export function healthTone(connection) {
  const status = String(connection == null ? "" : connection).trim().toUpperCase();
  return TONES[status] || "unknown";
}
