/* RF Vision research console — boot.
   RF Vision native. Wiring (adapted lifecycle concept from RuView app.js,
   dd02efe2): health monitor → source chrome → tab manager → WS stream →
   store fan-out. No sensing logic lives here; frames flow
   backend contract → store → tabs. */
import { SourceStore } from "./store.js";
import { TabManager } from "./tabs.js";
import { bindSourceChrome } from "./banner.js";
import { HealthMonitor } from "./health.js";
import { WsClient } from "./ws.js";
import { api } from "./api.js";
import { OverviewTab } from "./tabs/overview.js";
import { SensingTab } from "./tabs/sensing.js";
import { RfFieldTab } from "./tabs/rffield.js";
import { LocalizationTab } from "./tabs/localization.js";
import { XaiTab } from "./tabs/xai.js";
import { ExperimentsTab } from "./tabs/experiments.js";
import { HardwareTab } from "./tabs/hardware.js";
import { ModelsTab } from "./tabs/models.js";
import { SettingsTab } from "./tabs/settings.js";

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
  tabs.register("localization", LocalizationTab);
  tabs.register("xai", XaiTab);
  tabs.register("experiments", ExperimentsTab);
  tabs.register("hardware", HardwareTab);
  tabs.register("models", ModelsTab);
  tabs.register("settings", SettingsTab);

  const ctx = { store, ws, api, tabs, health };
  bindSourceChrome(store);
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
