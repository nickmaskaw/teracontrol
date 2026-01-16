from PySide6 import QtWidgets, QtCore

class ConnectionWidget(QtWidgets.QWidget):
    """Generic Widget for managing instrument connection."""

    connect_requested = QtCore.Signal(str, str)
    # name, address
    disconnect_requested = QtCore.Signal(str)
    # name

    def __init__(self, config: dict):
        super().__init__()

        self.config = config
        self.names = list(self.config.keys())

        self.edits: dict[str, QtWidgets.QLineEdit] = {}
        self.buttons: dict[str, QtWidgets.QPushButton] = {}

        # --- Internal UI state ---
        self._connected: dict[str, bool] = {name: False for name in self.names}
        self._connecting: dict[str, bool] = {name: False for name in self.names}

        layout = QtWidgets.QFormLayout()

        for name in self.names:
            # --- Address edit ---
            edit = QtWidgets.QLineEdit()
            edit.setText(self.config[name].get("address", ""))
            edit.setToolTip(self.config[name].get("address_hint", ""))
            edit.returnPressed.connect(
                lambda n=name: self._on_return_pressed(n)
            )

            # --- Connect / Disconnect button ---
            button = QtWidgets.QPushButton("Connect")
            button.clicked.connect(
                lambda _, n=name: self._on_button_clicked(n)
            )

            self.edits[name] = edit
            self.buttons[name] = button
            
            sub_layout = QtWidgets.QHBoxLayout()
            sub_layout.addWidget(edit)
            sub_layout.addWidget(button)

            layout.addRow(name, sub_layout)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # UI → Controller intent
    # ------------------------------------------------------------------

    def _on_button_clicked(self, name:str):
        if self._connecting[name]:
            return # Ignore clicks while busy
        
        if not self._connected[name]:
            self._update_edit(name)
            self.set_connecting(name, True)
            self.connect_requested.emit(name, self.edits[name].text())
        else:
            self.disconnect_requested.emit(name)

    def _on_return_pressed(self, name: str):
        if not self._connected[name] and not self._connecting[name]:
            self._button_clicked(name)

    def _update_edit(self, name: str):
        edit = self.edits[name]
        edit.setText(edit.text().strip())

    # ------------------------------------------------------------------
    # Controller → UI state updates
    # ------------------------------------------------------------------

    def set_connecting(self, name: str, connecting: bool):
        """Logical state only. No UI side effects."""
        self._connecting[name] = connecting

    def set_connected(self, name: str, connected: bool):
        """Update final connection state."""
        self._connected[name] = connected
        self._connecting[name] = False

        button = self.buttons[name]
        edit = self.edits[name]

        button.setText("Disconnect" if connected else "Connect")
        edit.setEnabled(not connected)