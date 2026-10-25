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
import { frameFreshness, STALE_AFTER_MS } from "../services/sources.js";
import { nodeKey, emptySlots, routeSnapshot, updateSlotDisturbance } from "../services/pernode.js";
import { emptyStreak, updateField, fieldSummary } from "../services/spatial.js";
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

// Phase 1 (room twin foundation): approximate ESP32-A/B visual placement
// presets. Layout only — NOT SURVEYED, NOT MEASURED; never an input to
// calibration, inference, contracts, or research analysis.
const PLACE_PRESETS = {
  ends: { A: { x: -2, z: 1.6 }, B: { x: 2, z: 1.6 } },
  corners: { A: { x: -2, z: 1.6 }, B: { x: 2, z: -1.6 } },
  side: { A: { x: -1, z: 1.6 }, B: { x: 1, z: 1.6 } },
};

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
  // Per-node live signal state (G2): slots keyed by envelope node_id via
  // routeSnapshot — an A frame returns the untouched B slot object and vice
  // versa, so streams can never overwrite each other. Timestamps track
  // per-node freshness against the existing STALE rule. Presentation only.
  const nodes = R.useRef(emptySlots());
  const nodeAt = R.useRef({ A: 0, B: 0 });
  const paintAt = R.useRef(0);
  const paintRef = R.useRef(null);
  // Phase 3 (approximate RF evidence): streak/persistence state for the
  // deterministic 3-zone field + the baseline-hold decision for the next
  // ingested frame. Reset whenever the arrangement or RF session changes so
  // old spatial interpretation never leaks into a new geometry/session.
  const spatial = R.useRef({ streak: emptyStreak(), hold: false, field: null });
  const srcKey = R.useRef(null);
  // Phase 1 (room twin foundation): session-local room image + approximate
  // ESP32-A/B visual placement. The image is a browser object URL (never
  // uploaded, never persisted); markers are layout-only. Presentation only.
  const [roomImageUrl, setRoomImageUrl] = R.useState(null);
  const roomUrlRef = R.useRef(null);
  const fileRef = R.useRef(null);
  const [places, setPlaces] = R.useState(PLACE_PRESETS.ends);
  const [placePreset, setPlacePreset] = R.useState("ends");

  const ev = source.lastEvent;
  const p = (ev && ev.payload) || null;
  const L = sensing.live;
  const ageMs = source.lastEventTs ? Date.now() - source.lastEventTs : null;
  const fresh = frameFreshness(source.source, ageMs);

  // Per-node freshness against the existing 3 s STALE rule. The
  // single-source selector stays OFF by backend contract while the dual
  // session runs (server refuses mode=live during dual), so a fresh
  // per-node frame under source OFF is live dual-session data: it must not
  // be labeled "no source", and an aged slot must surface STALE (driving the
  // existing dimming) instead of riding silently. Validated single-source
  // semantics in sources.js are untouched — this helper only diverges for
  // the OFF + per-node-age case.
  const perNodeFreshness = (age) => {
    if (age === null || age === undefined) return frameFreshness(source.source, age);
    if (age > STALE_AFTER_MS) return { current: false, stale: true, label: `STALE — ${(age / 1000).toFixed(0)} s ago` };
    if (source.source === "OFF") return { current: true, stale: false, label: "dual live" };
    return frameFreshness(source.source, age);
  };

  // Per-node scene model + HUD summary. A slot contributes only from its
  // own routed frames (never the sibling's); stale slots ride along dimmed
  // with an explicit STALE flag — stale data is never presented as current.
  const nodeModel = (slot, at) => {
    if (!slot || !slot.amps) return null;
    const age = at ? Date.now() - at : null;
    const fr = perNodeFreshness(age);
    return {
      amplitudes: slot.amps, disturb: slot.disturb,
      disturbMean: slot.disturbMean, rssi: slot.rssi, seq: slot.seq,
      stale: fr.stale, ageLabel: fr.label,
    };
  };
  const nodeSummary = (tag, slot, at) => {
    if (!slot || !slot.amps) return `${tag}: no frames`;
    const age = at ? Date.now() - at : null;
    const fr = perNodeFreshness(age);
    const d = slot.disturbMean != null ? ` disturb ${slot.disturbMean.toFixed(2)}` : "";
    const stale = fr.stale ? " STALE" : "";
    return `${tag} rssi ${slot.rssi != null ? slot.rssi : "?"} seq ${slot.seq != null ? slot.seq : "?"}${d} (${fr.label})${stale}`;
  };

  // Phase 1 room-image lifecycle: upload/replace/remove a session-local
  // browser object URL. The previous URL is always revoked (no leaks); the
  // image never leaves the tab — no upload, no persistence, no repo bytes.
  const onRoomFile = (e) => {
    const f = e && e.target && e.target.files && e.target.files[0];
    if (!f) return;
    if (f.type && !String(f.type).startsWith("image/")) return;
    const url = URL.createObjectURL(f);
    if (roomUrlRef.current) { try { URL.revokeObjectURL(roomUrlRef.current); } catch { /* already revoked */ } }
    roomUrlRef.current = url;
    setRoomImageUrl(url);
    if (e.target) e.target.value = ""; // allow re-selecting the same file
  };
  const clearRoomImage = () => {
    if (roomUrlRef.current) { try { URL.revokeObjectURL(roomUrlRef.current); } catch { /* already revoked */ } }
    roomUrlRef.current = null;
    setRoomImageUrl(null);
    if (fileRef.current) fileRef.current.value = "";
  };
  // Phase 1 placement steppers (±0.5 m, clamped to the room volume in the
  // scene). Any manual nudge drops the preset selector to "custom".
  const nudge = (key, axis, delta) => {
    setPlaces((prev) => {
      const cur = (prev && prev[key]) || { x: 0, z: 0 };
      const nx = axis === "x" ? Math.max(-2.5, Math.min(2.5, cur.x + delta)) : cur.x;
      const nz = axis === "z" ? Math.max(-2, Math.min(2, cur.z + delta)) : cur.z;
      return { ...prev, [key]: { x: nx, z: nz } };
    });
    setPlacePreset("custom");
  };

  // Shared logical visualization state — one interpretation for both
  // renderers (WS-1C). Reads live above via closure; effects invoke it.
  paintRef.current = () => {
    const w = widthM;
    const amplitudes = amps.current;
    const positionT = pos.current;
    const showState = presenceLabel(p, vision);
    const nm = { A: nodeModel(nodes.current.A, nodeAt.current.A), B: nodeModel(nodes.current.B, nodeAt.current.B) };
    // Phase 3: fold the two per-node disturbMean values into the approximate
    // 3-zone RF evidence field (candidate evidence — NOT VALIDATED). Freshness
    // reuses the existing per-node STALE rule; no new timer, no new source.
    const nowMs = Date.now();
    const freshSlot = (slot, at) => Boolean(
      slot && slot.amps && slot.amps.length && at && (nowMs - at) <= STALE_AFTER_MS);
    const u = updateField(spatial.current.streak, {
      dA: nodes.current.A ? nodes.current.A.disturbMean : null,
      dB: nodes.current.B ? nodes.current.B.disturbMean : null,
      freshA: freshSlot(nodes.current.A, nodeAt.current.A),
      freshB: freshSlot(nodes.current.B, nodeAt.current.B),
      now: nowMs,
    });
    spatial.current = { streak: u.streak, hold: u.hold, field: u.field };
    const evidenceLine = fieldSummary(u.field);
    const perNode = (nm.A || nm.B)
      ? `${nodeSummary("A esp32-a", nodes.current.A, nodeAt.current.A)} · ${nodeSummary("B esp32-b", nodes.current.B, nodeAt.current.B)}`
      : "";
    const hud = [hudExtra(L), showState, perNode, evidenceLine].filter(Boolean).join(" · ") || null;
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
      describe(host, "3D RF signal field, per node. " +
        (w ? `Room width ${w} m.` : "Room uncalibrated.") +
        (roomImageUrl ? " Room image shown (visual context only, not RF evidence)." : "") +
        (perNode ? ` ${perNode}.` : " No per-node frames.") +
        (perNode ? " Live RF false-colour overlay, signal-derived (left A, right B)." : "") +
        ` Approximate RF evidence: ${evidenceLine}.` +
        (showState ? ` ${showState}.` : ""));
    }
    if (scene.current && !sceneFailed) {
      scene.current.setModel({
        widthM: w, amplitudes, positionT,
        uncertainty: null, // no validated uncertainty yet
        hudExtra: hud, nodes: nm,
        // Phase 3: coarse 3-zone evidence for the additive scene overlay.
        // Rendered only at RF_ESTIMATE tier; otherwise informational text.
        field: (u.field && u.field.evidenceTier === "RF_ESTIMATE")
          ? { tier: u.field.evidenceTier, zones: u.field.zones, leader: u.field.leader }
          : null,
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
      if (roomUrlRef.current) { try { URL.revokeObjectURL(roomUrlRef.current); } catch { /* already revoked */ } roomUrlRef.current = null; }
      try { s.destroy(); } catch { /* already torn down */ }
      scene.current = null;
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Phase 1: push the session-local room image into the 3D scene backdrop.
  // Visual context only — never RF evidence; freshness semantics untouched.
  R.useEffect(() => {
    const s = scene.current;
    if (s && !sceneFailed) {
      try { s.setRoomImage(roomImageUrl); } catch (e) { console.error("room image", e); }
    }
  }, [roomImageUrl, sceneFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  // Phase 1: push approximate A/B visual placement (layout only — NOT
  // SURVEYED, NOT MEASURED; never enters calibration or inference).
  // Phase 3: a changed arrangement invalidates the streak/hold/field built
  // under the old geometry — reset it so old evidence is never reinterpreted
  // under the new layout. Markers and acquisition are untouched.
  R.useEffect(() => {
    spatial.current = { streak: emptyStreak(), hold: false, field: null };
    const s = scene.current;
    if (s && !sceneFailed) {
      try { s.setPlacements(places); } catch (e) { console.error("placements", e); }
    }
    paintSoon(true);
  }, [places, sceneFailed]); // eslint-disable-line react-hooks/exhaustive-deps

  // Ingest every WS frame into latest-model refs (no data loss while
  // paused); repaint throttled. Pause freezes presentation only.
  // Frames carrying the dual-session node_id are routed into per-node
  // slots (A/B isolation — no cross-over); frames without node_id
  // (single-source path) keep the exact legacy single-strip behavior.
  R.useEffect(() => {
    if (!ev || ev.type !== "sensing.snapshot" || !ev.payload) return;
    // Phase 3: a new RF source/session invalidates spatial interpretation
    // (streak + hold + last field). Raw acquisition slots are untouched.
    const key = `${source.source}|${source.sourceState}`;
    if (srcKey.current !== null && srcKey.current !== key) {
      spatial.current = { streak: emptyStreak(), hold: false, field: null };
    }
    srcKey.current = key;
    if (nodeKey(ev.node_id)) {
      const r = routeSnapshot(nodes.current, ev);
      if (r.routed) {
        const k = r.routed;
        // Phase 3 hold: freeze this slot's EMA baseline while a directional
        // event is held, so persistent occupancy is not absorbed as drift.
        // Default false preserves the validated adaptation behavior.
        nodes.current = { ...r.slots, [k]: updateSlotDisturbance(r.slots[k], undefined, spatial.current.hold) };
        nodeAt.current[k] = Date.now();
      } else {
        return;
      }
    } else {
      const q = ev.payload;
      amps.current = Array.isArray(q.amplitudes) && q.amplitudes.length ? q.amplitudes : null;
      pos.current = (typeof q.position === "number") ? q.position : null;
    }
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
  // Phase 3: last computed approximate-evidence summary (refreshed on every
  // throttled paint; informational text, never a localization claim).
  const evidenceShow = fieldSummary(spatial.current.field);
  const slotA = nodes.current.A;
  const slotB = nodes.current.B;
  // True while any per-node slot holds frames within the existing STALE
  // rule. The OFF banner below claims "last captured state" — that is only
  // true when no per-node data is live either.
  const dualLive = [nodeAt.current.A, nodeAt.current.B].some(
    (at) => at && (Date.now() - at) <= STALE_AFTER_MS);
  const slotRow = (tag, slot, at) => {
    if (!slot || !slot.amps) return "no frames yet";
    const age = at ? Date.now() - at : null;
    const fr = perNodeFreshness(age);
    const d = slot.disturbMean != null ? ` · disturb ${slot.disturbMean.toFixed(3)}` : "";
    const stale = fr.stale ? " · STALE" : "";
    return `${tag} · rssi ${slot.rssi != null ? `${slot.rssi} dBm` : "?"} · seq ${slot.seq != null ? slot.seq : "?"} · ${fr.label}${d}${stale}`;
  };

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
    source.source === "OFF" && !dualLive
      ? h("p", { className: "rfreact-note", style: { marginBottom: "16px" } }, "Source OFF — no live RF claim. Views below show last captured state for reference only.")
      : null,
    source.source === "OFF" && dualLive
      ? h("p", { className: "rfreact-note", style: { marginBottom: "16px" } }, "Dual session live — per-node views below show live measured signal. The single-source selector stays OFF while dual runs.")
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
            ["node A", slotRow("esp32-a", slotA, nodeAt.current.A)],
            ["node B", slotRow("esp32-b", slotB, nodeAt.current.B)],
            ["field", "LIVE RF FIELD · SIGNAL-DERIVED · PER-NODE · NOT CALIBRATED · NO LOCATION CLAIM"],
            ["disturbance", "RF DISTURBANCE = MEASURED SIGNAL CHANGE (presentation emphasis, no threshold, no detection)"],
            ["approx evidence", evidenceShow],
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
        h(Card, { label: "Scene", title: "3D RF signal field — per-node (three.js r160, local)" },
          sceneFailed
            ? h("p", { className: "rfreact-note" }, `3D unavailable (${sceneFailed}). 2D view remains.`)
            : h("div", {
              className: "rfreact-scene-wrap", ref: sceneHost,
              role: "img", "aria-label": "3D RF signal field, per node. Room uncalibrated.",
            }),
          h("div", { className: "rfreact-row", style: { marginTop: "4px" } },
            h("input", {
              ref: fileRef, type: "file", accept: "image/*", onChange: onRoomFile,
              "aria-label": "Upload room image (visual context only)",
              title: "Upload room image — session-local visual context only",
              style: { maxWidth: "100%" },
            }),
            roomImageUrl
              ? h(SafeButton, {
                action: "visualization only: remove session-local room image; hardware, acquisition and data untouched",
                label: "REMOVE IMAGE", kind: "danger",
                onClick: async () => { clearRoomImage(); return "room image removed (was session-local only)"; },
              })
              : null),
          h("p", { className: "rfreact-note" },
            "ROOM IMAGE = VISUAL CONTEXT · NOT RF EVIDENCE · NOT CALIBRATED. " +
            "Stays in this browser tab only — never uploaded, never stored, cleared on reload."),
          h("div", { className: "rfreact-row" },
            h("label", { className: "rfreact-note", htmlFor: "rf-place-preset" }, "ESP32 placement:"),
            h("select", {
              id: "rf-place-preset", className: "rfreact-select", value: placePreset,
              onChange: (e) => {
                const v = e.target.value;
                setPlacePreset(v);
                if (PLACE_PRESETS[v]) setPlaces(PLACE_PRESETS[v]);
              },
            },
              h("option", { value: "ends" }, "ends"),
              h("option", { value: "corners" }, "corners"),
              h("option", { value: "side" }, "side-by-side"),
              placePreset === "custom" ? h("option", { value: "custom" }, "custom") : null),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("A", "x", -0.5), title: "move marker A left (visual layout only)" }, "A x−"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("A", "x", 0.5), title: "move marker A right (visual layout only)" }, "A x+"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("A", "z", -0.5), title: "move marker A back (visual layout only)" }, "A z−"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("A", "z", 0.5), title: "move marker A forward (visual layout only)" }, "A z+"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("B", "x", -0.5), title: "move marker B left (visual layout only)" }, "B x−"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("B", "x", 0.5), title: "move marker B right (visual layout only)" }, "B x+"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("B", "z", -0.5), title: "move marker B back (visual layout only)" }, "B z−"),
            h("button", { className: "rfreact-btn", type: "button", onClick: () => nudge("B", "z", 0.5), title: "move marker B forward (visual layout only)" }, "B z+")),
          h("p", { className: "rfreact-note" },
            `VISUAL PLACEMENT — NOT SURVEYED · NOT MEASURED. Layout only ` +
            `(A ${places.A.x.toFixed(1)}, ${places.A.z.toFixed(1)} · B ${places.B.x.toFixed(1)}, ${places.B.z.toFixed(1)}); ` +
            "never enters calibration, inference, or any scientific calculation."),
          h("div", { className: "rfreact-row", style: { alignItems: "center" } },
            h("span", { className: "rfreact-note" }, "RF CHANGE:"),
            h("div", {
              role: "img",
              "aria-label": "False-colour legend: cool blue low measured change to red high measured change",
              title: "False-colour legend — visual encoding only, no threshold",
              style: {
                width: "160px", height: "12px", borderRadius: "3px",
                background: "linear-gradient(90deg,#00268c,#008cd9,#1ab373,#f2d933,#f2731a,#f21414)",
              },
            }),
            h("span", { className: "rfreact-note" }, "low → high")),
          h("p", { className: "rfreact-note" },
            "LIVE RF FIELD — SIGNAL-DERIVED. Left band = NODE A RF CHANGE · right band = NODE B RF CHANGE. " +
            "RELATIVE MEASURED CHANGE · NO THRESHOLD · NO LOCATION CLAIM. Colours encode per-tone signal change " +
            "(tone order along the band — NOT room position); stale nodes dim with STALE, never shown as live."),
          h("p", { className: "rfreact-note" },
            "Drag to orbit · scroll to zoom. One signal strip per node, driven only by that node's live amplitude " +
            "vector (tone index along the strip — NOT room coordinates). Strip height = measured signal change " +
            "(RF DISTURBANCE). Strip layout is presentation arrangement, not physical geometry. " +
            "LIVE RF FIELD · SIGNAL-DERIVED · PER-NODE · NOT CALIBRATED · NO LOCATION CLAIM. No bodies, no mesh.")),
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
