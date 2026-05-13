import pybullet as p
import random

class DynamicCreature:
    def __init__(self, body_id, client_id, genome):
        self.body_id = body_id
        self.client_id = client_id
        self.genome = genome
        self.num_joints = p.getNumJoints(body_id, physicsClientId=client_id)
        
        # parts dict for replay export
        self.parts = {}
        for i, gene in enumerate(genome.morphology):
            self.parts[f"part_{i}"] = {"shape": "box", "size": gene.size}

    def set_joint_positions(self, target_angles):
        """Use POSITION_CONTROL to move joints to target angles.
        This naturally respects joint limits and produces smooth back-and-forth motion."""
        for i, angle in enumerate(target_angles):
            if i < self.num_joints:
                p.setJointMotorControl2(
                    bodyUniqueId=self.body_id,
                    jointIndex=i,
                    controlMode=p.POSITION_CONTROL,
                    targetPosition=angle,
                    force=5.0,           # max force the motor can exert
                    maxVelocity=3.0,     # limit how fast joints can swing
                    physicsClientId=self.client_id,
                )

    def joint_angles(self):
        angles = []
        for i in range(self.num_joints):
            angles.append(p.getJointState(self.body_id, i, physicsClientId=self.client_id)[0])
        return angles
    
    def joint_velocities(self):
        vels = []
        for i in range(self.num_joints):
            vels.append(p.getJointState(self.body_id, i, physicsClientId=self.client_id)[1])
        return vels

    def torso_position(self):
        position, _ = p.getBasePositionAndOrientation(self.body_id, physicsClientId=self.client_id)
        return position
    
    def torso_orientation(self):
        _, orientation = p.getBasePositionAndOrientation(self.body_id, physicsClientId=self.client_id)
        return orientation
    
    def torso_velocity(self):
        lin, ang = p.getBaseVelocity(self.body_id, physicsClientId=self.client_id)
        return lin, ang

    def body_transforms(self):
        transforms = {}
        torso_pos, torso_ori = p.getBasePositionAndOrientation(
            self.body_id, physicsClientId=self.client_id
        )
        transforms["part_0"] = {
            "position": list(torso_pos),
            "orientation": list(torso_ori),
        }
        
        for i in range(self.num_joints):
            state = p.getLinkState(
                self.body_id, i, computeForwardKinematics=True, physicsClientId=self.client_id
            )
            transforms[f"part_{i+1}"] = {
                "position": list(state[4]),
                "orientation": list(state[5]),
            }
        return transforms


def build_creature_from_genome(genome, client_id):
    """Build a PyBullet articulated body from a Genome.
    
    Limbs are connected to parents via hinge joints with strict limits.
    Uses POSITION_CONTROL to prevent spinning."""
    if not genome.morphology:
        return None

    root_gene = genome.morphology[0]
    root_half = [v / 2.0 for v in root_gene.size]
    
    root_col = p.createCollisionShape(
        p.GEOM_BOX, halfExtents=root_half, physicsClientId=client_id
    )
    root_vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=root_half,
        rgbaColor=[0.23, 0.51, 0.96, 1.0],
        physicsClientId=client_id
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
    
    # Color palette for limbs
    limb_colors = [
        [0.55, 0.36, 0.96, 1.0],  # purple
        [0.96, 0.62, 0.13, 1.0],  # amber
        [0.06, 0.73, 0.51, 1.0],  # emerald
        [0.94, 0.27, 0.27, 1.0],  # red
        [0.02, 0.71, 0.83, 1.0],  # cyan
        [0.93, 0.28, 0.60, 1.0],  # pink
    ]

    for i in range(1, len(genome.morphology)):
        gene = genome.morphology[i]
        limb_half = [v / 2.0 for v in gene.size]
        color = limb_colors[(i - 1) % len(limb_colors)]
        
        col = p.createCollisionShape(
            p.GEOM_BOX, halfExtents=limb_half, physicsClientId=client_id
        )
        vis = p.createVisualShape(
            p.GEOM_BOX, halfExtents=limb_half, rgbaColor=color, physicsClientId=client_id
        )
        
        link_masses.append(0.3)
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
        baseMass=2.0,
        baseCollisionShapeIndex=root_col,
        baseVisualShapeIndex=root_vis,
        basePosition=[0, 0, 0.6],
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

    # Base (torso) dynamics
    p.changeDynamics(body_id, -1, lateralFriction=1.0, restitution=0.0, physicsClientId=client_id)
    
    # Joint limits and dynamics for each limb
    for i in range(len(genome.morphology) - 1):
        p.changeDynamics(
            body_id, i, 
            jointLowerLimit=-1.0, 
            jointUpperLimit=1.0,
            jointDamping=0.5,
            lateralFriction=1.5,
            restitution=0.0,
            physicsClientId=client_id
        )

    return DynamicCreature(body_id, client_id, genome)
