class Viewer3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.replay = null;
    this.currentFrame = 0;
    this.isPlaying = false;
    this.playbackSpeed = 0.25;
    this.frameAccumulator = 0;
    this.meshes = {};
    this.jointLines = [];  // visual connectors between parts
    
    this.partColors = [
      0x3b82f6, 0x8b5cf6, 0xf59e0b, 0x10b981,
      0xef4444, 0x06b6d4, 0xec4899, 0x84cc16,
    ];
    
    this.playPauseBtn = document.getElementById('btn-play-pause');
    this.resetBtn = document.getElementById('btn-reset');
    this.scrubber = document.getElementById('playback-scrubber');
    this.speedBtn = document.getElementById('btn-speed');
    this.frameCountEl = document.getElementById('demo-frame-count');
    
    this.initThree();
    this.bindEvents();
  }

  initThree() {
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x0a0a0c, 0.025);
    
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 200);
    this.camera.position.set(3, 2, 3);
    
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setClearColor(0x0a0a0c, 1);
    this.container.appendChild(this.renderer.domElement);
    
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.target.set(0, 0.4, 0);
    this.controls.minDistance = 0.5;
    this.controls.maxDistance = 15;
    
    // Lighting
    this.scene.add(new THREE.AmbientLight(0xffffff, 0.4));
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.85);
    dirLight.position.set(5, 8, 5);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 30;
    dirLight.shadow.camera.left = -8;
    dirLight.shadow.camera.right = 8;
    dirLight.shadow.camera.top = 8;
    dirLight.shadow.camera.bottom = -8;
    this.scene.add(dirLight);
    
    const fillLight = new THREE.DirectionalLight(0x6366f1, 0.12);
    fillLight.position.set(-3, -1, -3);
    this.scene.add(fillLight);
    
    // Ground
    const groundGeo = new THREE.PlaneGeometry(30, 30);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x111115, roughness: 0.95 });
    this.ground = new THREE.Mesh(groundGeo, groundMat);
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.receiveShadow = true;
    this.scene.add(this.ground);
    
    const grid = new THREE.GridHelper(30, 30, 0x1e1e2e, 0x1a1a28);
    grid.position.y = 0.003;
    this.scene.add(grid);
    
    window.addEventListener('resize', () => {
      if (!this.container) return;
      this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    });

    this.animate();
  }

  loadReplay(replayData) {
    this.replay = replayData;
    this.currentFrame = 0;
    this.frameAccumulator = 0;
    
    // Clear old meshes and joints
    Object.values(this.meshes).forEach(mesh => this.scene.remove(mesh));
    this.meshes = {};
    this.jointLines.forEach(line => this.scene.remove(line));
    this.jointLines = [];
    
    const parts = this.replay.parts;
    
    // Create body part meshes
    let partIndex = 0;
    for (const [partName, partData] of Object.entries(parts)) {
      if (partData.shape === 'box') {
        const [w, h, d] = partData.size;
        const geometry = new THREE.BoxGeometry(w, h, d);
        // Rounded edges via beveling would need BufferGeometry manipulation
        // Instead use slightly glossy material to make them look better
        const material = new THREE.MeshStandardMaterial({ 
          color: this.partColors[partIndex % this.partColors.length],
          roughness: 0.3,
          metalness: 0.35,
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        this.scene.add(mesh);
        this.meshes[partName] = mesh;
        partIndex++;
      }
    }
    
    // Create joint connector lines
    if (this.replay.connections) {
      for (const conn of this.replay.connections) {
        const points = [new THREE.Vector3(0,0,0), new THREE.Vector3(0,0,0)];
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ 
          color: 0x888888,
          linewidth: 2,
        });
        const line = new THREE.Line(geometry, material);
        line._parentPart = conn.parent;
        line._childPart = conn.child;
        this.scene.add(line);
        this.jointLines.push(line);
      }
    }
    
    // Setup UI
    this.scrubber.max = this.replay.frames.length - 1;
    this.scrubber.disabled = false;
    this.playPauseBtn.disabled = false;
    this.resetBtn.disabled = false;
    
    if (this.frameCountEl) {
      this.frameCountEl.textContent = this.replay.frames.length.toLocaleString();
    }
    
    if (this.replay.metadata) {
      const m = this.replay.metadata;
      this.updateStats(m.generation, m.fitness, m.population_size, m.num_parts);
      const titleEl = document.querySelector('.player-title');
      if (titleEl) {
        titleEl.textContent = `generation ${m.generation} — fitness ${m.fitness.toFixed(2)}m`;
      }
    }
    
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) loadingOverlay.style.display = 'none';
    
    this.updateFrame(0);
    this.play();
  }
  
  updateStats(generation, fitness, popSize, numParts) {
    const statValues = document.querySelectorAll('.stat-value');
    if (statValues.length >= 4) {
      statValues[0].textContent = generation;
      statValues[1].textContent = fitness.toFixed(2) + 'm';
      statValues[2].textContent = popSize;
      statValues[3].textContent = numParts;
    }
  }

  bindEvents() {
    this.playPauseBtn.addEventListener('click', () => {
      if (this.isPlaying) this.pause();
      else this.play();
    });
    
    this.resetBtn.addEventListener('click', () => {
      this.pause();
      this.updateFrame(0);
    });
    
    this.scrubber.addEventListener('input', (e) => {
      this.pause();
      this.updateFrame(parseInt(e.target.value));
    });
    
    if (this.speedBtn) {
      this.speedBtn.addEventListener('click', () => {
        const speeds = [0.1, 0.25, 0.5, 1.0];
        const labels = ['0.1x', '0.25x', '0.5x', '1x'];
        const currentIdx = speeds.indexOf(this.playbackSpeed);
        const nextIdx = (currentIdx + 1) % speeds.length;
        this.playbackSpeed = speeds[nextIdx];
        this.speedBtn.textContent = labels[nextIdx];
      });
    }
  }

  play() {
    this.isPlaying = true;
    this.playPauseBtn.textContent = 'Pause';
  }

  pause() {
    this.isPlaying = false;
    this.playPauseBtn.textContent = 'Play';
  }

  updateFrame(frameIndex) {
    if (!this.replay || !this.replay.frames[frameIndex]) return;
    this.currentFrame = frameIndex;
    this.scrubber.value = frameIndex;
    
    const frameData = this.replay.frames[frameIndex].parts;
    
    // Update body part positions
    for (const [partName, transform] of Object.entries(frameData)) {
      const mesh = this.meshes[partName];
      if (mesh) {
        // PyBullet Z-up to Three.js Y-up
        mesh.position.set(transform.position[0], transform.position[2], -transform.position[1]);
        const q = transform.orientation; 
        mesh.quaternion.set(q[0], q[2], -q[1], q[3]);
      }
    }
    
    // Update joint connector lines
    for (const line of this.jointLines) {
      const parentMesh = this.meshes[line._parentPart];
      const childMesh = this.meshes[line._childPart];
      if (parentMesh && childMesh) {
        const positions = line.geometry.attributes.position;
        positions.setXYZ(0, parentMesh.position.x, parentMesh.position.y, parentMesh.position.z);
        positions.setXYZ(1, childMesh.position.x, childMesh.position.y, childMesh.position.z);
        positions.needsUpdate = true;
      }
    }
    
    // Smooth camera follow
    if (this.meshes['part_0']) {
      this.controls.target.lerp(this.meshes['part_0'].position, 0.08);
    }
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    if (this.isPlaying && this.replay) {
      this.frameAccumulator += this.playbackSpeed;
      while (this.frameAccumulator >= 1.0) {
        this.frameAccumulator -= 1.0;
        let nextFrame = this.currentFrame + 1;
        if (nextFrame >= this.replay.frames.length) {
          nextFrame = 0;
        }
        this.updateFrame(nextFrame);
      }
    }
    
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
