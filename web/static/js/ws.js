/* WebSocket client — RF Vision native.
   Adapted pattern from RuView services/websocket.service.js (dd02efe2):
   multiplexed connect, heartbeat ping, exponential-backoff reconnect.
   Simplified: single stream endpoint, JSON text only, no auth tickets
   (reserved for a future multi-user phase). */
import { CONSOLE, wsUrl } from "./config.js";

export class WsClient {
  constructor() {
    this.sock = null;
    this.attempts = 0;
    this.wanted = false;
    this.handlers = { event: [], state: [] };
    this.state = "disconnected"; // disconnected|connecting|connected|reconnecting
    this._pingTimer = null;
  }

  on(kind, cb) {
    this.handlers[kind].push(cb);
  }

  _emit(kind, data) {
    for (const cb of this.handlers[kind]) {
      try { cb(data); } catch (err) { console.error("ws handler", err); }
    }
  }

  _setState(state) {
    this.state = state;
    this._emit("state", state);
  }

  connect() {
    this.wanted = true;
    this.attempts = 0;
    this._dial();
  }

  disconnect() {
    this.wanted = false;
    this._cleanup();
    this._setState("disconnected");
  }

  _cleanup() {
    if (this._pingTimer) { clearInterval(this._pingTimer); this._pingTimer = null; }
    if (this.sock) { try { this.sock.close(); } catch { /* already closed */ } this.sock = null; }
  }

  _dial() {
    if (!this.wanted) return;
    this._cleanup();
    this._setState(this.attempts === 0 ? "connecting" : "reconnecting");
    let sock;
    try {
      sock = new WebSocket(wsUrl());
    } catch {
      return this._schedule();
    }
    this.sock = sock;
    sock.onopen = () => {
      this.attempts = 0;
      this._setState("connected");
      this._pingTimer = setInterval(() => this.send({ command: "ping" }), 30000);
    };
    sock.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg && msg.type === "pong") return;
      this._emit("event", msg);
    };
    sock.onclose = () => {
      if (this.sock === sock) this.sock = null;
      if (this._pingTimer) { clearInterval(this._pingTimer); this._pingTimer = null; }
      if (this.wanted) this._schedule();
      else this._setState("disconnected");
    };
    sock.onerror = () => { try { sock.close(); } catch { /* noop */ } };
  }

  _schedule() {
    if (!this.wanted) return;
    if (this.attempts >= CONSOLE.WS_MAX_ATTEMPTS) {
      this.wanted = false;
      this._setState("disconnected");
      return;
    }
    const delay = CONSOLE.WS_RECONNECT_DELAYS_MS[
      Math.min(this.attempts, CONSOLE.WS_RECONNECT_DELAYS_MS.length - 1)];
    this.attempts += 1;
    this._setState("reconnecting");
    setTimeout(() => this._dial(), delay);
  }

  send(obj) {
    if (this.sock && this.sock.readyState === WebSocket.OPEN) {
      this.sock.send(JSON.stringify(obj));
      return true;
    }
    return false;
  }
}
