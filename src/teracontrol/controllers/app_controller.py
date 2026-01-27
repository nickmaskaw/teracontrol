from PySide6 import QtCore

from teracontrol.core.instruments import (
    InstrumentRegistry,
    THZ,
    TEMP,
    FIELD,
)
from teracontrol.hal import (
    TeraflashTHzSystem,
    MercuryITCController,
    MercuryIPSController,
)
from teracontrol.engines import ConnectionEngine


class AppController(QtCore.QObject):
    
    def __init__(self, registry: InstrumentRegistry):
        super().__init__()

        self._registry = registry
        self._register_instruments()

        self._connection = ConnectionEngine(self._registry)

    # --- Internal helpers ------------------------------------------------

    def _register_instruments(self) -> None:
        self._registry.register(THZ, TeraflashTHzSystem())
        self._registry.register(TEMP, MercuryITCController())
        self._registry.register(FIELD, MercuryIPSController())

    # --- Connection API --------------------------------------------------

    def connect(self, name: str, address: str) -> bool:
        return self._connection.connect(name, address)
    
    def disconnect(self, name: str) -> None:
        self._connection.disconnect(name)