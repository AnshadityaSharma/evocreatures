from simulation.physics_world import PhysicsWorld
from simulation.creature_builder import build_creature_from_genome
from simulation.sensors import DynamicSensors
from simulation.controller import GenomeController
from utils.config import SIMULATION_STEPS, TIME_STEP

def evaluate_fitness(genome, gui=False):
    world = PhysicsWorld(gui=gui)
    creature = build_creature_from_genome(genome, world.client_id)
    
    if not creature:
        world.disconnect()
        return 0.0
        
    sensors = DynamicSensors(creature)
    controller = GenomeController(genome)
    
    start_pos = creature.torso_position()
    
    # Track height over time for stability scoring
    max_height = start_pos[2]
    height_sum = 0.0
    ground_contact_steps = 0
    
    for step in range(SIMULATION_STEPS):
        time_seconds = step * TIME_STEP
        sensor_data = sensors.get_state()
        torques = controller.get_torques(time_seconds, sensor_data)
        creature.apply_torques(torques)
        world.step()
        
        pos = creature.torso_position()
        height = pos[2]
        max_height = max(max_height, height)
        height_sum += height
        
        # Check if any part is touching the ground (via sensor)
        if len(sensor_data) > 0:
            # Touch sensors are after joint angles in sensor_data
            num_joints = len(creature.joint_angles())
            touch_data = sensor_data[num_joints:]
            if any(t > 0 for t in touch_data):
                ground_contact_steps += 1
        
    end_pos = creature.torso_position()
    world.disconnect()
    
    # ----- FITNESS COMPONENTS -----
    
    # 1. Forward distance (X-axis in PyBullet is usually forward)
    #    Use the larger of X or Y displacement to be direction-agnostic
    dx = abs(end_pos[0] - start_pos[0])
    dy = abs(end_pos[1] - start_pos[1])
    forward_distance = max(dx, dy)
    
    # 2. Height penalty — heavily penalize flying creatures
    avg_height = height_sum / SIMULATION_STEPS
    height_penalty = 0.0
    if max_height > 2.0:
        # If creature flew above 2m, it's exploiting physics
        height_penalty = (max_height - 2.0) * 5.0
    if avg_height > 1.5:
        height_penalty += (avg_height - 1.5) * 3.0
    
    # 3. Stability bonus — reward staying near ground level
    stability_bonus = 0.0
    if 0.15 < avg_height < 1.0:
        stability_bonus = 0.5  # reward for staying grounded
    
    # 4. Ground contact bonus — reward creatures that actually touch the ground
    contact_ratio = ground_contact_steps / SIMULATION_STEPS
    contact_bonus = contact_ratio * 0.3
    
    # 5. Falling penalty
    fall_penalty = 0.0
    if end_pos[2] < 0.1:
        fall_penalty = 1.0
    
    fitness = forward_distance + stability_bonus + contact_bonus - height_penalty - fall_penalty
    
    return max(0.001, fitness)
