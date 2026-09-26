/* SafeButton — every state-changing control carries explicit semantics.
   Labels are never bare verbs: START SENSING, STOP SENSING, CONNECT RF NODES,
   RESET VIEW, SCAN NETWORKS, REFRESH STATUS, RECORD. The `action` prop names
   the backend/visual effect for auditability (see data-action in the DOM). */
import { h } from "../h.js";

const R = window.React;

export function SafeButton({ action, label, onClick, kind, disabled, title }) {
  const [busy, setBusy] = R.useState(false);
  const [msg, setMsg] = R.useState(null);
  const click = async () => {
    if (busy || disabled) return;
    setBusy(true);
    setMsg(null);
    try {
      const out = await onClick();
      if (typeof out === "string" && out) setMsg({ ok: true, text: out });
    } catch (err) {
      setMsg({ ok: false, text: String((err && err.message) || err) });
    } finally {
      setBusy(false);
    }
  };
  const cls = `rfreact-btn${kind === "primary" ? " primary" : ""}${kind === "danger" ? " danger" : ""}`;
  return h("span", null,
    h("button", {
      className: cls, onClick: click, disabled: busy || disabled,
      "data-action": action, title: title || action, type: "button",
    }, busy ? "working…" : label),
    msg ? h("span", { className: msg.ok ? "rfreact-ok" : "rfreact-err" }, ` ${msg.text}`) : null);
}
