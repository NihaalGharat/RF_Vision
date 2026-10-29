/* Hardware — "What physical RF system is connected and ready?"
   Network (read-only discovery) · RF Nodes (backend identity) ·
   Provisioning (CONNECT RF NODES, transient password) · RF READY chain ·
   Diagnostics. SCAN NETWORKS only re-reads state; it connects to nothing. */
import { h, kv, unknown } from "../h.js";
import { Card, ErrorRow, ModePill, PageHeader, RfReadyBadge } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { networkMatch } from "../services/sources.js";
import { healthTone } from "./hardwareHealth.js";
import { hardwareStore, sensingStore, sourceStore, useStore } from "../state/store.js";

const R = window.React;
const NODE_IDS = ["esp32-a", "esp32-b"];

const NODE_HEALTH_COLORS = {
  healthy: "#34d399",
  degraded: "#fbbf24",
  unavailable: "#f87171",
  unknown: "#94a3b8",
};

const NETWORK_MATCH_COLORS = {
  MATCH: "#34d399",
  MISMATCH: "#f87171",
  UNKNOWN: "#94a3b8",
};

const NODE_STATE_COLORS = {
  CSI_VERIFIED: "#34d399",
  NODE_CONNECTED: "#34d399",
  NODE_DISCONNECTED: "#fbbf24",
  LIVE_PENDING: "#fbbf24",
  CSI_STALE: "#fbbf24",
  NODE_SILENT: "#f87171",
  NODE_MISSING: "#f87171",
  BAD_CREDENTIALS: "#f87171",
  PROVISIONING_FAILED: "#f87171",
  NODE_ERROR: "#f87171",
  NOT_CHECKED: "#94a3b8",
};

function esc(s) {
  return String(s == null ? "" : s);
}

function StatusBadge({ label, color }) {
  return h("span", {
    className: "rfreact-badge",
    style: { color, borderColor: `${color}55`, background: `${color}14` },
  }, label);
}

export function HardwareView({ refresh }) {
  const hw = useStore(hardwareStore);
  const sensing = useStore(sensingStore);
  const source = useStore(sourceStore);
  const [ssid, setSsid] = R.useState("");
  const [ssidTouched, setSsidTouched] = R.useState(false);
  const [selected, setSelected] = R.useState({ "esp32-a": true, "esp32-b": true });
  const [pending, setPending] = R.useState(null);
  const passRef = R.useRef(null);
  const net = hw.network;
  const rfr = hw.readiness;
  const target = net && net.network ? net.network : null;
  const targetReady = !!(net && net.state === "NETWORK_DETECTED"
    && target && target.ssid);
  const selectedIds = NODE_IDS.filter((nid) => selected[nid]);

  // Track the detected SSID until the operator edits the field.
  R.useEffect(() => {
    if (!ssidTouched) {
      setSsid(net && net.network ? (net.network.ssid || "") : "");
    }
  }, [net]);

  const liveNodes = hw.nodes && hw.nodes.available ? (hw.nodes.nodes || []) : [];
  const liveById = {};
  liveNodes.forEach((n) => { liveById[n.node_id] = n; });
  const inspectById = {};
  ((hw.nodeInspect && hw.nodeInspect.nodes) || []).forEach((n) => {
    inspectById[n.node_id] = n;
  });
  const provById = {};
  ((hw.provResult && hw.provResult.nodes) || []).forEach((n) => {
    provById[n.node_id] = n;
  });

  const nodeState = (nid) => {
    const live = liveById[nid];
    if (live && live.source_state === "LIVE_VERIFIED"
        && Number(live.valid) > 0 && live.connection !== "DEGRADED") {
      return {
        code: "CSI_VERIFIED", color: NODE_STATE_COLORS.CSI_VERIFIED,
        detail: `${live.valid} valid records · ${live.connection}${live.sync_ready ? " · sync ready" : ""}`,
      };
    }
    const inspected = inspectById[nid];
    if (inspected) {
      return {
        code: inspected.state,
        color: NODE_STATE_COLORS[inspected.state] || NODE_STATE_COLORS.NOT_CHECKED,
        detail: inspected.reason || "",
      };
    }
    if (live) {
      const code = live.connection === "DISCONNECTED"
        ? "NODE_SILENT"
        : (live.connection === "DEGRADED" ? "CSI_STALE" : "LIVE_PENDING");
      return {
        code, color: NODE_STATE_COLORS[code],
        detail: `${live.source_state} · ${live.valid} valid records · ${live.connection}`,
      };
    }
    const prov = provById[nid];
    if (prov) {
      const code = prov.observed || (prov.state === "PROVISIONED"
        ? "NODE_CONNECTED" : prov.state);
      return {
        code, color: NODE_STATE_COLORS[code] || NODE_STATE_COLORS.NOT_CHECKED,
        detail: prov.reason || "",
      };
    }
    return { code: "NOT_CHECKED", color: NODE_STATE_COLORS.NOT_CHECKED,
      detail: "inspect the node to read its current association" };
  };

  const nodeNetwork = (nid) => {
    const inspected = inspectById[nid];
    if (inspected && inspected.status) {
      return { origin: "current", ...inspected.status };
    }
    const prov = provById[nid];
    if (prov && prov.status && prov.status.ssid) {
      return { origin: "last provision", ...prov.status };
    }
    const live = liveById[nid];
    if (live && (live.bssid || live.channel != null)) {
      return {
        origin: "current", ssid: null,
        bssid: live.bssid, channel: live.channel,
      };
    }
    return null;
  };

  const currentNetwork = (nid) => {
    const observed = nodeNetwork(nid);
    if (!observed) return "current: not queried — use INSPECT NODE NETWORK";
    return `${observed.origin}: ${esc(observed.ssid || "SSID not queried")} · ${esc(observed.bssid || "BSSID ?")} · CH ${observed.channel != null ? observed.channel : "?"}`;
  };

  const networkByNode = {};
  NODE_IDS.forEach((nid) => {
    networkByNode[nid] = networkMatch(target, nodeNetwork(nid));
  });
  const networkMismatch = NODE_IDS.some(
    (nid) => networkByNode[nid].state === "MISMATCH");
  const networkUnknown = NODE_IDS.some(
    (nid) => networkByNode[nid].state === "UNKNOWN");
  const networkVerdict = !target
    ? { state: "UNKNOWN", text: "NETWORK UNKNOWN — no laptop network target is available." }
    : networkMismatch
      ? { state: "MISMATCH", text: "NODE NETWORK MISMATCH — Verify both ESP32s are connected to the laptop's active 2.4 GHz network." }
      : networkUnknown
        ? { state: "UNKNOWN", text: "NODE NETWORK UNVERIFIED — Inspect both ESP32s; do not assume a match without BSSID and channel." }
        : { state: "MATCH", text: "NODE NETWORK MATCH — both ESP32s report the laptop's BSSID and channel." };

  const toggleNode = (nid) => {
    setSelected((prev) => ({ ...prev, [nid]: !prev[nid] }));
  };

  const reviewConnect = async () => {
    const password = (passRef.current && passRef.current.value) || "";
    if (!targetReady || !target) {
      throw new Error("No supported 2.4 GHz network was detected. Provisioning is locked to the detected hotspot.");
    }
    if (ssid.trim() !== target.ssid) {
      throw new Error("SSID must match the detected hotspot. Re-scan the network if it changed.");
    }
    if (!password) {
      throw new Error("Password is required. It travels only in the provisioning POST body.");
    }
    if (!selectedIds.length) {
      throw new Error("Select at least one RF node before provisioning.");
    }
    setPending({
      ssid: ssid.trim(),
      nodes: selectedIds,
      target: target ? {
        ssid: target.ssid, bssid: target.bssid,
        channel: target.channel, band: target.band,
      } : null,
    });
    return "Review the change, then confirm";
  };

  const cancelConnect = () => {
    setPending(null);
    if (passRef.current) passRef.current.value = "";
  };

  const confirmConnect = async () => {
    const password = (passRef.current && passRef.current.value) || "";
    const review = pending;
    setPending(null);
    if (passRef.current) passRef.current.value = "";
    if (!review) throw new Error("No provisioning review is pending.");
    if (!password) {
      throw new Error("Password was cleared. Re-enter it and review again.");
    }
    try {
      const current = await api.network();
      const now = current && current.network;
      if (!now || current.state !== "NETWORK_DETECTED"
          || now.ssid !== review.ssid
          || (review.target && review.target.bssid
              && now.bssid !== review.target.bssid)) {
        throw new Error(
          "The detected network changed after review. Re-scan and confirm the new target.");
      }
      const res = await api.provision(review.ssid, password, review.nodes);
      hardwareStore.set({ provResult: res, nodeInspect: null,
        nodeInspectError: null });
      await refresh();
      const perNode = (res.nodes || []).map((n) => {
        const observed = n.observed || n.state;
        return `${n.node_id}: ${observed}`;
      }).join("; ");
      return `${res.state}${perNode ? ` — ${perNode}` : ""}`;
    } catch (err) {
      hardwareStore.set({ nodeInspectError: String(err.message || err) });
      throw err;
    }
  };

  const inspect = async () => {
    if (!selectedIds.length) {
      throw new Error("Select at least one RF node to inspect.");
    }
    try {
      const res = await api.inspectNodes(selectedIds);
      hardwareStore.set({ nodeInspect: res, nodeInspectError: null,
        provResult: null });
      const perNode = (res.nodes || []).map(
        (n) => `${n.node_id}: ${n.state}`).join("; ");
      return `${res.state}${perNode ? ` — ${perNode}` : ""}`;
    } catch (err) {
      hardwareStore.set({ nodeInspectError: String(err.message || err) });
      throw err;
    }
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
        h(ModePill, { source: source.source, stale: false, dual: source.dual }),
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
        h("p", { className: `rfreact-status-banner ${networkVerdict.state.toLowerCase()}` },
          networkVerdict.text),
        target
          ? h("p", { className: "rfreact-note" },
            `Laptop target: ${esc(target.ssid)} · ${esc(target.bssid || "BSSID ?")} · CH ${target.channel != null ? target.channel : "?"}`)
          : null,
        rfr && !rfr.rf_ready && rfr.reason
          ? h("p", { className: "rfreact-note" },
            `Backend readiness: ${esc(rfr.state || "UNKNOWN")} — ${esc(rfr.reason)}`)
          : null,
        nodeList === null
          ? unknown(hw.nodes && hw.nodes.reason ? hw.nodes.reason : "STANDBY (dual session not started)")
          : h("ul", { className: "rfreact-rows", style: { listStyle: "none", margin: 0, padding: 0 } },
            nodeList.map((n) => {
              const color = NODE_HEALTH_COLORS[healthTone(n.connection)];
              const nm = networkByNode[n.node_id] || networkMatch(target, null);
              const observed = nodeNetwork(n.node_id);
              return h("li", { key: n.node_id, className: "rfreact-divrow" },
                h("div", { style: { minWidth: 0 } },
                  h("p", { className: "rfreact-linetitle" },
                    n.node_id,
                    " ",
                    h(StatusBadge, {
                      label: nm.label,
                      color: NETWORK_MATCH_COLORS[nm.state] || NETWORK_MATCH_COLORS.UNKNOWN,
                    })),
                  h("p", { className: "rfreact-linemono" },
                    `${n.board_mac || "mac ?"} · BSSID ${esc((observed && observed.bssid) || n.bssid || "?")} · CH ${n.channel != null ? n.channel : (observed && observed.channel != null ? observed.channel : "?")} · ${n.rssi != null ? `${n.rssi} dBm` : "rssi ?"} · ${n.sync_ready ? "SYNC READY" : "sync pending"}`)),
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
      h("details", { className: "rfreact-scene-options" },
        h("summary", null, "Advanced — provisioning / recovery"),
        h(Card, { label: "Provisioning", title: "Provisioning — CONNECT RF NODES" },
        h("p", { className: "rfreact-note" },
          "Select one node for recovery or both for a normal change. Inspect is read-only (RFV_NET_STATUS); provisioning writes credentials/reboots association only."),
        h("div", { className: "rfreact-nodechecks" },
          NODE_IDS.map((nid) => {
            const st = nodeState(nid);
            return h("label", { key: nid, className: "rfreact-nodecheck" },
              h("input", {
                type: "checkbox", checked: !!selected[nid],
                onChange: () => toggleNode(nid),
                "aria-label": `Include ${nid} in provisioning`,
              }),
              h("span", { className: "rfreact-nodecheckbody" },
                h("span", { className: "rfreact-nodeline" },
                  h("strong", null, nid),
                  h(StatusBadge, { label: st.code, color: st.color })),
                h("span", { className: "rfreact-linemono" }, currentNetwork(nid)),
                h("span", { className: "rfreact-linemono" },
                  `target: ${target ? `${esc(target.ssid)} · ${esc(target.bssid || "?")} · CH ${target.channel != null ? target.channel : "?"}` : "no detected network"}`),
                h("span", { className: "rfreact-note" }, st.detail)));
          })),
        h(ErrorRow, { error: hw.nodeInspectError, onRetry: inspect, what: "node network status" }),
        h("div", { className: "rfreact-row" },
          h(SafeButton, {
            action: "read-only: POST /api/v1/network/inspect sends RFV_NET_STATUS only; no credentials changed",
            label: "INSPECT NODE NETWORK", onClick: inspect,
          }),
        ),
        h("div", { className: "rfreact-row" },
          h("input", {
            className: "rfreact-input", type: "text", placeholder: "SSID", autoComplete: "off",
            "aria-label": "Wi-Fi SSID", value: ssid,
            onChange: (e) => { setSsid(e.target.value); setSsidTouched(true); },
          }),
          h("input", {
            className: "rfreact-input", type: "password", placeholder: "password", autoComplete: "new-password",
            "aria-label": "Wi-Fi password", ref: passRef,
          }),
          h(SafeButton, {
            action: "opens explicit confirmation; provisioning is not sent until confirmed",
            label: "CONNECT RF NODES", kind: "primary", onClick: reviewConnect,
            disabled: !targetReady,
            title: targetReady
              ? "opens explicit confirmation; provisioning is not sent until confirmed"
              : "waiting for a supported 2.4 GHz network",
          }),
        ),
        h("p", { className: "rfreact-note" },
          `Provisioning is locked to the detected network${targetReady ? "" : " — no supported target detected"}. The password travels only in the provisioning POST body — never displayed, logged, or stored.`),
        hw.provResult
          ? kv((hw.provResult.nodes || []).map((n) => [`node ${esc(n.node_id)}`, `${esc(n.observed || n.state)}${n.reason ? ` — ${esc(n.reason)}` : ""}`]))
          : null)),
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
      h("details", { className: "rfreact-scene-options" },
        h("summary", null, "Advanced — transport & packet diagnostics"),
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
          : source.dual
            ? kv([
              ["session", source.dual.label],
              ["sync", source.dual.sync],
              ["nodes live", `${source.dual.live}/${source.dual.expected}`],
              ...((hw.nodes && hw.nodes.nodes) || []).map((n) => [
                `node ${esc(n.node_id)}`,
                `${esc(n.source_state)} · ${esc(n.connection)} · ${n.valid} valid · ${n.malformed} malformed`,
              ]),
            ])
            : unknown(`NO LIVE SESSION (source ${source.source})`))),
      ),
    ),
    pending ? h("div", { className: "rfreact-modal-backdrop" },
      h("div", {
        className: "rfreact-modal", role: "dialog", "aria-modal": "true",
        "aria-labelledby": "provision-confirm-title",
      },
        h("h3", { id: "provision-confirm-title", className: "rfreact-card-title" },
          "Confirm provisioning change"),
        h("p", { className: "rfreact-note" },
          "This writes Wi-Fi credentials to the selected node(s) and restarts their association. A node on another AP will disconnect. One node at a time is recommended for recovery."),
        kv([
          ["target SSID", pending.target ? esc(pending.target.ssid) : esc(pending.ssid)],
          ["target BSSID", pending.target ? esc(pending.target.bssid || "?") : "not detected"],
          ["target channel", pending.target && pending.target.channel != null ? String(pending.target.channel) : "not detected"],
          ["band", pending.target ? esc(pending.target.band || "") : "unknown"],
          ["nodes", pending.nodes.join(", ")],
          ["current status", pending.nodes.map((nid) => `${nid}: ${nodeState(nid).code}`).join("; ")],
        ]),
        h("p", { className: "rfreact-note" },
          "Confirm re-checks the detected BSSID/SSID before sending. Credentials are sent only in this POST body. Do not close this tab until the operation completes."),
        h("div", { className: "rfreact-modal-actions" },
          h("button", {
            className: "rfreact-btn", type: "button", onClick: cancelConnect,
          }, "CANCEL"),
          h(SafeButton, {
            action: "provisioning/configuration: POST /api/v1/network/provision for the reviewed node set",
            label: "CONFIRM PROVISION", kind: "primary", onClick: confirmConnect,
          }),
        ))) : null);
}
