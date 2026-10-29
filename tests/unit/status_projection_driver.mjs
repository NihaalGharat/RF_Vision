/* P0 pytest driver: exercises the real source-projection module against
   batched JSON scenarios on stdin. No DOM, no build step, no mocks. */
const base = process.argv[2];
const sources = await import(`${base}/web/static/react/js/services/sources.js`);

let buf = "";
for await (const chunk of process.stdin) buf += chunk;
const scenarios = JSON.parse(buf);

const out = [];
for (const sc of scenarios) {
  try {
    if (sc.op === "networkMatch") {
      out.push({ id: sc.id, ...sources.networkMatch(sc.network, sc.node) });
      continue;
    }
    const dual = sources.dualProjection(sc.nodes);
    const fallback = sources.sourceFromMode(sc.mode);
    out.push({
      id: sc.id,
      projection: dual,
      fallback,
      operatorLabel: dual ? dual.label : fallback,
    });
  } catch (error) {
    out.push({ id: sc.id, error: String(error && error.stack || error) });
  }
}
process.stdout.write(JSON.stringify(out));
