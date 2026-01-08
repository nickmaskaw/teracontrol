import time
import numpy as np

from .base import THzAcquisitionSystem


class SimulatedTHzSystem(THzAcquisitionSystem):
    """
    A minimal simulated THz acquisition system.
    """

    def __init__(self, data_points: int = 1024):
        self.data_points = data_points
        self._connected = False

    def connect(self) -> None:
        time.sleep(0.5)  # simulate connection time
        if np.random.random() < 0.25:
            raise RuntimeError("Simulated connection failure.")
        self._connected = True
        print("Simulated THz system connected.")

    def disconnect(self) -> None:
        time.sleep(0.2)  # simulate disconnection time
        self._connected = False
        print("Simulated THz system disconnected.")
    
    def acquire(self):
        if not self._connected:
            raise RuntimeError("Simulated THz system is not connected.")
        
        time.sleep(0.25)  # simulate acqusition time

        # fake time axis (ps)
        t = np.linspace(-10, 10, self.data_points)
        # fake THz pulse
        noise = 0.02 * np.random.normal(size=self.data_points)
        signal = np.exp(-t**2) * np.cos(2 * np.pi * 0.5 * t)

        return {
            "time_ps": t,
            "signal": signal + noise,
        }



