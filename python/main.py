import argparse
import math
import time
from pathlib import Path

from replay.recorder import ReplayRecorder
from simulation.creature_builder import create_simple_creature
from simulation.physics_world import PhysicsWorld
from simulation.sensors import CreatureSensors
from simulation.controller import OscillatoryController
from utils.config import SIMULATION_STEPS, TIME_STEP, TORQUE_FREQUENCY, TORQUE_STRENGTH


DEFAULT_REPLAY_PATH = Path(__file__).resolve().parents[1] / "web" / "replays" / "phase1_creature.json"


def run_phase_1(gui=False, replay_path=DEFAULT_REPLAY_PATH):
    world = PhysicsWorld(gui=gui)
    creature = create_simple_creature(world.client_id)
    recorder = ReplayRecorder(TIME_STEP, creature)
    
    sensors = CreatureSensors(creature)
    controller = OscillatoryController(num_sensors=3, num_outputs=1, amplitude=TORQUE_STRENGTH, frequency=TORQUE_FREQUENCY)

    start_position = creature.torso_position()
    min_angle = max_angle = creature.joint_angle()

    try:
        recorder.record_frame(0)

        for step in range(SIMULATION_STEPS):
            time_seconds = step * TIME_STEP
            
            # Phase 5: Sensor reading and Controller feedback
            sensor_data = sensors.get_state()
            torques = controller.get_torques(time_seconds, sensor_data)
            
            creature.apply_torque(torques[0])
            world.step()
            if gui:
                time.sleep(TIME_STEP)

            angle = creature.joint_angle()
            min_angle = min(min_angle, angle)
            max_angle = max(max_angle, angle)
            recorder.record_frame(step + 1)

        end_position = creature.torso_position()
        saved_replay_path = recorder.save(replay_path)
    finally:
        world.disconnect()

    print("Phase 1 simulation complete")
    print(f"Start torso position: {tuple(round(value, 3) for value in start_position)}")
    print(f"End torso position: {tuple(round(value, 3) for value in end_position)}")
    print(f"Hinge angle range: {round(min_angle, 3)} to {round(max_angle, 3)} radians")
    print(f"Replay frames exported: {len(recorder.frames)}")
    print(f"Replay file: {saved_replay_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Phase 1 creature simulation.")
    parser.add_argument("--gui", action="store_true", help="Show the PyBullet GUI while the simulation runs.")
    parser.add_argument("--replay-file", default=DEFAULT_REPLAY_PATH, type=Path, help="Path for exported replay JSON.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_phase_1(gui=args.gui, replay_path=args.replay_file)
