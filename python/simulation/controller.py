"""Central pattern generator (CPG) that turns a genome into joint commands.

Each joint follows a sinusoid ``center + amplitude * sin(2*pi*f*t + phase)``.
A *single shared frequency* ``f`` acts as one gait clock, so the segments can
lock into a coordinated travelling wave — the ingredient that lets evolution
discover smooth crawling instead of uncoordinated thrashing.

The controller drives pymunk's velocity motors with a proportional law:
the commanded joint rate is proportional to the error between the current and
target angle, clamped to a maximum rate. Together with each motor's torque
ceiling this behaves like a servo (position control).
"""
from __future__ import annotations

import math

from utils import config


class CPGController:
    def __init__(self, genome) -> None:
        self.frequency = genome.frequency
        self.amplitudes = genome.amplitudes
        self.phases = genome.phases
        self.centers = genome.centers

    def target_angle(self, joint: int, t: float) -> float:
        return self.centers[joint] + self.amplitudes[joint] * math.sin(
            2.0 * math.pi * self.frequency * t + self.phases[joint]
        )

    def apply(self, creature, t: float) -> float:
        """Drive every joint motor toward its target angle at time ``t``.

        Returns the total commanded motor effort this step, used by the fitness
        function as an energy proxy.
        """
        effort = 0.0
        for i, motor in enumerate(creature.motors):
            error = self.target_angle(i, t) - creature.joint_angle(i)
            rate = config.MOTOR_GAIN * error
            rate = max(-config.MOTOR_MAX_RATE, min(config.MOTOR_MAX_RATE, rate))
            motor.rate = rate
            effort += abs(rate)
        return effort
