# Evolving Virtual Creatures Project

## Goal
Build a Karl Sims inspired evolutionary locomotion system and present it through a public website so anyone can understand, inspect, and replay the work.

The system evolves:
- Creature morphology (body structure)
- Creature controllers

using:
- Genetic Algorithms
- Physics simulation in PyBullet
- Replay data exported from Python
- A browser-based Three.js viewer

The website should explain what the project is, how it works, what technologies it uses, and then let visitors view the actual simulation results.

---

## Public Website Goal

The website is the public face of the project.

It should include:
- A clear project description
- A simple explanation of evolutionary virtual creatures
- A visual explanation of the pipeline: genome -> creature -> physics simulation -> fitness -> evolution -> replay
- A technology section covering Python, PyBullet, NumPy, genetic algorithms, Three.js, HTML, CSS, and JavaScript
- A project/demo section where visitors can view exported creature replays
- A lightweight design that works on normal laptops and phones

The browser does not run physics.
It only displays explanations and replays motion data exported by the Python backend.

---

## Architecture

### Python Backend
Responsible for:
- Physics simulation
- Creature construction
- Torque/controller execution
- Sensors
- Genome mutation
- Fitness evaluation
- Evolution loop
- Replay JSON export

### Web Frontend
Responsible for:
- Project presentation
- Explaining how the simulator works
- Loading replay JSON files
- Rendering creature motion with Three.js
- Making the work easy to access and share publicly

---

## Tech Stack

### Backend
- Python 3.11
- PyBullet
- NumPy

### Frontend
- HTML
- CSS
- JavaScript
- Three.js

---

## Constraints

- Must run on weak laptop CPU
- No GPU assumptions for backend simulation
- Use PyBullet DIRECT mode for automated simulation
- Use PyBullet GUI only for local debugging and demonstration
- Keep body part count low initially
- Website must stay lightweight and static-host friendly
- Browser viewer replays exported data only

---

## Current Status

Phase 1 is complete.

Implemented:
- PyBullet physics world
- One fixed articulated creature
- Torso, one leg, one hinge joint
- Torque control
- Basic simulation verification

---

## Current File Structure

python/
    simulation/
    genome/
    evolution/
    replay/
    utils/

web/
    replays/

---

## Important Design Decisions

- Evolution and physics are offline in Python
- Replay system exports JSON frames
- Browser viewer replays motion only
- Mutation-only GA initially
- No crossover initially
- The public website should explain the system before showing the replay viewer
- Keep architecture modular and lightweight

---

## Future Features

- Sensors
- Oscillatory controllers
- Replay recording
- Three.js replay viewer
- Genome-based morphology
- Mutation operators
- Fitness evolution
- Terrain adaptation
- Public project website
