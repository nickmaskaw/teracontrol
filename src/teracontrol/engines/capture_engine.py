from typing import Any

from teracontrol.core.instruments import (
    InstrumentRegistry, InstrumentCatalog
)
from teracontrol.hal import BaseHAL
from teracontrol.core.data import capture_data, Waveform, DataAtom
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class CaptureEngine:
    def __init__(self, registry: InstrumentRegistry):
        self._registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture(self, meta: dict[str, Any], index: int = 0) -> DataAtom:
        read_status = lambda: self._read_status(meta)
        read_data = lambda: self._read_data()
        return capture_data(read_status, read_data, index=index)
    
    # --- Averaging lifecycle --------------------------------------------

    def begin_averaging(self) -> None:
        thz = self._get_thz()
        thz.set_auto_off()  # ensure averaging is off
        thz.set_wait_off()  # ensure waiting is off
        thz.set_auto_on()
    
    def is_averaging_done(self) -> bool:
        thz = self._get_thz()
        return thz.read_wait_state() == "ON"
    
    def end_averaging(self) -> None:
        thz = self._get_thz()
        thz.set_auto_off()  # in case of aborting
        thz.set_wait_off()

    def estimate_timeout_s(self) -> float:
        """
        Estimate a safe timeout for firmware averaging.
        """
        thz = self._get_thz()
        try:
            tac = thz.read_tactime_s()
            return max(thz.timeout, 2.0 * tac + 3.0)
        except Exception:
            log.warning("Failed to read TAC.TIME; using default timeout")
            return thz.timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_thz(self) -> BaseHAL:
        try:
            return self._registry.get(InstrumentCatalog.THZ)
        except KeyError:
            raise KeyError("No THz instrument registered")
        

    def _read_status(self, meta: dict[str, Any]) -> dict[str, Any]:
        status = {"Metadata": meta}
        for name in self._registry.names():
            status[name] = self._registry.describe(name)
        return status
    
    def _read_data(self) -> Waveform:
        thz = self._get_thz()

        trace = thz.acquire_trace()
        time_header = "time_abs_ps"
        signal_header = (
            "signal1_na" if thz.channel == 1 else "signal2_na"
        )

        return Waveform(
            time=trace[time_header],
            signal=trace[signal_header],
        )
