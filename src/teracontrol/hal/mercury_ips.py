from typing import Any

from teracontrol.hal.generic_mercury import GenericMercuryController


class MercuryIPSController(GenericMercuryController):
    """
    Hardware Abstraction layer (HAL) for a Mercury IPS controller.
    """
    enabled_kinds: dict[str, bool] = {
        "TEMP": True,
        "HTR": False,
        "PRES": False,
        "AUX": False,
        "PSU": True,
    }

    def __init__(self, timeout_s: float = 5.0):
        super().__init__("Mercury ITC Controller", timeout_s)

        # --- Update ignored devices ---
        self.ignored_devices["TEMP"] = [
            "PT1_DB8",
        ]
        self.ignored_devices["PSU"] = [
            "GRPS",
            "GRPX",
            "GRPY",
            "PSU.M1",
            "PSU.M2",
        ]