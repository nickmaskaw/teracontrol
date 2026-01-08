from PySide6 import QtWidgets, QtCore


class THzControlWidget(QtWidgets.QWidget):
    """
    Minimal widget to control THz system connection.
    """

    connect_requested = QtCore.Signal()
    disconnect_requested = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self._connected = False

        self.button = QtWidgets.QPushButton("Connect")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.button.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        if not self._connected:
            self.connect_requested.emit()
            self.set_connected(True)
        else:
            self.disconnect_requested.emit()
            self.set_connected(False)

    def set_connected(self, connected: bool):
        """
        Update UI state to reflect connection status.
        """
        self._connected = connected
        self.button.setText("Disconnect" if connected else "Connect")
