from typing import Protocol


class Connectable(Protocol):
    """Minimal protocol for connectable instruments."""
    def connect(self, address: str) -> None: ...
    def disconnect(self) -> None: ...


class ConnectionEngine:
    """Manages connection state for a set of instruments."""

    def __init__(self, instruments: dict[str, Connectable]):
        """
        Parameters
        ----------
        instruments: dict[str, Connectable]
            Mapping of instrument name -> HAL instance.
            Each HAL must implement connect(address) / disconnect().
        """
        self.instruments = dict(instruments)
        self.connected: dict[str, bool] = {name: False for name in instruments}
        self.last_error: dict[str, Exception | None] = {
            name: None for name in instruments
        }

    # --- Public API ---

    def connect(self, name: str, address: str) -> bool:
        """
        Attempt to connect an instrument.

        Returns
        -------
        success : bool
            True if connection succeeded, False otherwise.
        """
        try:
            self.instruments[name].connect(address)
            self.connected[name] = True
            self.last_error[name] = None
            return True
        
        except Exception as e:
            self.connected[name] = False
            self.last_error[name] = e
            return False
        
    def disconnect(self, name: str) -> None:
        """Disconnect an instrument.        

        This method is idempotent: disconnecting an already
        disconnected instrument is safe.
        """
        self._check_name(name)

        if not self.connected.get(name, False):
            return
        
        try:
            self.instruments[name].disconnect()
        finally:
            # Ensure engine state is always consistent
            self.connected[name] = False

    def is_connected(self, name:str) -> bool:
        """
        Retrun True if the isntrument is currently marked as connected.
        """
        self._check_name(name)
        return self.connected[name]
    
    def connection_status(self) -> dict[str, bool]:
        """Return connection status of all instruments."""
        return dict(self.connected)
    
    def get_last_error(self, name: str) -> Exception | None:
        """
        Return the last connection error for an instrument, if any.
        """
        try:
            self._check_name(name)
            return self.last_error[name]
        except Exception as e:
            return e

    # --- Internal helpers ---

    def _check_name(self, name: str) -> None:
        if name not in self.instruments:
            raise KeyError(f"Unknown instrument: {name}")