import json
from pathlib import Path


class ReplayRecorder:
    def __init__(self, time_step, creature):
        self.time_step = time_step
        self.creature = creature
        self.frames = []

    def record_frame(self, step):
        self.frames.append(
            {
                "step": step,
                "time": step * self.time_step,
                "parts": self.creature.body_transforms(),
                "joints": {
                    "hinge": {
                        "angle": self.creature.joint_angle(),
                    },
                },
            }
        )

    def save(self, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        replay = {
            "name": "phase1_simple_creature",
            "version": 1,
            "time_step": self.time_step,
            "parts": self.creature.parts,
            "frames": self.frames,
        }

        output_path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
        return output_path
