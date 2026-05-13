from simulation.physics_world import PhysicsWorld
from simulation.creature_builder import build_creature_from_genome
from simulation.sensors import DynamicSensors
from simulation.controller import GenomeController
from utils.config import SIMULATION_STEPS, TIME_STEP
import math

def evaluate_fitness(genome, gui=False):
    world = PhysicsWorld(gui=gui)
    creature = build_creature_from_genome(genome, world.client_id)
    
    if not creature:
        world.disconnect()
        return 0.0
        
    sensors = DynamicSensors(creature)
    controller = GenomeController(genome)
    
    start_pos = creature.torso_position()
    
    height_sum = 0.0
    max_height = start_pos[2]
    angular_vel_sum = 0.0
    
    for step in range(SIMULATION_STEPS):
        time_seconds = step * TIME_STEP
        sensor_data = sensors.get_state()
        targets = controller.get_target_angles(time_seconds, sensor_data)
        creature.set_joint_positions(targets)
        world.step()
        
        pos = creature.torso_position()
        height_sum += pos[2]
        max_height = max(max_height, pos[2])
        
        # Track torso spin
        _, ang_vel = creature.torso_velocity()
        angular_vel_sum += math.sqrt(ang_vel[0]**2 + ang_vel[1]**2 + ang_vel[2]**2)
        
    end_pos = creature.torso_position()
    world.disconnect()
    
    # --- FITNESS ---
    
    # 1. Horizontal distance traveled (any direction)
    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]
    horiz_distance = math.sqrt(dx*dx + dy*dy)
    
    # 2. Height penalty: heavily punish flying
    avg_height = height_sum / SIMULATION_STEPS
    height_penalty = 0.0
    if max_height > 1.5:
        height_penalty = (max_height - 1.5) * 10.0
    if avg_height > 1.0:
        height_penalty += (avg_height - 1.0) * 5.0
    
    # 3. Spinning penalty: punish torso rotation
    avg_angular_vel = angular_vel_sum / SIMULATION_STEPS
    spin_penalty = 0.0
    if avg_angular_vel > 2.0:
        spin_penalty = (avg_angular_vel - 2.0) * 2.0
    
    # 4. Upright bonus: reward keeping torso near starting height
    upright_bonus = 0.0
    if 0.2 < avg_height < 0.8:
        upright_bonus = 0.5
    
    # 5. Falling penalty
    fall_penalty = 0.0
    if end_pos[2] < 0.05:
        fall_penalty = 2.0
    
    fitness = horiz_distance + upright_bonus - height_penalty - spin_penalty - fall_penalty
    
    return max(0.001, fitness)
