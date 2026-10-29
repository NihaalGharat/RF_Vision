import { pathToFileURL } from "node:url";
import path from "node:path";

const repo = process.argv[2];
const moduleUrl = pathToFileURL(
  path.join(repo, "web/static/react/js/services/websocket.js")
).href;

let now = 0;
let nextId = 1;
const timers = new Map();

globalThis.location = { protocol: "http:", host: "127.0.0.1:9999" };
globalThis.setTimeout = (fn, ms) => {
  const id = nextId++;
  timers.set(id, { fn, at: now + ms, interval: null });
  return id;
};
globalThis.clearTimeout = (id) => timers.delete(id);
globalThis.setInterval = (fn, ms) => {
  const id = nextId++;
  timers.set(id, { fn, at: now + ms, interval: ms });
  return id;
};
globalThis.clearInterval = (id) => timers.delete(id);

let serverUp = false;
const sockets = [];

class FakeWebSocket {
  static OPEN = 1;

  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this._closed = false;
    sockets.push(this);
    Promise.resolve().then(() => {
      if (this._closed) return;
      if (serverUp) {
        this.readyState = 1;
        if (this.onopen) this.onopen();
      } else {
        this.readyState = 3;
        if (this.onerror) this.onerror();
      }
    });
  }

  send() {}

  close() {
    if (this._closed) return;
    this._closed = true;
    this.readyState = 3;
    Promise.resolve().then(() => {
      if (this.onclose) this.onclose();
    });
  }
}

globalThis.WebSocket = FakeWebSocket;

async function flush() {
  for (let i = 0; i < 8; i += 1) await Promise.resolve();
}

function nextTimer() {
  let best = null;
  for (const entry of timers) {
    if (!best || entry[1].at < best[1].at) best = entry;
  }
  return best;
}

async function runNextTimer() {
  const entry = nextTimer();
  if (!entry) return false;
  timers.delete(entry[0]);
  now = entry[1].at;
  entry[1].fn();
  await flush();
  return true;
}

const { WsService } = await import(moduleUrl);
const ws = new WsService();
const states = [];
ws.onState = (state) => states.push(state);

ws.connect();
await flush();

const failures = 12;
let dials = 0;
for (let i = 0; i < failures; i += 1) {
  const ran = await runNextTimer();
  if (!ran) break;
  dials += 1;
}

const afterFailures = {
  dials,
  state: ws.state,
  pendingTimers: timers.size,
  socketCount: sockets.length,
};

serverUp = true;
const reconnected = await runNextTimer();
await flush();

const result = {
  failures,
  afterFailures,
  reconnected,
  state: ws.state,
  socketCount: sockets.length,
  states,
};

ws.disconnect();
console.log(JSON.stringify(result));
