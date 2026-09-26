/* WebSocket service — preserves the existing /ws/sensing contract.
   Same semantics as the legacy console client: single stream endpoint, JSON
   text only, 30 s ping, exponential-backoff reconnect (max 10 attempts),
   schema-1 envelope validation, pong filtering. Not a new protocol. */

const RECONNECT_DELAYS_MS = [1000, 2000, 4000, 8000, 16000, 30000];
const MAX_ATTEMPTS = 10;

function wsUrl(path = "/ws/sensing") {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  return `${proto}://${location.host}${path}`;
}

export class WsService {
  constructor() {
    this.sock = null;
    this.attempts = 0;
    this.wanted = false;
    this.state = "disconnected"; // disconnected|connecting|connected|reconnecting
    this.onEvent = null; // (envelope) => void
    this.onState = null; // (state) => void
    this._pingTimer = null;
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

  send(obj) {
    if (this.sock && this.sock.readyState === WebSocket.OPEN) {
      this.sock.send(JSON.stringify(obj));
      return true;
    }
    return false;
  }

  _setState(state) {
    this.state = state;
    if (this.onState) {
      try { this.onState(state); } catch (err) { console.error("ws state cb", err); }
    }
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
      if (!msg || msg.schema !== 1 || !msg.type) return;
      if (this.onEvent) {
        try { this.onEvent(msg); } catch (err) { console.error("ws event cb", err); }
      }
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
    if (this.attempts >= MAX_ATTEMPTS) {
      this.wanted = false;
      this._setState("disconnected");
      return;
    }
    const delay = RECONNECT_DELAYS_MS[Math.min(this.attempts, RECONNECT_DELAYS_MS.length - 1)];
    this.attempts += 1;
    this._setState("reconnecting");
    setTimeout(() => this._dial(), delay);
  }
}
