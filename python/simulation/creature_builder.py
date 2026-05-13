import pybullet as p


TORSO_SIZE = [0.7, 0.4, 0.3]
LEG_SIZE = [0.16, 0.16, 0.7]


class SimpleCreature:
    def __init__(self, body_id, client_id, hinge_joint_index=0):
        self.body_id = body_id
        self.client_id = client_id
        self.hinge_joint_index = hinge_joint_index
        self.parts = {
            "torso": {"shape": "box", "size": TORSO_SIZE},
            "leg": {"shape": "box", "size": LEG_SIZE},
        }

    def apply_torque(self, torque):
        p.setJointMotorControl2(
            bodyUniqueId=self.body_id,
            jointIndex=self.hinge_joint_index,
            controlMode=p.TORQUE_CONTROL,
            force=torque,
            physicsClientId=self.client_id,
        )

    def joint_angle(self):
        return p.getJointState(self.body_id, self.hinge_joint_index, physicsClientId=self.client_id)[0]

    def torso_position(self):
        position, _ = p.getBasePositionAndOrientation(self.body_id, physicsClientId=self.client_id)
        return position

    def body_transforms(self):
        torso_position, torso_orientation = p.getBasePositionAndOrientation(
            self.body_id,
            physicsClientId=self.client_id,
        )
        leg_state = p.getLinkState(
            self.body_id,
            self.hinge_joint_index,
            computeForwardKinematics=True,
            physicsClientId=self.client_id,
        )

        return {
            "torso": {
                "position": list(torso_position),
                "orientation": list(torso_orientation),
            },
            "leg": {
                "position": list(leg_state[4]),
                "orientation": list(leg_state[5]),
            },
        }


def create_simple_creature(client_id):
    torso_collision = p.createCollisionShape(
        p.GEOM_BOX,
        halfExtents=[value / 2.0 for value in TORSO_SIZE],
        physicsClientId=client_id,
    )
    torso_visual = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[value / 2.0 for value in TORSO_SIZE],
        rgbaColor=[0.25, 0.45, 0.9, 1.0],
        physicsClientId=client_id,
    )
    leg_collision = p.createCollisionShape(
        p.GEOM_BOX,
        halfExtents=[value / 2.0 for value in LEG_SIZE],
        physicsClientId=client_id,
    )
    leg_visual = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[value / 2.0 for value in LEG_SIZE],
        rgbaColor=[0.9, 0.55, 0.2, 1.0],
        physicsClientId=client_id,
    )

    body_id = p.createMultiBody(
        baseMass=1.0,
        baseCollisionShapeIndex=torso_collision,
        baseVisualShapeIndex=torso_visual,
        basePosition=[0, 0, 0.8],
        linkMasses=[0.35],
        linkCollisionShapeIndices=[leg_collision],
        linkVisualShapeIndices=[leg_visual],
        linkPositions=[[0.28, 0, -0.15]],
        linkOrientations=[[0, 0, 0, 1]],
        linkInertialFramePositions=[[0, 0, 0]],
        linkInertialFrameOrientations=[[0, 0, 0, 1]],
        linkParentIndices=[0],
        linkJointTypes=[p.JOINT_REVOLUTE],
        linkJointAxis=[[0, 1, 0]],
        physicsClientId=client_id,
    )

    # Add joint limits and stabilization
    p.changeDynamics(
        body_id, 0, 
        jointLowerLimit=-1.5, 
        jointUpperLimit=1.5,
        jointDamping=2.0,
        lateralFriction=1.0, 
        physicsClientId=client_id
    )
    p.changeDynamics(body_id, -1, lateralFriction=0.8, physicsClientId=client_id)
    p.setJointMotorControl2(
        bodyUniqueId=body_id,
        jointIndex=0,
        controlMode=p.VELOCITY_CONTROL,
        force=0,
        physicsClientId=client_id,
    )

    return SimpleCreature(body_id, client_id)
