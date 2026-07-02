/**
 * Viewer3D — renders a recorded creature replay (format version 3) with Three.js.
 *
 * The simulation is planar: every part has an (x, y) position and a single
 * rotation angle about the out-of-plane (z) axis. Parts are drawn as 3D boxes
 * for depth and lighting, giving a polished "2.5D" look while staying faithful
 * to the 2D physics. The camera tracks the creature as it crawls along +x.
 */
class Viewer3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.replay = null;
    this.currentFrame = 0;
    this.isPlaying = false;
    this.playbackSpeed = 1.0;
    this.frameAccumulator = 0;
    this.meshes = [];

    // Warm gradient across the body, head (front) brightest.
    this.segmentColors = [
      0x22d3ee, 0x38bdf8, 0x60a5fa, 0x818cf8,
      0xa78bfa, 0xc084fc, 0xe879f9, 0xf472b6,
    ];

    this.onFrame = null; // callback(frameIndex, totalFrames)
    this.initThree();
  }

  initThree() {
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x0b0f1a, 0.018);

    this.camera = new THREE.PerspectiveCamera(48, w / h, 0.1, 400);
    this.camera.position.set(0, 2.2, 7);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(w, h);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setClearColor(0x000000, 0);
    this.container.appendChild(this.renderer.domElement);

    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.1;
    this.controls.minDistance = 2;
    this.controls.maxDistance = 30;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.02;

    // Lighting
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const key = new THREE.DirectionalLight(0xffffff, 1.0);
    key.position.set(6, 12, 8);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { near: 0.5, far: 60, left: -30, right: 30, top: 20, bottom: -20 });
    this.scene.add(key);
    const rim = new THREE.DirectionalLight(0x6366f1, 0.35);
    rim.position.set(-6, 4, -6);
    this.scene.add(rim);

    // Ground (horizontal XZ plane at y = 0)
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(600, 40),
      new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 1.0, metalness: 0.0 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);

    // Distance grid so forward progress is obvious. Lines every 1 m.
    this.grid = new THREE.GridHelper(600, 600, 0x1e293b, 0x172033);
    this.scene.add(this.grid);

    window.addEventListener('resize', () => this.onResize());
    this.animate = this.animate.bind(this);
    this.animate();
  }

  onResize() {
    if (!this.container) return;
    const w = this.container.clientWidth;
    const h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
  }

  loadReplay(replayData) {
    this.replay = replayData;
    this.currentFrame = 0;
    this.frameAccumulator = 0;

    this.meshes.forEach((m) => this.scene.remove(m));
    this.meshes = [];

    const specs = Object.values(replayData.parts);
    specs.forEach((spec, i) => {
      const [pw, ph, depth] = spec.size;
      const geo = new THREE.BoxGeometry(pw, ph, depth);
      const mat = new THREE.MeshStandardMaterial({
        color: this.segmentColors[i % this.segmentColors.length],
        roughness: 0.35,
        metalness: 0.4,
        emissive: this.segmentColors[i % this.segmentColors.length],
        emissiveIntensity: 0.06,
      });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      this.scene.add(mesh);
      this.meshes.push(mesh);
    });

    // Reset camera to the creature's starting position.
    const [sx] = replayData.frames[0].parts[0];
    this.camera.position.set(sx, 2.0, 6.5);
    this.controls.target.set(sx, 0.35, 0);
    this._lastCx = undefined;

    this.updateFrame(0);
  }

  updateFrame(frameIndex) {
    if (!this.replay) return;
    const frame = this.replay.frames[frameIndex];
    if (!frame) return;
    this.currentFrame = frameIndex;

    let cx = 0;
    frame.parts.forEach((part, i) => {
      const mesh = this.meshes[i];
      if (!mesh) return;
      const [x, y, angle] = part;
      mesh.position.set(x, y, 0);
      mesh.rotation.z = angle;
      cx += x;
    });
    cx /= frame.parts.length;

    // Follow the creature by translating the camera by exactly how far the body
    // moved this frame. This keeps framing rock-steady while preserving whatever
    // zoom and orbit angle the user has chosen.
    if (this._lastCx !== undefined) {
      this.camera.position.x += cx - this._lastCx;
    }
    this._lastCx = cx;
    this.controls.target.x = cx;
    this.controls.target.y = 0.35;

    if (this.onFrame) this.onFrame(frameIndex, this.replay.frames.length);
  }

  play() { this.isPlaying = true; }
  pause() { this.isPlaying = false; }
  reset() { this.updateFrame(0); }

  animate() {
    requestAnimationFrame(this.animate);
    if (this.isPlaying && this.replay) {
      this.frameAccumulator += this.playbackSpeed;
      while (this.frameAccumulator >= 1.0) {
        this.frameAccumulator -= 1.0;
        let next = this.currentFrame + 1;
        if (next >= this.replay.frames.length) next = 0;
        this.updateFrame(next);
      }
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
