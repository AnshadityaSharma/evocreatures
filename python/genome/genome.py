import random
import copy

class MorphologyGene:
    def __init__(self, size=None, parent_index=None, attach_offset=None, joint_axis=None):
        # Size of the box part (width, height, depth)
        self.size = size or [random.uniform(0.1, 0.8) for _ in range(3)]
        # Index of the parent part to attach to. -1 means this is the root (torso).
        self.parent_index = parent_index if parent_index is not None else 0
        # Where to attach on the parent relative to parent's center
        self.attach_offset = attach_offset or [random.uniform(-0.5, 0.5) for _ in range(3)]
        # The axis of the hinge joint
        axis_choices = [[1,0,0], [0,1,0], [0,0,1]]
        self.joint_axis = joint_axis or random.choice(axis_choices)

    def mutate(self):
        # Mutate size
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.size[idx] += random.uniform(-0.2, 0.2)
            self.size[idx] = max(0.1, min(1.2, self.size[idx]))
            
        # Mutate attach offset
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.attach_offset[idx] += random.uniform(-0.2, 0.2)
            self.attach_offset[idx] = max(-1.0, min(1.0, self.attach_offset[idx]))
            
        # Mutate joint axis
        if random.random() < 0.1:
            axis_choices = [[1,0,0], [0,1,0], [0,0,1]]
            self.joint_axis = random.choice(axis_choices)


class BrainGene:
    def __init__(self, amplitude=None, frequency=None, phase=None, sensor_weights=None):
        self.amplitude = amplitude if amplitude is not None else random.uniform(1.0, 10.0)
        self.frequency = frequency if frequency is not None else random.uniform(0.5, 5.0)
        self.phase = phase if phase is not None else random.uniform(-3.14, 3.14)
        # Weights for sensor feedback: [joint_angle, torso_touch, leg_touch]
        self.sensor_weights = sensor_weights or [random.uniform(-1.0, 1.0) for _ in range(3)]

    def mutate(self):
        if random.random() < 0.3:
            self.amplitude += random.uniform(-2.0, 2.0)
            self.amplitude = max(0.0, min(20.0, self.amplitude))
            
        if random.random() < 0.3:
            self.frequency += random.uniform(-1.0, 1.0)
            self.frequency = max(0.1, min(10.0, self.frequency))
            
        if random.random() < 0.3:
            self.phase += random.uniform(-1.0, 1.0)
            
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.sensor_weights[idx] += random.uniform(-0.5, 0.5)
            self.sensor_weights[idx] = max(-2.0, min(2.0, self.sensor_weights[idx]))


class Genome:
    def __init__(self, num_initial_parts=None):
        self.morphology = []
        self.brain = []
        
        if num_initial_parts is not None:
            # The root node (torso)
            self.morphology.append(MorphologyGene(parent_index=-1))
            self.brain.append(BrainGene()) # Torso doesn't have a joint, but we keep indices aligned
            
            # Additional limbs
            for _ in range(num_initial_parts - 1):
                self.add_random_part()
                
    def add_random_part(self):
        # Randomly select a parent from existing parts
        parent_idx = random.randint(0, len(self.morphology) - 1)
        self.morphology.append(MorphologyGene(parent_index=parent_idx))
        self.brain.append(BrainGene())

    def mutate(self):
        """Applies parametric and structural mutations to the genome."""
        # 1. Parametric Mutations (change existing genes)
        for m_gene in self.morphology:
            m_gene.mutate()
        for b_gene in self.brain:
            b_gene.mutate()
            
        # 2. Structural Mutations (add or remove body parts)
        # Add a part (max 8 parts to prevent simulation freezing)
        if random.random() < 0.15 and len(self.morphology) < 8:
            self.add_random_part()
            
        # Remove a part
        if random.random() < 0.10 and len(self.morphology) > 2:
            # We just pop the last added part to avoid breaking parent references
            self.morphology.pop()
            self.brain.pop()

    def clone(self):
        """Returns a deep copy of this genome."""
        new_genome = Genome()
        new_genome.morphology = copy.deepcopy(self.morphology)
        new_genome.brain = copy.deepcopy(self.brain)
        return new_genome
