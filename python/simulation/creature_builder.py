import pybullet as p

class DynamicCreature:
    def __init__(self, body_id, client_id, genome):
        self.body_id = body_id
        self.client_id = client_id
        self.genome = genome
        # parts dict: "part_0" is torso, "part_1" is leg1, etc.
        self.parts = {}
        for i, gene in enumerate(genome.morphology):
            self.parts[f"part_{i}"] = {"shape": "box", "size": gene.size}

    def apply_torques(self, torques):
        for i, torque in enumerate(torques):
            p.setJointMotorControl2(
                bodyUniqueId=self.body_id,
                jointIndex=i,
                controlMode=p.TORQUE_CONTROL,
                force=torque,
                physicsClientId=self.client_id,
            )

    def joint_angles(self):
        angles = []
        num_joints = p.getNumJoints(self.body_id, physicsClientId=self.client_id)
        for i in range(num_joints):
            angles.append(p.getJointState(self.body_id, i, physicsClientId=self.client_id)[0])
        return angles

    def torso_position(self):
        position, _ = p.getBasePositionAndOrientation(self.body_id, physicsClientId=self.client_id)
        return position

    def body_transforms(self):
        transforms = {}
        torso_pos, torso_ori = p.getBasePositionAndOrientation(
            self.body_id, physicsClientId=self.client_id
        )
        transforms["part_0"] = {
            "position": list(torso_pos),
            "orientation": list(torso_ori),
        }
        
        num_joints = p.getNumJoints(self.body_id, physicsClientId=self.client_id)
        for i in range(num_joints):
            state = p.getLinkState(
                self.body_id, i, computeForwardKinematics=True, physicsClientId=self.client_id
            )
            transforms[f"part_{i+1}"] = {
                "position": list(state[4]),
                "orientation": list(state[5]),
            }
        return transforms

def build_creature_from_genome(genome, client_id):
    if not genome.morphology:
        return None

    root_gene = genome.morphology[0]
    root_col = p.createCollisionShape(
        p.GEOM_BOX, halfExtents=[v / 2.0 for v in root_gene.size], physicsClientId=client_id
    )
    root_vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=[v / 2.0 for v in root_gene.size], rgbaColor=[0.25, 0.45, 0.9, 1.0], physicsClientId=client_id
    )

    link_masses = []
    link_cols = []
    link_vis = []
    link_positions = []
    link_orientations = []
    link_inertial_pos = []
    link_inertial_ori = []
    link_parents = []
    link_joint_types = []
    link_joint_axes = []

    for i in range(1, len(genome.morphology)):
        gene = genome.morphology[i]
        
        col = p.createCollisionShape(
            p.GEOM_BOX, halfExtents=[v / 2.0 for v in gene.size], physicsClientId=client_id
        )
        vis = p.createVisualShape(
            p.GEOM_BOX, halfExtents=[v / 2.0 for v in gene.size], rgbaColor=[0.9, 0.55, 0.2, 1.0], physicsClientId=client_id
        )
        
        link_masses.append(0.35)
        link_cols.append(col)
        link_vis.append(vis)
        link_positions.append(gene.attach_offset)
        link_orientations.append([0, 0, 0, 1])
        link_inertial_pos.append([0, 0, 0])
        link_inertial_ori.append([0, 0, 0, 1])
        
        link_parents.append(gene.parent_index)
        link_joint_types.append(p.JOINT_REVOLUTE)
        link_joint_axes.append(gene.joint_axis)

    body_id = p.createMultiBody(
        baseMass=1.5,
        baseCollisionShapeIndex=root_col,
        baseVisualShapeIndex=root_vis,
        basePosition=[0, 0, 0.8],
        linkMasses=link_masses,
        linkCollisionShapeIndices=link_cols,
        linkVisualShapeIndices=link_vis,
        linkPositions=link_positions,
        linkOrientations=link_orientations,
        linkInertialFramePositions=link_inertial_pos,
        linkInertialFrameOrientations=link_inertial_ori,
        linkParentIndices=link_parents,
        linkJointTypes=link_joint_types,
        linkJointAxis=link_joint_axes,
        physicsClientId=client_id,
    )

    # Base dynamics — high friction to grip ground
    p.changeDynamics(body_id, -1, lateralFriction=1.2, restitution=0.1, physicsClientId=client_id)
    
    # Joint limits and heavy damping for each link
    for i in range(len(genome.morphology) - 1):
        p.changeDynamics(
            body_id, i, 
            jointLowerLimit=-1.2, 
            jointUpperLimit=1.2,
            jointDamping=3.0,
            lateralFriction=1.2,
            restitution=0.1,
            physicsClientId=client_id
        )
        # Disable default motor so torque control works
        p.setJointMotorControl2(
            bodyUniqueId=body_id,
            jointIndex=i,
            controlMode=p.VELOCITY_CONTROL,
            force=0,
            physicsClientId=client_id,
        )

    return DynamicCreature(body_id, client_id, genome)
