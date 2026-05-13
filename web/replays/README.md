# Replay Format

Replay files are JSON exports from the Python simulation.

The browser does not run physics. It reads these frames and renders them with Three.js.

## Top Level
- `name`: replay name
- `version`: replay format version
- `time_step`: simulation time between frames
- `parts`: render metadata for each creature body part
- `frames`: recorded simulation frames

## Frame
Each frame contains:
- `step`: simulation step index
- `time`: elapsed simulation time in seconds
- `parts`: world transforms for each body part
- `joints`: joint state values, such as hinge angle

## Part Transform
Each part transform contains:
- `position`: `[x, y, z]`
- `orientation`: quaternion `[x, y, z, w]`
