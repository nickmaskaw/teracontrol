import time
from typing import Callable

class THzLiveStreamEngine:


    def __init__(self, thz_system, on_new_trace: Callable):
        self.thz_system = thz_system
        self.on_new_trace = on_new_trace
        self._running = False

    def run(self):
        self._running = True

        while self._running:
            trace = self.thz_system.acquire_trace()
            self.on_new_trace(trace["time_ps"], trace["signal_ch1"])
            time.sleep(0.25)

    def stop(self):
        self._running = False