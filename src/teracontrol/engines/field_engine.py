from teracontrol.hal import GenericMercuryController


class FieldEngine:
    def __init__(self, instrument: GenericMercuryController, device: str):
        self._instrument = instrument
        self._device = device

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_target_field(self, value: float) -> None:
        self._instrument.set_target_field(self._device, value)

    def set_current_rate(self, value: float) -> None:
        self._instrument.set_current_rate(self._device, value)

    def goto_set(self) -> None:
        self._instrument.magnet_to_set(self._device)

    def hold(self) -> None:
        self._instrument.magnet_to_hold(self._device)

    def goto_zero(self) -> None:
        self._instrument.magnet_to_zero(self._device)

    def read_field(self) -> float:
        return self._instrument.read_field(self._device)
    
    def read_field_rate(self) -> float:
        return self._instrument.read_field_rate(self._device)
    
    def read_current_rate(self) -> float:
        return self._instrument.read_current_rate(self._device)
    
    def is_holding(self) -> bool:
        return self._instrument.read_magnet_status(self._device) == "HOLD"
    
    def is_ramping_to_set(self) -> bool:
        return self._instrument.read_magnet_status(self._device) == "RTOS"
    
    def is_ramping_to_zero(self) -> bool:
        return self._instrument.read_magnet_status(self._device) == "RTOZ"
    
    def read_status(self) -> str:
        return self._instrument.read_magnet_status(self._device)