import random
import copy

class MorphologyGene:
    def __init__(self, size=None, parent_index=None, attach_offset=None, joint_axis=None):
        self.size = size or [0.1, 0.1, 0.3]
        self.parent_index = parent_index if parent_index is not None else 0
        self.attach_offset = attach_offset or [0, 0, -0.05]
        self.joint_axis = joint_axis or [1, 0, 0]

    def mutate(self):
        # Allow more dramatic size mutations to grow longer legs
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.size[idx] += random.uniform(-0.1, 0.1)
            self.size[idx] = max(0.04, min(1.0, self.size[idx]))
        
        if random.random() < 0.2:
            idx = random.randint(0, 2)
            self.attach_offset[idx] += random.uniform(-0.05, 0.05)
            self.attach_offset[idx] = max(-0.6, min(0.6, self.attach_offset[idx]))


class BrainGene:
    def __init__(self, amplitude=None, frequency=None, phase=None, sensor_weights=None):
        self.amplitude = amplitude if amplitude is not None else random.uniform(0.1, 1.0)
        self.frequency = frequency if frequency is not None else random.uniform(0.5, 3.0)
        self.phase = phase if phase is not None else random.uniform(-3.14, 3.14)
        self.sensor_weights = sensor_weights or [random.uniform(-0.5, 0.5) for _ in range(3)]

    def mutate(self):
        # Increased mutation rates and ranges to allow for significant evolution
        if random.random() < 0.5:
            self.amplitude += random.uniform(-0.2, 0.2)
            self.amplitude = max(0.1, min(1.5, self.amplitude)) # allow larger swings
        if random.random() < 0.5:
            self.frequency += random.uniform(-0.5, 0.5)
            self.frequency = max(0.2, min(5.0, self.frequency)) # allow faster swings
        if random.random() < 0.5:
            self.phase += random.uniform(-0.8, 0.8)
            # Wrap phase between -pi and pi
            if self.phase > 3.14: self.phase -= 6.28
            if self.phase < -3.14: self.phase += 6.28
        if random.random() < 0.3:
            idx = random.randint(0, 2)
            self.sensor_weights[idx] += random.uniform(-0.2, 0.2)
            self.sensor_weights[idx] = max(-1.0, min(1.0, self.sensor_weights[idx]))


class Genome:
    def __init__(self, num_initial_parts=None):
        self.morphology = []
        self.brain = []
        
        if num_initial_parts is not None:
            self._build_quadruped()
    
    def _build_quadruped(self):
        """Create a basic quadruped layout, but with COMPLETELY RANDOM brain parameters.
        
        This forces evolution to start from a completely uncoordinated state
        (flailing randomly) and learn a coordinated gait over time.
        """
        # --- TORSO ---
        torso_w = random.uniform(0.25, 0.4)
        torso_d = random.uniform(0.3, 0.5)
        torso_h = random.uniform(0.08, 0.14)
        
        self.morphology.append(MorphologyGene(
            size=[torso_w, torso_d, torso_h],
            parent_index=-1
        ))
        self.brain.append(BrainGene())
        
        # --- 4 LEGS ---
        leg_thickness = random.uniform(0.04, 0.08)
        leg_length = random.uniform(0.2, 0.3) # Start with short legs
        
        corners = [
            ( torso_w * 0.4,  torso_d * 0.35, -torso_h * 0.5),
            (-torso_w * 0.4,  torso_d * 0.35, -torso_h * 0.5),
            ( torso_w * 0.4, -torso_d * 0.35, -torso_h * 0.5),
            (-torso_w * 0.4, -torso_d * 0.35, -torso_h * 0.5),
        ]
        
        for leg_i, (cx, cy, cz) in enumerate(corners):
            leg_w = leg_thickness + random.uniform(-0.01, 0.01)
            leg_d = leg_thickness + random.uniform(-0.01, 0.01)
            leg_h = leg_length + random.uniform(-0.02, 0.02)
            
            self.morphology.append(MorphologyGene(
                size=[leg_w, leg_d, leg_h],
                parent_index=0,
                attach_offset=[cx, cy, cz],
                joint_axis=[1, 0, 0]
            ))
            # No hardcoded trot! Completely random phases and frequencies.
            self.brain.append(BrainGene(
                amplitude=random.uniform(0.2, 0.6),
                frequency=random.uniform(0.5, 2.0),
                phase=random.uniform(-3.14, 3.14)
            ))

    def mutate(self):
        """Mutate brain parameters (heavily) and morphology."""
        for b_gene in self.brain:
            b_gene.mutate()
        for m_gene in self.morphology:
            m_gene.mutate()

    def clone(self):
        new_genome = Genome()
        new_genome.morphology = copy.deepcopy(self.morphology)
        new_genome.brain = copy.deepcopy(self.brain)
        return new_genome
