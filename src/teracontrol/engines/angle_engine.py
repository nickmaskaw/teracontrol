from teracontrol.hal import KDC101Controller


class AngleEngine:
    def __init__(self, instrument: KDC101Controller):
        self._instrument = instrument

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def move_to(self, angle_deg: float) -> None:
        self._instrument.move_to(angle_deg)

    def get_position(self) -> float:
        return self._instrument.get_position()

    def is_connected(self) -> bool:
        return self._instrument.is_connected()