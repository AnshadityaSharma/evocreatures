"""Builds a physical creature — a segmented worm — inside a physics world."""
from __future__ import annotations

import pymunk

from utils import config

# All segments of one creature share a shape-filter group so neighbouring
# segments never collide with each other — only with the ground.
_SELF_GROUP = pymunk.ShapeFilter(group=1)


class Creature:
    """A segmented worm: a horizontal chain of boxes joined by motorised hinges.

    The morphology is identical for every genome; only the controller that
    drives the joint motors differs, which keeps evolutionary comparisons fair.
    """

    def __init__(self, world) -> None:
        space = world.space
        seg_len, seg_h = config.SEGMENT_SIZE

        # -- segments ------------------------------------------------------- #
        self.segments = []
        start_x = -(config.NUM_SEGMENTS - 1) * seg_len / 2.0
        for i in range(config.NUM_SEGMENTS):
            body = pymunk.Body(
                config.SEGMENT_MASS,
                pymunk.moment_for_box(config.SEGMENT_MASS, config.SEGMENT_SIZE),
            )
            body.position = (start_x + i * seg_len, config.SPAWN_Y)
            shape = pymunk.Poly.create_box(body, config.SEGMENT_SIZE)
            shape.friction = config.SEGMENT_FRICTION
            shape.elasticity = 0.0
            shape.filter = _SELF_GROUP
            space.add(body, shape)
            self.segments.append(body)

        # -- motorised hinges between consecutive segments ------------------ #
        self.motors = []
        for i in range(config.NUM_JOINTS):
            anchor_x = self.segments[i].position.x + seg_len / 2.0
            hinge = pymunk.PivotJoint(
                self.segments[i], self.segments[i + 1], (anchor_x, config.SPAWN_Y)
            )
            hinge.collide_bodies = False
            motor = pymunk.SimpleMotor(self.segments[i], self.segments[i + 1], 0.0)
            motor.max_force = config.MOTOR_MAX_FORCE
            space.add(hinge, motor)
            self.motors.append(motor)

    # -- state queries ------------------------------------------------------ #
    @property
    def num_parts(self) -> int:
        return len(self.segments)

    def joint_angle(self, i: int) -> float:
        """Relative angle across hinge ``i`` (rad)."""
        return self.segments[i + 1].angle - self.segments[i].angle

    def centroid_x(self) -> float:
        return sum(s.position.x for s in self.segments) / len(self.segments)

    def centroid_y(self) -> float:
        return sum(s.position.y for s in self.segments) / len(self.segments)

    def has_launched(self) -> bool:
        """True if the body has been flung into the air by an unstable gait."""
        return self.centroid_y() > config.LAUNCH_Y

    def part_states(self):
        """Return ``[(x, y, angle), ...]`` for each segment (for replays)."""
        return [(s.position.x, s.position.y, s.angle) for s in self.segments]

    def part_specs(self):
        """Return render geometry for every segment: ``[(w, h), ...]``."""
        return [config.SEGMENT_SIZE] * len(self.segments)
