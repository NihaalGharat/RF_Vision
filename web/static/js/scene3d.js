/* Three.js RF link scene — RF Vision native (scene foundation).
   Adapted architecture (not code) from RuView components/scene.js +
   environment.js + gaussian-splats.js (dd02efe2): layered scene graph
   (base → room → nodes → field overlay), meter Y-up coordinates, orbit
   controls, HUD overlay. Content is ours: EXACTLY ONE link (router → ESP32),
   uncertainty segment, amplitude-driven field strip. No bodies, no mesh,
   no pose — those would fabricate unvalidated capabilities.
   three.js r160 vendored locally (see docs/software/THREEJS_VERSION.md). */
import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";
import { ReferenceVisualLayer } from "./referenceVisualLayer.js";
// Phase 2: pure false-colour mapping for the live RF disturbance overlay.
// Presentation only (no acquisition/inference); pernode.js has no imports,
// so this adds no load cascade for any consumer of this scene.
import { thermalColor } from "../react/js/services/pernode.js";

export class RfLinkScene {
  constructor(container) {
    this.container = container;
    this.ready = false;
    this.model = {
      widthM: null, amplitudes: null, positionT: null, uncertainty: null,
    };
    this.referenceLayer = null;
    this._referenceOn = false;
    this._refSaved = null;
  }

  // Scene height follows the CSS breakpoints (420 default, 300 ≤1024px,
  // 260 ≤640px) so the renderer never fights the stylesheet.
  sceneHeight() {
    const w = window.innerWidth || 1280;
    return w <= 640 ? 260 : (w <= 1024 ? 300 : 420);
  }

  init() {
    const w = this.container.clientWidth || 600;
    const h = this.sceneHeight();
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h);
    this.container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this._bgTheme = "";
    this._syncThemeBg();
    this.camera = new THREE.PerspectiveCamera(50, w / h, 0.1, 200);
    this.camera.position.set(4.5, 3.5, 6.5);
    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.target.set(0, 0.8, 0);
    this.controls.enableDamping = true;

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const key = new THREE.DirectionalLight(0xffffff, 1.1);
    key.position.set(5, 8, 4);
    this.scene.add(key);
    this.scene.add(new THREE.HemisphereLight(0x8fb8c0, 0x1a2126, 0.4));

    // Room: dashed UNKNOWN outline until calibration provides dimensions.
    this.roomGroup = new THREE.Group();
    this.scene.add(this.roomGroup);
    this._buildRoom(null);

    // Grid floor (1 m cells, 8×8 — reference only, not a claim).
    const grid = new THREE.GridHelper(8, 8, 0x2c353b, 0x222c31);
    grid.position.y = 0;
    this.grid = grid;
    this.scene.add(grid);

    // Nodes: router (tx, blue) at x=-2, ESP32 (rx, green) at x=+2.
    this.routerNode = this._makeNode(0x4d8de0, "router");
    this.routerNode.position.set(-2, 0.5, 0);
    this.espNode = this._makeNode(0x3fce7a, "esp32");
    this.espNode.position.set(2, 0.5, 0);
    this.scene.add(this.routerNode, this.espNode);

    // Link line router → ESP32.
    const linkGeo = new THREE.BufferGeometry().setFromPoints(
      [new THREE.Vector3(-2, 0.5, 0), new THREE.Vector3(2, 0.5, 0)]);
    this.link = new THREE.Line(linkGeo,
      new THREE.LineBasicMaterial({ color: 0x37c6d4 }));
    this.scene.add(this.link);

    // Uncertainty segment (translucent, hidden until an estimate exists).
    this.uncMesh = new THREE.Mesh(
      new THREE.BoxGeometry(0.2, 0.3, 0.3),
      new THREE.MeshBasicMaterial({
        color: 0xe0a63c, transparent: true, opacity: 0.35,
      }));
    this.uncMesh.visible = false;
    this.scene.add(this.uncMesh);

    // Position marker (hidden until an estimate exists).
    this.posMarker = new THREE.Mesh(
      new THREE.SphereGeometry(0.09, 16, 16),
      new THREE.MeshBasicMaterial({ color: 0xe0a63c }));
    this.posMarker.visible = false;
    this.scene.add(this.posMarker);

    // RF field strip: 64-segment plane under the link, vertex-colored by
    // the latest amplitude vector (abstraction, not a propagation model).
    // Node-A signal strip (existing mesh, cyan→red presentation ramp).
    const SEG = 64;
    const fieldGeo = new THREE.PlaneGeometry(4, 1.2, SEG - 1, 1);
    fieldGeo.rotateX(-Math.PI / 2);
    const colors = new Float32Array(fieldGeo.attributes.position.count * 3);
    fieldGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    this.field = new THREE.Mesh(fieldGeo, new THREE.MeshBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.75, side: THREE.DoubleSide,
    }));
    this.field.position.y = 0.02;
    this.scene.add(this.field);
    // Node-B signal strip: created lazily on first per-node B frame (same
    // tone-index mapping, parallel offset). fieldB is null until then, so
    // single-source callers never pay for or see a second strip.
    // The z-offset is PRESENTATION ARRANGEMENT ONLY — not physical distance.
    this.fieldB = null;

    // Phase 2 (live RF thermal disturbance overlay): per-node false-colour
    // planes painted from each node's OWN disturb vector. Created lazily on
    // first per-node frame; null until then. Vertical, immediately in front
    // of the Phase 1 room-image plane, translucent so the room stays
    // recognizable. Tone index runs along the width — the SAME signal-domain
    // convention as the strips, NOT room coordinates. Left half = NODE A RF
    // CHANGE, right half = NODE B RF CHANGE (explicit composition, never a
    // calibrated spatial fusion). SIGNAL-DERIVED presentation only.
    this.thermalA = null;
    this.thermalB = null;

    // Phase 3 (approximate RF evidence field): three coarse translucent floor
    // bands for the NEAR-A / BETWEEN / NEAR-B evidence zones. Created lazily,
    // null until the first RF_ESTIMATE field arrives. Band centers are thirds
    // of the CURRENT approximate A/B marker layout (presentation arrangement
    // only — not surveyed geometry, not room coordinates); opacity encodes
    // the deterministic zone evidence score. Shown ONLY at RF_ESTIMATE tier —
    // RF_ACTIVITY and below render nothing (no spatial claim visualized).
    this.zoneField = null;

    this.referenceLayer = new ReferenceVisualLayer(this.scene);

    this.hud = document.createElement("div");
    this.hud.className = "scene-hud";
    this.container.appendChild(this.hud);
    this._updateHud();

    this._onResize = () => this.resize();
    window.addEventListener("resize", this._onResize);
    const reduceMotion = window.matchMedia &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    this._animate = !reduceMotion;
    this.ready = true;
    this._loop();
  }

  // Canvas background follows the UI theme (no dark island in light
  // mode). Cached per theme value — not re-read per frame.
  _syncThemeBg() {
    if (this._referenceOn && this.scene) return;
    const theme = (document.documentElement.dataset || {}).theme || "";
    if (theme === this._bgTheme) return;
    this._bgTheme = theme;
    let css = "";
    try {
      css = getComputedStyle(document.documentElement)
        .getPropertyValue("--bg-0").trim();
    } catch { /* fallback below */ }
    this.scene.background = new THREE.Color(css || "#141a1e");
  }

  _makeNode(color) {
    const group = new THREE.Group();
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(0.25, 0.5, 0.25),
      new THREE.MeshStandardMaterial({ color }));
    box.position.y = 0.25;
    group.add(box);
    const mast = new THREE.Mesh(
      new THREE.CylinderGeometry(0.02, 0.02, 0.5),
      new THREE.MeshBasicMaterial({ color: 0x7d8b8b }));
    mast.position.y = -0.25;
    group.add(mast);
    return group;
  }

  _buildRoom(widthM) {
    while (this.roomGroup.children.length) {
      const child = this.roomGroup.children.pop();
      child.geometry?.dispose();
      child.material?.dispose();
    }
    const w = widthM && widthM > 0 ? widthM : 5.0;
    const h = 2.6, d = 4.0;
    const geo = new THREE.BoxGeometry(w, h, d);
    const edges = new THREE.EdgesGeometry(geo);
    // Solid cyan when calibrated, dashed grey while UNKNOWN.
    const mat = widthM
      ? new THREE.LineBasicMaterial({ color: 0x37c6d4 })
      : new THREE.LineDashedMaterial({
          color: 0x7d8b8b, dashSize: 0.25, gapSize: 0.15,
        });
    const box = new THREE.LineSegments(edges, mat);
    box.position.y = h / 2;
    if (mat.isLineDashedMaterial) box.computeLineDistances();
    this.roomGroup.add(box);
    this.roomKnown = Boolean(widthM);
    this._updateHud();
  }

  // Per-node signal-strip layer (additive; legacy single-strip callers
  // never pass `nodes` and keep byte-identical behavior).
  // RAMP_A reuses the existing cyan→red presentation encoding; RAMP_B is a
  // distinct violet→amber encoding so the streams stay distinguishable.
  // Ramps encode RELATIVE amplitude within one frame — never absolute
  // power, never space. DISTURB_HEIGHT_M is a presentation scale for
  // measured signal change (RF DISTURBANCE), not a physical unit.
  static RAMP_A = { r0: 0.2, r1: 0.8, g0: 0.75, g1: -0.55, b0: 0.85, b1: -0.45 };
  static RAMP_B = { r0: 0.45, r1: 0.55, g0: 0.35, g1: 0.30, b0: 0.9, b1: -0.7 };
  static DISTURB_HEIGHT_M = 0.9;

  _ensureFieldB() {
    if (this.fieldB) return;
    const SEG = 64;
    const geo = new THREE.PlaneGeometry(4, 1.2, SEG - 1, 1);
    geo.rotateX(-Math.PI / 2);
    const colors = new Float32Array(geo.attributes.position.count * 3);
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    this.fieldB = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.75, side: THREE.DoubleSide,
    }));
    this.fieldB.position.set(0, 0.02, -1.3);
    this.fieldB.visible = false;
    this.scene.add(this.fieldB);
  }

  // Paint one node strip from that node's OWN amplitude vector (+ optional
  // measured disturbance for vertex height). Pure presentation.
  _paintStrip(mesh, slot, ramp) {
    const amps = slot.amplitudes;
    let lo = Math.min(...amps), hi = Math.max(...amps);
    if (!(hi > lo)) hi = lo + 1;
    const attr = mesh.geometry.attributes;
    const pos = attr.position, col = attr.color;
    const dev = (slot.disturb && slot.disturb.length === amps.length) ? slot.disturb : null;
    const H = RfLinkScene.DISTURB_HEIGHT_M;
    for (let i = 0; i < pos.count; i++) {
      const seg = Math.min(amps.length - 1,
        Math.floor(((pos.getX(i) + 2) / 4) * amps.length));
      const t = (amps[seg] - lo) / (hi - lo);
      col.setXYZ(i,
        ramp.r0 + ramp.r1 * t, ramp.g0 + ramp.g1 * t, ramp.b0 + ramp.b1 * t);
      pos.setY(i, dev ? Math.max(0, Math.min(1, dev[seg])) * H : 0);
    }
    col.needsUpdate = true;
    pos.needsUpdate = true;
    mesh.material.opacity = slot.stale ? 0.15 : 0.75;
    mesh.visible = true;
  }

  // Phase 2: build (once) and paint (per frame) the per-node thermal
  // planes. Each plane paints ONLY its own node's disturb vector via the
  // pure thermalColor mapping; stale slots ride dimmed (opacity 0.08) with
  // STALE in the HUD — never presented as current. Bounded: two fixed
  // 63×2-vertex planes, colors updated in place, no history, no new loop.
  _ensureThermal() {
    if (this.thermalA && this.thermalB) return;
    const mk = (x) => {
      const geo = new THREE.PlaneGeometry(2.5, 2.6, 62, 1);
      const colors = new Float32Array(geo.attributes.position.count * 3);
      geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
      const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({
        vertexColors: true, transparent: true, opacity: 0.5,
        side: THREE.DoubleSide, depthWrite: false,
      }));
      mesh.position.set(x, 1.3, -1.9);
      mesh.renderOrder = 1;
      mesh.visible = false;
      this.scene.add(mesh);
      return mesh;
    };
    if (!this.thermalA) this.thermalA = mk(-1.25);
    if (!this.thermalB) this.thermalB = mk(1.25);
  }

  _paintThermal(mesh, slot) {
    const dev = slot.disturb;
    const attr = mesh.geometry.attributes;
    const col = attr.color;
    const n = dev.length;
    for (let i = 0; i < col.count; i++) {
      // PlaneGeometry emits (63 × 2) vertices left-to-right; column index
      // selects the tone — signal-domain order, not room position.
      const ix = i % 63;
      const seg = Math.min(n - 1, Math.floor((ix / 63) * n));
      const c = thermalColor(dev[seg]);
      col.setXYZ(i, c[0], c[1], c[2]);
    }
    col.needsUpdate = true;
    mesh.material.opacity = slot.stale ? 0.08 : 0.5;
    mesh.visible = true;
  }

  _clearThermal() {
    for (const k of ["thermalA", "thermalB"]) {
      const m = this[k];
      this[k] = null;
      if (!m) continue;
      if (m.parent) m.parent.remove(m);
      try { m.geometry.dispose(); } catch { /* already torn down */ }
      try { m.material.dispose(); } catch { /* already torn down */ }
    }
  }

  // Phase 3: build (once) and paint (per field) the three coarse evidence
  // bands. field = {tier, zones:{nearA,between,nearB}, leader} or null.
  // Anything but RF_ESTIMATE hides the group — stale/reset states can never
  // leave a spatial claim on screen. Bounded: three unit boxes, scaled and
  // re-tinted in place, no history, no new loop.
  _ensureZoneField() {
    if (this.zoneField) return;
    const group = new THREE.Group();
    const meshes = {};
    for (const k of ["nearA", "between", "nearB"]) {
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(1, 0.06, 1),
        new THREE.MeshBasicMaterial({
          color: 0xe0a63c, transparent: true, opacity: 0,
          depthWrite: false,
        }));
      mesh.position.y = 0.05;
      mesh.renderOrder = 2;
      mesh.visible = false;
      group.add(mesh);
      meshes[k] = mesh;
    }
    group.visible = false;
    this.scene.add(group);
    this.zoneField = { group, meshes };
  }

  _paintZoneField(field) {
    this._ensureZoneField();
    const { group, meshes } = this.zoneField;
    const show = Boolean(
      field && field.tier === "RF_ESTIMATE" && field.zones &&
      this.markerA && this.markerB);
    group.visible = show;
    if (!show) {
      for (const k of ["nearA", "between", "nearB"]) meshes[k].visible = false;
      return;
    }
    // Thirds between the approximate marker positions (layout only).
    const ax = this.markerA.position.x, az = this.markerA.position.z;
    const bx = this.markerB.position.x, bz = this.markerB.position.z;
    const order = ["nearA", "between", "nearB"];
    for (let i = 0; i < order.length; i++) {
      const k = order[i];
      const mesh = meshes[k];
      const c0 = i / 3, c1 = (i + 1) / 3, cm = (c0 + c1) / 2;
      const score = Math.max(0, Math.min(1, Number(field.zones[k]) || 0));
      mesh.position.x = ax + (bx - ax) * cm;
      mesh.position.z = az + (bz - az) * cm;
      mesh.scale.x = Math.max(Math.abs(bx - ax) / 3, 0.05);
      mesh.scale.z = Math.max(Math.abs(bz - az) / 3, 0.05);
      mesh.material.opacity = 0.05 + 0.30 * score;
      mesh.visible = true;
    }
  }

  _clearZoneField() {
    const zf = this.zoneField;
    this.zoneField = null;
    if (!zf) return;
    if (zf.group.parent) zf.group.parent.remove(zf.group);
    for (const k of ["nearA", "between", "nearB"]) {
      try { zf.meshes[k].geometry.dispose(); } catch { /* already torn down */ }
      try { zf.meshes[k].material.dispose(); } catch { /* already torn down */ }
    }
  }

  // Phase 1 (room twin foundation): session-local room-image backdrop.
  // A textured plane on the back face of the room volume; the RF strips
  // render in front of it. `url` is a session-local browser object URL (or
  // null for the no-image state) — never uploaded, never persisted.
  // VISUAL CONTEXT ONLY: never an RF reconstruction, never calibrated.
  setRoomImage(url) {
    if (!this.ready || !this.scene) return;
    const token = (this._roomImageToken = (this._roomImageToken || 0) + 1);
    this._clearRoomImage();
    if (!url) return;
    try {
      new THREE.TextureLoader().load(url, (tex) => {
        if (token !== this._roomImageToken || !this.ready || !this.scene) {
          try { tex.dispose(); } catch { /* already torn down */ }
          return;
        }
        if (THREE.SRGBColorSpace !== undefined) tex.colorSpace = THREE.SRGBColorSpace;
        const mesh = new THREE.Mesh(
          new THREE.PlaneGeometry(5, 2.6),
          new THREE.MeshBasicMaterial({ map: tex }));
        mesh.position.set(0, 1.3, -1.95);
        this.scene.add(mesh);
        this.roomImage = mesh;
        if (this._referenceOn) this._syncReferenceVisibility();
      }, undefined, () => { /* load failed: keep the no-image state */ });
    } catch { /* keep the no-image state */ }
  }

  _clearRoomImage() {
    const m = this.roomImage;
    this.roomImage = null;
    if (!m) return;
    if (m.parent) m.parent.remove(m);
    try { m.geometry.dispose(); } catch { /* already torn down */ }
    const mat = m.material;
    if (mat) {
      try { if (mat.map) mat.map.dispose(); } catch { /* already torn down */ }
      try { mat.dispose(); } catch { /* already torn down */ }
    }
  }

  // Phase 1: approximate ESP32-A/B visual placement markers (layout only).
  // p = {A:{x,z}, B:{x,z}} in room meters, clamped to the room volume.
  // Presentation only — NOT SURVEYED, NOT MEASURED. Never an input to
  // calibration, inference, contracts, or research analysis.
  setPlacements(p) {
    if (!this.ready || !this.scene) return;
    this._ensureMarkers();
    const put = (key, mesh) => {
      const v = (p && p[key]) || {};
      const x = Math.max(-2.5, Math.min(2.5, Number(v.x) || 0));
      const z = Math.max(-2, Math.min(2, Number(v.z) || 0));
      mesh.position.set(x, 0.15, z);
    };
    put("A", this.markerA);
    put("B", this.markerB);
    if (this._referenceOn) this._syncReferenceVisibility();
  }

  _ensureMarkers() {
    if (this.markerA && this.markerB) return;
    const mk = (color, css, tag) => {
      const g = new THREE.Group();
      const dot = new THREE.Mesh(
        new THREE.SphereGeometry(0.12, 16, 16),
        new THREE.MeshBasicMaterial({ color }));
      dot.position.y = 0.1;
      g.add(dot);
      const label = this._textSprite(tag, css);
      label.position.y = 0.5;
      g.add(label);
      this.scene.add(g);
      return g;
    };
    // Cyan (A) / violet (B): distinct from the router-blue / ESP32-green
    // single-link pair and from the amber uncertainty marker.
    this.markerA = mk(0x37c6d4, "#37c6d4", "A");
    this.markerB = mk(0xc084fc, "#c084fc", "B");
  }

  _textSprite(text, css) {
    const c = document.createElement("canvas");
    c.width = 128; c.height = 128;
    const g = c.getContext("2d");
    g.beginPath(); g.arc(64, 64, 52, 0, Math.PI * 2);
    g.fillStyle = "rgba(0,0,0,0.6)"; g.fill();
    g.lineWidth = 6; g.strokeStyle = css; g.stroke();
    g.fillStyle = "#ffffff"; g.font = "bold 64px sans-serif";
    g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText(text, 64, 68);
    const tex = new THREE.CanvasTexture(c);
    if (THREE.SRGBColorSpace !== undefined) tex.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(
      new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: false }));
    sp.scale.set(0.5, 0.5, 1);
    return sp;
  }

  _evidenceObjects() {
    return [
      this.roomGroup, this.grid, this.routerNode, this.espNode, this.link,
      this.uncMesh, this.posMarker, this.field, this.fieldB,
      this.thermalA, this.thermalB, this.zoneField && this.zoneField.group,
      this.markerA, this.markerB, this.roomImage,
    ].filter(Boolean);
  }

  _syncReferenceVisibility() {
    if (!this._referenceOn) return;
    for (const object of this._evidenceObjects()) object.visible = false;
  }

  setReferenceView(on) {
    const next = Boolean(on);
    if (next === this._referenceOn) return;
    this._referenceOn = next;
    if (!this.ready || !this.scene || !this.referenceLayer) return;
    if (next) {
      this._refSaved = {
        position: this.camera.position.clone(),
        target: this.controls.target.clone(),
        fov: this.camera.fov,
        background: this.scene.background,
        fog: this.scene.fog,
        visibility: new Map(this._evidenceObjects().map((o) => [o, o.visible])),
      };
      this.referenceLayer.setVisible(true);
      this.scene.background = new THREE.Color(0x18171a);
      this.scene.fog = new THREE.Fog(0x18171a, 18, 30);
      this._applyReferenceCamera();
      this.controls.update();
      this._syncReferenceVisibility();
      this._referenceResponse();
      this.referenceLayer.tick(performance.now(), this._animate);
    } else {
      this.referenceLayer.setVisible(false);
      const saved = this._refSaved;
      if (saved) {
        this.camera.position.copy(saved.position);
        this.controls.target.copy(saved.target);
        this.camera.fov = saved.fov;
        this.camera.updateProjectionMatrix();
        this.scene.background = saved.background;
        this.scene.fog = saved.fog;
        this.controls.update();
        for (const [object, visible] of saved.visibility) object.visible = visible;
        for (const object of this._evidenceObjects()) {
          if (!saved.visibility.has(object)) object.visible = true;
        }
      }
      this._refSaved = null;
      this.setModel(this.model);
    }
  }

  setIllustrativeBody(on) {
    this._bodyOn = Boolean(on);
    if (this.referenceLayer) this.referenceLayer.setBody(this._bodyOn);
    if (this._referenceOn) {
      this._applyReferenceCamera();
      this.controls.update();
      this.referenceLayer.tick(performance.now(), this._animate);
    }
  }

  _applyReferenceCamera() {
    this.camera.fov = 33.4;
    this.camera.updateProjectionMatrix();
    if (this._bodyOn) {
      this.camera.position.set(3.1, 2.2, 16.0);
      this.controls.target.set(2.4, 1.2, 0.0);
    } else {
      this.camera.position.set(4.2415, 2.9481, 16.0);
      this.controls.target.set(3.5415, 1.9481, 0.0);
    }
  }

  _referenceResponse() {
    if (!this.referenceLayer) return;
    const a = this.model.nodes && this.model.nodes.A;
    const b = this.model.nodes && this.model.nodes.B;
    const aLive = Boolean(a) && !a.stale;
    const bLive = Boolean(b) && !b.stale;
    const level = (slot) => Math.max(0, Math.min(1, (Number(slot && slot.disturbMean) || 0) * 3));
    this.referenceLayer.setResponse({
      a: aLive ? level(a) : 0,
      b: bLive ? level(b) : 0,
      stale: Boolean((a || b) && !aLive && !bLive),
    });
  }

  resetView() {
    if (this._referenceOn) {
      this._applyReferenceCamera();
    } else {
      this.camera.fov = 50;
      this.camera.updateProjectionMatrix();
      this.camera.position.set(4.5, 3.5, 6.5);
      this.controls.target.set(0, 0.8, 0);
    }
    this.controls.update();
  }

  setModel(model) {
    Object.assign(this.model, model);
    if (!this.ready) return;
    this._syncThemeBg();
    if (model.widthM !== undefined) this._buildRoom(model.widthM);
    const pn = model.nodes;
    if (pn !== undefined) {
      // Per-node layer: each strip paints ONLY its own node's vector.
      // Stale slots ride dimmed (opacity 0.15) with STALE in the HUD —
      // never presented as current. The legacy single strip shows only
      // while neither node has frames.
      const aLive = pn && pn.A && pn.A.amplitudes && pn.A.amplitudes.length;
      const bLive = pn && pn.B && pn.B.amplitudes && pn.B.amplitudes.length;
      if (aLive) this._paintStrip(this.field, pn.A, RfLinkScene.RAMP_A);
      if (aLive || bLive) this.field.visible = Boolean(aLive);
      // Neither node live: leave the last captured strip untouched (same
      // "last state for reference" semantics as before).
      if (bLive) {
        this._ensureFieldB();
        this._paintStrip(this.fieldB, pn.B, RfLinkScene.RAMP_B);
      } else if (this.fieldB) {
        this.fieldB.visible = false;
      }
      // Phase 2: per-node thermal overlay from each node's OWN disturb
      // vector (painted in place on the existing setModel path — no new
      // loop). A slot without a disturb vector contributes no thermal layer.
      // Neither node live: last thermal state stays for reference (same as
      // strips); stale slots ride dimmed via _paintThermal.
      const aTherm = aLive && pn.A.disturb && pn.A.disturb.length;
      const bTherm = bLive && pn.B.disturb && pn.B.disturb.length;
      if (aTherm || bTherm) this._ensureThermal();
      if (aTherm) {
        this._paintThermal(this.thermalA, pn.A);
      } else if (this.thermalA) {
        this.thermalA.visible = false;
      }
      if (bTherm) {
        this._paintThermal(this.thermalB, pn.B);
      } else if (this.thermalB) {
        this.thermalB.visible = false;
      }
    } else {
      const amps = this.model.amplitudes;
      if (amps && amps.length) {
        let lo = Math.min(...amps), hi = Math.max(...amps);
        if (!(hi > lo)) hi = lo + 1;
        const attr = this.field.geometry.attributes;
        const pos = attr.position, col = attr.color;
        for (let i = 0; i < pos.count; i++) {
          const seg = Math.min(amps.length - 1,
            Math.floor(((pos.getX(i) + 2) / 4) * amps.length));
          const t = (amps[seg] - lo) / (hi - lo);
          // cyan → red ramp
          col.setXYZ(i, 0.2 + 0.8 * t, 0.75 - 0.55 * t, 0.85 - 0.45 * t);
        }
        col.needsUpdate = true;
      }
    }
    // Phase 3: coarse 3-zone approximate RF evidence overlay. Visibility is
    // decided inside _paintZoneField — only an RF_ESTIMATE field renders;
    // null / lower tiers / missing markers hide the group, so a reset or
    // stale state can never leave a spatial claim on screen.
    if (model.field !== undefined) this._paintZoneField(model.field);
    const t = this.model.positionT, u = this.model.uncertainty;
    const show = (t !== null && t !== undefined);
    this.posMarker.visible = show;
    this.uncMesh.visible = show;
    if (show) {
      const x = -2 + 4 * Math.max(0, Math.min(1, t));
      this.posMarker.position.set(x, 0.5, 0);
      const half = 4 * Math.max(0, u || 0);
      this.uncMesh.scale.x = Math.max(half * 2, 0.05) / 0.2;
      this.uncMesh.position.set(x, 0.5, 0);
    }
    if (this._referenceOn) this._syncReferenceVisibility();
    this._updateHud();
  }

  _updateHud() {
    if (!this.hud) return;
    const m = this.model;
    const room = m.widthM ? `${m.widthM.toFixed(1)} m link` : "ROOM: UNKNOWN";
    const pos = (m.positionT === null || m.positionT === undefined)
      ? "pos: —" : `pos: t=${m.positionT.toFixed(2)} ± ${(m.uncertainty ?? 0).toFixed(2)}`;
    const extra = m.hudExtra ? ` · ${m.hudExtra}` : "";
    this.hud.textContent = `1 LINK · Y-up m · ${room} · ${pos}${extra}`;
  }

  resize() {
    if (!this.ready) return;
    const w = this.container.clientWidth || 600;
    const h = this.sceneHeight();
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  // Pause rendering while the tab is hidden (revamp perf): stops the RAF
  // chain entirely; resume restarts it. No data affected — render only.
  pause(v) {
    const was = this._paused;
    this._paused = Boolean(v);
    if (was && !this._paused && this.ready) this._loop();
  }

  _loop() {
    if (!this.ready || this._paused) return;
    requestAnimationFrame(() => this._loop());
    if (!this._animate) {
      this.renderer.render(this.scene, this.camera);
      return;
    }
    this.controls.update();
    if (this.referenceLayer && this._referenceOn) {
      this._referenceResponse();
      this.referenceLayer.tick(performance.now(), this._animate);
    }
    this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    this.ready = false;
    try { this.referenceLayer?.dispose(); } catch { /* already torn down */ }
    this.referenceLayer = null;
    try { this._clearRoomImage(); } catch { /* already torn down */ }
    try { this._clearThermal(); } catch { /* already torn down */ }
    try { this._clearZoneField(); } catch { /* already torn down */ }
    window.removeEventListener("resize", this._onResize);
    this.renderer?.dispose();
    this.container.innerHTML = "";
  }
}
