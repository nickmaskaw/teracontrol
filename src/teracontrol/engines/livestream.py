import time
from typing import Callable, Optional

from teracontrol.hal.thz.base import THzAcquisitionSystem


class THzLiveStream:
    """
    Minimal livestream acquisition engine.

    Repeatedly acquires THz traces and forwards them to a callback.
    """

    def __init__(
        self,
        thz: THzAcquisitionSystem,
        on_new_trace: Callable[[object], None],
        period_s: float = 0.0,
    ):
        """
        Parameters
        ----------
        thz : THzAcquisitionSystem
            Connected THz system.
        on_new_trace : callable
            Function called with each newly acquired trace.
        period_s : float
            Optional pause between acquisitions.
        """
        self.thz = thz
        self.on_new_trace = on_new_trace
        self.period_s = period_s
        self._running = False

    def start(self, n_traces: Optional[int] = None):
        """
        Start the livestream.
        
        If n_traces is None, runs indefinitely.
        """
        self._running = True
        i = 0

        while self._running:
            trace = self.thz.acquire()
            self.on_new_trace(trace)

            i += 1
            if n_traces is not None and i >= n_traces:
                break

            if self.period_s > 0:
                time.sleep(self.period_s)

    def stop(self):
        """Stop the livestream."""
        self._running = False