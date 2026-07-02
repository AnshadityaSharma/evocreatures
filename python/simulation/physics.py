"""Thin wrapper around a pymunk (Chipmunk2D) physics space."""
from __future__ import annotations

import pymunk

from utils import config


class PhysicsWorld:
    """A 2D physics world with gravity and a static ground plane."""

    def __init__(self) -> None:
        self.space = pymunk.Space()
        self.space.gravity = (0.0, config.GRAVITY)
        self.space.iterations = config.SOLVER_ITERATIONS

        ground = pymunk.Segment(self.space.static_body, (-500, 0), (500, 0), 0.05)
        ground.friction = config.GROUND_FRICTION
        ground.elasticity = 0.0
        self.space.add(ground)

    def step(self) -> None:
        self.space.step(config.TIME_STEP)
