"""Fitness function.

Fitness rewards **efficient forward crawling**. It is computed from a summary of
one evaluation:

    fitness = forward_distance - ENERGY_PENALTY * energy

``forward_distance`` is the rightward (+x) displacement of the worm's centroid,
frozen at the instant it is flung into the air by an unstable gait. Because a
launch ends the evaluation, physically implausible "exploits" cannot accumulate
distance — steady crawling strictly dominates. The energy term gently favours
smooth, efficient undulation over frantic thrashing.

The score is floored at zero: creatures that crawl backwards or merely thrash in
place are all equally "unfit". This keeps selection focused on the forward
gradient and makes the population's *average* fitness a clean measure of how much
of the population has learned to move forward at all.
"""
from __future__ import annotations

from dataclasses import dataclass

from utils import config


@dataclass
class EvalSummary:
    forward_distance: float  # +x centroid displacement at launch / timeout
    energy: float            # accumulated motor effort
    launched: bool           # whether the body was flung airborne (incurs a penalty)


def compute_fitness(summary: EvalSummary) -> float:
    score = summary.forward_distance - config.ENERGY_PENALTY * summary.energy
    if summary.launched:
        score -= config.LAUNCH_PENALTY
    return max(0.0, score)
