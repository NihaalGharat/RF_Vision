/* Dependency-free 2D visualizations — RF Vision native.
   Adapted concept from RuView utils/pose-renderer.js + SensingTab sparklines
   (dd02efe2): custom canvas rendering, zero chart libraries. All helpers
   take plain numeric arrays (the validated visualization input shape) and
   render UNKNOWN placeholders for null input. */
function setupCanvas(canvas, height = 120) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = canvas.clientWidth || 300;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  canvas.style.height = `${height}px`;
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return { ctx, width, height };
}

function placeholder(canvas, text = "NO DATA") {
  const { ctx, width, height } = setupCanvas(canvas);
  ctx.fillStyle = "#1a2126";
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#7d8b8b";
  ctx.font = "11px monospace";
  ctx.textAlign = "center";
  ctx.fillText(text, width / 2, height / 2);
}

export function drawHeatmap(canvas, rows, opts = {}) {
  // rows: array of amplitude vectors (time-major). Null → placeholder.
  if (!rows || !rows.length || !rows[0] || !rows[0].length) {
    placeholder(canvas, opts.emptyText || "NO FRAMES YET");
    return;
  }
  const { ctx, width, height } = setupCanvas(canvas, opts.height || 140);
  const cols = rows[0].length;
  let lo = Infinity, hi = -Infinity;
  for (const row of rows) {
    for (const v of row) { if (v < lo) lo = v; if (v > hi) hi = v; }
  }
  if (!(hi > lo)) { hi = lo + 1; }
  const cw = width / cols, rh = height / rows.length;
  for (let r = 0; r < rows.length; r++) {
    for (let c = 0; c < cols; c++) {
      const t = (rows[r][c] - lo) / (hi - lo);
      const hue = Math.round(190 - 190 * t); // cyan → red
      ctx.fillStyle = `hsl(${hue}, 85%, ${25 + 30 * t}%)`;
      ctx.fillRect(c * cw, r * rh, Math.ceil(cw), Math.ceil(rh));
    }
  }
}

export function drawSparkline(canvas, series, opts = {}) {
  if (!series || !series.length) {
    placeholder(canvas, opts.emptyText || "NO DATA");
    return;
  }
  const { ctx, width, height } = setupCanvas(canvas, opts.height || 60);
  let lo = Math.min(...series), hi = Math.max(...series);
  if (!(hi > lo)) { hi = lo + 1; }
  ctx.strokeStyle = "#2c353b";
  ctx.beginPath();
  ctx.moveTo(0, height - 1);
  ctx.lineTo(width, height - 1);
  ctx.stroke();
  ctx.strokeStyle = opts.color || "#37c6d4";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  series.forEach((v, i) => {
    const x = (i / Math.max(series.length - 1, 1)) * width;
    const y = height - 4 - ((v - lo) / (hi - lo)) * (height - 8);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.fillStyle = "#7d8b8b";
  ctx.font = "10px monospace";
  ctx.textAlign = "left";
  const last = series[series.length - 1];
  ctx.fillText(`${opts.label || ""} ${Number(last).toFixed(1)} [${lo.toFixed(0)}..${hi.toFixed(0)}]`, 4, 11);
}

export function drawBars(canvas, entries, opts = {}) {
  // entries: [{label, value (0..1|null)}]; null → UNKNOWN slot.
  const { ctx, width } = setupCanvas(canvas, opts.height || 24 * Math.max(entries.length, 1) + 8);
  ctx.font = "10px monospace";
  entries.forEach((e, i) => {
    const y = 8 + i * 24;
    ctx.fillStyle = "#7d8b8b";
    ctx.textAlign = "left";
    ctx.fillText(e.label.slice(0, 18), 4, y + 10);
    const bx = 130, bw = Math.max(width - 190, 40);
    ctx.strokeStyle = "#2c353b";
    ctx.strokeRect(bx, y, bw, 12);
    if (e.value === null || e.value === undefined) {
      ctx.fillStyle = "#5f7373";
      ctx.fillText("UNKNOWN", bx + 4, y + 10);
    } else {
      const t = Math.max(0, Math.min(1, e.value));
      ctx.fillStyle = e.color || "#37c6d4";
      ctx.fillRect(bx, y, bw * t, 12);
      ctx.fillStyle = "#b9c6c6";
      ctx.textAlign = "right";
      ctx.fillText(Number(e.value).toFixed(2), width - 4, y + 10);
    }
  });
}

export function drawRoom2d(canvas, model) {
  // model: {widthM|null, lengthM|null, router:{x,z}|null, esp32:{x,z}|null,
  //         positionT|null (0..1 along link), uncertainty|null}.
  // Unknown geometry is drawn as a dashed UNKNOWN outline — never invented.
  const { ctx, width, height } = setupCanvas(canvas, 260);
  ctx.fillStyle = "#141a1e";
  ctx.fillRect(0, 0, width, height);
  const pad = 24;
  const W = model.widthM, L = model.lengthM;
  const known = W && L && W > 0 && L > 0;
  const rx = pad, ry = pad, rw = width - 2 * pad, rh = height - 2 * pad;
  // grid
  ctx.strokeStyle = "#222c31";
  ctx.lineWidth = 1;
  for (let gx = rx; gx <= rx + rw; gx += 20) {
    ctx.beginPath(); ctx.moveTo(gx, ry); ctx.lineTo(gx, ry + rh); ctx.stroke();
  }
  for (let gy = ry; gy <= ry + rh; gy += 20) {
    ctx.beginPath(); ctx.moveTo(rx, gy); ctx.lineTo(rx + rw, gy); ctx.stroke();
  }
  // room outline
  ctx.setLineDash(known ? [] : [6, 4]);
  ctx.strokeStyle = known ? "#37c6d4" : "#7d8b8b";
  ctx.strokeRect(rx, ry, rw, rh);
  ctx.setLineDash([]);
  ctx.fillStyle = "#7d8b8b";
  ctx.font = "10px monospace";
  ctx.textAlign = "left";
  ctx.fillText(known ? `${W.toFixed(1)} × ${L.toFixed(1)} m` : "ROOM: UNKNOWN (uncalibrated)", rx + 4, ry + 12);
  // nodes default to opposite ends when positions unknown
  const toXY = (t) => ({ x: rx + t * rw, y: ry + rh / 2 });
  const rXY = toXY(0), eXY = toXY(1);
  ctx.strokeStyle = "#1e7d87";
  ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(rXY.x, rXY.y); ctx.lineTo(eXY.x, eXY.y); ctx.stroke();
  // uncertainty region around position estimate
  if (model.positionT !== null && model.positionT !== undefined) {
    const px = rx + model.positionT * rw;
    const half = (model.uncertainty || 0) * rw;
    ctx.fillStyle = "rgba(224, 166, 60, 0.25)";
    ctx.fillRect(px - half, ry + rh / 2 - 14, half * 2, 28);
    ctx.fillStyle = "#e0a63c";
    ctx.beginPath(); ctx.arc(px, ry + rh / 2, 4, 0, Math.PI * 2); ctx.fill();
  }
  const node = (p, color, tag) => {
    ctx.fillStyle = color;
    ctx.fillRect(p.x - 5, p.y - 5, 10, 10);
    ctx.fillStyle = "#b9c6c6";
    ctx.fillText(tag, p.x + 8, p.y + 4);
  };
  node(rXY, "#4d8de0", "ROUTER");
  node(eXY, "#3fce7a", "ESP32");
  ctx.fillStyle = "#5f7373";
  ctx.fillText("1-D link view — 2-D/3-D not claimed", rx + 4, ry + rh - 6);
}
