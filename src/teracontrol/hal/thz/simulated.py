import time
import numpy as np

from .base import THzAcquisitionSystem


class SimulatedTHzSystem(THzAcquisitionSystem):
    """
    A minimal simulated THz acquisition system.

    This class exists to:
    - validate the THz HAL interface
    - allow experiment development without hardware
    """

    def __init__(self, delay_points: int = 1024):
        self.delay_points = delay_points
        self._connected = False

    def connect(self) -> None:
        self._connected = True
        print("Simulated THz system connected.")

    def disconnect(self) -> None:
        self._connected = False
        print("Simulated THz system disconnected.")
    
    def acquire(self):
        if not self._connected:
            raise RuntimeError("Simulated THz system is not connected.")
        
        # simulate acquisition time
        time.sleep(0.1)

        # fake time axis (ps)
        t = np.linspace(-10, 10, self.delay_points)

        # fake THz pulse
        signal = np.exp(-t**2) * np.cos(2 * np.pi * 0.5 * t)

        return {
            "time_ps": t,
            "signal": signal,
        }



