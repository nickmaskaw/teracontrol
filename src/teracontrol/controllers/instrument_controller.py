from PySide6 import QtCore

from teracontrol.hal import (
    TeraflashTHzSystem,
    MercuryITCController,
    MercuryIPSController,
    BaseHAL
)
from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.config.loader import load_config, save_config


class InstrumentController(QtCore.QObject):
    """
    Owns instrument instances and their connection lifecycle.
    Handles config persistence.
    """

    INSTRUMENT_CONFIG_PATH = "./configs/instruments.yaml"

    THZ = "THz System"
    TEMP = "Temperature Controller"
    FIELD = "Field Controller"

    # --- Signals (Controller -> App/GUI) ---
    status_updated = QtCore.Signal(str)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)

        # --- Config ---
        self._config = load_config(self.INSTRUMENT_CONFIG_PATH)

        # --- HAL instances ---
        self._instruments = {
            self.THZ: TeraflashTHzSystem(),
            self.TEMP: MercuryITCController(),
            self.FIELD: MercuryIPSController(),
        }

        # --- Engine ---
        self._connection_engine = ConnectionEngine(self._instruments)

        # --- Guard flag ---
        self._connecting: set[str] = set()

    @property
    def instruments(self) -> dict[str, BaseHAL]:
        return self._instruments
    
    @property
    def config(self) -> dict:
        return self._config

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def connect(self, name: str, address: str) -> bool:
        if name in self._connecting:
            self.status_updated.emit(f"{name}: connection already in progress")
            return False
        
        self._connecting.add(name)
        try:
            self.status_updated.emit(f"{name}: connecting to {address}...")
            ok = self._connection_engine.connect(name, address)

            if ok:
                self.status_updated.emit(
                    f"{name} (address: {address}) connected"
                )
                self._update_address(name, address)
            else:
                err = self._connection_engine.get_last_error(name)
                self.status_updated.emit(
                    f"Failed to connect {name} (address: {address})\n{err}"
                )
            
            return ok
        
        finally:
            # Aways release the guard
            self._connecting.remove(name)

    def disconnect(self, name: str) -> None:
        if name in self._connecting:
            self.status_updated.emit(f"{name}: cannot disconnect while connecting")
            return
        
        self._connection_engine.disconnect(name)
        self.status_updated.emit(f"{name} disconnected")

    def get(self, name: str) -> BaseHAL:
        """
        Access HAL instance.
        """
        return self._instruments[name]
    
    def is_connected(self, name: str) -> bool:
        return self._connection_engine.is_connected(name)
    
    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _update_address(self, name: str, address: str) -> None:
        if self._config[name].get("address") != address:
            self._config[name]["address"] = address
            save_config(self._config, self.INSTRUMENT_CONFIG_PATH)