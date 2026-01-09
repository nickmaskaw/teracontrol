from PySide6 import QtWidgets, QtCore


class InstrumentConnectionWidget(QtWidgets.QWidget):
    """Generic widget for managing instrument connection."""

    connect_requested = QtCore.Signal(str)
    disconnect_requested = QtCore.Signal(str)

    def __init__(self, instrument_names):
        super().__init__()

        self.buttons = {}

        layout = QtWidgets.QFormLayout()
        for name in instrument_names:
            btn = QtWidgets.QPushButton("Connect")
            btn.clicked.connect(lambda _, n=name: self._on_clicked(n))
            self.buttons[name] = btn
            layout.addRow(name, btn)

        self.setLayout(layout)

    def _on_clicked(self, name):
        if self.buttons[name].text() == "Connect":
            self.connect_requested.emit(name)
        else:
            self.disconnect_requested.emit(name)

    def set_connected(self, name:str, connected: bool):
        self.buttons[name].setText("Disconnect" if connected else "Connect")