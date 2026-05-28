"""
Decision-making logic.
"""

import math

from pymavlink import mavutil

from ..common.modules.logger import logger
from ..telemetry import telemetry


class Position:
    """
    3D vector struct.
    """

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class Command:  # pylint: disable=too-many-instance-attributes
    """
    Command class to make a decision based on recieved telemetry,
    and send out commands based upon the data.
    """

    __private_key = object()

    @classmethod
    def create(
        cls,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> "tuple[True, Command] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a Command object.
        """
        if connection is None:
            return False, None
        return True, Command(cls.__private_key, connection, target, local_logger)

    def __init__(
        self,
        key: object,
        connection: mavutil.mavfile,
        target: Position,
        local_logger: logger.Logger,
    ) -> None:
        assert key is Command.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.target = target
        self.local_logger = local_logger

        self.total_vx = 0.0
        self.total_vy = 0.0
        self.total_vz = 0.0
        self.time = 0

    def run(self, telemetry_data: telemetry.TelemetryData) -> "list[str]":
        """
        Make a decision based on received telemetry data.
        """
        if telemetry_data is None:
            self.local_logger.warning("No telemetry data received")
            return []
        # Log average velocity for this trip so far
        self.total_vx += telemetry_data.x_velocity
        self.total_vy += telemetry_data.y_velocity
        self.total_vz += telemetry_data.z_velocity
        self.time += 1

        avg_vx = self.total_vx / self.time
        avg_vy = self.total_vy / self.time
        avg_vz = self.total_vz / self.time

        self.local_logger.info(f"Average Velocity: {avg_vx}, {avg_vy}, {avg_vz}")

        # Use COMMAND_LONG (76) message, assume the target_system=1 and target_componenet=0
        # The appropriate commands to use are instructed below
        message = []
        # Adjust height using the comand MAV_CMD_CONDITION_CHANGE_ALT (113)
        # String to return to main: "CHANGE_ALTITUDE: {amount you changed it by, delta height in meters}"
        delta_z = abs(self.target.z - telemetry_data.z)
        if delta_z > 0.5:
            self.connection.mav.command_long_send(
                1,
                0,
                mavutil.mavlink.MAV_CMD_CONDITION_CHANGE_ALT,
                0,
                1,
                0,s
                0,
                0,
                0,
                0,
                self.target.z,
            )
            self.local_logger.info("Altitude changed")
            message.append(f"CHANGE_ALTITUDE: {delta_z}")

            return message

        # Adjust direction (yaw) using MAV_CMD_CONDITION_YAW (115). Must use relative angle to current state
        # String to return to main: "CHANGING_YAW: {degree you changed it by in range [-180, 180]}"
        # Positive angle is counter-clockwise as in a right handed system
        target_angle = math.atan2(
            self.target.y - telemetry_data.y, self.target.x - telemetry_data.x
        )
        delta_yaw = target_angle - telemetry_data.yaw
        delta_yaw = math.degrees(delta_yaw)

        while delta_yaw > 180:
            delta_yaw -= 360
        while delta_yaw < -180:
            delta_yaw += 360

        if abs(delta_yaw) > 5:
            self.connection.mav.command_long_send(
                1, 0, mavutil.mavlink.MAV_CMD_CONDITION_YAW, 0, abs(delta_yaw), 5, 0, 1, 0, 0, 0
            )
            self.local_logger.info("Yaw changed")
            message.append(f"CHANGING_YAW: {delta_yaw}")

        return message


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
