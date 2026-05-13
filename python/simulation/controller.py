import math

class GenomeController:
    """Converts brain genes into joint angle targets.
    
    Each leg oscillates sinusoidally, producing a rhythmic
    back-and-forth swing like an animal's gait."""
    
    def __init__(self, genome):
        self.genome = genome

    def get_target_angles(self, time_seconds, sensor_data):
        targets = []
        for i in range(1, len(self.genome.brain)):
            brain = self.genome.brain[i]
            
            # Sinusoidal swing: angle = amplitude * sin(2π * freq * t + phase)
            angle = brain.amplitude * math.sin(
                2.0 * math.pi * brain.frequency * time_seconds + brain.phase
            )
            
            # Small sensor feedback modulation
            feedback = 0.0
            for j in range(min(len(sensor_data), len(brain.sensor_weights))):
                feedback += sensor_data[j] * brain.sensor_weights[j]
            
            angle += feedback * 0.1
            
            # Clamp to safe joint range
            angle = max(-0.75, min(0.75, angle))
            targets.append(angle)
            
        return targets
