/* Research — "What is scientifically being measured, validated, analyzed?"
   Phase 1: real session provenance + stream state + bounded diagnostic
   recording. Trials, protocol automation, analysis values and results are NOT
   activated: unsupported areas render honest absence, never placeholder data.
   No research-session creation control exists (as in the legacy console). */
import { h, kv, unknown } from "../h.js";
import { Card, ErrorRow, ModePill, PageHeader } from "../components/global.js";
import { SafeButton } from "../components/controls.js";
import { api } from "../services/api.js";
import { researchStore, sourceStore, useStore } from "../state/store.js";

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

export function ResearchView({ refresh }) {
  const research = useStore(researchStore);
  const source = useStore(sourceStore);
  const exp = research.experiment;

  return h("div", null,
    h(PageHeader, {
      eyebrow: "RF Vision", title: "Research", back: true,
      actions: [h(ModePill, { source: source.source, stale: false })],
    }),
    h("div", { className: "rfreact-cols rfreact-cols-near" },
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Provenance", title: "Active session provenance" },
          h(ErrorRow, { error: research.experimentError, onRetry: refresh, what: "experiment" }),
          !exp ? unknown("BACKEND UNREACHABLE")
            : kv([
              ["session", exp.session_id],
              ["source", source.sourceState],
              ["stream", `${source.mode} · running=${source.running ? "true" : "false"}`],
              ["hardware", `${exp.hardware.esp32} · ${exp.hardware.router} · ${exp.hardware.band} · ${exp.hardware.transport}`],
              ["firmware", `${exp.firmware.name} · identity ${exp.firmware.identity}`],
              ["geometry", `room ${exp.geometry.room_width_m ?? "UNKNOWN"} × ${exp.geometry.room_length_m ?? "UNKNOWN"} (${exp.geometry.status})`],
              ["raw data", exp.raw_ref ? JSON.stringify(exp.raw_ref) : "none — no capture this session"],
              ["validation", exp.validation],
            ])),
        h(Card, { label: "Recorder", title: "Diagnostic recording (bounded)" },
          h("div", { className: "rfreact-row" },
            h(SafeButton, { action: "creates artifact: bounded ≤10 s diagnostic capture under research-data/", label: "RECORD 10 S", kind: "primary", onClick: recordStart() }),
            h(SafeButton, { action: "stops capture and returns manifest checksum", label: "STOP + CHECKSUM", onClick: recordStop() }),
          ),
          h("p", { className: "rfreact-note" }, research.recordMsg || "No automatic recording. Short diagnostics only, never committed."),
          h("p", { className: "rfreact-note" }, "Recording requires the live source (backend returns 409 otherwise) — the error is shown, not hidden.")),
      ),
      h("div", { className: "rfreact-col" },
        h(Card, { label: "Analysis", title: "Trials · protocol · analysis — not activated" },
          h("p", { className: "rfreact-note" },
            "Protocol state, trials, within/between-zone variation, separation ratio, drift, 1-NN analysis and results have no validated backend in this phase, so no values are displayed. Placeholders would be fabrication; they are omitted by policy.")),
      ),
    ));
}
