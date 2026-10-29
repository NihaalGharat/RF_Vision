/* Research — "What is scientifically being measured, validated, analyzed?"
   Phase 1: real session provenance + stream state + bounded diagnostic
   recording. Audio-guided trial recording now uses the existing dual-session
   providers; analysis values and sensing results remain honestly absent. */
import { h, kv, unknown } from "../h.js";
import { Card, ErrorRow, ModePill, PageHeader, RfReadyBadge } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { hardwareStore, researchStore, sourceStore, useStore } from "../state/store.js";

const R = window.React;

function audioSupported() {
  return typeof window !== "undefined"
    && !!window.speechSynthesis
    && typeof window.SpeechSynthesisUtterance === "function";
}

function recordStart() {
  return async () => {
    const res = await api.recordStart(10);
    researchStore.set({ recordMsg: `recording → ${res.path} (≤${res.max_seconds} s)` });
    return `recording → ${res.path}`;
  };
}

function recordStop() {
  return async () => {
    const res = await api.recordStop();
    const m = res.manifest;
    const msg = m && m.path ? `saved ${m.bytes} B · sha256 ${m.sha256}` : "no recording was active";
    researchStore.set({ recordMsg: msg });
    return msg;
  };
}

function stateColor(state) {
  if (state === "RUNNING" || state === "COMPLETE") return "#34d399";
  if (state === "ABORTED") return "#fbbf24";
  return "#94a3b8";
}

function formatSeconds(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(1)} s` : "—";
}

export function ResearchView({ refresh }) {
  const research = useStore(researchStore);
  const source = useStore(sourceStore);
  const hardware = useStore(hardwareStore);
  const readiness = hardware.readiness;
  const rfReady = readiness && readiness.rf_ready === true;
  const exp = research.experiment;
  const trial = research.trial;
  const trialState = trial ? trial.state : "IDLE";
  const cue = trial && trial.current_phase ? trial.current_phase.id : null;
  const [muted, setMuted] = R.useState(false);
  const spokenRef = R.useRef(null);
  const utteranceRef = R.useRef(null);
  const supported = audioSupported();

  const cancelSpeech = () => {
    if (!supported) return;
    try { window.speechSynthesis.cancel(); } catch { /* speech is optional */ }
    utteranceRef.current = null;
  };

  const speak = (text) => {
    if (!supported || !text) return;
    const utter = new window.SpeechSynthesisUtterance(text);
    utter.rate = 0.95;
    utter.pitch = 1;
    utter.volume = 1;
    try {
      const voices = window.speechSynthesis.getVoices() || [];
      const voice = voices.find((v) => /^en/i.test(v.lang) && v.localService)
        || voices.find((v) => /^en/i.test(v.lang));
      if (voice) utter.voice = voice;
      utteranceRef.current = utter;
      window.speechSynthesis.speak(utter);
    } catch {
      utteranceRef.current = null;
    }
  };

  R.useEffect(() => {
    if (!supported) return undefined;
    return () => cancelSpeech();
  }, []);

  R.useEffect(() => {
    if (!supported) return;
    if (muted) {
      cancelSpeech();
    } else {
      spokenRef.current = null;
    }
  }, [muted]);

  R.useEffect(() => {
    if (!supported) return;
    if (trialState === "COMPLETE") {
      if (spokenRef.current !== "__complete__") {
        cancelSpeech();
        speak("Trial complete.");
        spokenRef.current = "__complete__";
      }
      return;
    }
    if (trialState !== "RUNNING") return;
    if (muted) {
      cancelSpeech();
      spokenRef.current = cue;
      return;
    }
    if (cue && cue !== spokenRef.current) {
      cancelSpeech();
      const phase = trial.current_phase || {};
      speak(phase.instruction || phase.label || cue);
      spokenRef.current = cue;
    }
  }, [trialState, cue, muted]);

  R.useEffect(() => {
    if (trialState !== "RUNNING") return undefined;
    let alive = true;
    const tick = () => {
      api.trialCurrent().then(
        (d) => { if (alive) researchStore.set({ trial: d, trialError: null }); },
        (e) => { if (alive) researchStore.set({ trialError: String(e.message || e) }); });
    };
    tick();
    const id = setInterval(tick, 250);
    return () => { alive = false; clearInterval(id); };
  }, [trialState]);

  const startTrial = async () => {
    cancelSpeech();
    spokenRef.current = null;
    const res = await api.trialStart(!muted);
    researchStore.set({ trial: res, trialMsg: `started ${res.trial_id}`, trialError: null });
    return `trial ${res.trial_id} started (${formatSeconds(res.duration_s)})`;
  };

  const stopTrial = async () => {
    cancelSpeech();
    const res = await api.trialStop("operator stopped the trial from Research");
    researchStore.set({ trial: res, trialMsg: `stopped ${res.trial_id || ""}`.trim(), trialError: null });
    return res.state === "ABORTED"
      ? `trial ${res.trial_id} stopped; partial captures preserved`
      : `trial state: ${res.state}`;
  };

  const testAudio = async () => {
    if (!supported) throw new Error("This browser has no speechSynthesis support.");
    cancelSpeech();
    speak("Audio guidance is working.");
    return "audio test phrase queued";
  };

  const progress = trial && trial.duration_s
    ? Math.max(0, Math.min(100, (Number(trial.elapsed_s) / Number(trial.duration_s)) * 100))
    : 0;
  const current = trial && trial.current_phase ? trial.current_phase : null;

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "Research", back: true,
      actions: [
        h(ModePill, { source: source.source, stale: false, dual: source.dual }),
        h(RfReadyBadge, { readiness, error: hardware.readinessError }),
      ],
    }),
    h("div", { className: "rfreact-cols rfreact-cols-near" },
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Provenance", title: "Active session provenance" },
          h(ErrorRow, { error: research.experimentError, onRetry: refresh, what: "experiment" }),
          !exp ? unknown("BACKEND UNREACHABLE")
            : h("div", null,
              kv([
                ["session", exp.session_id],
                ["source", source.dual ? source.dual.label : source.sourceState],
                ["stream", source.dual ? `${source.dual.sync} · ${source.dual.live}/${source.dual.expected} live` : `${source.mode} · running=${source.running ? "true" : "false"}`],
                ["validation", exp.validation],
              ]),
              h("details", { className: "rfreact-scene-options" },
                h("summary", null, "Advanced — hardware, firmware & raw data"),
                kv([
                  ["hardware", `${exp.hardware.esp32} · ${exp.hardware.router} · ${exp.hardware.band} · ${exp.hardware.transport}`],
                  ["firmware", `${exp.firmware.name} · identity ${exp.firmware.identity}`],
                  ["geometry", `room ${exp.geometry.room_width_m ?? "UNKNOWN"} × ${exp.geometry.room_length_m ?? "UNKNOWN"} (${exp.geometry.status})`],
                  ["raw data", exp.raw_ref ? JSON.stringify(exp.raw_ref) : "none — no diagnostic capture this session"],
                ])))),
        h(Card, { label: "Trial", title: "Audio-guided trial recording — RF READY required" },
          h(ErrorRow, { error: research.trialError, onRetry: refresh, what: "trial state" }),
          h("p", {
            className: "rfreact-status-banner " + (
              trialState === "RUNNING" || rfReady ? "match"
                : (readiness ? "mismatch" : "unknown")),
          },
            trialState === "RUNNING"
              ? "TRIAL IN PROGRESS — the startup gate is not re-evaluated; recording continues under its original start conditions."
              : rfReady
                ? "RF READY — backend readiness is satisfied; a new trial may start."
                : `TRIAL START BLOCKED — ${readiness
                  ? `${readiness.state || "NOT READY"}: ${readiness.reason || "dual RF readiness is not satisfied"}`
                  : (hardware.readinessError || "RF READY unavailable")}`),
          h("p", { className: "rfreact-note" },
            "This is a backend-enforced prerequisite: POST /api/v1/trials/start refuses a new trial unless GET /api/v1/rf_readiness reports rf_ready=true. Trials already running are not retroactively rejected."),
          !trial ? unknown("TRIAL STATE UNREACHABLE")
            : h("div", { className: "rfreact-trial" },
              h("div", { className: "rfreact-row" },
                h("span", {
                  className: "rfreact-badge",
                  style: {
                    color: stateColor(trial.state),
                    borderColor: `${stateColor(trial.state)}55`,
                    background: `${stateColor(trial.state)}14`,
                  },
                }, trial.state || "IDLE"),
                trial.trial_id ? h("span", { className: "rfreact-linemono" }, trial.trial_id) : null,
                trial.partial ? h("span", { className: "rfreact-badge warn" }, "PARTIAL") : null),
              trialState === "RUNNING"
                ? h("div", null,
                  h("p", { className: "rfreact-trialphase" },
                    current ? current.label : "Awaiting phase"),
                  h("p", { className: "rfreact-note" },
                    current ? current.instruction : ""),
                  h("div", { className: "rfreact-trialbar", role: "progressbar",
                    "aria-valuemin": "0", "aria-valuemax": "100",
                    "aria-valuenow": String(Math.round(progress)) },
                    h("span", { style: { width: `${progress}%` } })),
                  kv([
                    ["phase", current ? `${current.label} · ${formatSeconds(current.phase_remaining_s)} left` : "—"],
                    ["elapsed", formatSeconds(trial.elapsed_s)],
                    ["planned total", formatSeconds(trial.duration_s)],
                    ["remaining", formatSeconds(trial.remaining_s)],
                    ["audio", muted ? "muted (speech cancelled)" : "on (local speechSynthesis)"],
                  ]))
                : null,
              trialState === "COMPLETE" || trialState === "ABORTED"
                ? kv([
                  ["state", trial.state],
                  ["reason", trial.reason || "—"],
                  ["elapsed", formatSeconds(trial.elapsed_s)],
                  ["metadata", trial.metadata_path || "not written"],
                  ["result", "COMPLETE = recording finished only — not an RF_READY, analysis, or sensing claim"],
                  ["analysis", "NOT_RUN — no sensing result is claimed"],
                ])
                : null,
              (trial.recordings || []).length
                ? h("div", { className: "rfreact-trial-files" },
                  h("p", { className: "rfreact-linemono" }, "Raw captures"),
                  (trial.recordings || []).map((r) => h("p", {
                    key: r.node_id, className: "rfreact-linemono",
                  }, trialState === "RUNNING"
                    ? `${r.node_id}: ${r.path || "pending"} · open — size/checksum finalized on stop`
                    : `${r.node_id}: ${r.path || "missing"} · ${r.bytes != null ? `${r.bytes} B` : "bytes ?"} · ${r.sha256 ? `sha256 ${r.sha256}` : "sha256 unavailable"}`)))
                : null,
              h("div", { className: "rfreact-row" },
                h(SafeButton, {
                  key: `trial-start-${trialState}-${rfReady ? "ready" : "blocked"}`,
                  action: trialState === "RUNNING"
                    ? "start refused while a trial is active"
                    : (rfReady
                      ? "creates trial sidecar + dual raw captures under research-data/web-trials/"
                      : "start refused: backend RF READY prerequisite is not satisfied"),
                  label: trialState === "RUNNING" ? "TRIAL RUNNING"
                    : (rfReady ? "START 110 S TRIAL" : "RF READY REQUIRED"),
                  kind: "primary",
                  disabled: trialState === "RUNNING" || !rfReady,
                  title: trialState === "RUNNING"
                    ? "a trial is already running"
                    : (rfReady ? "start a 110 s trial"
                      : (readiness && readiness.reason) || "RF READY is unavailable"),
                  onClick: startTrial,
                }),
                h(SafeButton, {
                  key: `trial-stop-${trialState}`,
                  action: "stops dual raw captures early and preserves partial files + sidecar",
                  label: "STOP TRIAL / PRESERVE PARTIAL", kind: "danger",
                  disabled: trialState !== "RUNNING", onClick: stopTrial,
                })),
              h("div", { className: "rfreact-row" },
                h(SafeButton, {
                  action: "local browser speechSynthesis test only; no audio leaves the browser",
                  label: "TEST AUDIO", disabled: !supported, onClick: testAudio,
                }),
                h("button", {
                  className: "rfreact-btn", type: "button",
                  "aria-pressed": muted ? "true" : "false",
                  onClick: () => setMuted((v) => !v),
                }, muted ? "UNMUTE AUDIO" : "MUTE AUDIO")),
              !supported
                ? h("p", { className: "rfreact-err" },
                  "speechSynthesis is unavailable in this browser. Visual phase labels still update; no audio will play.")
                : h("p", { className: "rfreact-note" },
                  "Voice guidance uses the browser's native speechSynthesis. No microphone, no audio upload, no password in trial metadata."),
              research.trialMsg ? h("p", { className: "rfreact-note" }, research.trialMsg) : null,
              trial.phases && trial.phases.length
                ? h("details", { className: "rfreact-scene-options" },
                  h("summary", null, "Trial phase plan"),
                  h("div", { className: "rfreact-rows" },
                    trial.phases.map((p) => h("p", {
                      key: p.id, className: "rfreact-linemono",
                    }, `${p.label} · ${formatSeconds(p.seconds)} · planned ${formatSeconds(p.planned_start_s)} → ${formatSeconds(p.planned_end_s)} · observed ${p.observed_start_s == null ? "pending" : formatSeconds(p.observed_start_s)}`))))
                : null,
              h("p", { className: "rfreact-note" },
                "Trial sidecars record phase markers, raw paths and checksums only. Analysis is NOT_RUN; no presence, activity, localization or sensing claim is made."),
            )),
        h("details", { className: "rfreact-scene-options" },
          h("summary", null, "Advanced — diagnostic recording"),
          h(Card, { label: "Recorder", title: "Diagnostic recording (bounded, single live source)" },
          h("div", { className: "rfreact-row" },
            h(SafeButton, { action: "creates artifact: bounded ≤10 s diagnostic capture under research-data/", label: "RECORD 10 S", kind: "primary", onClick: recordStart() }),
            h(SafeButton, { action: "stops capture and returns manifest checksum", label: "STOP + CHECKSUM", onClick: recordStop() }),
          ),
          h("p", { className: "rfreact-note" }, research.recordMsg || "No automatic recording. Short diagnostics only, never committed."),
          h("p", { className: "rfreact-note" }, "Recording requires the live source (backend returns 409 otherwise) — the error is shown, not hidden."))),
      ),
      h("div", { className: "rfreact-col" },
        h("details", { className: "rfreact-scene-options" },
          h("summary", null, "Advanced — analysis (not activated)"),
          h(Card, { label: "Analysis", title: "Trials · protocol · analysis — not activated" },
            h("p", { className: "rfreact-note" },
              "Trial recording is implemented; statistical analysis, within/between-zone variation, separation ratio, drift, 1-NN and results remain NOT_RUN. No placeholders are displayed; absence is explicit."))),
      ),
    ));
}
