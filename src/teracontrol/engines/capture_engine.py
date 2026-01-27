from typing import Any

from teracontrol.hal import BaseHAL
from teracontrol.core.data import capture_data, Waveform, DataAtom


class CaptureEngine:
    def __init__(self, thz: BaseHAL, itc: BaseHAL, ips: BaseHAL):
        self._thz = thz
        self._itc = itc
        self._ips = ips

        self.time_header = "time_abs_ps"
        self.signal_header = (
            "signal1_na" if self._thz.channel == 1 else "signal2_na"
        )

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
        return {
            "Metadata": meta,
            "THz System": self._thz.status(),
            "Temperature Controller": self._itc.status(),
            "Field Controller": self._ips.status(),
        }
    
    def _read_data(self) -> Waveform:
        trace = self._thz.acquire_averaged_trace()
        time_header = "time_abs_ps"
        signal_header = (
            "signal1_na" if self._thz.channel == 1 else "signal2_na"
        )

        return Waveform(
            time=trace[time_header],
            signal=trace[signal_header],
        )
        
