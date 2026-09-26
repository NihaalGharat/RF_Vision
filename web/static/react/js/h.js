/* h() — React.createElement alias + small render helpers.
   No JSX in this codebase (no build step by design); components use h(). */
const R = window.React;

export function h(tag, props, ...children) {
  const flat = children.flat(Infinity).filter((c) => c !== null && c !== undefined && c !== false);
  return R.createElement(tag, props || null, ...flat);
}

export function kv(rows) {
  return h("dl", { className: "rfreact-kv" },
    rows.map(([k, v], i) => [
      h("dt", { key: `k${i}` }, k),
      h("dd", { key: `v${i}` }, v),
    ]).flat());
}

export function unknown(text) {
  return h("span", { className: "rfreact-note" }, text || "UNKNOWN");
}

export function useClock(periodMs = 1000) {
  const [now, setNow] = R.useState(() => new Date());
  R.useEffect(() => {
    const t = setInterval(() => setNow(new Date()), periodMs);
    return () => clearInterval(t);
  }, [periodMs]);
  return now.toISOString().slice(11, 19);
}
