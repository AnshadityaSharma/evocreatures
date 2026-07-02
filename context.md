# context.md — how EvoCreatures actually works

This document is the single source of truth for the codebase. Read it top to
bottom and you will understand **what every file does, why it exists, how the
pieces connect, and how the whole thing is hosted** — from first principles.

> TL;DR: Python runs a genetic algorithm + physics simulation *offline* and writes
> JSON files into `web/replays/`. A static website reads those JSON files and
> animates them in the browser. Vercel serves the `web/` folder. There is no
> live server and no database — just Python that generates data, and a webpage that
> plays it back.

---

## 1. The big picture (read this first)

There are **two completely separate programs** in this repo:

1. **The backend** (`python/`) — a normal Python program you run on your computer.
   It simulates creatures, evolves them, and saves the results as `.json` files.
   It runs once, produces files, and exits. It is *not* a web server.

2. **The frontend** (`web/`) — a plain website (HTML + CSS + JavaScript). It runs
   in a web browser. It does **no** physics and **no** evolution. It just loads the
   `.json` files the backend produced and draws them.

**How are they connected?** By files on disk. The backend *writes* JSON into
`web/replays/`. The frontend *reads* that same JSON. That folder of JSON files is
the entire "API" between them. Nothing else links the two.

```
   YOU run:  python main.py
                    │
                    ▼
     writes  web/replays/gen_0.json, gen_5.json, ..., gen_30.json, history.json
                    │
                    ▼
   Browser opens index.html  ──fetch()──▶  reads those JSON files  ──▶  animates them
```

This design is deliberate: physics is expensive and messy, so we do it once in
Python where it's easy; the browser only does the cheap, pretty part (drawing).

---

## 2. How hosting works (basic to basic)

The website is **static** — it's just files (`index.html`, `style.css`, two `.js`
files, and the `web/replays/*.json` data). Static files can be served by anything.

### Locally
A browser refuses to `fetch()` JSON from `file://` for security reasons, so you
can't just double-click `index.html`. You run a tiny local web server instead:

```bash
cd web
python -m http.server 8000     # serves the current folder on port 8000
```

Then open `http://localhost:8000`. `python -m http.server` is a one-line web
server built into Python — it just hands out the files in the folder.

### On the internet (Vercel)
Hosting is on **Vercel**, configured by [`vercel.json`](vercel.json) at the repo root.
Here's the whole story:

1. The repo is imported once into Vercel and linked to GitHub.
2. You `git push` to the `main` branch (Vercel's production branch).
3. Vercel sees the push and reads `vercel.json`, whose `"outputDirectory": "web"`
   tells it the static site lives in the **`web/` folder** (not the repo root).
4. Vercel publishes those files at `https://evocreatures.vercel.app/`.

So **deploying = pushing to main**. There is no build step and no server to manage;
`vercel.json` just points Vercel at `web/`. Because the site is static, Vercel (or
Netlify, S3, GitHub Pages, anything) could host it. The `python/` backend is *not*
deployed — it only ever runs on your machine to regenerate the JSON, which you then
commit.

> ⚠️ Important consequence: the replays you see online are whatever `web/replays/`
> contained **when you last pushed**. If you re-run `main.py` and want the new
> creatures online, you must commit the updated JSON and push again.

---

## 3. The data contract (the JSON files)

Everything hinges on two kinds of file the backend writes into `web/replays/`.

### `gen_<n>.json` — one recorded replay (the best creature of generation *n*)

```jsonc
{
  "name": "evolved_creature",
  "version": 3,
  "time_step": 0.0167,                       // seconds between recorded frames (~60 fps)
  "parts": {                                 // static description of each body part
    "part_0": { "shape": "box", "size": [0.30, 0.12, 0.34] },  // [width, height, depth]
    "part_1": { "shape": "box", "size": [0.30, 0.12, 0.34] },
    ...
  },
  "connections": [                           // which parts are hinged together (for reference)
    { "parent": "part_0", "child": "part_1" }, ...
  ],
  "frames": [                                // the animation, one entry per recorded moment
    { "t": 0.0,    "parts": [[x, y, angle], [x, y, angle], ...] },  // one [x,y,angle] per part
    { "t": 0.0167, "parts": [[x, y, angle], ...] },
    ...
  ],
  "metadata": {                              // stats shown in the UI for this generation
    "generation": 30, "fitness": 13.919, "distance": 21.0,
    "average_fitness": 2.809, "population_size": 50, "num_parts": 7,
    "mutation_rate": 0.152, "survival_rate": 0.42, "frequency": 2.663,
    "sim_seconds": 8.0
  }
}
```

The simulation is **2D**, so a part's position is just `(x, y)` and its rotation is
a single `angle` (radians) about the axis pointing out of the screen. That's why
each frame entry is a compact `[x, y, angle]` triple.

### `history.json` — metrics for every generation (drives the chart)

```jsonc
{
  "generations": [
    { "generation": 0, "best": 0.0, "average": 0.0, "median": 0.0,
      "worst": 0.0, "std": 0.44, "survival_rate": 0.16,
      "mutation_rate": 1.0, "best_distance": 8.78 },
    ...
  ],
  "saved_generations": [0, 5, 10, 15, 20, 25, 30],  // which gens have a gen_<n>.json replay
  "config": { "population_size": 50, "generations": 30, ... }
}
```

The frontend reads `history.json` first: it uses `saved_generations` to build the
dropdown, `generations[]` to draw the fitness chart, and `config` for the hero
numbers.

---

## 4. The backend, module by module (`python/`)

The backend is a small pipeline. Data flows:
`config → genome → creature → controller → evaluator → fitness`, orchestrated by
`ga.py`, and `main.py` ties it all together and writes the JSON.

### `utils/config.py` — every knob in one place
All tunable numbers: physics constants, the worm's body plan, motor strengths, the
CPG parameter ranges, fitness weights, and GA settings (population size,
generations, mutation, seed). Nothing else in the codebase hard-codes a magic
number — they all import from here. Change a value here and re-run to run a
different experiment.

### `genome/genome.py` — the creature's "brain" and how it breeds
A **genome** is the thing evolution acts on. Here it's a flat NumPy array of CPG
parameters (see the gene table in the README). This file provides:
- `Genome.random()` — a fresh random brain within the configured bounds.
- structured read-only views: `.frequency`, `.amplitudes`, `.phases`, `.centers`.
- `mutate(sigma, rng)` — returns a copy with small bounded Gaussian noise added to
  ~30% of genes; `sigma` scales the noise (annealed over the run).
- `crossover(a, b, rng)` — returns a child where each gene is copied from parent
  `a` or `b` at random (uniform crossover).

Storing genes as one array is what makes crossover/mutation trivial array ops.

### `simulation/physics.py` — the world
A thin wrapper around a `pymunk.Space` (the Chipmunk2D physics engine). Sets
gravity, solver quality, and adds a static ground segment. `step()` advances the
simulation by one fixed time step.

### `simulation/creature.py` — building the body
Builds the **segmented worm**: seven box bodies in a horizontal row, each joined to
the next by a `PivotJoint` (the hinge that holds them together) plus a
`SimpleMotor` (the muscle that rotates the joint). All segments share a collision
group so they don't collide with each other — only with the ground. Also exposes
helpers the rest of the code needs: `joint_angle(i)`, `centroid_x()`,
`has_launched()`, and `part_states()` (the `[x, y, angle]` list recorded into
replays).

The body plan is **identical for every creature** — only the genome differs. This
keeps the comparison fair: everyone gets the same body, evolution just finds a
better way to drive it.

### `simulation/controller.py` — turning genes into motion
The **CPG controller**. Given the genome and the current time `t`, it computes each
joint's target angle: `center + amplitude · sin(2π · frequency · t + phase)`. One
shared `frequency` is the "gait clock" that lets segments coordinate into a
travelling wave. It then drives pymunk's velocity motors with a proportional law so
they behave like position-controlled servos (move toward the target angle, limited
by a max speed and a max torque). Returns the motor effort used, which the fitness
function reads as an energy cost.

### `simulation/evaluator.py` — running one creature
Ties physics + creature + controller together. It:
1. builds a world and a creature,
2. steps the simulation for 8 seconds (1920 physics steps),
3. each step: asks the controller to drive the motors, advances physics, checks for
   a launch (airborne = stop early), and tracks forward distance + energy,
4. (optionally) samples `[x, y, angle]` for every part at 60 fps to record a replay,
5. returns an `EvalResult` with the fitness score, distance, and (if recording) the
   frames.

### `evolution/fitness.py` — what "good" means
A pure function: `fitness = max(0, forward_distance − 0.015·energy − launch_penalty)`.
This is the heart of *why* evolution produces real crawling instead of random
motion — see the README's fitness section for the full rationale. Kept separate
from the simulation so the scoring rule is easy to find and change.

### `evolution/ga.py` — the genetic algorithm loop
The `GeneticAlgorithm` class holds the population and does one generation at a time:
- `evaluate_population()` — score everyone, sort best-first.
- `record_stats()` — compute best/avg/median/worst/std/survival/mutation for the
  generation (this becomes a row in `history.json`).
- `next_generation()` — build the next population: keep the top **elites** unchanged,
  add a few random **immigrants** for diversity, and fill the rest with children bred
  by **tournament selection → crossover → mutation**.
- `_sigma()` — the annealing schedule that shrinks mutation strength over the run.

### `main.py` — the conductor
The entry point. It runs the GA for all generations, prints the live log, and every
few generations re-simulates the current best creature **with recording on** and
writes its `gen_<n>.json`. At the end it writes `history.json`. This is the only
file that touches disk / produces the frontend's input.

---

## 5. The frontend, file by file (`web/`)

### `index.html` — the page structure
Static markup for all sections (hero, pipeline, algorithm explanation, the live
demo, tech stack, footer). The demo section contains the empty containers the JS
fills in: the viewer `<div>`, the player controls, the generation dropdown/slider,
the `<canvas>` for the chart, and the stat boxes. It loads Three.js + OrbitControls
from a CDN, then `Viewer3D.js`, then `main.js`.

### `Viewer3D.js` — the 3D replay renderer
A small class wrapping Three.js. `initThree()` sets up the scene, camera, lights,
ground, and grid once. `loadReplay(data)` creates one 3D box mesh per part (sized
from `parts[].size`, coloured with a gradient). `updateFrame(i)` reads frame `i`'s
`[x, y, angle]` for each part and positions/rotates the matching mesh, then pans the
camera by exactly how far the creature moved so it stays centred while the user
keeps zoom/orbit control. `animate()` is the render loop; when playing it advances
frames at `playbackSpeed`.

### `main.js` — the glue
Everything interactive:
- On load, `fetch()`es `history.json`, builds the generation dropdown from
  `saved_generations`, and fills the hero numbers.
- `loadGeneration(n)` fetches `gen_<n>.json` (cached after first load), hands it to
  the viewer, updates the eight stat boxes from its `metadata`, and redraws the
  chart with a marker on generation *n*.
- `drawChart()` draws the fitness-over-generations line chart directly on a
  `<canvas>` (no chart library) — a teal "best" line and a violet "average" line.
- Wires the play/pause, restart, speed, scrubber, dropdown, and slider controls.

### `style.css` — the look
A restrained, monochrome dark theme: near-black background, off-white text, hairline
borders, one subtle teal accent used sparingly. Flat panels (no glow), generous
spacing, responsive grids. The colour in the experience comes from the 3D creature
itself, not the UI chrome.

---

## 6. End-to-end: what happens when you change something

**"I want faster creatures / a different experiment":**
1. Edit a value in `python/utils/config.py` (e.g. `SIM_SECONDS`, `MOTOR_MAX_FORCE`,
   `POPULATION_SIZE`, `GENERATIONS`, mutation rates).
2. `cd python && python main.py` → new `gen_*.json` + `history.json` in `web/replays/`.
3. `cd web && python -m http.server 8000` → open `localhost:8000` to review.
4. Happy? `git add -A && git commit && git push` → Vercel redeploys the new
   replays automatically.

**"I want to change how the site looks":** edit `web/style.css` / `web/index.html`,
refresh the browser. No rebuild — it's static.

**"I want a different creature or a smarter brain":** change `simulation/creature.py`
(body) and/or `simulation/controller.py` + `genome/genome.py` (brain). Keep the
`part_states()` → replay `[x, y, angle]` contract intact and the viewer keeps working
unchanged.

---

## 7. Reproducibility & determinism

`config.RANDOM_SEED` seeds a single `random.Random` used for population
initialisation, tournament selection, crossover, and mutation. NumPy randomness in
genome creation is derived from that same generator. As a result, `python main.py`
produces **identical** output every time. The shipped replays were generated with
`RANDOM_SEED = 21`, chosen (via a quick seed sweep) because it yields a smooth,
compelling fitness curve — the best fitness rises in clear steps and the population
average climbs steadily.
