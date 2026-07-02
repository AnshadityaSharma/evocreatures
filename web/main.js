/**
 * main.js — wires the replay viewer, generation controls, evolution chart and
 * live statistics together. Reads the metrics exported by the Python backend:
 *   - replays/history.json  : per-generation stats + list of saved generations
 *   - replays/gen_<n>.json  : recorded replay of each saved generation
 */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const els = {
    select: $("generation-select"),
    genSlider: $("generation-slider"),
    playPause: $("btn-play-pause"),
    reset: $("btn-reset"),
    speed: $("btn-speed"),
    scrubber: $("playback-scrubber"),
    frameTime: $("frame-time"),
    title: $("player-title"),
    badge: $("player-badge"),
    loading: $("loading-overlay"),
    chart: $("evolution-chart"),
  };

  const stats = {
    gen: $("s-gen"), best: $("s-best"), avg: $("s-avg"), dist: $("s-dist"),
    forward: $("s-forward"), mut: $("s-mut"), freq: $("s-freq"), pop: $("s-pop"),
  };

  const SPEEDS = [0.5, 1.0, 2.0, 4.0];
  let speedIdx = 1;

  let viewer = null;
  let history = null;
  let savedGens = [];
  let currentGen = null;
  const replayCache = new Map();

  // ---- data loading ------------------------------------------------------- //
  async function fetchJSON(path) {
    const res = await fetch(`${path}?t=${Date.now()}`);
    if (!res.ok) throw new Error(`${path}: ${res.status}`);
    return res.json();
  }

  async function loadGeneration(gen) {
    currentGen = gen;
    els.select.value = String(gen);
    els.genSlider.value = String(savedGens.indexOf(gen));

    let replay = replayCache.get(gen);
    if (!replay) {
      replay = await fetchJSON(`replays/gen_${gen}.json`);
      replayCache.set(gen, replay);
    }
    if (!viewer) viewer = new Viewer3D("viewer-container");
    viewer.loadReplay(replay);
    viewer.playbackSpeed = SPEEDS[speedIdx];
    viewer.play();
    setPlayLabel(true);

    els.loading.style.display = "none";
    updateStats(replay.metadata);
    drawChart(gen);
  }

  // ---- statistics --------------------------------------------------------- //
  function updateStats(m) {
    els.title.textContent = `Generation ${m.generation}`;
    els.badge.textContent = m.fitness > 0 ? `fitness ${m.fitness.toFixed(1)}` : "no forward motion yet";
    els.badge.classList.toggle("badge-zero", m.fitness <= 0);

    stats.gen.textContent = m.generation;
    stats.best.textContent = m.fitness.toFixed(2);
    stats.avg.textContent = m.average_fitness.toFixed(2);
    stats.dist.textContent = `${m.distance.toFixed(1)} m`;
    stats.forward.textContent = `${Math.round(m.survival_rate * 100)}%`;
    stats.mut.textContent = m.mutation_rate.toFixed(2);
    stats.freq.textContent = `${m.frequency.toFixed(2)} Hz`;
    stats.pop.textContent = m.population_size;
  }

  // ---- evolution chart (dependency-free canvas line chart) ---------------- //
  function drawChart(highlightGen) {
    const c = els.chart;
    const ctx = c.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const W = c.clientWidth || 480, H = c.clientHeight || 240;
    if (c.width !== W * dpr) { c.width = W * dpr; c.height = H * dpr; }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);

    const gens = history.generations;
    const pad = { l: 34, r: 12, t: 14, b: 24 };
    const plotW = W - pad.l - pad.r;
    const plotH = H - pad.t - pad.b;
    const maxG = gens.length - 1;
    const maxY = Math.max(1, ...gens.map((g) => g.best)) * 1.1;

    const xOf = (gen) => pad.l + (gen / maxG) * plotW;
    const yOf = (v) => pad.t + plotH - (v / maxY) * plotH;

    // grid + axis labels
    ctx.strokeStyle = "rgba(148,163,184,0.12)";
    ctx.fillStyle = "rgba(148,163,184,0.6)";
    ctx.font = "10px Inter, sans-serif";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const v = (maxY / 4) * i;
      const y = yOf(v);
      ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(W - pad.r, y); ctx.stroke();
      ctx.fillText(v.toFixed(0), 6, y + 3);
    }
    ctx.textAlign = "center";
    for (let g = 0; g <= maxG; g += Math.ceil(maxG / 6)) {
      ctx.fillText(g, xOf(g), H - 8);
    }
    ctx.textAlign = "start";

    // highlight marker for the selected generation
    const hx = xOf(highlightGen);
    ctx.strokeStyle = "rgba(226,232,240,0.35)";
    ctx.setLineDash([4, 4]);
    ctx.beginPath(); ctx.moveTo(hx, pad.t); ctx.lineTo(hx, pad.t + plotH); ctx.stroke();
    ctx.setLineDash([]);

    const line = (key, color, fill) => {
      ctx.beginPath();
      gens.forEach((g, i) => {
        const x = xOf(g.generation), y = yOf(g[key]);
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      if (fill) {
        ctx.lineTo(xOf(maxG), yOf(0)); ctx.lineTo(xOf(0), yOf(0)); ctx.closePath();
        ctx.fillStyle = fill; ctx.fill();
        ctx.beginPath();
        gens.forEach((g, i) => {
          const x = xOf(g.generation), y = yOf(g[key]);
          i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        });
      }
      ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.stroke();
    };
    line("best", "#7fe7d4", "rgba(127,231,212,0.08)");
    line("average", "#b8a6ff", null);

    // dot on the best-fitness line at the selected generation
    const hg = gens.find((g) => g.generation === highlightGen);
    if (hg) {
      ctx.fillStyle = "#7fe7d4";
      ctx.beginPath(); ctx.arc(hx, yOf(hg.best), 4, 0, Math.PI * 2); ctx.fill();
    }
  }

  // ---- controls ----------------------------------------------------------- //
  function setPlayLabel(playing) {
    els.playPause.innerHTML = playing ? "&#10073;&#10073;&nbsp;Pause" : "&#9654;&nbsp;Play";
  }

  function bindControls() {
    els.playPause.addEventListener("click", () => {
      if (!viewer) return;
      viewer.isPlaying ? viewer.pause() : viewer.play();
      setPlayLabel(viewer.isPlaying);
    });
    els.reset.addEventListener("click", () => viewer && viewer.reset());
    els.speed.addEventListener("click", () => {
      speedIdx = (speedIdx + 1) % SPEEDS.length;
      els.speed.textContent = `${SPEEDS[speedIdx]}×`;
      if (viewer) viewer.playbackSpeed = SPEEDS[speedIdx];
    });
    els.scrubber.addEventListener("input", (e) => {
      if (!viewer) return;
      viewer.pause(); setPlayLabel(false);
      viewer.updateFrame(parseInt(e.target.value, 10));
    });
    els.select.addEventListener("change", (e) => loadGeneration(parseInt(e.target.value, 10)));
    els.genSlider.addEventListener("input", (e) => loadGeneration(savedGens[parseInt(e.target.value, 10)]));
    window.addEventListener("resize", () => history && drawChart(currentGen));
  }

  // ---- bootstrap ---------------------------------------------------------- //
  async function init() {
    bindControls();
    history = await fetchJSON("replays/history.json");
    savedGens = history.saved_generations.slice().sort((a, b) => a - b);

    els.select.innerHTML = savedGens.map((g) => {
      const label = g === 0 ? "Generation 0 — random start"
        : g === savedGens[savedGens.length - 1] ? `Generation ${g} — best evolved` : `Generation ${g}`;
      return `<option value="${g}">${label}</option>`;
    }).join("");
    els.genSlider.max = String(savedGens.length - 1);
    els.genSlider.value = String(savedGens.length - 1);

    // hero metrics
    const first = history.generations[0].best_distance;
    const last = history.generations[history.generations.length - 1].best_distance;
    $("hero-gens").textContent = history.config.generations;
    $("hero-pop").textContent = history.config.population_size;
    $("hero-gain").textContent = `${(last - first >= 0 ? "+" : "")}${(last - first).toFixed(0)} m`;

    // viewer frame -> scrubber/time sync
    viewer = new Viewer3D("viewer-container");
    viewer.onFrame = (idx, total) => {
      els.scrubber.max = String(total - 1);
      els.scrubber.value = String(idx);
      if (currentGen != null && replayCache.has(currentGen)) {
        els.frameTime.textContent = (idx * replayCache.get(currentGen).time_step).toFixed(1);
      }
    };

    await loadGeneration(savedGens[savedGens.length - 1]);
  }

  init().catch((err) => {
    console.error(err);
    els.title.textContent = "Failed to load replays";
    els.loading.querySelector("p").textContent = "Could not load replay data.";
  });
})();
