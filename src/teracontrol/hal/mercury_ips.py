from typing import Any

from teracontrol.hal.generic_mercury import GenericMercuryController


class MercuryIPSController(GenericMercuryController):
    """
    Hardware Abstraction layer (HAL) for a Mercury IPS controller.
    """
    capabilities: dict[str, bool] = {
        "temperature": True,
        "heater": False,
        "pressure": False,
        "nvalve": False,
        "magnet": True,
    }

    ignored_devices: dict[str, list[str]] = {
        "temperature": ["PT1_DB8"],
        "heater": [],
        "pressure": [],
        "nvalve": [],
        "magnet": [
            "GRPS",
            "GRPX",
            "GRPY",
        ],
    }

    def __init__(self, timeout_s: float = 5.0):
        super().__init__("Mercury ITC Controller", timeout_s)