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

    def connect(self, name: str, address: str) -> bool:
        try:
            self.instruments[name].connect(address)
            self.connected[name] = True
            return True
        except Exception:
            self.connected[name] = False
            return False
        
    def disconnect(self, name: str):
        self.instruments[name].disconnect()
        self.connected[name] = False

    def status(self) -> dict:
        return dict(self.connected)