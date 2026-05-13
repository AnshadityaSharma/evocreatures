const generationSelectEl = document.querySelector("#generation-select");
const demoFrameCountEl = document.querySelector("#demo-frame-count");
let viewer3d = null;

function loadReplay(replayFilename) {
  const replayPath = `replays/${replayFilename}`;
  fetch(`${replayPath}?t=${Date.now()}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Unable to load replay: ${response.status}`);
      }
      return response.json();
    })
    .then((replay) => {
      demoFrameCountEl.textContent = replay.frames.length.toLocaleString();
      if (!viewer3d) {
        viewer3d = new Viewer3D('viewer-container');
      }
      viewer3d.loadReplay(replay);
    })
    .catch((error) => {
      console.error(error);
      demoFrameCountEl.textContent = "Error loading";
    });
}

// Initial load
loadReplay(generationSelectEl.value);

// Handle dropdown changes
generationSelectEl.addEventListener("change", (e) => {
  loadReplay(e.target.value);
});
