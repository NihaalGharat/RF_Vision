/* Visualize — "What does the RF system currently infer spatially?"
   WS-1: validated legacy spatial experience (2D room + three.js r160 one-link
   scene) migrated into the React console. The renderers are the legacy
   implementation itself (RfLinkScene, drawRoom2d — single source of truth,
   never re-implemented); this view is presentation wiring only:
     backend → existing services/stores → shared model → 2D + 3D.
   Semantics preserved from web/static/js/tabs/rffield.js:
   - EXACTLY ONE router↔ESP32 link; UNKNOWN geometry stays UNKNOWN.
   - position == null → marker hidden; else RF-INFERRED / NOT VALIDATED.
   - uncertainty: none validated → always null (no region rendered).
   - Field strip = measured-amplitude abstraction, not a propagation model.
   Controls here NEVER touch hardware or acquisition: PAUSE freezes rendering
   only; RESET VIEW resets camera + local view token only. */
import { h, kv } from "../h.js";
import { Card, ModePill, PageHeader } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { frameFreshness } from "../services/sources.js";
import { sourceStore, sensingStore, vizStore, visionStore, useStore } from "../state/store.js";
// Validated spatial renderers, shared with the legacy console. Absolute-path
// import keeps one implementation; the three.js specifier resolves via the
// importmap in web/static/react/index.html (local r160, no new dependency).
import { RfLinkScene } from "/static/js/scene3d.js";
import { drawRoom2d, describe } from "/static/js/viz2d.js";

const R = window.React;
const PAINT_MIN_MS = 250;
// Mirrors RfLinkScene.init() camera defaults — RESET VIEW restores these.
const HOME_POS = [4.5, 3.5, 6.5];
const HOME_TARGET = [0, 0.8, 0];

// Same HUD-extra composition as the legacy RF-field tab: source state,
// stream rate, RSSI, sequence — telemetry only, no inference.
function hudExtra(live) {
  if (live && live.available) {
    const st = live.stream;
    const sg = live.signal;
    return `${live.source_state} · ` +
      `${st.rate_hz != null ? `${st.rate_hz.toFixed(1)} Hz` : "rate ?"} · ` +
      `rssi ${sg.rssi_last != null ? sg.rssi_last : "?"} · ` +
      `seq ${st.last_seq != null ? st.last_seq : "?"}`;
  }
  return "";
}

// Same presence rule as legacy: backend presence_state rides the HUD as an
// RF-inferred, uncalibrated observation — never a body, mesh, or claim.
// The vision pipeline aggregate (evidence + zone) rides alongside when
// attached; UNKNOWN/absent pipeline contributes nothing.
function presenceLabel(p, vision) {
  const base = (p && p.presence_state && p.presence_state !== "UNKNOWN")
    ? `${p.presence_state} (RF-INFERRED, UNCALIBRATED)` : "";
  if (!vision || !vision.evidence || vision.evidence === "UNKNOWN") return base;
  const zone = vision.spatial && vision.spatial.zone
    ? ` · zone ${vision.spatial.zone} (${vision.spatial.level})` : "";
  const extra = `${vision.evidence}${zone}`;
  return base ? `${base} · ${extra}` : `${extra} (RF-INFERRED, UNCALIBRATED)`;
}

// RF Vision pipeline rows: evidence + per-node state + ML + tracks +
// spatial + XAI. Every value is backend-provided; absent pipeline renders
// as explicitly unavailable (never synthesized).
function visionRows(vision, visionError) {
  if (visionError && !vision) return [["pipeline", `unavailable (${visionError})`]];
  if (!vision) return [["pipeline", "not attached (start the dual session)"]];
  const nodes = (vision.nodes || []).map((n) =>
    `${n.node_id}: ${n.stale ? "STALE" : `${n.presence_label}/${n.movement_label}`}`);
  const tracks = (vision.tracks || []).map((t) => `${t.id} (${t.state})`);
  const ml = vision.ml || {};
  const spatial = vision.spatial || {};
  const xai = vision.xai || {};
  return [
    ["evidence", vision.evidence || "UNKNOWN"],
    ["nodes", nodes.length ? nodes.join(" · ") : "none"],
    ["ML", `${ml.model_name || "none"} · ${ml.model_status || "UNAVAILABLE"}`],
    ["tracks", tracks.length ? tracks.join(", ") : "[] (no evidence-held track)"],
    ["spatial", `${spatial.level || "?"}${spatial.zone ? ` · ${spatial.zone}` : ""}`],
    ["XAI", xai.status || "XAI UNAVAILABLE"],
    ["provenance", `${vision.provenance || "?"} · ${vision.calibration || "UNCALIBRATED"}`],
  ];
}

export function VisualizeView() {
  const source = useStore(sourceStore);
  const sensing = useStore(sensingStore);
  const viz = useStore(vizStore);
  const visionState = useStore(visionStore);
  const vision = visionState.vision || null;
  const [widthM, setWidthM] = R.useState(null);
  const [sceneFailed, setSceneFailed] = R.useState(null);

  const sceneHost = R.useRef(null);
  const roomCanvas = R.useRef(null);
  const scene = R.useRef(null);
  const amps = R.useRef(null);
  const pos = R.useRef(null);
  const paintAt = R.useRef(0);
  const paintRef = R.useRef(null);

  const ev = source.lastEvent;
  const p = (ev && ev.payload) || null;
  const L = sensing.live;
  const ageMs = source.lastEventTs ? Date.now() - source.lastEventTs : null;
  const fresh = frameFreshness(source.source, ageMs);

  // Shared logical visualization state — one interpretation for both
  // renderers (WS-1C). Reads live above via closure; effects invoke it.
  paintRef.current = () => {
    const w = widthM;
    const amplitudes = amps.current;
    const positionT = pos.current;
    const showState = presenceLabel(p, vision);
    const hud = [hudExtra(L), showState].filter(Boolean).join(" · ") || null;
    const room = roomCanvas.current;
    if (room) {
      drawRoom2d(room, {
        widthM: w, lengthM: null, positionT, uncertainty: null,
      });
      describe(room, w
        ? `2D room view, width ${w} m.` +
          (positionT != null ? ` Position t=${positionT.toFixed(2)}.` : " No position estimate.")
        : "2D room view. Room unknown, uncalibrated." +
          (positionT != null ? ` Position t=${positionT.toFixed(2)} (NOT VALIDATED).` : ""));
    }
    const host = sceneHost.current;
    if (host) {
      describe(host, "3D RF link scene. " +
        (w ? `Room width ${w} m.` : "Room uncalibrated.") +
        (showState ? ` ${showState}.` : " No observation."));
    }
    if (scene.current && !sceneFailed) {
      scene.current.setModel({
        widthM: w, amplitudes, positionT,
        uncertainty: null, // no validated uncertainty yet
        hudExtra: hud,
      });
    }
  };

  const paintSoon = (force) => {
    if (viz.paused && !force) return;
    const now = (typeof performance !== "undefined" && performance.now)
      ? performance.now() : Date.now();
    if (!force && now - paintAt.current < PAINT_MIN_MS) return;
    paintAt.current = now;
    try {
      if (paintRef.current) paintRef.current();
    } catch (e) { console.error("visualize paint", e); }
  };

  // Mount: build the 3D scene once, fetch calibration, destroy on unmount.
  // One renderer, one scene, one camera, one loop; listeners owned by the
  // scene are released by destroy() — nothing leaks across route changes.
  R.useEffect(() => {
    let cancelled = false;
    const s = new RfLinkScene(sceneHost.current);
    scene.current = s;
    try {
      s.init();
      s.resize();
    } catch (e) {
      console.error("visualize scene init", e);
      if (!cancelled) setSceneFailed(e.message || String(e));
    }
    api.calibration().then(
      (cal) => { if (!cancelled) setWidthM(cal.room_width_m ?? null); },
      () => { if (!cancelled) setWidthM(null); });
    return () => {
      cancelled = true;
      try { s.destroy(); } catch { /* already torn down */ }
      scene.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Ingest every WS frame into latest-model refs (no data loss while
  // paused); repaint throttled. Pause freezes presentation only.
  R.useEffect(() => {
    if (!ev || ev.type !== "sensing.snapshot" || !ev.payload) return;
    const q = ev.payload;
    amps.current = Array.isArray(q.amplitudes) && q.amplitudes.length ? q.amplitudes : null;
    pos.current = (typeof q.position === "number") ? q.position : null;
    paintSoon(false);
  }, [source.lastEventTs]); // eslint-disable-line react-hooks/exhaustive-deps

  // Repaint on polled-telemetry / calibration / pause / resume changes.
  R.useEffect(() => {
    if (!viz.paused) paintSoon(false);
  }); // eslint-disable-line react-hooks/exhaustive-deps

  // Presentation pause only — acquisition, WS, sequence, backend untouched.
  R.useEffect(() => {
    if (scene.current && !sceneFailed) {
      try { scene.current.pause(viz.paused); } catch (e) { console.error("visualize pause", e); }
    }
    if (!viz.paused) paintSoon(true);
  }, [viz.paused]); // eslint-disable-line react-hooks/exhaustive-deps

  // RESET VIEW token: restore home camera, repaint, re-read calibration.
  // Never restarts acquisition or resets backend state.
  R.useEffect(() => {
    if (viz.viewToken === 0) return;
    const s = scene.current;
    if (s && s.ready) {
      try {
        s.camera.position.set(HOME_POS[0], HOME_POS[1], HOME_POS[2]);
        s.controls.target.set(HOME_TARGET[0], HOME_TARGET[1], HOME_TARGET[2]);
        s.controls.update();
        s.resize();
      } catch (e) { console.error("visualize reset", e); }
    }
    api.calibration().then(
      (cal) => setWidthM(cal.room_width_m ?? null),
      () => setWidthM(null));
    paintSoon(true);
  }, [viz.viewToken]); // eslint-disable-line react-hooks/exhaustive-deps

  const posShow = pos.current;
  const showState = presenceLabel(p, vision);

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "Visualize", back: true,
      actions: [h(ModePill, { source: source.source, stale: fresh.stale })],
    }),
    source.source === "SIMULATION"
      ? h("div", { className: "rfreact-sim-banner" }, "SIMULATED — backend simulated provider. Never evidence, never LIVE.")
      : null,
    source.source === "FIXTURE"
      ? h("div", { className: "rfreact-sim-banner" }, "OFFLINE FIXTURE — recorded replay. Never live.")
      : null,
    fresh.stale
      ? h("div", { className: "rfreact-sim-banner" }, `STALE — last frame ${fresh.label}. Old measurements are not current; no replacement data is synthesized.`)
      : null,
    source.source === "OFF"
      ? h("p", { className: "rfreact-note", style: { marginBottom: "16px" } }, "Source OFF — no live RF claim. Views below show last captured state for reference only.")
      : null,
    h("div", { className: "rfreact-cols rfreact-cols-narrow" },
      h("div", { className: "rfreact-col" },
        h(Card, { label: "HUD", title: "Visualization HUD (real state)" },
          kv([
            ["source", `${source.source} (${source.sourceState})`],
            ["rate", L && L.stream.rate_hz != null ? `${L.stream.rate_hz.toFixed(1)} Hz` : "UNKNOWN"],
            ["rssi", p && p.rssi != null ? `${p.rssi} dBm` : (L && L.signal.rssi_last != null ? `${L.signal.rssi_last} dBm` : "UNKNOWN")],
            ["seq", ev ? String(ev.seq) : (L && L.stream.last_seq != null ? String(L.stream.last_seq) : "UNKNOWN")],
            ["geometry", widthM != null ? `${widthM.toFixed(1)} m link (reference only)` : "UNKNOWN (uncalibrated)"],
            ["position", posShow != null ? `${posShow.toFixed(3)} RF-INFERRED (NOT VALIDATED)` : "none"],
            ["observation", showState || "none"],
            ["rendering", viz.paused ? "paused" : "live"],
          ]),
          h("div", { className: "rfreact-row" },
            h(SafeButton, {
              action: "visualization only: pause/resume rendering; hardware and acquisition untouched",
              label: viz.paused ? "RESUME VISUALIZATION" : "PAUSE VISUALIZATION",
              onClick: async () => { vizStore.set({ paused: !viz.paused }); return viz.paused ? "rendering resumed" : "rendering paused"; },
            }),
            h(SafeButton, {
              action: "visualization only: reset camera and local view token; hardware, acquisition and data untouched",
              label: "RESET VIEW",
              onClick: async () => { vizStore.set({ viewToken: viz.viewToken + 1, paused: false }); return "view reset (visualization only)"; },
            }),
          ),
          h("p", { className: "rfreact-note" },
            "Visualization controls are fenced off from hardware controls by route: nothing on this screen can provision, start, or stop anything physical.")),
        h(Card, { label: "RF Vision", title: "RF Vision pipeline (dual only, engineering)" },
          kv(visionRows(vision, visionState.visionError)),
          vision && vision.xai && vision.xai.statement
            ? h("p", { className: "rfreact-note" }, `Why: ${vision.xai.statement}`)
            : null,
          h("p", { className: "rfreact-note" },
            "Engineering/demonstration state. UNCALIBRATED, NOT VALIDATED. No identity, no bodies, no calibrated probability.")),
        h(Card, { label: "Scene", title: "3D RF environment — one link (three.js r160, local)" },
          sceneFailed
            ? h("p", { className: "rfreact-note" }, `3D unavailable (${sceneFailed}). 2D view remains.`)
            : h("div", {
              className: "rfreact-scene-wrap", ref: sceneHost,
              role: "img", "aria-label": "3D RF link scene. Room uncalibrated.",
            }),
          h("p", { className: "rfreact-note" },
            "Drag to orbit · scroll to zoom. Field strip is a measured-amplitude abstraction, not a propagation model. No bodies, no mesh.")),
      ),
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Room", title: "2D room view" },
          h("canvas", {
            className: "rfreact-viz", ref: roomCanvas,
            role: "img", "aria-label": "2D room view. Room unknown, uncalibrated.",
          }),
          h("p", { className: "rfreact-note" },
            "Dashed outline = uncalibrated. Positions default to link ends until measured. 1-D link view — 2-D/3-D not claimed.")),
      ),
    ));
}
