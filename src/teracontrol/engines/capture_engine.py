from typing import Any

from teracontrol.core.instruments import InstrumentRegistry, THZ
from teracontrol.core.data import capture_data, Waveform, DataAtom


class CaptureEngine:
    def __init__(self, registry: InstrumentRegistry):
        self._registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture(self, meta: dict[str, Any]) -> DataAtom:
        read_status = lambda: self._read_status(meta)
        read_data = lambda: self._read_data()
        return capture_data(read_status, read_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_status(self, meta: dict[str, Any]) -> dict[str, Any]:
        status = {"Metadata": meta}
        for name in self._registry.names():
            status[name] = self._registry.describe(name)
        return status
        
    def _read_data(self) -> Waveform:
        if THZ not in self._registry.names():
            raise KeyError(f"No {THZ} instrument registered")
        
        thz = self._registry.get(THZ)

        trace = thz.acquire_averaged_trace()
        time_header = "time_abs_ps"
        signal_header = (
            "signal1_na" if thz.channel == 1 else "signal2_na"
        )

        return Waveform(
            time=trace[time_header],
            signal=trace[signal_header],
        )
        
