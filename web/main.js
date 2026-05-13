const replayPath = "replays/phase1_creature.json";

const demoFrameCountEl = document.querySelector("#demo-frame-count");
let viewer3d = null;

function initializeApp(replay) {
  // Update text stats
  demoFrameCountEl.textContent = replay.frames.length.toLocaleString();

  // Initialize the true 3D Viewer
  viewer3d = new Viewer3D('viewer-container');
  viewer3d.loadReplay(replay);
}

fetch(`${replayPath}?t=${Date.now()}`)
  .then((response) => {
    if (!response.ok) {
      throw new Error(`Unable to load replay: ${response.status}`);
    }
    return response.json();
  })
  .then(initializeApp)
  .catch((error) => {
    console.error(error);
    demoFrameCountEl.textContent = "Error";
  });
