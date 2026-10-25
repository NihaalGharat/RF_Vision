/* Hardware — "What physical RF system is connected and ready?"
   Network (read-only discovery) · RF Nodes (backend identity) ·
   Provisioning (CONNECT RF NODES, transient password) · RF READY chain ·
   Diagnostics. SCAN NETWORKS only re-reads state; it connects to nothing. */
import { h, kv, unknown } from "../h.js";
import { Card, ErrorRow, ModePill, PageHeader, RfReadyBadge } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { healthTone } from "./hardwareHealth.js";
import { hardwareStore, sensingStore, sourceStore, useStore } from "../state/store.js";

const R = window.React;

const NODE_HEALTH_COLORS = {
  healthy: "#34d399",
  degraded: "#fbbf24",
  unavailable: "#f87171",
  unknown: "#94a3b8",
};

function esc(s) {
  return String(s == null ? "" : s);
}

export function HardwareView({ refresh }) {
  const hw = useStore(hardwareStore);
  const sensing = useStore(sensingStore);
  const source = useStore(sourceStore);
  const [ssid, setSsid] = R.useState("");
  const [ssidTouched, setSsidTouched] = R.useState(false);
  const passRef = R.useRef(null);
  const net = hw.network;
  const rfr = hw.readiness;

  // Prefill SSID from detection until the operator types their own.
  R.useEffect(() => {
    if (!ssidTouched && net && net.network && net.network.ssid && !ssid) {
      setSsid(net.network.ssid);
    }
  }, [net]);

  const connect = async () => {
    const password = (passRef.current && passRef.current.value) || "";
    if (passRef.current) passRef.current.value = ""; // never retained in the DOM
    if (!ssid.trim() || !password) {
      throw new Error("SSID and password are required. The password travels only in the provisioning POST body.");
    }
    const res = await api.provision(ssid.trim(), password);
    hardwareStore.set({ provResult: res });
    await refresh();
    const perNode = (res.nodes || []).map((n) => `${n.node_id}: ${n.state}`).join("; ");
    return `${res.state}${perNode ? ` — ${perNode}` : ""}`;
  };

  const nodeList = hw.nodes && hw.nodes.available ? (hw.nodes.nodes || []) : null;

  const dual = async (start) => {
    const res = start ? await api.dualStart() : await api.dualStop();
    await refresh();
    return `${res.running ? "RUNNING" : "STOPPED"}${res.reason ? ` — ${res.reason}` : ""}${res.note ? ` — ${res.note}` : ""}`;
  };

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "Hardware", back: true,
      actions: [
        h(ModePill, { source: source.source, stale: false }),
        h(RfReadyBadge, { readiness: rfr, error: hw.readinessError }),
      ],
    }),
    h("div", { className: "rfreact-cols rfreact-cols-near" },
      h("div", { className: "rfreact-col" },
      h(Card, { label: "Discovery", title: "Network — current (read-only discovery)" },
        h(ErrorRow, { error: hw.networkError, onRetry: refresh, what: "network" }),
        !net ? unknown("BACKEND UNREACHABLE")
          : kv([
            ["state", net.state || "UNKNOWN"],
            ["ssid", net.network ? esc(net.network.ssid) : "—"],
            ["bssid", net.network ? esc(net.network.bssid || "?") : "—"],
            ["channel", net.network && net.network.channel != null ? String(net.network.channel) : "—"],
            ["band", net.network ? esc(net.network.band || "") : "—"],
            ["compatibility", `ESP32 requires ${esc(net.esp32_band || "2.4 GHz")}`],
            ["detail", esc(net.reason || "")],
          ]),
        h("div", { className: "rfreact-row" },
          h(SafeButton, {
            action: "read-only: re-read GET /api/v1/network; connects to nothing, configures nothing",
            label: "SCAN NETWORKS", onClick: async () => { await refresh(); return "network state re-read (no connection attempted)"; },
          }),
        )),
      h(Card, { label: "Nodes", title: "RF Nodes — backend identity" },
        h(ErrorRow, { error: hw.nodesError, onRetry: refresh, what: "nodes" }),
        nodeList === null
          ? unknown(hw.nodes && hw.nodes.reason ? hw.nodes.reason : "STANDBY (dual session not started)")
          : h("ul", { className: "rfreact-rows", style: { listStyle: "none", margin: 0, padding: 0 } },
            nodeList.map((n) => {
              const color = NODE_HEALTH_COLORS[healthTone(n.connection)];
              return h("li", { key: n.node_id, className: "rfreact-divrow" },
                h("div", { style: { minWidth: 0 } },
                  h("p", { className: "rfreact-linetitle" }, n.node_id),
                  h("p", { className: "rfreact-linemono" },
                    `${n.board_mac || "mac ?"} · CH ${n.channel != null ? n.channel : "?"} · ${n.rssi != null ? `${n.rssi} dBm` : "rssi ?"}`)),
                h("span", {
                  className: "rfreact-badge", style: { color, borderColor: `${color}55`, background: `${color}14` },
                },
                  h("span", { className: "dot", style: { width: "6px", height: "6px", borderRadius: "999px", background: color, boxShadow: `0 0 6px ${color}` } }),
                  (n.connection || "unknown").toUpperCase()));
            })),
        h("div", { className: "rfreact-row" },
          h(SafeButton, {
            action: "dual session: POST /api/v1/dual/start (both nodes required; refuses while single live source runs)",
            label: "START DUAL SESSION", kind: "primary", onClick: () => dual(true),
          }),
          h(SafeButton, {
            action: "dual session: POST /api/v1/dual/stop (idempotent; releases both serial ports)",
            label: "STOP", onClick: () => dual(false),
          }),
        )),
      h(Card, { label: "Provisioning", title: "Provisioning — CONNECT RF NODES" },
        h("div", { className: "rfreact-row" },
          h("input", {
            className: "rfreact-input", type: "text", placeholder: "SSID", autoComplete: "off",
            "aria-label": "Wi-Fi SSID", value: ssid,
            onChange: (e) => { setSsid(e.target.value); setSsidTouched(true); },
          }),
          h("input", {
            className: "rfreact-input", type: "password", placeholder: "password", autoComplete: "off",
            "aria-label": "Wi-Fi password", ref: passRef,
          }),
          h(SafeButton, {
            action: "provisioning/configuration: POST /api/v1/network/provision then readiness re-read",
            label: "CONNECT RF NODES", kind: "primary", onClick: connect,
          }),
        ),
        h("p", { className: "rfreact-note" },
          "Provision targets the detected network. The password travels only in the provisioning POST body — never displayed, logged, or stored."),
        hw.provResult
          ? kv((hw.provResult.nodes || []).map((n) => [`node ${esc(n.node_id)}`, `${esc(n.state)}${n.reason ? ` — ${esc(n.reason)}` : ""}`]))
          : null),
      ),
      h("div", { className: "rfreact-col" },
      h(Card, { label: "Readiness", title: "RF READY — readiness chain (backend verdict)" },
        h(ErrorRow, { error: hw.readinessError, onRetry: refresh, what: "rf_readiness" }),
        !rfr ? unknown("BACKEND UNREACHABLE")
          : kv([
            ["overall", rfr.rf_ready ? "RF READY" : `NOT READY (${rfr.state || "?"})`],
            ["reason", esc(rfr.reason || "")],
            ["degraded", String(!!rfr.degraded)],
            ["network change", rfr.network_change ? `${rfr.network_change.changed ? "CHANGED" : "stable"} — ${esc(rfr.network_change.reason || "")}` : "UNKNOWN"],
          ]),
        h("p", { className: "rfreact-note" }, "RF READY is rendered only from backend readiness — never set in this UI.")),
      h(Card, { label: "Diagnostics", title: "Diagnostics — transport · packets · sync" },
        sensing.live
          ? kv([
            ["transport", sensing.live.transport.open ? `open (${sensing.live.port} @ ${sensing.live.baud})` : "closed"],
            ["throughput", sensing.live.transport.bytes_per_s != null ? `${(sensing.live.transport.bytes_per_s / 1000).toFixed(1)} kB/s` : "UNKNOWN"],
            ["packets", `${sensing.live.stream.valid} valid · ${sensing.live.stream.malformed} malformed · ${sensing.live.stream.gaps} gaps`],
            ["sequence", sensing.live.stream.last_seq != null ? `last seq ${sensing.live.stream.last_seq}` : "UNKNOWN"],
            ["frame age", sensing.live.stream.last_update_age_s != null ? `${sensing.live.stream.last_update_age_s.toFixed(1)} s ago${sensing.live.stream.stale ? " — STALE" : ""}` : "no data"],
            ["csi structure", `tones ${sensing.live.signal.tones ?? "?"} · CH ${sensing.live.signal.channel ?? "?"} · ${esc(sensing.live.signal.bssid || "?")}`],
            ["sync", hw.nodes && hw.nodes.available ? `sync ${hw.nodes.sync_state}` : "UNKNOWN (no session)"],
          ])
          : unknown(`NO LIVE SESSION (source ${source.source})`)),
      ),
    ));
}
