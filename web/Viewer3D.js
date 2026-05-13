class Viewer3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.replay = null;
    this.currentFrame = 0;
    this.isPlaying = false;
    this.playbackSpeed = 0.25; // Default to quarter speed so it's watchable
    this.frameAccumulator = 0;
    this.meshes = {};
    
    // Color palette for body parts
    this.partColors = [
      0x3b82f6, // blue — torso
      0x8b5cf6, // purple
      0xf59e0b, // amber
      0x10b981, // emerald
      0xef4444, // red
      0x06b6d4, // cyan
      0xec4899, // pink
      0x84cc16, // lime
    ];
    
    // UI elements
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
    this.scene.fog = new THREE.FogExp2(0x0a0a0c, 0.04);
    
    // Camera — further out so we can see the whole scene
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 200);
    this.camera.position.set(4, 3, 4);
    
    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.setClearColor(0x0a0a0c, 1);
    this.container.appendChild(this.renderer.domElement);
    
    // Controls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.08;
    this.controls.target.set(0, 0.5, 0);
    this.controls.minDistance = 1;
    this.controls.maxDistance = 20;
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.35);
    this.scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.9);
    dirLight.position.set(5, 10, 5);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    dirLight.shadow.camera.near = 0.5;
    dirLight.shadow.camera.far = 50;
    dirLight.shadow.camera.left = -10;
    dirLight.shadow.camera.right = 10;
    dirLight.shadow.camera.top = 10;
    dirLight.shadow.camera.bottom = -10;
    this.scene.add(dirLight);
    
    // Subtle fill light from below
    const fillLight = new THREE.DirectionalLight(0x6366f1, 0.15);
    fillLight.position.set(-3, -2, -3);
    this.scene.add(fillLight);
    
    // Ground plane
    const groundGeo = new THREE.PlaneGeometry(40, 40);
    const groundMat = new THREE.MeshStandardMaterial({ 
      color: 0x111115, 
      roughness: 0.9, 
      metalness: 0.1 
    });
    this.ground = new THREE.Mesh(groundGeo, groundMat);
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.receiveShadow = true;
    this.scene.add(this.ground);
    
    // Grid overlay on ground
    const grid = new THREE.GridHelper(40, 40, 0x1a1a2e, 0x1a1a2e);
    grid.position.y = 0.005;
    this.scene.add(grid);
    
    // Resize handler
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
    
    // Clear old meshes
    Object.values(this.meshes).forEach(mesh => this.scene.remove(mesh));
    this.meshes = {};
    
    const parts = this.replay.parts;
    
    // Create meshes for each body part
    let partIndex = 0;
    for (const [partName, partData] of Object.entries(parts)) {
      if (partData.shape === 'box') {
        const [w, h, d] = partData.size;
        const geometry = new THREE.BoxGeometry(w, h, d);
        // Round the edges slightly
        const material = new THREE.MeshStandardMaterial({ 
          color: this.partColors[partIndex % this.partColors.length],
          roughness: 0.35,
          metalness: 0.3,
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        this.scene.add(mesh);
        this.meshes[partName] = mesh;
        partIndex++;
      }
    }
    
    // Setup UI
    this.scrubber.max = this.replay.frames.length - 1;
    this.scrubber.disabled = false;
    this.playPauseBtn.disabled = false;
    this.resetBtn.disabled = false;
    
    // Update frame count
    if (this.frameCountEl) {
      this.frameCountEl.textContent = this.replay.frames.length.toLocaleString();
    }
    
    // Update stats from metadata
    if (this.replay.metadata) {
      const m = this.replay.metadata;
      this.updateStats(m.generation, m.fitness, m.population_size, m.num_parts);
    }
    
    // Update player title
    const titleEl = document.querySelector('.player-title');
    if (titleEl && this.replay.metadata) {
      titleEl.textContent = `generation ${this.replay.metadata.generation} — fitness ${this.replay.metadata.fitness}`;
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
    
    // Speed button cycles through speeds
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
    
    for (const [partName, transform] of Object.entries(frameData)) {
      const mesh = this.meshes[partName];
      if (mesh) {
        // PyBullet (Z up) to Three.js (Y up)
        mesh.position.set(transform.position[0], transform.position[2], -transform.position[1]);
        
        const q = transform.orientation; 
        const mappedQ = new THREE.Quaternion(q[0], q[2], -q[1], q[3]);
        mesh.quaternion.copy(mappedQ);
      }
    }
    
    // Follow the torso with camera target (smoothly)
    if (this.meshes['part_0']) {
      const torsoPos = this.meshes['part_0'].position;
      this.controls.target.lerp(torsoPos, 0.1);
    }
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    if (this.isPlaying && this.replay) {
      // Accumulate fractional frames based on playback speed
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
