from PySide6 import QtCore

from .instrument_controller import InstrumentController
from .query_controller import QueryController
#from .experiment_controller import ExperimentController


class AppController(QtCore.QObject):
    """
    This application coordinator.
    
    Responsibilities:
    - Own sub-controllers
    - Wire signals between controllers and GUI
    - Expose high-level slots for the GUI
    """

    # --- Signals (App -> Gui) ---
    status_updated = QtCore.Signal(str)
    query_response_updated = QtCore.Signal(str, str, str)
    
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)

        # --- Controllers ---
        self.instruments = InstrumentController()
        self.query = QueryController(self.instruments)
        #self.experiment = ExperimentController(self.instruments)

        # --- Signal wiring ---
        self.instruments.status_updated.connect(self.status_updated)
        self.query.response_ready.connect(self.query_response_updated)

    # ------------------------------------------------------------------
    # Instrument API (GUI-facing)
    # ------------------------------------------------------------------

    def connect_instrument(self, name: str, address: str) -> bool:
        return self.instruments.connect(name, address)
    
    def disconnect_instrument(self, name: str) -> None:
        self.instruments.disconnect(name)

    # ------------------------------------------------------------------
    # Query API (GUI-facing)
    # ------------------------------------------------------------------

    def send_query(self, name: str, query: str) -> None:
        self.query.send(name, query)