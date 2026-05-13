import random
import copy

class MorphologyGene:
    def __init__(self, size=None, parent_index=None, attach_offset=None, joint_axis=None):
        self.size = size or [0.1, 0.1, 0.3]
        self.parent_index = parent_index if parent_index is not None else 0
        self.attach_offset = attach_offset or [0, 0, -0.05]
        self.joint_axis = joint_axis or [1, 0, 0]

    def mutate(self):
        # Only slightly adjust size
        if random.random() < 0.2:
            idx = random.randint(0, 2)
            self.size[idx] += random.uniform(-0.03, 0.03)
            self.size[idx] = max(0.04, min(0.8, self.size[idx]))
        
        # Slightly adjust attachment point
        if random.random() < 0.15:
            idx = random.randint(0, 2)
            self.attach_offset[idx] += random.uniform(-0.03, 0.03)
            self.attach_offset[idx] = max(-0.5, min(0.5, self.attach_offset[idx]))


class BrainGene:
    def __init__(self, amplitude=None, frequency=None, phase=None, sensor_weights=None):
        self.amplitude = amplitude if amplitude is not None else random.uniform(0.3, 0.7)
        self.frequency = frequency if frequency is not None else random.uniform(0.5, 2.0)
        self.phase = phase if phase is not None else random.uniform(-3.14, 3.14)
        self.sensor_weights = sensor_weights or [random.uniform(-0.3, 0.3) for _ in range(3)]

    def mutate(self):
        if random.random() < 0.4:
            self.amplitude += random.uniform(-0.1, 0.1)
            self.amplitude = max(0.15, min(0.75, self.amplitude))
        if random.random() < 0.4:
            self.frequency += random.uniform(-0.3, 0.3)
            self.frequency = max(0.2, min(3.0, self.frequency))
        if random.random() < 0.3:
            self.phase += random.uniform(-0.4, 0.4)
        if random.random() < 0.2:
            idx = random.randint(0, 2)
            self.sensor_weights[idx] += random.uniform(-0.15, 0.15)
            self.sensor_weights[idx] = max(-0.5, min(0.5, self.sensor_weights[idx]))


class Genome:
    def __init__(self, num_initial_parts=None):
        self.morphology = []
        self.brain = []
        
        if num_initial_parts is not None:
            self._build_quadruped()
    
    def _build_quadruped(self):
        """Create a proper quadruped: flat torso + 4 legs hanging below.
        
        PyBullet coords: X=left/right, Y=front/back, Z=up/down
        
        Torso is a flat rectangle.
        Legs are vertical sticks attached at the 4 corners of the
        torso's bottom face, with hinge joints that swing front/back.
        """
        # --- TORSO ---
        torso_w = random.uniform(0.25, 0.4)   # X width (left-right)
        torso_d = random.uniform(0.3, 0.5)    # Y depth (front-back)
        torso_h = random.uniform(0.08, 0.14)  # Z height (thin/flat)
        
        self.morphology.append(MorphologyGene(
            size=[torso_w, torso_d, torso_h],
            parent_index=-1
        ))
        self.brain.append(BrainGene())  # placeholder, torso has no joint
        
        # --- 4 LEGS ---
        leg_thickness = random.uniform(0.04, 0.07)
        leg_length = random.uniform(0.25, 0.45)
        
        # Leg positions: 4 corners of torso bottom
        # [x_offset, y_offset, z_offset] from torso center
        corners = [
            ( torso_w * 0.4,  torso_d * 0.35, -torso_h * 0.5),  # front-right
            (-torso_w * 0.4,  torso_d * 0.35, -torso_h * 0.5),  # front-left
            ( torso_w * 0.4, -torso_d * 0.35, -torso_h * 0.5),  # back-right
            (-torso_w * 0.4, -torso_d * 0.35, -torso_h * 0.5),  # back-left
        ]
        
        # Trot gait: diagonal legs swing together
        # front-right + back-left in phase, front-left + back-right opposite
        phases = [0, 3.14, 3.14, 0]
        
        for leg_i, (cx, cy, cz) in enumerate(corners):
            leg_w = leg_thickness + random.uniform(-0.01, 0.01)
            leg_d = leg_thickness + random.uniform(-0.01, 0.01)
            leg_h = leg_length + random.uniform(-0.05, 0.05)
            
            self.morphology.append(MorphologyGene(
                size=[leg_w, leg_d, leg_h],
                parent_index=0,
                attach_offset=[cx, cy, cz],
                joint_axis=[1, 0, 0]  # swing forward/backward (rotation around X)
            ))
            self.brain.append(BrainGene(
                amplitude=random.uniform(0.35, 0.65),
                frequency=random.uniform(0.8, 1.8),
                phase=phases[leg_i] + random.uniform(-0.3, 0.3),
            ))

    def mutate(self):
        """Mutate brain parameters (heavily) and morphology (lightly)."""
        # Brain mutations are the main driver of evolution
        for b_gene in self.brain:
            b_gene.mutate()
        
        # Light morphology mutations
        for m_gene in self.morphology:
            m_gene.mutate()

    def clone(self):
        new_genome = Genome()
        new_genome.morphology = copy.deepcopy(self.morphology)
        new_genome.brain = copy.deepcopy(self.brain)
        return new_genome
