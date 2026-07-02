"""Central configuration for the EvoCreatures simulation and genetic algorithm.

Every tunable number in the project lives here so experiments are reproducible
and easy to reason about. Units are SI-like: metres, kilograms, seconds, radians.
"""

# --------------------------------------------------------------------------- #
# Physics
# --------------------------------------------------------------------------- #
GRAVITY = -9.81            # m/s^2, acting on the -y axis (2D sagittal plane)
TIME_STEP = 1.0 / 240.0    # physics integration step (240 Hz for stability)
SOLVER_ITERATIONS = 30     # Chipmunk constraint solver iterations per step
GROUND_FRICTION = 1.5
BODY_FRICTION = 1.8

SIM_SECONDS = 8.0          # how long each creature is evaluated
SIM_STEPS = int(SIM_SECONDS / TIME_STEP)

# Replays are recorded at a lower rate than the physics runs to keep JSON small.
RECORD_HZ = 60
RECORD_EVERY = max(1, round((1.0 / TIME_STEP) / RECORD_HZ))

# --------------------------------------------------------------------------- #
# Morphology (fixed body plan — see README "Design decisions")
# --------------------------------------------------------------------------- #
# The creature is a segmented worm: a horizontal chain of boxes joined by
# motorised hinges. Lying flat on the ground it cannot topple, so the genetic
# algorithm can focus entirely on discovering an efficient undulating gait that
# propels the body forward — evolutionary progress that is easy to observe.
NUM_SEGMENTS = 7
SEGMENT_MASS = 0.5
SEGMENT_SIZE = (0.30, 0.12)  # (length, height) of each body segment, metres
SEGMENT_FRICTION = 1.5       # grip against the ground (drives forward thrust)
SPAWN_Y = 0.08               # centre height at spawn (segment resting on ground)
RENDER_DEPTH = 0.34          # out-of-plane thickness used only for 3D rendering

NUM_JOINTS = NUM_SEGMENTS - 1  # motorised hinges between consecutive segments

# --------------------------------------------------------------------------- #
# Controller (central pattern generator)
# --------------------------------------------------------------------------- #
# Each joint follows a sinusoid; a single shared frequency acts as one gait
# clock so segments can lock into a coordinated travelling wave. See controller.py.
MOTOR_MAX_FORCE = 60.0     # torque ceiling for each joint motor (N*m)
MOTOR_GAIN = 8.0           # proportional gain converting angle error -> rate
MOTOR_MAX_RATE = 10.0      # clamp on commanded joint angular velocity (rad/s)

FREQ_RANGE = (0.5, 3.0)    # Hz, allowed gait frequencies
AMPLITUDE_RANGE = (0.0, 0.9)   # rad, per-joint swing amplitude
CENTER_RANGE = (-0.4, 0.4)     # rad, per-joint rest offset
PHASE_RANGE = (-3.14159, 3.14159)  # rad, per-joint phase offset

# --------------------------------------------------------------------------- #
# Launch detection — a well-behaved worm hugs the ground. If a violent gait
# flings it into the air the evaluation ends early and its forward progress is
# frozen, so physically implausible "exploits" cannot out-score real crawling.
# --------------------------------------------------------------------------- #
LAUNCH_Y = 1.0             # body centroid height that counts as launched

# --------------------------------------------------------------------------- #
# Fitness weights
# --------------------------------------------------------------------------- #
ENERGY_PENALTY = 0.015     # penalty per unit of motor effort (favours efficient gaits)
LAUNCH_PENALTY = 4.0       # flat penalty for flinging airborne (favours smooth crawlers)

# --------------------------------------------------------------------------- #
# Genetic algorithm
# --------------------------------------------------------------------------- #
POPULATION_SIZE = 50
GENERATIONS = 30
ELITE_COUNT = 3            # best genomes copied unchanged into the next generation
TOURNAMENT_SIZE = 5        # candidates compared per parent selection
CROSSOVER_RATE = 0.80      # probability two parents are recombined
GENE_MUTATION_RATE = 0.32  # per-gene probability of a Gaussian perturbation
IMMIGRANT_COUNT = 4        # fresh random genomes injected each generation for diversity

# Mutation strength anneals from SIGMA_START to SIGMA_END across the run so early
# generations explore broadly and later ones converge and fine-tune.
SIGMA_START = 1.0
SIGMA_END = 0.18

RANDOM_SEED = 21           # makes every run reproducible

# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
SAVE_EVERY_N_GENS = 5      # snapshot the best creature's replay at this cadence
