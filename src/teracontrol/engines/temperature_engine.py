from teracontrol.hal import GenericMercuryController


class TemperatureEngine:
    def __init__(self, instrument: GenericMercuryController, device: str):
        self._instrument = instrument
        self._device = device

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def begin_temperature_control(self, setpoint: float) -> None:
        self._instrument.set_temperature_setpoint(self._device, setpoint)
        self._instrument.enable_temperature_control(self._device)

    def end_temperature_control(self) -> None:
        self._instrument.disable_temperature_control(self._device)

    def read_temperature(self) -> float:
        return self._instrument.read_temperature(self._device)
    
    def read_temperature_setpoint(self) -> float:
        return self._instrument.read_temperature_setpoint(self._device)
