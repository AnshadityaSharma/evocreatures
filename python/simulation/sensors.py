import pybullet as p
import math

class DynamicSensors:
    def __init__(self, creature):
        self.creature = creature

    def get_state(self):
        state = []
        
        # 1. Joint angles
        angles = self.creature.joint_angles()
        for angle in angles:
            state.append(math.tanh(angle))
            
        # 2. Touch sensors (one for each part)
        num_parts = len(self.creature.parts)
        touches = [0.0] * num_parts
        
        contacts = p.getContactPoints(physicsClientId=self.creature.client_id)
        for contact in contacts:
            body_a = contact[1]
            body_b = contact[2]
            link_a = contact[3]
            link_b = contact[4]
            
            if body_a == self.creature.body_id:
                idx = link_a + 1
                if 0 <= idx < num_parts:
                    touches[idx] = 1.0
            
            if body_b == self.creature.body_id:
                idx = link_b + 1
                if 0 <= idx < num_parts:
                    touches[idx] = 1.0
                    
        state.extend(touches)
        return state
