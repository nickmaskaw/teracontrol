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
            self.instruments[name].connect()
            self.connected[name] = True
            return True
        except Exception:
            self.connected[name] = False
            return False
        
    def disconnect(self, name: str):
        self.instruments[name].disconnect()
        self.connected[name] = False

    def connect_all(self) -> dict:
        return {name: self.connect(name) for name in self.instruments}
    
    def disconnect_all(self):
        for name in self.instruments:
            self.disconnect(name)

    def status(self) -> dict:
        return dict(self.connected)