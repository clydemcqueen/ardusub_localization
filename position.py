import math
from typing import NamedTuple

import numpy as np


class LL(NamedTuple):
    lat: float
    lon: float


class LLI(NamedTuple):
    lat: int
    lon: int


class Position:
    """
    NED world frame. Moves in a circle clockwise at a constant velocity. Start at (r, 0) pointing east.
    """
    RADIUS = 10.0
    VELOCITY = 0.5  # m/s
    PERIOD = 2.0 * math.pi * RADIUS / VELOCITY
    THETA_V = VELOCITY / RADIUS  # r/s
    ORIGIN = LL(47.607886, -122.344324)
    GPS_NOISE = 1.0  # m

    @staticmethod
    def gps_int(ll: LL) -> LLI:
        return LLI(math.floor(ll.lat * 1e7), math.floor(ll.lon * 1e7))

    @staticmethod
    def origin_int() -> LLI:
        return Position.gps_int(Position.ORIGIN)

    def __init__(self):
        self.t = 0.0
        self.theta = 0.0
        self.x = math.cos(self.theta) * Position.RADIUS
        self.y = math.sin(self.theta) * Position.RADIUS
        self.yaw = self.theta + math.pi / 2.0  # Facing the direction of motion (east)
        self.angle_delta = [0.0, 0.0, 0.0]
        self.position_delta = [0.0, 0.0, 0.0]

    def update(self, dt: float):
        new_t = self.t + dt

        # Wrap around
        if new_t > Position.PERIOD:
            new_t -= Position.PERIOD

        new_theta = Position.THETA_V * new_t

        new_x = math.cos(new_theta) * Position.RADIUS
        new_y = math.sin(new_theta) * Position.RADIUS

        new_yaw = new_theta + math.pi / 2.0  # Facing the direction of motion
        if new_yaw > math.pi * 2.0:
            new_yaw -= math.pi * 2.0

        self.angle_delta = [0.0, 0.0, new_yaw - self.yaw]
        self.position_delta = [new_x - self.x, new_y - self.y, 0.0]

        self.t = new_t
        self.theta = new_theta
        self.x = new_x
        self.y = new_y
        self.yaw = new_yaw

    def noisy_xy(self) -> tuple[float, float]:
        return self.x + np.random.normal(0, Position.GPS_NOISE), self.y + np.random.normal(0, Position.GPS_NOISE)

    def noisy_gps(self) -> tuple[float, float]:
        nx, ny = self.noisy_xy()

        # Approximate
        dlat = nx * 180.0 / math.pi / 6371000.0
        dlon = ny / 74900.0

        return Position.gps_int(LL(Position.ORIGIN.lat + dlat, Position.ORIGIN.lon + dlon))


