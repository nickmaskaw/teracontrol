from teracontrol.hal.generic_mercury import GenericMercuryController


class MercuryITCController(GenericMercuryController):
    """
    Hardware Abstraction layer (HAL) for a Mercury ITC controller.
    """
    enabled_kinds = {
        "TEMP": True,
        "HTR": True,
        "PRES": True,
        "AUX": True,
        "PSU": False,
    }

    def __init__(self, timeout_s: float = 5.0):
        super().__init__("Mercury ITC Controller", timeout_s)