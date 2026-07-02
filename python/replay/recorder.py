"""Serialises an evaluation into a compact replay JSON for the web viewer.

Replay format (version 3)
-------------------------
The simulation is planar, so each part is described by an ``(x, y)`` position and
a single rotation angle about the out-of-plane axis::

    {
      "version": 3,
      "time_step": <seconds between recorded frames>,
      "parts":  { "part_0": {"shape": "box", "size": [w, h, depth]}, ... },
      "connections": [ {"parent": "part_0", "child": "part_1"}, ... ],
      "frames": [ {"t": <s>, "parts": [[x, y, angle], ...]}, ... ],
      "metadata": { ... generation stats for the UI ... }
    }
"""
from __future__ import annotations

import json
from pathlib import Path

from utils import config


def build_replay(result, metadata: dict) -> dict:
    parts = {}
    for i, (w, h) in enumerate(result.part_specs):
        parts[f"part_{i}"] = {"shape": "box", "size": [w, h, config.RENDER_DEPTH]}

    connections = [
        {"parent": "part_0", "child": f"part_{i}"}
        for i in range(1, len(result.part_specs))
    ]

    frames = [
        {"t": frame["t"], "parts": [[round(v, 4) for v in part] for part in frame["parts"]]}
        for frame in result.frames
    ]

    return {
        "name": "evolved_creature",
        "version": 3,
        "time_step": round(config.RECORD_EVERY * config.TIME_STEP, 5),
        "parts": parts,
        "connections": connections,
        "frames": frames,
        "metadata": metadata,
    }


def save_replay(replay: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(replay, separators=(",", ":")), encoding="utf-8")
