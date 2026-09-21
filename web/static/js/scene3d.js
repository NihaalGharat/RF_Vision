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

export class RfLinkScene {
  constructor(container) {
    this.container = container;
    this.ready = false;
    this.model = {
      widthM: null, amplitudes: null, positionT: null, uncertainty: null,
    };
  }

  init() {
    const w = this.container.clientWidth || 600;
    const h = 420;
    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(w, h);
    this.container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x141a1e);
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

  setModel(model) {
    Object.assign(this.model, model);
    if (!this.ready) return;
    if (model.widthM !== undefined) this._buildRoom(model.widthM);
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
    this._updateHud();
  }

  _updateHud() {
    if (!this.hud) return;
    const m = this.model;
    const room = m.widthM ? `${m.widthM.toFixed(1)} m link` : "ROOM: UNKNOWN";
    const pos = (m.positionT === null || m.positionT === undefined)
      ? "pos: —" : `pos: t=${m.positionT.toFixed(2)} ± ${(m.uncertainty ?? 0).toFixed(2)}`;
    this.hud.textContent = `1 LINK · Y-up m · ${room} · ${pos}`;
  }

  resize() {
    if (!this.ready) return;
    const w = this.container.clientWidth || 600;
    this.camera.aspect = w / 420;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, 420);
  }

  _loop() {
    if (!this.ready) return;
    requestAnimationFrame(() => this._loop());
    if (!this._animate) {
      this.renderer.render(this.scene, this.camera);
      return;
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }

  destroy() {
    this.ready = false;
    window.removeEventListener("resize", this._onResize);
    this.renderer?.dispose();
    this.container.innerHTML = "";
  }
}
