/* Live RF — "What is RF Vision sensing right now?"
   Phase 2: full Live RF/CSI experience migrated from the legacy sensing +
   acquisition tabs (functional/semantic parity, not pixel parity).
   - Acquisition controls use the existing source/stream contract only.
   - All charts render real backend frames (WS sensing.snapshot envelopes);
     empty input renders explicit NO DATA placeholders — never synthetic data.
   - PAUSE VISUALIZATION freezes canvas rendering only; acquisition, WS,
     recording and source state are untouched.
   - Presence/activity/position are backend values labelled NOT VALIDATED;
     nothing here claims localization. */
import { h, kv, unknown } from "../h.js";
import { Card, ErrorRow, ModePill, PageHeader } from "../components/global.js";
import { Ring } from "../charts.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { frameFreshness } from "../services/sources.js";
import { sourceFromMode } from "../services/sources.js";
import { sourceStore, sensingStore, vizStore, useStore } from "../state/store.js";
import { drawHeatmap, drawSparkline, drawBars, drawLine, placeholder, describe } from "../viz.js";

const R = window.React;

const AMP_ROWS = 40;
const RSSI_N = 120;
const PAINT_MIN_MS = 250;

function startSensing(ws) {
  return async () => {
    const res = await api.setSource("live");
    if (res && res.source_state) {
      sourceStore.set({ mode: res.mode || "live", running: !!res.running, source: sourceFromMode(res.mode || "live"), sourceState: res.source_state });
    }
    await api.streamStart();
    if (ws) ws.send({ command: "stream:start" });
    return `source=live, stream started (${res.source_state || "?"})`;
  };
}

function stopSensing() {
  return async () => {
    await api.streamStop();
    const res = await api.setSource("off");
    sourceStore.set({ mode: "off", running: false, source: "OFF", sourceState: (res && res.source_state) || "DISCONNECTED" });
    return "stream stopped, source parked OFF";
  };
}

function fmt(n, digits = 1) {
  return n === null || n === undefined ? "UNKNOWN" : Number(n).toFixed(digits);
}

function paintAll(refs, bufs, meta) {
  const { heatRef, ampRef, rssiRef, barsRef, trailRef, phaseRef } = refs;
  drawHeatmap(heatRef.current, bufs.amps);
  describe(heatRef.current,
    bufs.amps.length ? `Amplitude heatmap, last ${bufs.amps.length} frames.` : "Amplitude heatmap. No frames yet.");
  drawLine(ampRef.current, meta.latestAmps, { label: "amplitude" });
  describe(ampRef.current,
    meta.latestAmps ? `Latest amplitude frame, ${meta.latestAmps.length} subcarriers.` : "Latest amplitude frame chart. No data yet.");
  drawSparkline(rssiRef.current, bufs.rssi, { label: "rssi" });
  describe(rssiRef.current,
    bufs.rssi.length ? `RSSI history, ${bufs.rssi.length} samples, latest ${bufs.rssi[bufs.rssi.length - 1]} dBm.` : "RSSI history chart. No data yet.");
  drawBars(barsRef.current, [
    { label: "presence_prob", value: meta.p ? meta.p.presence_prob ?? null : null },
    { label: "movement_prob", value: meta.p ? meta.p.movement_prob ?? null : null },
    { label: "confidence", value: meta.p ? meta.p.confidence ?? null : null },
    { label: "rf_evidence", value: meta.p ? meta.p.rf_evidence_confidence ?? null : null },
  ]);
  describe(barsRef.current, meta.p
    ? `Presence bars. RF evidence ${meta.p.rf_evidence_confidence != null ? `${meta.p.rf_evidence_confidence.toFixed(2)}, UNCALIBRATED` : "none"}.`
    : "Presence and confidence bars. No data yet.");
  drawSparkline(trailRef.current, bufs.trail.length ? bufs.trail : null, { label: "link position t" });
  describe(trailRef.current,
    bufs.trail.length ? `Position trail, ${bufs.trail.length} points.` : "Position trail chart. No trail available.");
  placeholder(phaseRef.current, "PHASE GATED — AMPLITUDE ONLY");
  describe(phaseRef.current, "Phase stream placeholder. Phase is gated; amplitude only.");
}

export function LiveView({ ws, refresh }) {
  const source = useStore(sourceStore);
  const sensing = useStore(sensingStore);
  const viz = useStore(vizStore);

  const bufs = R.useRef({ amps: [], rssi: [], trail: [] });
  const heatRef = R.useRef(null);
  const ampRef = R.useRef(null);
  const rssiRef = R.useRef(null);
  const barsRef = R.useRef(null);
  const trailRef = R.useRef(null);
  const phaseRef = R.useRef(null);
  const paintAt = R.useRef(0);

  const ev = source.lastEvent;
  const p = (ev && ev.payload) || null;
  const ageMs = source.lastEventTs ? Date.now() - source.lastEventTs : null;
  const fresh = frameFreshness(source.source, ageMs);
  const L = sensing.live;
  const latestAmps = p && Array.isArray(p.amplitudes) && p.amplitudes.length ? p.amplitudes : null;
  const renderingPaused = viz.paused;

  // Ingest every WS frame into rolling buffers (no data loss); repaint the
  // canvases at most every 250 ms; a paused view keeps buffering but skips
  // painting so RESUME shows the current stream, not a restarted one.
  R.useEffect(() => {
    if (!ev || ev.type !== "sensing.snapshot" || !ev.payload) return;
    const b = bufs.current;
    const q = ev.payload;
    if (Array.isArray(q.amplitudes) && q.amplitudes.length) {
      b.amps.push(q.amplitudes);
      if (b.amps.length > AMP_ROWS) b.amps.shift();
    }
    if (typeof q.rssi === "number") {
      b.rssi.push(q.rssi);
      if (b.rssi.length > RSSI_N) b.rssi.shift();
    }
    if (Array.isArray(q.trail) && q.trail.length) {
      b.trail = q.trail.slice(-60);
    }
    if (renderingPaused) return;
    const now = (typeof performance !== "undefined" && performance.now) ? performance.now() : Date.now();
    if (now - paintAt.current < PAINT_MIN_MS) return;
    paintAt.current = now;
    paintAll({ heatRef, ampRef, rssiRef, barsRef, trailRef, phaseRef },
      b, { p: q, latestAmps: Array.isArray(q.amplitudes) && q.amplitudes.length ? q.amplitudes : null });
  }, [source.lastEventTs]); // eslint-disable-line react-hooks/exhaustive-deps

  // First paint / unpause / polled-telemetry refresh.
  R.useEffect(() => {
    if (renderingPaused) return;
    const b = bufs.current;
    paintAll({ heatRef, ampRef, rssiRef, barsRef, trailRef, phaseRef }, b, { p, latestAmps });
  }); // eslint-disable-line react-hooks/exhaustive-deps

  let ampSummary = "UNKNOWN";
  if (latestAmps) {
    const vs = latestAmps.filter((v) => typeof v === "number");
    if (vs.length) {
      const mean = vs.reduce((a, b) => a + b, 0) / vs.length;
      ampSummary = `n=${vs.length} min=${Math.min(...vs).toFixed(1)} max=${Math.max(...vs).toFixed(1)} mean=${mean.toFixed(1)}`;
    }
  } else if (L && L.signal && L.signal.amplitude && L.signal.amplitude.mean != null) {
    const a = L.signal.amplitude;
    ampSummary = `min=${fmt(a.min)} max=${fmt(a.max)} mean=${fmt(a.mean)} (session aggregate)`;
  }

  const seq = ev ? ev.seq : (L && L.stream.last_seq != null ? L.stream.last_seq : null);
  const rssiShow = p && p.rssi != null ? `${p.rssi} dBm`
    : (L && L.signal.rssi_last != null ? `${L.signal.rssi_last} dBm` : "UNKNOWN");
  const tones = latestAmps ? String(latestAmps.length)
    : (L && L.signal.tones != null ? String(L.signal.tones) : "UNKNOWN");

  // Validity health uses only backend-declared states: no invented thresholds.
  let health = "UNAVAILABLE";
  if (L) {
    if (L.stream.stale) health = "STALE";
    else if (L.gate.passed) health = "VALID (gate VERIFIED)";
    else health = "INVALID (gate UNVERIFIED)";
  } else if (ev) {
    health = fresh.stale ? "STALE" : "UNAVAILABLE (no live session)";
  }

  const dup = L && L.duplication;
  const dupShow = !L ? "UNKNOWN"
    : dup.storm ? "STORM SIGNATURE"
      : dup.impossible_throughput ? "IMPOSSIBLE THROUGHPUT" : "none";

  const activityShow = p && (p.presence_state ?? p.presence) != null
    ? String(p.presence_state ?? p.presence).toUpperCase() : "IDLE";
  const evConfShow = p && p.rf_evidence_confidence != null
    ? `${(p.rf_evidence_confidence * 100).toFixed(0)}% UNCALIBRATED` : "UNCALIBRATED";
  const nodeShow = p && p.node_mode ? p.node_mode
    : (L ? `CH ${L.signal.channel ?? "?"} · ${L.signal.bssid || "?"}` : "NO NODES");

  const validPct = L && L.stream.valid_pct != null ? L.stream.valid_pct : null;

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "Live Sensing",
      actions: [
        h(ModePill, { source: source.source, stale: fresh.stale }),
        h("span", { className: "rfreact-note" }, `frame: ${fresh.label}`),
      ],
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
      ? h("p", { className: "rfreact-note", style: { marginBottom: "16px" } }, "Source OFF — canvases below retain last captured frames for reference only; they are not live.")
      : null,
    h("div", { className: "rfreact-cols rfreact-cols-narrow" },
      h("div", { className: "rfreact-col" },
        h(Card, {
          label: "RF Vision", title: "Live Sensing",
          footer: [
            h("span", { style: { color: "var(--rv-text-2)" } },
              activityShow, " · RF evidence ",
              h("span", { className: "rfreact-mono", style: { color: "var(--rv-cyan)" } }, evConfShow)),
            h("span", { className: "rfreact-mono", style: { color: "var(--rv-muted)" } }, nodeShow),
          ],
        },
          h("p", { className: "rfreact-note", style: { fontSize: "12.5px", lineHeight: 1.6, color: "var(--rv-text-2)" } },
            "Real-time RF perception from the attached node. Every pixel below is a measured CSI frame — never synthesized."),
          renderingPaused ? h("p", { className: "rfreact-note" }, "Rendering paused — acquisition still running. Canvases frozen.") : null,
          h("canvas", { className: "rfreact-viz", ref: heatRef, role: "img", "aria-label": "Amplitude heatmap. No frames yet." }),
          h("p", { className: "rfreact-note" }, `Heatmap: latest ${AMP_ROWS} frames, oldest first.`),
          h("div", { className: "rfreact-viz-row" },
            h("canvas", { className: "rfreact-viz", ref: ampRef, role: "img", "aria-label": "Latest amplitude frame chart. No data yet." }),
            h("canvas", { className: "rfreact-viz", ref: rssiRef, role: "img", "aria-label": "RSSI history chart. No data yet." }),
          )),
        h(Card, { label: "Frame", title: "Latest frame" },
          p
            ? kv([
              ["seq", seq != null ? String(seq) : "UNKNOWN"],
              ["received", source.lastEventTs ? `${new Date(source.lastEventTs).toISOString().slice(11, 19)} UTC (${fresh.label})` : "UNKNOWN"],
              ["rssi", rssiShow],
              ["tones", tones],
              ["amplitude", ampSummary],
              ["validated", String(p.validated)],
              ["source", p.source_state || source.sourceState],
              ["nodes", p.node_mode || "UNKNOWN"],
            ])
            : unknown(source.source === "OFF" ? "no source — OFF" : "no frames yet")),
        h(Card, { label: "Diagnostics", title: "Packets / sequence" },
          (ev || L)
            ? kv([
              ["last seq", seq != null ? String(seq) : "UNKNOWN"],
              ["subcarriers", latestAmps ? String(latestAmps.length) : (L && L.signal.tones != null ? String(L.signal.tones) : "—")],
              ["gaps", L ? String(L.stream.gaps) : "UNKNOWN"],
              ["missing", L ? (L.stream.missing.length ? L.stream.missing.join(", ") : "none") : "UNKNOWN"],
              ["duplicates", L ? String(L.stream.duplicates) : "UNKNOWN"],
              ["out-of-order", L ? String(L.stream.out_of_order) : "UNKNOWN"],
              ["records (lossless)", L ? String(L.stream.valid) : "UNKNOWN"],
              ["rate", L && L.stream.rate_hz != null ? `${L.stream.rate_hz.toFixed(1)} Hz` : "UNKNOWN"],
            ])
            : unknown("none yet")),
        h(Card, { label: "Trail", title: "1-D trajectory — RF-inferred position trail" },
          h("canvas", { className: "rfreact-viz", ref: trailRef, role: "img", "aria-label": "Position trail chart. No trail available." }),
          h("p", { className: "rfreact-note" }, "Recent RF-inferred link positions, oldest first. Empty = none available (no models, or nobody detected). NOT VALIDATED — do not cite.")),
      ),
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Acquisition", title: "Acquisition state" },
          kv([
            ["source", `${source.source} (${source.sourceState})`],
            ["stream", source.running ? "running" : "stopped"],
            ["mode", source.mode],
            ["freshness", fresh.label],
            ["ws", sensing.status ? `${sensing.status.connection}` : "UNKNOWN"],
          ]),
          h(ErrorRow, { error: sensing.liveError, onRetry: refresh, what: "live" }),
          h("div", { className: "rfreact-row" },
            h(SafeButton, { action: "acquisition state change: source=live + stream start", label: "START SENSING", kind: "primary", onClick: startSensing(ws) }),
            h(SafeButton, { action: "acquisition state change: stream stop + source=off", label: "STOP SENSING", kind: "danger", onClick: stopSensing() }),
            h(SafeButton, {
              action: "visualization only: pause/resume frame rendering; acquisition untouched",
              label: renderingPaused ? "RESUME VISUALIZATION" : "PAUSE VISUALIZATION",
              onClick: async () => { vizStore.set({ paused: !viz.paused }); return viz.paused ? "rendering resumed" : "rendering paused — acquisition still running"; },
            }),
          ),
          h("p", { className: "rfreact-note" }, "START/STOP change real acquisition. PAUSE affects rendering only.")),
        h(Card, { label: "Validity", title: "Validity gate" },
          h("div", { style: { display: "flex", alignItems: "center", justifyContent: "space-between", gap: "16px" } },
            h(Ring, {
              value: validPct, size: 104,
              label: validPct != null ? `${validPct.toFixed(1)}%` : null,
              sublabel: L ? (L.stream.stale ? "STALE" : (L.gate.passed ? "GATE VERIFIED" : "GATE UNVERIFIED")) : "NO SESSION",
            }),
            h("p", { className: "rfreact-mono", style: { fontSize: "10px", lineHeight: 1.8, color: "var(--rv-muted)", textAlign: "right", margin: 0 } },
              L && L.stream.rate_hz != null ? `rate ${L.stream.rate_hz.toFixed(1)} Hz` : "rate UNKNOWN",
              h("br", null),
              L ? `malformed ${L.stream.malformed}` : "malformed UNKNOWN",
              h("br", null),
              dupShow === "none" ? "duplication none" : `duplication ${dupShow}`)),
          L
            ? kv([
              ["health", health],
              ["gate", L.gate.passed ? "VERIFIED" : `UNVERIFIED — ${(L.gate.reasons || []).join("; ")}`],
              ["valid", L.stream.valid_pct != null ? `${L.stream.valid_pct.toFixed(2)} %` : "UNKNOWN"],
              ["freshness", L.stream.last_update_age_s != null
                ? `${L.stream.last_update_age_s.toFixed(1)} s ago${L.stream.stale ? " — STALE" : ""}` : "no data"],
            ])
            : (ev
              ? kv([
                ["health", health],
                ["gate", "NOT AVAILABLE FROM CURRENT BACKEND (non-live provider)"],
                ["source", p.source_state || source.sourceState],
              ])
              : unknown("NO LIVE SESSION"))),
        h(Card, { label: "Sensing", title: "Presence / activity — NOT VALIDATED" },
          h("canvas", { className: "rfreact-viz", ref: barsRef, role: "img", "aria-label": "Presence and confidence bars. No data yet." }),
          p
            ? kv([
              ["state", p.presence_state ?? p.presence ?? "UNKNOWN"],
              ["rf evidence", p.rf_evidence_confidence != null
                ? `${(p.rf_evidence_confidence * 100).toFixed(0)} % (UNCALIBRATED)` : "none"],
              ["provenance", p.provenance ?? "UNKNOWN"],
              ["nodes", p.node_mode ?? "UNKNOWN"],
            ])
            : unknown("no frames yet"),
          h("p", { className: "rfreact-note" }, "NOT VALIDATED — no human-presence claim, no activity classification. RF Evidence Confidence is UNCALIBRATED product state, never a probability.")),
        h(Card, { label: "Phase", title: "Phase stream — gated" },
          h("canvas", { className: "rfreact-viz", ref: phaseRef, role: "img", "aria-label": "Phase stream placeholder. Phase is gated; amplitude only." }),
          h("p", { className: "rfreact-note" }, "Amplitude-only pipeline: phase is not consumed until validated. Displayed as GATED, never synthesized.")),
      ),
    ));
}
