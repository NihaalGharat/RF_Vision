/* RF Vision research console — boot.
   RF Vision native. Wiring (adapted lifecycle concept from RuView app.js,
   dd02efe2): health monitor → source chrome → tab manager → WS stream →
   store fan-out. No sensing logic lives here; frames flow
   backend contract → store → tabs. */
import { SourceStore } from "./store.js";
import { TabManager } from "./tabs.js";
import { bindSourceChrome } from "./banner.js";
import { bindStatusBand } from "./statusband.js";
import { HealthMonitor } from "./health.js";
import { WsClient } from "./ws.js";
import { PollScheduler } from "./scheduler.js";
import { api } from "./api.js";
import { OverviewTab } from "./tabs/overview.js";
import { SensingTab } from "./tabs/sensing.js";
import { RfFieldTab } from "./tabs/rffield.js";
import { InsightsTab } from "./tabs/insights.js";
import { SessionTab } from "./tabs/session.js";
import { SystemTab } from "./tabs/system.js";

function tickClock() {
  const node = document.getElementById("clock");
  const update = () => {
    node.textContent = new Date().toISOString().slice(11, 19);
  };
  update();
  setInterval(update, 1000);
}

async function boot() {
  tickClock();
  const store = new SourceStore();
  const ws = new WsClient();
  const health = new HealthMonitor(store);
  const tabs = new TabManager(
    document.querySelector(".tabs"), document.getElementById("panels"));

  tabs.register("overview", OverviewTab);
  tabs.register("sensing", SensingTab);
  tabs.register("rffield", RfFieldTab);
  tabs.register("insights", InsightsTab);
  tabs.register("session", SessionTab);
  tabs.register("system", SystemTab);

  const ctx = { store, ws, api, tabs, health, poll: new PollScheduler() };
  // Global retry delegation for fetch-error rows rendered by any tab.
  document.addEventListener("click", (ev) => {
    if (ev.target && ev.target.matches && ev.target.matches("[data-retry]")) {
      ctx.poll.refresh();
    }
  });
  bindSourceChrome(store);
  bindStatusBand(store);
  health.start();
  tabs.init(ctx);
  store.subscribe((snap) => tabs.dispatchState(snap));

  ws.on("event", (msg) => {
    if (!msg || typeof msg !== "object") return;
    if (msg.schema === 1 && msg.type) {
      // Envelope event from the backend contract.
      store.ingest(msg);
      tabs.dispatchEvent(msg);
    }
    // Stream-control acknowledgements need no store action; tabs refresh
    // their own REST state on show.
  });
  ws.on("state", (wsState) => {
    store.setWsState(wsState);
    if (wsState === "disconnected") {
      // Transport loss with no frames: honest empty state.
      api.status().then((s) => {
        if (!s || s.packets === 0) store.markDisconnected();
      }).catch(() => store.markDisconnected());
    }
  });

  // Initial source sync: adopt whatever the backend reports (default off).
  try {
    const status = await api.streamStatus();
    if (status && status.source_state) {
      store.setBaseState(status.source_state);
    }
  } catch {
    store.markDisconnected();
  }
  ws.connect();
}

document.addEventListener("DOMContentLoaded", () => {
  boot().catch((e) => {
    console.error("boot failed", e);
    document.getElementById("source-banner").hidden = false;
    document.getElementById("source-banner").textContent =
      `BOOT FAILURE — ${e.message}`;
  });
});
