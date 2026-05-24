"""
Heartbeat receiving logic.
"""

from pymavlink import mavutil

from ..common.modules.logger import logger


# =================================================================================================
#                            ↓ BOOTCAMPERS MODIFY BELOW THIS COMMENT ↓
# =================================================================================================
class HeartbeatReceiver:
    """
    HeartbeatReceiver class to send a heartbeat
    """

    __private_key = object()

    @classmethod
    def create(
        cls, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> "tuple[True, HeartbeatReceiver] | tuple[False, None]":
        """
        Falliable create (instantiation) method to create a HeartbeatReceiver object.
        """
        if connection is None:
            return False, None
        return True, HeartbeatReceiver(cls.__private_key, connection, local_logger)

    def __init__(
        self, key: object, connection: mavutil.mavfile, local_logger: logger.Logger
    ) -> None:
        assert key is HeartbeatReceiver.__private_key, "Use create() method"

        # Do any intializiation here
        self.connection = connection
        self.local_logger = local_logger
        self.missed = 0
        self.connected = False

    def run(self) -> bool:
        """
        Attempt to recieve a heartbeat message.
        If disconnected for over a threshold number of periods,
        the connection is considered disconnected.
        """
        try:
            message = self.connection.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
        except (OSError, TypeError, AttributeError) as e:
            self.local_logger.warning(f"Exception receiving heartbeat: {e}")
            self.connected = False
            return self.connected

        if message is None:
            self.missed += 1
            self.local_logger.warning("Warning, message missed")
            if self.missed >= 5:
                self.connected = False

        else:
            self.missed = 0
            self.connected = True
        return self.connected


# =================================================================================================
#                            ↑ BOOTCAMPERS MODIFY ABOVE THIS COMMENT ↑
# =================================================================================================
