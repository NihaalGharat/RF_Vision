import * as THREE from "three";

const SHELLS = [
  { radius: 1.81, width: 27, height: 14, theta: 0.70, color: 0x18378c, order: 1.12 },
  { radius: 3.10, width: 21, height: 11, theta: 0.75, color: 0x102a68, order: 1.08 },
  { radius: 4.55, width: 20, height: 10, theta: 0.80, color: 0x10265f, order: 1.06 },
  { radius: 6.05, width: 20, height: 10, theta: 0.85, color: 0x0d1f54, order: 1.04 },
];
const FLOOR_N = 60;
const FLOOR_STEP = 0.52;
const FLOOR_CELL = 0.16;
const WAVES = {
  count: 3,
  minRadius: 0.22,
  maxRadius: 5.75,
  period: 3.8,
  color: 0x2a6cff,
};
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const rngFrom = (seed) => {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
};

function radialTexture(stops, size) {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
  for (const [at, color] of stops) g.addColorStop(at, color);
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, size, size);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function bodyMaterial(color, opacity = 1) {
  return new THREE.MeshBasicMaterial({
    color,
    transparent: opacity < 1,
    opacity,
    depthWrite: opacity >= 1,
    side: THREE.DoubleSide,
  });
}

export class ReferenceVisualLayer {
  constructor(scene) {
    this.scene = scene;
    this.group = new THREE.Group();
    this.group.visible = false;
    this.shells = [];
    this.floorCenters = [];
    this.floorWeights = [];
    this.textures = [];
    this.level = 0;
    this.stale = false;
    this.waveClock = 0;
    this.lastTick = null;
    this.bodyOn = false;
    this.visible = false;
    this.buildShells();
    this.buildFloor();
    this.buildEmitter();
    this.buildWaves();
    this.buildBody();
    scene.add(this.group);
  }

  track(texture) {
    this.textures.push(texture);
    return texture;
  }

  buildShells() {
    this.domeGroup = new THREE.Group();
    this.domeGroup.position.set(0.60, 2.55, 0);
    this.group.add(this.domeGroup);
    for (const spec of SHELLS) {
      const geometry = new THREE.SphereGeometry(
        spec.radius, spec.width, spec.height, 0, Math.PI * 2, 0, Math.PI * spec.theta);
      const material = new THREE.MeshBasicMaterial({
        color: spec.color,
        wireframe: true,
        depthWrite: false,
        depthTest: true,
        side: THREE.DoubleSide,
        fog: true,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.renderOrder = spec.order;
      this.domeGroup.add(mesh);
      this.shells.push({ mesh, material, baseColor: new THREE.Color(spec.color) });
    }
    const coreTexture = this.track(radialTexture([
      [0, "rgba(100, 246, 255, 0.44)"],
      [0.22, "rgba(36, 150, 255, 0.24)"],
      [0.58, "rgba(24, 65, 255, 0.08)"],
      [1, "rgba(0, 20, 80, 0)"],
    ], 256));
    this.core = new THREE.Sprite(new THREE.SpriteMaterial({
      map: coreTexture,
      color: 0x5ba7ff,
      transparent: true,
      opacity: 0.46,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    this.core.position.set(0.60, 2.70, 0);
    this.core.scale.set(5.2, 5.2, 1);
    this.core.renderOrder = 1.5;
    this.group.add(this.core);
  }

  buildFloor() {
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(52, 30),
      new THREE.MeshBasicMaterial({ color: 0x0f0c09, side: THREE.DoubleSide }),
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.set(0, -0.002, 3.0);
    floor.renderOrder = 0;
    this.group.add(floor);

    const rng = rngFrom(0x21d5a9);
    const geometry = new THREE.PlaneGeometry(1, 1);
    geometry.rotateX(-Math.PI / 2);
    const material = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      vertexColors: false,
      transparent: true,
      opacity: 0.92,
      depthWrite: false,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
    });
    this.floor = new THREE.InstancedMesh(geometry, material, FLOOR_N * FLOOR_N);
    this.floor.renderOrder = 3;
    this.floor.frustumCulled = false;
    const dummy = new THREE.Object3D();
    const color = new THREE.Color();
    let n = 0;
    for (let iz = 0; iz < FLOOR_N; iz += 1) {
      for (let ix = 0; ix < FLOOR_N; ix += 1) {
        if (rng() < 0.42) continue;
        const x = (ix - (FLOOR_N - 1) / 2) * FLOOR_STEP;
        const z = (iz - (FLOOR_N - 1) / 2) * FLOOR_STEP;
        dummy.position.set(x, 0.018, z);
        dummy.scale.set(FLOOR_CELL, 1, FLOOR_CELL);
        dummy.updateMatrix();
        this.floor.setMatrixAt(n, dummy.matrix);
        color.setRGB(0, 0, 0);
        this.floor.setColorAt(n, color);
        this.floorCenters.push([x, z]);
        this.floorWeights.push(0.2 + rng() * 0.8);
        n += 1;
      }
    }
    this.floor.count = n;
    this.floor.instanceMatrix.needsUpdate = true;
    if (this.floor.instanceColor) this.floor.instanceColor.needsUpdate = true;
    this.group.add(this.floor);
  }

  buildEmitter() {
    const pedestal = new THREE.Mesh(
      new THREE.BoxGeometry(0.84, 0.68, 0.72),
      new THREE.MeshStandardMaterial({ color: 0x4a3022, roughness: 0.78, metalness: 0.08 }),
    );
    pedestal.position.set(0.80, 1.52, 0.0);
    pedestal.renderOrder = 4;
    this.group.add(pedestal);

    const top = new THREE.Mesh(
      new THREE.PlaneGeometry(0.80, 0.68),
      new THREE.MeshBasicMaterial({ color: 0x8d6041 }),
    );
    top.rotation.x = -Math.PI / 2;
    top.position.set(0.80, 1.864, 0.0);
    top.renderOrder = 4.1;
    this.group.add(top);

    const edge = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(0.84, 0.68, 0.72)),
      new THREE.LineBasicMaterial({ color: 0x2d1b14, transparent: true, opacity: 0.72 }),
    );
    edge.position.copy(pedestal.position);
    edge.renderOrder = 4.2;
    this.group.add(edge);

    this.emitter = new THREE.Mesh(
      new THREE.SphereGeometry(0.038, 12, 10),
      new THREE.MeshBasicMaterial({ color: 0x5dff9a }),
    );
    this.emitter.position.set(0.87, 2.06, 0.0);
    this.emitter.renderOrder = 4.4;
    this.group.add(this.emitter);

    const glowTexture = this.track(radialTexture([
      [0, "rgba(114, 255, 156, 0.95)"],
      [0.18, "rgba(40, 255, 118, 0.52)"],
      [0.55, "rgba(20, 160, 88, 0.1)"],
      [1, "rgba(0, 80, 40, 0)"],
    ], 128));
    this.emitterGlow = new THREE.Sprite(new THREE.SpriteMaterial({
      map: glowTexture,
      color: 0x5dff9a,
      transparent: true,
      opacity: 0.92,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    this.emitterGlow.position.copy(this.emitter.position);
    this.emitterGlow.scale.set(0.22, 0.22, 1);
    this.emitterGlow.renderOrder = 4.5;
    this.group.add(this.emitterGlow);

    const poolTexture = this.track(radialTexture([
      [0, "rgba(255, 127, 54, 0.31)"],
      [0.45, "rgba(170, 79, 31, 0.12)"],
      [1, "rgba(80, 40, 15, 0)"],
    ], 256));
    this.warmPool = new THREE.Mesh(
      new THREE.PlaneGeometry(5.4, 5.4),
      new THREE.MeshBasicMaterial({
        map: poolTexture,
        transparent: true,
        opacity: 0.1,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
      }),
    );
    this.warmPool.rotation.x = -Math.PI / 2;
    this.warmPool.position.set(0.80, 0.022, 0.0);
    this.warmPool.renderOrder = 0.6;
    this.group.add(this.warmPool);
  }

  buildWaves() {
    this.waveGroup = new THREE.Group();
    this.waveGroup.position.copy(this.emitter.position);
    this.group.add(this.waveGroup);
    const geometry = new THREE.SphereGeometry(
      1, 24, 12, 0, Math.PI * 2, 0, Math.PI * 0.62);
    this.waves = [];
    for (let i = 0; i < WAVES.count; i += 1) {
      const material = new THREE.MeshBasicMaterial({
        color: WAVES.color,
        wireframe: true,
        transparent: true,
        opacity: 0,
        depthWrite: false,
        depthTest: true,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending,
        fog: true,
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.renderOrder = 1.02 + i * 0.002;
      this.waveGroup.add(mesh);
      this.waves.push({
        mesh,
        material,
        baseColor: new THREE.Color(WAVES.color),
        phase: i / WAVES.count,
      });
    }
  }

  buildBody() {
    this.body = new THREE.Group();
    this.body.position.set(3.36, 0, 2.0);
    this.body.scale.set(0.72, 0.79, 0.72);
    this.body.rotation.y = -0.24;
    this.body.visible = false;
    this.group.add(this.body);

    const cyan = bodyMaterial(0x00ffff, 1);
    const green = new THREE.MeshBasicMaterial({
      color: 0x18ff54,
      transparent: true,
      opacity: 0.72,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    const torso = new THREE.CapsuleGeometry(0.27, 1.08, 8, 20);
    torso.translate(0, 1.30, 0);
    const head = new THREE.SphereGeometry(0.245, 20, 16);
    head.translate(0, 2.07, 0);
    const legL = new THREE.CapsuleGeometry(0.105, 0.64, 6, 14);
    legL.translate(-0.11, 0.42, 0);
    const legR = new THREE.CapsuleGeometry(0.105, 0.64, 6, 14);
    legR.translate(0.11, 0.42, 0);
    const armL = new THREE.CapsuleGeometry(0.075, 0.72, 6, 12);
    armL.translate(-0.285, 1.25, 0);
    const armR = new THREE.CapsuleGeometry(0.075, 0.72, 6, 12);
    armR.translate(0.285, 1.25, 0);
    for (const geometry of [torso, head, legL, legR, armL, armR]) {
      const part = new THREE.Mesh(geometry, cyan);
      part.renderOrder = 6;
      this.body.add(part);
    }
    const glowGroup = new THREE.Group();
    glowGroup.scale.set(1.18, 1.07, 1.18);
    for (const geometry of [torso, head, legL, legR, armL, armR]) {
      const glow = new THREE.Mesh(geometry, green);
      glow.renderOrder = 5;
      glowGroup.add(glow);
    }
    this.body.add(glowGroup);

    const haloTexture = this.track(radialTexture([
      [0, "rgba(88, 255, 132, 0.54)"],
      [0.38, "rgba(34, 255, 110, 0.32)"],
      [0.72, "rgba(0, 150, 190, 0.11)"],
      [1, "rgba(0, 40, 70, 0)"],
    ], 256));
    const halo = new THREE.Sprite(new THREE.SpriteMaterial({
      map: haloTexture,
      color: 0x40ff7d,
      transparent: true,
      opacity: 1,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    halo.position.set(0, 1.2, -0.02);
    halo.scale.set(1.82, 3.32, 1);
    halo.renderOrder = 4.8;
    this.body.add(halo);

    const footTexture = this.track(radialTexture([
      [0, "rgba(76, 255, 136, 0.28)"],
      [0.5, "rgba(30, 150, 92, 0.09)"],
      [1, "rgba(0, 50, 30, 0)"],
    ], 256));
    const foot = new THREE.Mesh(
      new THREE.PlaneGeometry(2.4, 2.4),
      new THREE.MeshBasicMaterial({
        map: footTexture,
        transparent: true,
        opacity: 0.62,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
        side: THREE.DoubleSide,
      }),
    );
    foot.rotation.x = -Math.PI / 2;
    foot.position.set(0, 0.026, 0);
    foot.renderOrder = 3.6;
    this.body.add(foot);

    const hot = [
      [0.05, 2.19, 0.23, 0xff6b24, 0.026], [-0.08, 2.14, 0.22, 0xff3b1f, 0.024],
      [0.18, 1.94, 0.25, 0xff2c2c, 0.021], [-0.18, 1.92, 0.24, 0xff2c2c, 0.022],
      [0.05, 1.57, 0.29, 0xff6b24, 0.026], [0.29, 1.41, 0.21, 0xff8b2f, 0.021],
      [-0.27, 1.24, 0.21, 0xff7a24, 0.025], [0.12, 1.09, 0.29, 0xff3b1f, 0.020],
      [-0.17, 0.83, 0.25, 0xff6b24, 0.021], [0.17, 0.57, 0.2, 0xff3b1f, 0.021],
      [-0.16, 0.37, 0.18, 0xff6b24, 0.021], [0.1, 0.17, 0.16, 0xff3b1f, 0.019],
      [0.23, 2.02, 0.23, 0xffe0d0, 0.016], [-0.08, 0.99, 0.3, 0xffe4dc, 0.014],
      [0.18, 0.28, 0.17, 0xffd9d0, 0.013],
    ];
    const positions = new Float32Array(hot.length * 3);
    const colors = new Float32Array(hot.length * 3);
    const c = new THREE.Color();
    for (let i = 0; i < hot.length; i += 1) {
      const [x, y, z, hex, radius] = hot[i];
      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
      const spot = new THREE.Mesh(
        new THREE.SphereGeometry(radius * 1.25, 8, 6),
        new THREE.MeshBasicMaterial({ color: hex }),
      );
      spot.position.set(x, y, z);
      spot.renderOrder = 6.4;
      this.body.add(spot);
      c.setHex(hex);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }
    const hotGeo = new THREE.BufferGeometry();
    hotGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    hotGeo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const hotMap = this.track(radialTexture([
      [0, "rgba(255, 190, 120, 0.95)"],
      [0.24, "rgba(255, 100, 40, 0.6)"],
      [1, "rgba(255, 30, 10, 0)"],
    ], 64));
    const hotPoints = new THREE.Points(hotGeo, new THREE.PointsMaterial({
      vertexColors: true, size: 0.16, sizeAttenuation: true, map: hotMap,
      transparent: true, opacity: 0.86, depthWrite: false,
      blending: THREE.AdditiveBlending,
    }));
    hotPoints.renderOrder = 6.4;
    this.body.add(hotPoints);
  }

  setVisible(on) {
    this.visible = Boolean(on);
    this.group.visible = this.visible;
  }

  setBody(on) {
    this.bodyOn = Boolean(on);
    this.body.visible = this.visible && this.bodyOn;
  }

  setResponse({ a = 0, b = 0, stale = false } = {}) {
    const level = clamp(Math.max(Number(a) || 0, Number(b) || 0), 0, 1);
    this.level = Number.isFinite(level) ? level : 0;
    this.stale = Boolean(stale);
  }

  tick(now, animate = true) {
    if (!this.visible) return;
    const stamp = Number.isFinite(now) ? now : 0;
    if (animate) {
      const dt = this.lastTick == null ? 0 : clamp((stamp - this.lastTick) / 1000, 0, 0.1);
      this.waveClock += dt;
    }
    this.lastTick = stamp;
    const pulse = animate ? 0.5 + 0.5 * Math.sin(now * 0.00135) : 0.5;
    const dim = this.stale ? 0.26 : 1;
    const live = this.level * dim;
    for (const shell of this.shells) {
      const factor = (0.42 + 0.56 * live) * (this.stale ? 0.46 : 1) * (0.82 + 0.18 * pulse);
      shell.material.color.copy(shell.baseColor).multiplyScalar(factor);
    }
    this.domeGroup.scale.setScalar(1 + 0.0065 * pulse * dim);
    this.core.material.opacity = (0.22 + 0.32 * live) * (this.stale ? 0.4 : 1);
    this.emitterGlow.material.opacity = (0.68 + 0.24 * pulse) * (this.stale ? 0.35 : 1);
    this.updateWaves(pulse, dim, live);
    this.paintFloor(now, dim);
    this.body.visible = this.bodyOn;
  }

  updateWaves(pulse, dim, live) {
    const intensity = (0.075 + 0.44 * live) * (this.stale ? 0.45 : 1);
    const brightness = 0.62 + 0.38 * live;
    for (const wave of this.waves) {
      const t = ((this.waveClock / WAVES.period) + wave.phase) % 1;
      const radius = WAVES.minRadius + (WAVES.maxRadius - WAVES.minRadius) * t;
      const fadeIn = clamp(t / 0.14, 0, 1);
      const fadeOut = clamp((1 - t) / 0.26, 0, 1);
      wave.mesh.scale.setScalar(radius);
      wave.material.opacity = clamp(intensity * fadeIn * fadeOut * (0.82 + 0.18 * pulse), 0, 1);
      wave.material.color.copy(wave.baseColor).multiplyScalar(brightness * dim);
    }
  }

  paintFloor(now, dim) {
    if (!this.floor.instanceColor) return;
    const color = new THREE.Color();
    const phase = now * 0.0012;
    for (let i = 0; i < this.floorCenters.length; i += 1) {
      const wa = this.floorWeights[i];
      const [cx, cz] = this.floorCenters[i];
      const waveA = 0.5 + 0.5 * Math.sin(wa * 23 + phase * 2.1);
      const waveB = 0.5 + 0.5 * Math.sin(wa * 19 - phase * 1.7 + 1.2);
      const active = Math.max(0, waveA * 0.65 + waveB * 0.35 - 0.42) * this.level * dim;
      const dx = (cx - 3.0) / 3.8;
      const dz = (cz - 2.0) / 5.5;
      const edge = clamp(1.12 - Math.hypot(dx, dz), 0, 1);
      const depthFade = clamp((cz + 7) / 7, 0, 1);
      const nearFade = clamp((10.5 - cz) / 3, 0, 1);
      const signal = Math.pow(active * edge * depthFade * nearFade, 1.35);
      const bx = (cx - 2.6) / 12;
      const bz = (cz - 1.0) / 16;
      const baseEdge = clamp(1.25 - Math.hypot(bx, bz), 0, 1);
      const baseDepth = clamp((cz + 22) / 10, 0, 1);
      const baseNear = clamp((13 - cz) / 5, 0, 1);
      const base = 0.0072 * baseEdge * baseDepth * baseNear * (0.34 + 0.66 * wa) * (this.stale ? 0.55 : 1);
      color.setRGB(
        signal * 0.01 + base * 0.05,
        clamp(signal * 2.9 + base, 0, 0.95),
        signal * 0.016 + base * 0.12);
      this.floor.setColorAt(i, color);
    }
    this.floor.instanceColor.needsUpdate = true;
  }

  dispose() {
    this.scene.remove(this.group);
    const geometries = new Set();
    const materials = new Set();
    this.group.traverse((object) => {
      if (object.geometry) geometries.add(object.geometry);
      const list = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of list) if (material) materials.add(material);
    });
    for (const geometry of geometries) geometry.dispose();
    for (const material of materials) material.dispose();
    for (const texture of this.textures) texture.dispose();
    this.textures.length = 0;
    this.group.clear();
  }
}
