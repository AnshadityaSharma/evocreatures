class Viewer3D {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.replay = null;
    this.currentFrame = 0;
    this.isPlaying = false;
    this.meshes = {};
    
    // UI elements
    this.playPauseBtn = document.getElementById('btn-play-pause');
    this.resetBtn = document.getElementById('btn-reset');
    this.scrubber = document.getElementById('playback-scrubber');
    
    this.initThree();
    this.bindEvents();
  }

  initThree() {
    this.scene = new THREE.Scene();
    
    // Camera
    const aspect = this.container.clientWidth / this.container.clientHeight;
    this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 100);
    this.camera.position.set(3, 2, 3);
    
    // Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    this.renderer.setPixelRatio(window.devicePixelRatio);
    this.renderer.shadowMap.enabled = true;
    this.container.appendChild(this.renderer.domElement);
    
    // Controls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.target.set(0, 0, 0);
    
    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
    this.scene.add(ambientLight);
    
    const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight.position.set(5, 10, 5);
    dirLight.castShadow = true;
    this.scene.add(dirLight);
    
    // Grid
    const grid = new THREE.GridHelper(10, 10, 0x06b6d4, 0x222222);
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
    
    // Clear old meshes if any
    Object.values(this.meshes).forEach(mesh => this.scene.remove(mesh));
    this.meshes = {};
    
    const parts = this.replay.parts;
    
    // Create meshes based on parts
    for (const [partName, partData] of Object.entries(parts)) {
      if (partData.shape === 'box') {
        // The JSON exported size is already full extents, so pass directly to Three.js BoxGeometry
        const [w, h, d] = partData.size;
        const geometry = new THREE.BoxGeometry(w, h, d);
        const material = new THREE.MeshStandardMaterial({ 
          color: partName === 'torso' ? 0x3b82f6 : 0x8b5cf6,
          roughness: 0.3,
          metalness: 0.2
        });
        const mesh = new THREE.Mesh(geometry, material);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        this.scene.add(mesh);
        this.meshes[partName] = mesh;
      }
    }
    
    // Setup UI
    this.scrubber.max = this.replay.frames.length - 1;
    this.scrubber.disabled = false;
    this.playPauseBtn.disabled = false;
    this.playPauseBtn.classList.remove('disabled');
    this.resetBtn.disabled = false;
    this.resetBtn.classList.remove('disabled');
    
    document.getElementById('loading-overlay').style.display = 'none';
    
    this.updateFrame(0);
    this.play();
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
    
    // Follow the torso with camera target
    if (this.meshes['torso']) {
        this.controls.target.copy(this.meshes['torso'].position);
    }
  }

  animate() {
    requestAnimationFrame(this.animate.bind(this));
    
    if (this.isPlaying && this.replay) {
      let nextFrame = this.currentFrame + 1;
      if (nextFrame >= this.replay.frames.length) {
        nextFrame = 0; // Loop
      }
      this.updateFrame(nextFrame);
    }
    
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
