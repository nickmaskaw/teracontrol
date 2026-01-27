from PySide6 import QtCore

from teracontrol.engines.query_engine import QueryEngine
from .instrument_controller import InstrumentController


class QueryController(QtCore.QObject):
    """
    Sends ad-hoc queries to instruments and forwards responses.
    No state, no persistence, no experiment logic.
    """

    # --- Signals (Controller -> App/GUI) ---
    response_ready = QtCore.Signal(str, str, str)  # name, query, response

    def __init__(
            self,
            instruments: InstrumentController,
            parent: QtCore.QObject | None = None,
    ):
        super().__init__(parent)

        self._instruments = instruments
        
        self._engine = QueryEngine(
            instruments=self._instruments.instruments,
            on_response=self._on_response,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(self, name: str, query: str) -> None:
        if not self._instruments.is_connected(name):
            self.response_ready.emit(
                name,
                query,
                "Instrument not connected",
            )
            return
        
        self._engine.query(name, query)

    # ------------------------------------------------------------------
    # Engine callbacks
    # ------------------------------------------------------------------

    def _on_response(self, name: str, query: str, response: str) -> None:
        self.response_ready.emit(name, query, response)