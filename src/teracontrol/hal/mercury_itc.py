from typing import Any

from teracontrol.hal.generic_mercury import GenericMercuryController


class MercuryITCController(GenericMercuryController):
    """
    Hardware Abstraction layer (HAL) for a Mercury ITC controller.
    """

    def __init__(self, timeout_s: float = 5.0):
        super().__init__("Mercury ITC Controller", timeout_s)

    def get_status(self) -> dict[str, Any]:
        """Return the status of the instrument."""
        return {
            "connected": self.is_connected(),
        }