# Project Phases

## Phase 1: Physics Foundation
- [x] Create physics world
- [x] Create fixed creature
- [x] Apply torque control
- [x] Verify simulation stability

## Phase 2: Replay Export
- [x] Record creature body transforms per frame
- [x] Export replay JSON from Python
- [x] Save replay files into `web/replays/`
- [x] Keep replay format simple and documented

## Phase 3: Public Website Foundation
- [x] Build static website structure
- [x] Add project description section
- [x] Add "how it works" pipeline section
- [x] Add technology stack section
- [x] Add project/demo section

## Phase 4: Three.js Replay Viewer
- [x] Modularize frontend JavaScript (separate 3D viewer logic from UI logic)
- [x] Load replay JSON in browser
- [x] Render torso and leg with Three.js
- [x] Animate exported frames
- [x] Add basic camera, lighting, and playback controls

## Phase 5: Sensors and Controller
- [x] Add simple creature sensors
- [x] Add oscillatory controller
- [x] Use controller outputs as joint torques
- [x] Export improved replay examples

## Phase 6: Genome and Mutation
- [x] Define genome structure
- [x] Add morphology parameters
- [x] Add controller parameters
- [x] Add mutation operators

## Phase 7: Fitness and Evolution
- [x] Measure distance traveled
- [x] Add fitness evaluation
- [x] Add mutation-only genetic algorithm loop
- [x] Save best creature replay

## Phase 8: Website Polish and Publishing
- [x] Add best evolved replay to website
- [x] Add screenshots or short demo clips if useful
- [x] Improve responsive layout
- [x] Prepare for static deployment
