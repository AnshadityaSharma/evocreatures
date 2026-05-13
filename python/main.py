import os
import json
from evolution.ga import init_population, mutate_population
from evolution.fitness import evaluate_fitness
from simulation.physics_world import PhysicsWorld
from simulation.creature_builder import build_creature_from_genome
from simulation.sensors import DynamicSensors
from simulation.controller import GenomeController
from replay.recorder import ReplayRecorder
from utils.config import SIMULATION_STEPS, TIME_STEP

GENERATIONS = 100
POPULATION_SIZE = 20
SAVE_EVERY_N_GENS = 10

def record_and_save_replay(genome, filename, generation, fitness):
    world = PhysicsWorld(gui=False)
    creature = build_creature_from_genome(genome, world.client_id)
    sensors = DynamicSensors(creature)
    controller = GenomeController(genome)
    recorder = ReplayRecorder(TIME_STEP, creature)
    
    for step in range(SIMULATION_STEPS):
        time_seconds = step * TIME_STEP
        sensor_data = sensors.get_state()
        torques = controller.get_torques(time_seconds, sensor_data)
        creature.apply_torques(torques)
        world.step()
        recorder.record_frame(step)
        
    world.disconnect()
    
    replay_data = recorder.get_replay_data()
    # Embed metadata for the frontend
    replay_data["metadata"] = {
        "generation": generation,
        "fitness": round(fitness, 4),
        "num_parts": len(genome.morphology),
        "population_size": POPULATION_SIZE,
        "sim_seconds": round(SIMULATION_STEPS * TIME_STEP, 2),
    }
    
    replays_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "replays")
    os.makedirs(replays_dir, exist_ok=True)
    filepath = os.path.join(replays_dir, filename)
    with open(filepath, "w") as f:
        json.dump(replay_data, f)
    print(f"  Saved replay: {filename}")


def run_evolution():
    print(f"Starting evolution: {GENERATIONS} generations, {POPULATION_SIZE} creatures each")
    print(f"Simulation: {SIMULATION_STEPS} steps ({SIMULATION_STEPS * TIME_STEP:.1f}s) per creature")
    print("-" * 60)
    
    population = init_population(POPULATION_SIZE, num_parts=4)
    
    for generation in range(GENERATIONS + 1):
        # 1. Evaluate Fitness
        fitness_scores = []
        for genome in population:
            score = evaluate_fitness(genome, gui=False)
            fitness_scores.append((score, genome))
            
        # 2. Sort by fitness descending
        fitness_scores.sort(key=lambda x: x[0], reverse=True)
        population = [g for s, g in fitness_scores]
        best_score = fitness_scores[0][0]
        avg_score = sum(s for s, g in fitness_scores) / len(fitness_scores)
        
        parts_count = len(population[0].morphology)
        print(f"Gen {generation:03d} | Best: {best_score:7.3f} | Avg: {avg_score:7.3f} | Parts: {parts_count}")
        
        # 3. Export replay for every 10th generation
        if generation % SAVE_EVERY_N_GENS == 0:
            record_and_save_replay(population[0], f"gen_{generation}.json", generation, best_score)
            
        # 4. Mutate for next generation
        if generation < GENERATIONS:
            population = mutate_population(population, keep_best=True)
    
    print("-" * 60)
    print("Evolution complete!")

if __name__ == "__main__":
    run_evolution()
