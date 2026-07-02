"""Entry point: run the evolutionary loop and export replays + metrics.

Usage
-----
    python main.py

Outputs (written to ``web/replays/``):
* ``gen_<n>.json``  — replay of the best creature at generation ``n``
* ``history.json``  — per-generation metrics used to draw the evolution charts
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from evolution.ga import GeneticAlgorithm
from replay.recorder import build_replay, save_replay
from simulation.evaluator import evaluate
from utils import config

REPLAYS_DIR = Path(__file__).resolve().parent.parent / "web" / "replays"


def _record_best(algo: GeneticAlgorithm, stats, saved_gens: list[int]) -> None:
    """Re-run the generation's best genome with recording on and save its replay."""
    result = evaluate(algo.best.genome, record=True)
    metadata = {
        "generation": stats.generation,
        "fitness": round(stats.best, 3),
        "distance": round(stats.best_distance, 3),
        "average_fitness": round(stats.average, 3),
        "population_size": config.POPULATION_SIZE,
        "num_parts": len(result.part_specs),
        "mutation_rate": round(stats.mutation_rate, 3),
        "survival_rate": round(stats.survival_rate, 3),
        "frequency": round(algo.best.genome.frequency, 3),
        "sim_seconds": config.SIM_SECONDS,
    }
    replay = build_replay(result, metadata)
    save_replay(replay, REPLAYS_DIR / f"gen_{stats.generation}.json")
    saved_gens.append(stats.generation)


def run_evolution() -> None:
    print(
        f"Evolving {config.POPULATION_SIZE} creatures over {config.GENERATIONS} "
        f"generations ({config.SIM_SECONDS:.0f}s evaluation each)."
    )
    print("-" * 68)

    algo = GeneticAlgorithm()
    saved_gens: list[int] = []
    total = config.GENERATIONS

    for generation in range(total + 1):
        algo.evaluate_population()
        sigma = algo._sigma(generation)
        stats = algo.record_stats(generation, sigma)

        print(
            f"Gen {generation:3d} | best {stats.best:7.3f} | avg {stats.average:7.3f} "
            f"| dist {stats.best_distance:6.2f}m | forward {stats.survival_rate:4.0%}"
        )

        if generation % config.SAVE_EVERY_N_GENS == 0 or generation == total:
            _record_best(algo, stats, saved_gens)

        if generation < total:
            algo.next_generation(sigma)

    history = {
        "generations": [dataclasses.asdict(s) for s in algo.history],
        "saved_generations": sorted(set(saved_gens)),
        "config": {
            "population_size": config.POPULATION_SIZE,
            "generations": config.GENERATIONS,
            "elite_count": config.ELITE_COUNT,
            "tournament_size": config.TOURNAMENT_SIZE,
            "crossover_rate": config.CROSSOVER_RATE,
            "sim_seconds": config.SIM_SECONDS,
        },
    }
    (REPLAYS_DIR / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    print("-" * 68)
    print(f"Done. Saved {len(set(saved_gens))} replays + history.json to {REPLAYS_DIR}")


if __name__ == "__main__":
    run_evolution()
