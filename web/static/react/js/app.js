/* App root — providers, shared polling, WebSocket wiring, layout.
   Fan-out (mirrors the legacy console lifecycle):
     health poll (5 s) + union REST poll (2 s) + WS events → domain stores → routes.
   Components read stores; they never fetch directly (except explicit commands
   via the api service) and never hold backend state locally. */
import { h } from "./h.js";
import { Nav, useRoute } from "./router.js";
import { api } from "./services/api.js";
import { WsService } from "./services/websocket.js";
import { sourceFromMode } from "./services/sources.js";
import {
  systemStore, sourceStore, hardwareStore, sensingStore,
  researchStore, visionStore, useStore,
} from "./state/store.js";
import { ConnDot, Icon, ThemeToggle, Clock } from "./components/global.js";import { LiveView } from "./features/live.js";
import { VisualizeView } from "./features/visualize.js";
import { ResearchView } from "./features/research.js";
import { HardwareView } from "./features/hardware.js";
import { SystemView } from "./features/system.js";

const R = window.React;
const POLL_MS = 2000;
const HEALTH_MS = 5000;

async function refreshAll() {
  const jobs = {
    health: api.health().then(
      (d) => systemStore.set({ health: d, healthError: null, contract: d.contract, version: d.version }),
      (e) => systemStore.set({ health: null, healthError: String(e.message || e) })),
    stream: api.streamStatus().then(
      (d) => sourceStore.set({
        mode: d.mode, running: !!d.running, sourceState: d.source_state,
        source: sourceFromMode(d.mode),
      }),
      () => {}),
    network: api.network().then(
      (d) => hardwareStore.set({ network: d, networkError: null }),
      (e) => hardwareStore.set({ networkError: String(e.message || e) })),
    readiness: api.rfReadiness().then(
      (d) => hardwareStore.set({ readiness: d, readinessError: null }),
      (e) => hardwareStore.set({ readinessError: String(e.message || e) })),
    nodes: api.nodes().then(
      (d) => hardwareStore.set({ nodes: d, nodesError: null }),
      (e) => hardwareStore.set({ nodesError: String(e.message || e) })),
    experiment: api.experiment().then(
      (d) => researchStore.set({ experiment: d, experimentError: null }),
      (e) => researchStore.set({ experimentError: String(e.message || e) })),
    live: api.live().then(
      (d) => sensingStore.set({ live: d && d.available ? d : null, liveError: null }),
      (e) => sensingStore.set({ liveError: String(e.message || e) })),
    status: api.status().then(
      (d) => sensingStore.set({ status: d }),
      () => {}),
    vision: api.vision().then(
      (d) => visionStore.set({ vision: d && d.available ? d.vision : null, visionError: null }),
      (e) => visionStore.set({ visionError: String(e.message || e) })),
  };
  await Promise.allSettled(Object.values(jobs));
}

function Shell({ ws }) {
  const R = window.React;
  const route = useRoute();
  const system = useStore(systemStore);
  const ctx = { ws, refresh: refreshAll };
  const [glowStrong, setGlowStrong] = R.useState(false);

  const view = route === "live" ? h(LiveView, ctx)
    : route === "visualize" ? h(VisualizeView, ctx)
    : route === "research" ? h(ResearchView, ctx)
    : route === "hardware" ? h(HardwareView, ctx)
    : h(SystemView, ctx);

  return h("div", { className: "rfreact" },
    h("div", {
      className: "rfreact-glow", "aria-hidden": "true",
      style: { opacity: glowStrong ? 1 : 0.55 },
    }),
    h("div", { className: "rfreact-shell" },
      h("aside", { className: "rfreact-side", "aria-label": "Primary navigation" },
        h("a", {
          className: "rfreact-logo", href: "#/live",
          title: "RF Vision", "aria-label": "RF Vision overview",
        }, "RF"),
        h(Nav, { current: route }),
        h("div", { className: "rfreact-sidefoot" },
          h("button", {
            className: `rfreact-iconbtn${glowStrong ? " on" : ""}`,
            onClick: () => setGlowStrong((v) => !v),
            title: "Ambient glow",
            "aria-label": glowStrong ? "Reduce ambient glow" : "Increase ambient glow",
          }, h(Icon, { name: "sun", size: 17 })),
          h(ThemeToggle, null),
          h("span", { style: { padding: "8px 0 2px" } },
            h(ConnDot, { wsState: system.wsState, backendUp: !!system.health })))),
      h("main", { className: "rfreact-main" },
        view,
        h("footer", { className: "rfreact-foot" },
          h("span", null, system.health
            ? `provenance: ${system.health.source} · ${system.health.source_state} · web ${system.health.version}`
            : "provenance: console unreachable"),
          h("span", null, "RF Vision research instrument — estimates are not conclusions"),
          h(Clock, null),
          h("span", null, h("a", { href: "/legacy" }, "Legacy console"))))));
}

function boot() {
  const ws = new WsService();
  ws.onEvent = (msg) => {
    if (!msg || typeof msg !== "object") return;
    // Frame state tracks sensing frames only: status/heartbeat envelopes
    // must never render as measurement frames (legacy sensing-tab rule).
    if (msg.type !== "sensing.snapshot") return;
    sourceStore.set({ lastEvent: msg, lastEventTs: Date.now() });
    sensingStore.set({ frameCount: sensingStore.get().frameCount + 1 });
  };
  ws.onState = (wsState) => {
    systemStore.set({ wsState });
    if (wsState === "disconnected") {
      // Transport loss with no frames: honest empty state (legacy rule).
      api.status().then((s) => {
        if (!s || s.packets === 0) {
          sourceStore.set({ lastEvent: null, lastEventTs: 0 });
        }
      }).catch(() => sourceStore.set({ lastEvent: null, lastEventTs: 0 }));
    }
  };

  refreshAll().catch((e) => console.error("initial refresh", e));
  setInterval(() => refreshAll().catch((e) => console.error("poll", e)), POLL_MS);
  ws.connect();

  const root = ReactDOM.createRoot(document.getElementById("react-root"));
  root.render(h(Shell, { ws }));
}

document.addEventListener("DOMContentLoaded", () => {
  try {
    boot();
  } catch (e) {
    console.error("react boot failed", e);
    const el = document.getElementById("react-boot-error");
    el.hidden = false;
    el.textContent = `BOOT FAILURE — ${e.message}. Legacy console unaffected at /legacy`;
  }
});
