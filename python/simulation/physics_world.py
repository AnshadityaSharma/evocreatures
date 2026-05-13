import pybullet as p
import pybullet_data

from utils.config import GRAVITY, TIME_STEP


class PhysicsWorld:
    def __init__(self, gui=False):
        self.client_id = p.connect(p.GUI if gui else p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=self.client_id)
        p.setGravity(0, 0, GRAVITY, physicsClientId=self.client_id)
        p.setTimeStep(TIME_STEP, physicsClientId=self.client_id)
        self.plane_id = p.loadURDF("plane.urdf", physicsClientId=self.client_id)

    def step(self):
        p.stepSimulation(physicsClientId=self.client_id)

    def disconnect(self):
        if p.isConnected(self.client_id):
            p.disconnect(physicsClientId=self.client_id)
