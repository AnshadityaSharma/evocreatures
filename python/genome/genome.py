import random
import copy

class MorphologyGene:
    def __init__(self, size=None, parent_index=None, attach_offset=None, joint_axis=None):
        self.size = size or [random.uniform(0.12, 0.5) for _ in range(3)]
        self.parent_index = parent_index if parent_index is not None else 0
        # Attachment offset relative to parent center
        self.attach_offset = attach_offset or [random.uniform(-0.3, 0.3) for _ in range(3)]
        # Hinge joint axis
        axis_choices = [[1,0,0], [0,1,0], [0,0,1]]
        self.joint_axis = joint_axis or random.choice(axis_choices)

    def mutate(self):
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.size[idx] += random.uniform(-0.08, 0.08)
            self.size[idx] = max(0.08, min(0.6, self.size[idx]))
            
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.attach_offset[idx] += random.uniform(-0.1, 0.1)
            self.attach_offset[idx] = max(-0.5, min(0.5, self.attach_offset[idx]))
            
        if random.random() < 0.05:
            axis_choices = [[1,0,0], [0,1,0], [0,0,1]]
            self.joint_axis = random.choice(axis_choices)


class BrainGene:
    def __init__(self, amplitude=None, frequency=None, phase=None, sensor_weights=None):
        # Amplitude is now a target angle range, not a force
        self.amplitude = amplitude if amplitude is not None else random.uniform(0.2, 0.8)
        self.frequency = frequency if frequency is not None else random.uniform(0.3, 2.5)
        self.phase = phase if phase is not None else random.uniform(-3.14, 3.14)
        self.sensor_weights = sensor_weights or [random.uniform(-0.3, 0.3) for _ in range(3)]

    def mutate(self):
        if random.random() < 0.3:
            self.amplitude += random.uniform(-0.15, 0.15)
            self.amplitude = max(0.1, min(0.9, self.amplitude))
            
        if random.random() < 0.3:
            self.frequency += random.uniform(-0.4, 0.4)
            self.frequency = max(0.1, min(3.0, self.frequency))
            
        if random.random() < 0.3:
            self.phase += random.uniform(-0.5, 0.5)
            
        if random.random() < 0.2:
            idx = random.randint(0, 2)
            self.sensor_weights[idx] += random.uniform(-0.2, 0.2)
            self.sensor_weights[idx] = max(-0.6, min(0.6, self.sensor_weights[idx]))


class Genome:
    def __init__(self, num_initial_parts=None):
        self.morphology = []
        self.brain = []
        
        if num_initial_parts is not None:
            self._build_initial_creature(num_initial_parts)
    
    def _build_initial_creature(self, num_parts):
        """Create a creature with a torso and legs attached below it."""
        # Torso: wide, flat body
        torso_w = random.uniform(0.3, 0.5)
        torso_h = random.uniform(0.1, 0.2)
        torso_d = random.uniform(0.2, 0.35)
        self.morphology.append(MorphologyGene(
            size=[torso_w, torso_h, torso_d],
            parent_index=-1
        ))
        self.brain.append(BrainGene())
        
        # Create legs: attach to sides/bottom of torso
        num_legs = num_parts - 1
        for leg_i in range(num_legs):
            # Leg dimensions: thin and longish
            leg_w = random.uniform(0.06, 0.12)
            leg_h = random.uniform(0.15, 0.35)
            leg_d = random.uniform(0.06, 0.12)
            
            # Attach to sides of torso
            if num_legs == 2:
                x_off = torso_w * 0.5 * (1 if leg_i == 0 else -1)
            elif num_legs == 4:
                x_off = torso_w * 0.5 * (1 if leg_i % 2 == 0 else -1)
            else:
                x_off = random.uniform(-torso_w * 0.5, torso_w * 0.5)
            
            # Spread legs along the body length
            if num_legs >= 4:
                z_off = torso_d * 0.3 * (1 if leg_i < 2 else -1)
            else:
                z_off = random.uniform(-torso_d * 0.3, torso_d * 0.3)
            
            y_off = -torso_h * 0.5  # attach below torso
            
            self.morphology.append(MorphologyGene(
                size=[leg_w, leg_h, leg_d],
                parent_index=0,
                attach_offset=[x_off, y_off, z_off],
                joint_axis=[0, 0, 1]  # swing forward/backward
            ))
            self.brain.append(BrainGene(
                phase=3.14 * (leg_i % 2)  # Alternate phase for walking gait
            ))
                
    def add_random_part(self):
        parent_idx = 0 if random.random() < 0.8 else random.randint(0, len(self.morphology) - 1)
        self.morphology.append(MorphologyGene(parent_index=parent_idx))
        self.brain.append(BrainGene())

    def mutate(self):
        """Applies parametric and structural mutations."""
        for m_gene in self.morphology:
            m_gene.mutate()
        for b_gene in self.brain:
            b_gene.mutate()
            
        # Structural: add a limb (rare, max 6)
        if random.random() < 0.08 and len(self.morphology) < 6:
            self.add_random_part()
            
        # Structural: remove a limb (very rare, keep min 3)
        if random.random() < 0.03 and len(self.morphology) > 3:
            self.morphology.pop()
            self.brain.pop()

    def clone(self):
        new_genome = Genome()
        new_genome.morphology = copy.deepcopy(self.morphology)
        new_genome.brain = copy.deepcopy(self.brain)
        return new_genome
