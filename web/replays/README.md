# Replay data (generated)

These JSON files are **generated** by the Python backend (`python/main.py`) — do
not edit them by hand. The browser does not run physics; it reads these files and
renders them with Three.js. See [`../../context.md`](../../context.md) for the full
data contract.

- `gen_<n>.json` — recorded replay of the best creature at generation `n`.
- `history.json` — per-generation metrics used to draw the evolution chart.

## Replay format (version 3)

The simulation is 2D, so each part has an `(x, y)` position and one rotation
`angle` (radians).

| Field         | Meaning                                                        |
|---------------|----------------------------------------------------------------|
| `version`     | replay format version (3)                                      |
| `time_step`   | seconds between recorded frames (~1/60)                        |
| `parts`       | `{ "part_i": { "shape": "box", "size": [w, h, depth] } }`      |
| `connections` | `[{ "parent": "part_0", "child": "part_1" }, ...]` (reference) |
| `frames`      | `[{ "t": seconds, "parts": [[x, y, angle], ...] }, ...]`       |
| `metadata`    | generation stats displayed in the UI                          |
