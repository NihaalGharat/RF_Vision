/* Tab manager — RF Vision native.
   Adapted pattern from RuView ui/components/TabManager.js (dd02efe2):
   DOM-query tabs, lazy per-tab init, change callbacks, badges.
   Rewritten: lifecycle hooks (init/destroy/onEvent/onState), disabled-tab
   guard, hash routing. */
export class TabManager {
  constructor(navEl, panelRoot) {
    this.navEl = navEl;
    this.panelRoot = panelRoot;
    this.tabs = [];
    this.modules = {};
    this.active = null;
    this.onChange = [];
  }

  register(id, module) {
    this.modules[id] = { ...module, id, inited: false };
  }

  init(ctx) {
    this.ctx = ctx;
    this.tabs = Array.from(this.navEl.querySelectorAll(".tab"));
    this.tabs.forEach((btn) => {
      btn.addEventListener("click", () => this.switchTo(btn.dataset.tab));
    });
    window.addEventListener("hashchange", () => {
      const id = location.hash.replace("#", "");
      if (id && this.modules[id]) this.switchTo(id);
    });
    const initial = location.hash.replace("#", "");
    this.switchTo(this.modules[initial] ? initial : "overview", true);
  }

  switchTo(id, silent = false) {
    const mod = this.modules[id];
    if (!mod) return;
    const btn = this.navEl.querySelector(`[data-tab="${id}"]`);
    if (btn && btn.disabled) return;
    if (this.active && this.modules[this.active].onHide) {
      try { this.modules[this.active].onHide(); } catch (e) { console.error(e); }
    }
    this.tabs.forEach((b) => {
      const on = b.dataset.tab === id;
      b.classList.toggle("active", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    this.panelRoot.querySelectorAll(".panel").forEach((p) => {
      const on = p.id === `panel-${id}`;
      p.classList.toggle("active", on);
      if (on) p.hidden = false; else p.hidden = true;
    });
    if (!mod.inited && mod.init) {
      const el = document.getElementById(`panel-${id}`);
      try { mod.init(el, this.ctx); } catch (e) {
        el.innerHTML = `<div class="card"><h3>Load error</h3><p class="state-note">${e.message}</p></div>`;
        console.error(`tab ${id} init`, e);
      }
      mod.inited = true;
    }
    this.active = id;
    if (!silent) history.replaceState(null, "", `#${id}`);
    if (mod.onShow) {
      try { mod.onShow(); } catch (e) { console.error(e); }
    }
    for (const cb of this.onChange) {
      try { cb(id); } catch (e) { console.error(e); }
    }
  }

  dispatchEvent(event) {
    for (const id of Object.keys(this.modules)) {
      const mod = this.modules[id];
      if (mod.inited && mod.onEvent) {
        try { mod.onEvent(event); } catch (e) { console.error(`tab ${id}`, e); }
      }
    }
  }

  dispatchState(snap) {
    for (const id of Object.keys(this.modules)) {
      const mod = this.modules[id];
      if (mod.inited && mod.onState) {
        try { mod.onState(snap); } catch (e) { console.error(`tab ${id}`, e); }
      }
    }
  }

  setBadge(id, text) {
    const btn = this.navEl.querySelector(`[data-tab="${id}"]`);
    if (!btn) return;
    let badge = btn.querySelector(".badge");
    if (text === null || text === undefined || text === "") {
      if (badge) badge.remove();
      return;
    }
    if (!badge) {
      badge = document.createElement("span");
      badge.className = "badge";
      btn.appendChild(badge);
    }
    badge.textContent = text;
  }
}
