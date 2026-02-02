from PySide6 import QtWidgets, QtCore
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class QueryWidget(QtWidgets.QWidget):
    
    # --- Signals ---
    query_requested = QtCore.Signal(str, str)  # name, message

    def __init__(self, instrument_names: list[str]):
        super().__init__()

        self._names = list(instrument_names)

        self._queries: dict[str, QtWidgets.QLineEdit] = {}
        self._buttons: dict[str, QtWidgets.QPushButton] = {}
        self._response = QtWidgets.QPlainTextEdit()
        self._waiting: dict[str, bool] = {
            name: False for name in self._names
        }

        self._setup_widgets()
        self.set_enabled(False)

    # --- Internal helpers ------------------------------------------------

    def _setup_widgets(self) -> None:
        layout = QtWidgets.QFormLayout()

        self._response.setReadOnly(True)
        self._response.font().setFamily("Monospace")

        for name in self._names:
            query = QtWidgets.QLineEdit()
            query.returnPressed.connect(
                lambda n=name: self._on_return_pressed(n)
            )

            button = QtWidgets.QPushButton("Query")
            button.clicked.connect(
                lambda _, n=name: self._on_button_clicked(n)
            )

            self._queries[name] = query
            self._buttons[name] = button

            query_row = QtWidgets.QHBoxLayout()
            query_row.addWidget(query)
            query_row.addWidget(button)

            layout.addRow(name, query_row)

        layout.addRow("Response", self._response)

        self.setLayout(layout)

    
    # --- UI -> Controller intent -----------------------------------------

    def _on_button_clicked(self, name:str):
        if self._waiting[name]:
            return # Ignore clicks while waiting
        
        self._waiting[name] = True
        cmd = self._queries[name].text()
        log.info("Query requested: %s -> %s", name, cmd)
        self.query_requested.emit(name, cmd)

    def _on_return_pressed(self, name: str):
        self._on_button_clicked(name)

    # --- Controller -> UI state updates ---------------------------------

    def update_response(self, name: str, query: str, response: str):
        self._response.appendPlainText(
            f"{name}:\n    Query: {query}\n    Response: {response}\n"
        )
        self._waiting[name] = False
        log.info("Query response: %s -> %s -> %s", name, query, response)

    def set_enabled(self, enabled: bool, name: str | None = None) -> None:
        if name is None:
            names = self._names
        else:
            names = [name]

        for name in names:
            self._buttons[name].setEnabled(enabled)
            self._queries[name].setEnabled(enabled)
