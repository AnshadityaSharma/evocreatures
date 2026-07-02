"""Runs a single creature through the physics world and scores it."""
from __future__ import annotations

from dataclasses import dataclass, field

from evolution.fitness import EvalSummary, compute_fitness
from simulation.controller import CPGController
from simulation.creature import Creature
from simulation.physics import PhysicsWorld
from utils import config


@dataclass
class EvalResult:
    fitness: float
    distance: float          # forward distance travelled (m)
    launched: bool
    frames: list = field(default_factory=list)   # populated only when recording
    part_specs: list = field(default_factory=list)


def evaluate(genome, record: bool = False) -> EvalResult:
    """Simulate ``genome`` for the configured duration and return its score.

    When ``record`` is true, part transforms are sampled at ``RECORD_HZ`` and
    returned in ``frames`` for later replay export.
    """
    world = PhysicsWorld()
    creature = Creature(world)
    controller = CPGController(genome)

    start_x = creature.centroid_x()
    forward_distance = 0.0
    energy = 0.0
    launched = False
    frames = []

    for step in range(config.SIM_STEPS):
        t = step * config.TIME_STEP
        energy += controller.apply(creature, t) * config.TIME_STEP
        world.step()

        if creature.has_launched():
            launched = True
            break

        forward_distance = creature.centroid_x() - start_x

        if record and step % config.RECORD_EVERY == 0:
            frames.append({"t": round(t, 4), "parts": creature.part_states()})

    summary = EvalSummary(forward_distance, energy, launched)
    result = EvalResult(
        fitness=compute_fitness(summary),
        distance=forward_distance,
        launched=launched,
    )
    if record:
        result.frames = frames
        result.part_specs = creature.part_specs()
    return result
