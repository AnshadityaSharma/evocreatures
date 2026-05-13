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
                    "angles": self.creature.joint_angles(),
                },
            }
        )

    def get_replay_data(self):
        return {
            "name": "evolved_creature",
            "version": 2,
            "time_step": self.time_step,
            "parts": self.creature.parts,
            "frames": self.frames,
        }

    def save(self, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        replay = self.get_replay_data()
        output_path.write_text(json.dumps(replay, indent=2), encoding="utf-8")
        return output_path
