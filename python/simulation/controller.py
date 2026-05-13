import math

class OscillatoryController:
    def __init__(self, num_sensors, num_outputs, amplitude=3.0, frequency=2.0):
        self.num_sensors = num_sensors
        self.num_outputs = num_outputs
        
        # Hardcoded parameters for Phase 5.
        # In Phase 6 (Genome), these will be driven by DNA and mutation.
        self.amplitude = amplitude
        self.frequency = frequency
        self.phase_offset = 0.0
        
        # Simple sensor weights to feedback into the oscillation
        self.sensor_weights = [0.5, 1.0, -1.0]

    def get_torques(self, time_seconds, sensor_data):
        """
        Calculate torque outputs based on an internal clock (oscillation) 
        modulated by sensor feedback.
        """
        # Base internal pattern generator
        oscillation = math.sin(2.0 * math.pi * self.frequency * time_seconds + self.phase_offset)
        
        # Sensor feedback modulation
        sensor_feedback = 0.0
        for i in range(min(len(sensor_data), len(self.sensor_weights))):
            sensor_feedback += sensor_data[i] * self.sensor_weights[i]
        
        # Combine and scale
        torque = self.amplitude * (oscillation + sensor_feedback * 0.5)
        
        # Clamp torque for stability
        torque = max(min(torque, 15.0), -15.0)
        
        return [torque]
