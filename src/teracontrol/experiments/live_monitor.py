from typing import Callable, Optional

from teracontrol.acquisition.livestream import THzLiveStream


class LiveMonitorExperiment:
    """
    Headless experiment for live THz monitoring.

    This experiment:
    - starts a livestream acquisition
    - forwards traces to registered callbacks
    - can be started/stopped externally

    No GUI, no threading, no Qt.
    """

    def __init__(
        self,
        thz,
        livestream_config: dict,
        on_new_trace: Optional[Callable[[object], None]] = None,
    ):
        self.thz = thz
        self.livestream_config = livestream_config
        self._on_new_trace = on_new_trace
        self._engine: Optional[THzLiveStream] = None

    def start(self):
        if self._engine is not None:
            return
        
        period_s = self.livestream_config.get("period_s", 0.0)
        
        self._engine = THzLiveStream(
            thz=self.thz,
            on_new_trace=self._on_new_trace,
            period_s=period_s,
        )

        self._engine.start()

    def stop(self):
        if self._engine is None:
            return
        
        self._engine.stop()
        self._engine = None

    def _handle_new_trace(self, trace):
        if self._on_new_trace is not None:
            self._on_new_trace(trace)