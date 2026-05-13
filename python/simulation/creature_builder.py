import pybullet as p

class DynamicCreature:
    def __init__(self, body_id, client_id, genome):
        self.body_id = body_id
        self.client_id = client_id
        self.genome = genome
        self.num_joints = p.getNumJoints(body_id, physicsClientId=client_id)
        
        self.parts = {}
        for i, gene in enumerate(genome.morphology):
            self.parts[f"part_{i}"] = {"shape": "box", "size": gene.size}

    def set_joint_positions(self, target_angles):
        """Use POSITION_CONTROL to move joints to target angles."""
        for i, angle in enumerate(target_angles):
            if i < self.num_joints:
                p.setJointMotorControl2(
                    bodyUniqueId=self.body_id,
                    jointIndex=i,
                    controlMode=p.POSITION_CONTROL,
                    targetPosition=angle,
                    force=25.0,         # Stronger muscles
                    maxVelocity=12.0,   # Faster swings
                    physicsClientId=self.client_id,
                )

    def joint_angles(self):
        return [p.getJointState(self.body_id, i, physicsClientId=self.client_id)[0]
                for i in range(self.num_joints)]
    
    def joint_velocities(self):
        return [p.getJointState(self.body_id, i, physicsClientId=self.client_id)[1]
                for i in range(self.num_joints)]

    def torso_position(self):
        pos, _ = p.getBasePositionAndOrientation(self.body_id, physicsClientId=self.client_id)
        return pos
    
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
                self.body_id, i, computeForwardKinematics=True,
                physicsClientId=self.client_id
            )
            transforms[f"part_{i+1}"] = {
                "position": list(state[4]),
                "orientation": list(state[5]),
            }
        return transforms


def build_creature_from_genome(genome, client_id):
    """Build a proper quadruped from genome.
    
    PyBullet coordinate system:
      X = left/right
      Y = front/back  
      Z = up/down (gravity is -Z)
    
    The creature is a flat torso with 4 legs hanging below it.
    Each leg is a vertical stick attached via a hinge joint at the
    bottom face of the torso. The inertial frame offset makes
    legs hang DOWN from the joint pivot.
    """
    if not genome.morphology:
        return None

    root_gene = genome.morphology[0]
    # Torso: size = [width_x, depth_y, height_z]
    root_half = [v / 2.0 for v in root_gene.size]
    
    root_col = p.createCollisionShape(
        p.GEOM_BOX, halfExtents=root_half, physicsClientId=client_id
    )
    root_vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=root_half,
        rgbaColor=[0.2, 0.5, 0.95, 1.0],
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
    
    limb_colors = [
        [0.55, 0.36, 0.96, 1.0],
        [0.96, 0.62, 0.13, 1.0],
        [0.06, 0.73, 0.51, 1.0],
        [0.94, 0.27, 0.27, 1.0],
        [0.02, 0.71, 0.83, 1.0],
        [0.93, 0.28, 0.60, 1.0],
    ]

    torso_half_x = root_half[0]  # half width
    torso_half_y = root_half[1]  # half depth
    torso_half_z = root_half[2]  # half height

    for i in range(1, len(genome.morphology)):
        gene = genome.morphology[i]
        limb_half = [v / 2.0 for v in gene.size]
        color = limb_colors[(i - 1) % len(limb_colors)]
        
        col = p.createCollisionShape(
            p.GEOM_BOX, halfExtents=limb_half, physicsClientId=client_id
        )
        vis = p.createVisualShape(
            p.GEOM_BOX, halfExtents=limb_half, rgbaColor=color,
            physicsClientId=client_id
        )
        
        # Leg hangs down: inertial frame offset puts COM below the joint
        leg_half_z = limb_half[2]
        
        link_masses.append(0.25)
        link_cols.append(col)
        link_vis.append(vis)
        # Joint position relative to parent (torso center)
        link_positions.append(gene.attach_offset)
        link_orientations.append([0, 0, 0, 1])
        # KEY: offset the center of mass BELOW the joint so leg hangs down
        link_inertial_pos.append([0, 0, -leg_half_z])
        link_inertial_ori.append([0, 0, 0, 1])
        link_parents.append(gene.parent_index)
        link_joint_types.append(p.JOINT_REVOLUTE)
        link_joint_axes.append(gene.joint_axis)

    # Spawn high enough that legs don't clip ground
    spawn_z = 0.8
    # Estimate: torso bottom + longest leg
    if len(genome.morphology) > 1:
        max_leg_z = max(g.size[2] for g in genome.morphology[1:])
        spawn_z = torso_half_z + max_leg_z + 0.05

    body_id = p.createMultiBody(
        baseMass=2.0,
        baseCollisionShapeIndex=root_col,
        baseVisualShapeIndex=root_vis,
        basePosition=[0, 0, spawn_z],
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

    # Torso: high friction, no bounce
    p.changeDynamics(body_id, -1, lateralFriction=0.8, restitution=0.0,
                     physicsClientId=client_id)
    
    # Each leg: joint limits, friction on feet
    for i in range(len(genome.morphology) - 1):
        p.changeDynamics(
            body_id, i, 
            jointLowerLimit=-0.8, 
            jointUpperLimit=0.8,
            jointDamping=0.3,
            lateralFriction=2.0,   # high friction on feet for grip
            restitution=0.0,
            physicsClientId=client_id
        )

    return DynamicCreature(body_id, client_id, genome)
