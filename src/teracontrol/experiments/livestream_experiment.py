from typing import Callable, Optional

from teracontrol.engines.livestream_engine import THzLiveStreamEngine

class LiveStreamExperiment:

    def __init__(self, thz_system, on_new_trace: Callable):
        self.thz_system = thz_system
        self._on_new_trace = on_new_trace
        self._engine: Optional[THzLiveStreamEngine] = None

    def run(self):
        if self._engine is not None:
            return
        
        self._engine = THzLiveStreamEngine(self.thz_system, self._on_new_trace)
        self._engine.run()

    def stop(self):
        if self._engine is None:
            return
        
        self._engine.stop()
        self._engine = None

    def _handle_new_trace(self, trace):
        if self._on_new_trace is not None:
            self._on_new_trace(trace)