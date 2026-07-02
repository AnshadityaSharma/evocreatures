"""The genetic algorithm: selection, crossover, mutation, and the evolve loop."""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass

from genome.genome import Genome
from simulation.evaluator import evaluate
from utils import config


@dataclass
class Individual:
    genome: Genome
    fitness: float = 0.0
    distance: float = 0.0


@dataclass
class GenerationStats:
    """Per-generation metrics, exported for the website's evolution charts."""

    generation: int
    best: float
    average: float
    median: float
    worst: float
    std: float
    survival_rate: float   # fraction of the population making net forward progress
    mutation_rate: float   # annealed mutation strength (sigma) used this gen
    best_distance: float


class GeneticAlgorithm:
    def __init__(self, seed: int = config.RANDOM_SEED) -> None:
        self.rng = random.Random(seed)
        self.population = [
            Individual(Genome.random(self.rng)) for _ in range(config.POPULATION_SIZE)
        ]
        self.history: list[GenerationStats] = []

    # -- evolutionary operators --------------------------------------------- #
    def _sigma(self, generation: int) -> float:
        """Mutation strength annealed linearly from SIGMA_START to SIGMA_END."""
        if config.GENERATIONS <= 1:
            return config.SIGMA_END
        frac = generation / (config.GENERATIONS - 1)
        return config.SIGMA_START + (config.SIGMA_END - config.SIGMA_START) * frac

    def _tournament(self) -> Individual:
        """Pick the fittest of a small random sample (tournament selection)."""
        contenders = self.rng.sample(self.population, config.TOURNAMENT_SIZE)
        return max(contenders, key=lambda ind: ind.fitness)

    def _breed(self, sigma: float) -> Genome:
        parent_a = self._tournament()
        if self.rng.random() < config.CROSSOVER_RATE:
            parent_b = self._tournament()
            child = Genome.crossover(parent_a.genome, parent_b.genome, self.rng)
        else:
            child = parent_a.genome.clone()
        return child.mutate(sigma, self.rng)

    # -- main loop ---------------------------------------------------------- #
    def evaluate_population(self) -> None:
        for ind in self.population:
            result = evaluate(ind.genome)
            ind.fitness = result.fitness
            ind.distance = result.distance
        self.population.sort(key=lambda ind: ind.fitness, reverse=True)

    def record_stats(self, generation: int, sigma: float) -> GenerationStats:
        scores = [ind.fitness for ind in self.population]
        survivors = sum(1 for ind in self.population if ind.fitness > 0)
        stats = GenerationStats(
            generation=generation,
            best=max(scores),
            average=statistics.mean(scores),
            median=statistics.median(scores),
            worst=min(scores),
            std=statistics.pstdev(scores),
            survival_rate=survivors / len(self.population),
            mutation_rate=sigma,
            best_distance=self.population[0].distance,
        )
        self.history.append(stats)
        return stats

    def next_generation(self, sigma: float) -> None:
        """Build the next population: elites + immigrants + tournament-bred offspring.

        A few fresh random genomes ("immigrants") are injected each generation to
        keep the gene pool diverse and stop the search stalling in a local optimum.
        """
        elites = [self.population[i].genome.clone() for i in range(config.ELITE_COUNT)]
        immigrants = [Genome.random(self.rng) for _ in range(config.IMMIGRANT_COUNT)]
        remaining = config.POPULATION_SIZE - len(elites) - len(immigrants)
        children = [self._breed(sigma) for _ in range(remaining)]
        self.population = [Individual(g) for g in elites + immigrants + children]

    @property
    def best(self) -> Individual:
        return self.population[0]
