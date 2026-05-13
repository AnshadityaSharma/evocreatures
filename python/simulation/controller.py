import math

class GenomeController:
    """Converts brain genes into joint angle targets (not torques).
    
    Each joint oscillates between -limit and +limit at the gene's frequency.
    This produces a rhythmic swinging motion like real limbs."""
    
    def __init__(self, genome):
        self.genome = genome

    def get_target_angles(self, time_seconds, sensor_data):
        """Return a list of target joint angles (one per joint)."""
        targets = []
        # Torso (index 0) has no joint, brain genes 1..N map to joints 0..N-1
        for i in range(1, len(self.genome.brain)):
            brain = self.genome.brain[i]
            
            # Base oscillation: swing between -amplitude and +amplitude
            swing = math.sin(2.0 * math.pi * brain.frequency * time_seconds + brain.phase)
            
            # Modulate with sensor feedback (small influence)
            feedback = 0.0
            for j in range(min(len(sensor_data), len(brain.sensor_weights))):
                feedback += sensor_data[j] * brain.sensor_weights[j]
            
            # Target angle in radians, clamped to joint limits
            target = brain.amplitude * (swing + feedback * 0.2)
            target = max(-0.9, min(0.9, target))
            
            targets.append(target)
            
        return targets
