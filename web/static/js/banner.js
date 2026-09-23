/* Global source banner + header connection chip — RF Vision native.
   Adapted concept from RuView utils/data-source-banner.js +
   utils/connection-status.js (dd02efe2): a global always-visible banner
   plus a header dot, with per-state text that never lets non-live data
   look live. */
import { SOURCE_META } from "./config.js";

export function bindSourceChrome(store) {
  const banner = document.getElementById("source-banner");
  const dot = document.getElementById("conn-dot");
  const label = document.getElementById("conn-label");

  function render(snap) {
    const meta = SOURCE_META[snap.state] || SOURCE_META.DISCONNECTED;
    if (meta.banner) {
      banner.hidden = false;
      banner.dataset.state = snap.state;
      banner.textContent = `${snap.state} — ${meta.banner}`;
    } else {
      banner.hidden = true;
      banner.textContent = "";
    }
    dot.className = `conn-dot ${meta.conn}`;
    let text = snap.state;
    if (snap.state !== "DISCONNECTED" && snap.wsState !== "connected") {
      text += ` (ws ${snap.wsState})`;
    }
    label.textContent = text;
  }

  store.subscribe(render);
}

export function pillFor(state) {
  const meta = SOURCE_META[state] || SOURCE_META.DISCONNECTED;
  return `<span class="pill ${meta.pill}">${state}</span>`;
}

export function fmtUnknown(value, fmt) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return `<span class="unknown">UNKNOWN</span>`;
  }
  return fmt ? fmt(value) : String(value);
}

// Failed-poll row: never leave stale-looking values without context.
// Shows which endpoint failed, the error, last-good age, and a Retry
// button (handled by the global [data-retry] delegation in app.js).
export function fetchErrors(view, endpoints) {
  const names = (endpoints || Object.keys(view.errors || {}))
    .filter((n) => view.errors && view.errors[n]);
  if (!names.length) return "";
  const rows = names.map((n) => {
    const age = view.okAt && view.okAt[n]
      ? ` · last good ${Math.max(0, Math.round((view.at - view.okAt[n]) / 1000))} s ago`
      : " · no good read this session";
    return `<div class="err-row"><span class="warn-text">fetch failed: ` +
      `${n} (${view.errors[n]}${age})</span>` +
      `<button class="linklike" data-retry type="button">Retry</button></div>`;
  });
  return rows.join("");
}
