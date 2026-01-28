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
from teracontrol.engines import ConnectionEngine, QueryEngine


class AppController(QtCore.QObject):
    
    def __init__(self, registry: InstrumentRegistry):
        super().__init__()

        self._registry = registry
        self._register_instruments()

        self._connection = ConnectionEngine(self._registry)
        self._query = QueryEngine(self._registry)

    # --- Internal helpers ------------------------------------------------

    def _register_instruments(self) -> None:
        self._registry.register(THZ, TeraflashTHzSystem())
        self._registry.register(TEMP, MercuryITCController())
        self._registry.register(FIELD, MercuryIPSController())

    # --- Public API ------------------------------------------------------

    def instrument_names(self) -> list[str]:
        return list(self._registry.names())

    # --- Connection API --------------------------------------------------

    def connect(self, name: str, address: str) -> bool:
        return self._connection.connect(name, address)
    
    def disconnect(self, name: str) -> None:
        self._connection.disconnect(name)

    # --- Query API -------------------------------------------------------

    def query(self, name: str, cmd: str) -> str:
        return self._query.query(name, cmd)