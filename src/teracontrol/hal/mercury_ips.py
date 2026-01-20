from typing import Any

from teracontrol.hal.generic_mercury import GenericMercuryController


class MercuryIPSController(GenericMercuryController):
    """
    Hardware Abstraction layer (HAL) for a Mercury IPS controller.
    """
    capabilities = {
        "temperature": True,
        "heater": False,
        "pressure": False,
        "nvalve": False,
        "magnet": True,
    }

    def __init__(self, timeout_s: float = 5.0):
        super().__init__("Mercury ITC Controller", timeout_s)