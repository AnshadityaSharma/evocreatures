import math

class GenomeController:
    def __init__(self, genome):
        self.genome = genome

    def get_torques(self, time_seconds, sensor_data):
        torques = []
        # Torso (index 0) has a brain gene but no joint, so skip index 0
        for i in range(1, len(self.genome.brain)):
            brain_gene = self.genome.brain[i]
            
            oscillation = math.sin(2.0 * math.pi * brain_gene.frequency * time_seconds + brain_gene.phase)
            
            sensor_feedback = 0.0
            for j in range(min(len(sensor_data), len(brain_gene.sensor_weights))):
                sensor_feedback += sensor_data[j] * brain_gene.sensor_weights[j]
            
            torque = brain_gene.amplitude * (oscillation + sensor_feedback * 0.3)
            # Hard clamp to prevent explosive forces
            torque = max(min(torque, 8.0), -8.0)
            torques.append(torque)
            
        return torques
