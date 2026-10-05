"""Small camera implementation; matrices use OpenGL's column-major layout."""
import math
import numpy as np


def normalized(v):
    return v / max(float(np.linalg.norm(v)), 1e-8)


def perspective(aspect, near=0.08, far=2500.0):
    f = 1.0 / math.tan(math.radians(55) / 2)
    return np.array([[f/aspect, 0, 0, 0], [0, f, 0, 0],
                     [0, 0, (far+near)/(near-far), 2*far*near/(near-far)],
                     [0, 0, -1, 0]], dtype="f4")


class Camera:
    def __init__(self):
        self.position = np.zeros(3, dtype="f4")
        self.focus = np.zeros(3, dtype="f4")
        self.yaw = -math.pi / 2
        self.pitch = 0.0
        self.orbit_angle = 0.0
        self.orbit_radius = 125.0
        self.orbit_height = 62.0
        self.flying = False
        self.reset("galaxy")

    @property
    def forward(self):
        return np.array([math.cos(self.pitch)*math.cos(self.yaw), math.sin(self.pitch),
                         math.cos(self.pitch)*math.sin(self.yaw)], dtype="f4")

    @property
    def right(self):
        return normalized(np.cross(self.forward, [0, 1, 0])).astype("f4")

    def look_at(self, target):
        direction = normalized(np.asarray(target) - self.position)
        self.pitch = math.asin(float(np.clip(direction[1], -0.9999, 0.9999)))
        self.yaw = math.atan2(float(direction[2]), float(direction[0]))

    def reset(self, scene):
        self.focus[:] = 0
        self.orbit_angle = 0.15
        self.orbit_radius, self.orbit_height = {
            "galaxy": (112.0, 64.0), "nebula": (76.0, 13.0),
            "system": (75.0, 42.0)}[scene]
        self.flying = False
        self.orbit(0)

    def orbit(self, dt):
        self.orbit_angle += dt * 0.022
        self.position[:] = self.focus + [math.sin(self.orbit_angle)*self.orbit_radius,
                                        self.orbit_height,
                                        math.cos(self.orbit_angle)*self.orbit_radius]
        self.look_at(self.focus)

    def look(self, dx, dy):
        self.yaw += dx * 0.0025
        self.pitch = float(np.clip(self.pitch - dy * 0.0025, -1.54, 1.54))

    def move(self, local, dt, speed):
        vector = self.right * local[0] + np.array([0, 1, 0])*local[1] + self.forward*local[2]
        if np.linalg.norm(vector) > 0:
            self.position += normalized(vector) * min(dt, 0.1) * speed

    def view(self):
        f = self.forward
        r = self.right
        up = np.cross(r, f)
        matrix = np.eye(4, dtype="f4")
        matrix[0, :3] = r
        matrix[1, :3] = up
        matrix[2, :3] = -f
        matrix[:3, 3] = -matrix[:3, :3] @ self.position
        return matrix

    def matrix_bytes(self, aspect):
        return (perspective(aspect) @ self.view()).T.astype("f4").tobytes()
