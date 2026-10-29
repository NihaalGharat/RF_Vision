/* System — "How is the RF Vision software itself operating?"
   Backend status, WebSocket status, contract/software versions, appearance,
   safety boundary. Nothing here changes acquisition or hardware. */
import { h, kv, unknown } from "../h.js";
import { Card, ModePill, PageHeader, ThemeToggle } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { sourceStore, systemStore, useStore } from "../state/store.js";

const WS_LABEL = {
  connected: "connected", connecting: "connecting…",
  reconnecting: "reconnecting…", disconnected: "disconnected",
};

export function SystemView({ refresh }) {
  const system = useStore(systemStore);
  const source = useStore(sourceStore);
  const health = system.health;

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "System", back: true,
      actions: [h(ModePill, { source: source.source, stale: false, dual: source.dual })],
    }),
    h("div", { className: "rfreact-cols rfreact-cols-near" },
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Backend", title: "Backend status" },
          health
            ? h("div", null,
              kv([
                ["health", health.status],
                ["acquisition", source.dual
                  ? `${source.dual.label} · ${source.dual.live}/${source.dual.expected} live`
                  : `${health.source} · ${health.source_state}`],
                ["uptime", `${Math.round(health.uptime_s)} s`],
              ]),
              h("details", { className: "rfreact-scene-options" },
                h("summary", null, "Advanced — build, backend & session details"),
                kv([
                  ["contract", `v${health.contract}`],
                  ["software", `web ${health.version}`],
                  ["legacy source", `${health.source} · ${health.source_state}`],
                  ["backend session", source.dual ? source.dual.label : "single-source / none"],
                ])))
            : unknown(system.healthError ? `UNREACHABLE (${system.healthError})` : "loading…"),
          h("div", { className: "rfreact-row" },
            h(SafeButton, {
              action: "read-only: re-read backend status; modifies no configuration",
              label: "REFRESH STATUS", onClick: async () => { await refresh(); return "status re-read"; },
            }),
          )),
        h(Card, { label: "Transport", title: "WebSocket status" },
          kv([
            ["state", WS_LABEL[system.wsState] || system.wsState],
          ]),
          h("details", { className: "rfreact-scene-options" },
            h("summary", null, "Advanced — endpoint & protocol"),
            kv([["endpoint", "/ws/sensing (existing contract)"]]),
            h("p", { className: "rfreact-note" },
              "JSON text, 30 s ping, indefinite backoff reconnect (capped at 30 s). No new protocol."))),
        h(Card, { label: "Display", title: "Appearance" },
          h("div", { className: "rfreact-row" }, h(ThemeToggle, null))),
      ),
      h("div", { className: "rfreact-col" },
        h("details", { className: "rfreact-scene-options" },
          h("summary", null, "Advanced — safety boundary"),
          h(Card, { label: "Boundary", title: "Safety — out of scope for this console" },
            kv([
              ["flash / erase / reset", "never"],
              ["router changes", "never"],
              ["live capture", "diagnostic only (explicit, bounded)"],
              ["human experiments", "not in this phase"],
              ["model training", "not in this phase"],
              ["mock as live", "never — SIMULATION/FIXTURE always badged"],
            ]))),
      ),
    ));
}
