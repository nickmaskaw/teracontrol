import time
import numpy as np


class ConnectionEngine:
    """Manages connection state for a set of instruments."""

    def __init__(self, instruments: dict):
        """
        Parameters
        ----------
        instruments: dict[str, object]
            Mapping of instrument name -> HAL instance.
            Each HAL must implement connect() / disconnect().
        """
        self.instruments = instruments
        self.connected = {name: False for name in instruments}

    def connect(self, name: str) -> bool:
        try:
            connection_simulation(name)
            self.connected[name] = True
            return True
        except Exception:
            self.connected[name] = False
            return False
        
    def disconnect(self, name: str):
        disconnection_simulation()
        self.connected[name] = False


def connection_simulation(name: str, success_weigth: float = 0.5):
    if np.random.random() < success_weigth:
        time.sleep(0.25)
    else:
        raise Exception(f"Failed to connect {name}")
    
def disconnection_simulation():
    time.sleep(0.25)