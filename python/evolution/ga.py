import random
from genome.genome import Genome
from evolution.fitness import evaluate_fitness

def init_population(size, num_parts=3):
    return [Genome(num_parts) for _ in range(size)]

def mutate_population(population, keep_best=True):
    new_population = []
    
    if keep_best and population:
        # Keep the best creature exactly as is (elitism)
        new_population.append(population[0].clone())
        
    while len(new_population) < len(population):
        # Tournament selection
        tournament = random.sample(population, min(3, len(population)))
        # Population should already be sorted by fitness in the main loop, 
        # but let's just pick a good one from the tournament.
        parent = tournament[0] # assuming sorted, tournament[0] could be best? 
        # Wait, if we sample randomly, we must know their fitness.
        # Let's just pick from the top 50% of the population since the array will be sorted
        top_half = population[:max(1, len(population)//2)]
        parent = random.choice(top_half)
        
        child = parent.clone()
        child.mutate()
        new_population.append(child)
        
    return new_population
