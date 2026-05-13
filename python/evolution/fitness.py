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
    
    for step in range(SIMULATION_STEPS):
        time_seconds = step * TIME_STEP
        sensor_data = sensors.get_state()
        torques = controller.get_torques(time_seconds, sensor_data)
        creature.apply_torques(torques)
        world.step()
        
    end_pos = creature.torso_position()
    world.disconnect()
    
    # Distance in the Y-axis (or X-axis)
    # Evolve to travel in the positive Y direction
    distance = end_pos[1] - start_pos[1]
    
    # Penalize falling down too much
    if end_pos[2] < 0.2:
        distance -= 0.5
        
    return max(0.001, distance)
