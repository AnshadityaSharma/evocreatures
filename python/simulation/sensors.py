import pybullet as p
import math

class CreatureSensors:
    def __init__(self, creature):
        self.creature = creature

    def get_state(self):
        """
        Returns a list of sensor readings:
        1. Normalized joint angle
        2. Torso touch (1.0 if touching ground, 0.0 otherwise)
        3. Leg touch (1.0 if touching ground, 0.0 otherwise)
        """
        angle = self.creature.joint_angle()
        norm_angle = math.tanh(angle)
        
        contacts = p.getContactPoints(physicsClientId=self.creature.client_id)
        
        torso_touch = 0.0
        leg_touch = 0.0
        
        for contact in contacts:
            body_a = contact[1]
            body_b = contact[2]
            link_a = contact[3]
            link_b = contact[4]
            
            if body_a == self.creature.body_id:
                if link_a == -1:
                    torso_touch = 1.0
                elif link_a == self.creature.hinge_joint_index:
                    leg_touch = 1.0
            
            if body_b == self.creature.body_id:
                if link_b == -1:
                    torso_touch = 1.0
                elif link_b == self.creature.hinge_joint_index:
                    leg_touch = 1.0

        return [norm_angle, torso_touch, leg_touch]
