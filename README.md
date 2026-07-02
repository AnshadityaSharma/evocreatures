# 🧬 EvoCreatures — Evolving Virtual Creatures

> A population of virtual creatures that **teach themselves to move** using a genetic algorithm and 2D rigid-body physics. No motion is scripted — coordinated locomotion emerges, generation after generation, from selection and mutation alone.

**Live demo:** https://anshadityasharma.github.io/evocreatures/

Inspired by Karl Sims' 1994 *Evolved Virtual Creatures*, this project shows a real, reproducible genetic algorithm in action and presents the results in an interactive browser viewer.

---

## Table of contents

- [What it does](#what-it-does)
- [Features](#features)
- [How it works — the evolution pipeline](#how-it-works--the-evolution-pipeline)
- [The genetic algorithm](#the-genetic-algorithm)
- [The fitness function](#the-fitness-function)
- [Architecture](#architecture)
- [Technologies used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Folder structure](#folder-structure)
- [Technical implementation details](#technical-implementation-details)
- [Future improvements](#future-improvements)

---

## What it does

Every creature is a **segmented worm** — a chain of seven boxes joined by motorised
hinges. The body plan is identical for every creature; what differs is its
**brain**: a small set of numbers (a *genome*) that controls how each joint moves.

The genetic algorithm:

1. Simulates a whole population of creatures in a physics world.
2. Scores each one on how far it crawls to the right.
3. Breeds the winners and mutates their offspring.
4. Repeats for 30 generations.

The result is a clear, watchable progression: generation 0 creatures thrash
uselessly and go nowhere; by generation 30 they have discovered a smooth,
coordinated undulating gait that travels **~21 metres** in 8 seconds.

<!-- SCREENSHOT: drop a screen-capture of the evolved worm mid-crawl here -->

---

## Features

- **Genuine, observable evolution** — best *and* average fitness climb over
  generations; the improvement is visible both in the numbers and in the motion.
- **Meaningful selection pressure** — directional fitness with anti-exploit
  safeguards, so spinning/hopping tricks score zero and real crawling wins.
- **Interactive 3D replay viewer** — scrub, play, change speed, and step through
  every saved generation to compare gaits side by side.
- **Live evolution chart** — a fitness-over-generations graph rendered in-browser.
- **Full metrics dashboard** — generation, best/average fitness, distance,
  forward-mover rate, mutation rate, gait frequency, and population size.
- **Fully reproducible** — a fixed random seed makes every run identical.
- **Zero-dependency frontend** — static HTML/CSS/JS + Three.js from a CDN; hosts
  anywhere (GitHub Pages, Netlify, or any static server).

---

## How it works — the evolution pipeline

```
 ┌─────────┐   ┌────────────┐   ┌──────────┐   ┌─────────┐   ┌──────────────┐   ┌─────────┐
 │ Genome  │──▶│ Build body │──▶│ Simulate │──▶│ Fitness │──▶│ Select+breed │──▶│ Replay  │
 │ (CPG    │   │ in pymunk  │   │ 8 s of   │   │ score   │   │ tournament + │   │ JSON →  │
 │ params) │   │            │   │ physics  │   │ distance│   │ crossover    │   │ Three.js│
 └─────────┘   └────────────┘   └──────────┘   └─────────┘   └──────┬───────┘   └─────────┘
       ▲                                                             │
       └──────────────────────── next generation ───────────────────┘
```

Everything except the final replay runs **offline in Python**. The browser never
runs physics — it only plays back the recorded motion the backend exports as JSON.

---

## The genetic algorithm

Each creature's brain is a **central pattern generator (CPG)**: every joint follows
a sine wave, and one shared frequency acts as a single "gait clock" so the
segments can lock into a coordinated travelling wave.

A genome is a flat vector of these parameters:

| Gene            | Count | Meaning                                        |
|-----------------|-------|------------------------------------------------|
| `frequency`     | 1     | shared gait frequency (Hz)                     |
| `amplitude[i]`  | 6     | swing size of joint *i* (rad)                  |
| `phase[i]`      | 6     | timing offset of joint *i* (rad)               |
| `center[i]`     | 6     | rest-angle offset of joint *i* (rad)           |

The GA loop uses four classic ingredients:

- **Tournament selection** — pick 5 creatures at random, keep the fittest as a
  parent. Fitter creatures win more tournaments, so their genes spread.
- **Elitism** — the best 3 genomes are copied unchanged into the next generation,
  so progress is never lost to unlucky mutation.
- **Uniform crossover** — two parents are recombined gene-by-gene, letting good
  "half-solutions" from different lineages combine.
- **Annealed Gaussian mutation** — genes get small random nudges whose strength
  starts large (broad exploration) and shrinks each generation (fine-tuning).
  This is why improvement is *gradual* rather than random.

A few **random immigrants** are also injected each generation to keep the gene
pool diverse and stop the search stalling in a local optimum.

---

## The fitness function

Fitness rewards **efficient forward crawling** and nothing else:

```
fitness = max(0, forward_distance − 0.015 · energy − launch_penalty)
```

- **`forward_distance`** — rightward (+x) displacement of the body's centroid.
- **`energy`** — total motor effort; a small penalty favours smooth, efficient
  gaits over frantic thrashing.
- **`launch_penalty`** — if a violent gait flings the worm airborne, the
  evaluation stops and a flat penalty applies, so physically implausible
  "exploits" can never out-score real crawling.
- **Floored at zero** — creatures that crawl backwards or wiggle in place are all
  equally unfit, which keeps selection focused on the forward gradient and makes
  the population's *average* fitness a clean measure of progress.

This directional, exploit-resistant design is the key fix for the classic failure
mode where creatures wander, spin, or spiral without ever really moving.

---

## Architecture

The project is split into an **offline Python backend** and a **static web frontend**
connected by a single, simple contract: **JSON files**.

```
   PYTHON BACKEND (offline)                         WEB FRONTEND (browser)
   ────────────────────────                         ──────────────────────
   evolve population ─┐
                      ├─▶ web/replays/gen_<n>.json ──▶ Three.js replay viewer
   record best of  ───┘                              │
   each generation                                   │
                                                      │
   collect metrics ────▶ web/replays/history.json ──▶ evolution chart + stats
```

The backend writes replay + history JSON into `web/replays/`. The frontend
`fetch()`es those files and renders them. There is **no server-side code at
runtime** — the site is 100% static. See [`context.md`](context.md) for a line-by-line
walkthrough of every module and the exact JSON schema.

---

## Technologies used

| Layer      | Tech            | Role                                             |
|------------|-----------------|--------------------------------------------------|
| Backend    | **Python 3**    | Evolution loop, genome, fitness, orchestration   |
| Physics    | **pymunk**      | Chipmunk2D rigid-body engine (joints, motors)    |
| Compute    | **NumPy**       | Vectorised gene storage and operators            |
| Frontend   | **Three.js**    | WebGL rendering of the recorded replays          |
| Frontend   | **Vanilla JS**  | Controls, stats, and the canvas evolution chart  |
| Hosting    | **GitHub Pages**| Static hosting via GitHub Actions                |

---

## Installation

**Requirements:** Python 3.9+ (works on 3.9–3.13) and pip. No compiler or GPU needed.

```bash
# 1. Clone
git clone https://github.com/AnshadityaSharma/evocreatures.git
cd evocreatures

# 2. Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Run the evolution (backend)

```bash
cd python
python main.py
```

This evolves the population and writes fresh replays + `history.json` into
`web/replays/`. It prints a live log:

```
Gen   0 | best   0.000 | avg   0.000 | dist   6.92m | forward   0%
Gen   5 | best   1.278 | avg   0.026 | dist   8.27m | forward   2%
...
Gen  30 | best  13.919 | avg   2.809 | dist  21.00m | forward  42%
```

### View the results (frontend)

The browser must load the JSON over HTTP (not `file://`), so serve the `web/`
folder with any static server:

```bash
cd web
python -m http.server 8000
# then open http://localhost:8000
```

### Tune the experiment

Every knob lives in [`python/utils/config.py`](python/utils/config.py) —
population size, generations, mutation rates, body shape, physics constants, and
the fitness weights. Change a value, re-run `main.py`, and refresh the page.

---

## Folder structure

```
evolving-virtual-creatures/
├── python/                     # offline backend
│   ├── main.py                 # entry point: runs the GA, exports replays + history
│   ├── genome/
│   │   └── genome.py           # genome vector + crossover/mutation operators
│   ├── simulation/
│   │   ├── physics.py          # pymunk world (gravity + ground)
│   │   ├── creature.py         # builds the segmented worm from the body plan
│   │   ├── controller.py       # CPG: genome → joint motor commands
│   │   └── evaluator.py        # runs one creature, returns fitness (+ replay frames)
│   ├── evolution/
│   │   ├── fitness.py          # the fitness function
│   │   └── ga.py               # selection, crossover, mutation, evolve loop
│   ├── replay/
│   │   └── recorder.py         # serialises an evaluation to replay JSON
│   └── utils/
│       └── config.py           # every tunable parameter
├── web/                        # static frontend (this folder is what gets hosted)
│   ├── index.html
│   ├── style.css
│   ├── main.js                 # controls, stats, evolution chart, data loading
│   ├── Viewer3D.js             # Three.js replay renderer
│   └── replays/                # generated: gen_<n>.json + history.json
├── .github/workflows/deploy.yml# GitHub Pages deployment
├── requirements.txt
├── README.md
└── context.md                  # deep-dive: how every part works and connects
```

---

## Technical implementation details

- **Why a 2D worm?** A creature lying flat on the ground cannot topple, which makes
  "survival" trivial and lets the GA focus entirely on *speed and coordination*.
  This produces a far more convincing, monotonic evolution story than a legged
  creature that spends most of its effort just trying not to fall over.
- **2.5D rendering.** Physics is strictly planar (each part is an `(x, y, angle)`),
  but the viewer draws each part as a 3D box with depth and shadows, so it looks
  polished without any 3D physics cost.
- **Servo-style motors.** pymunk exposes *velocity* motors. The controller turns
  them into *position* control with a proportional law: commanded joint speed is
  proportional to the error between the current and target angle, clamped, and
  each motor has a torque ceiling.
- **Deterministic runs.** A single seeded `random.Random` drives population init,
  selection, crossover, and mutation, so results are byte-for-byte reproducible.
- **Compact replays.** Physics runs at 240 Hz for stability but replays are sampled
  at 60 Hz and stored with rounded floats to keep the JSON small.

For the full walkthrough — schemas, data flow, and how hosting works — read
[`context.md`](context.md).

---

## Future improvements

- **Co-evolve morphology** — let segment count, lengths, and masses evolve
  alongside the controller (closer to Karl Sims' original).
- **Sensory feedback** — add ground-contact sensors so gaits can adapt to terrain.
- **Harder environments** — slopes, obstacles, and gaps to select for robustness.
- **In-browser evolution** — port the physics to WebAssembly to run the GA live.
- **Neural controllers** — replace the CPG with a small recurrent network.
- **Speciation / novelty search** — maintain diverse gaits instead of converging
  on one.

---

## Credits

Inspired by **Karl Sims, *Evolved Virtual Creatures* (SIGGRAPH 1994)**.
Built with Python, pymunk, NumPy, and Three.js.
