from PySide6 import QtWidgets, QtCore
from teracontrol.config.loader import save_config

class ConnectionWidget(QtWidgets.QWidget):
    """Generic Widget for managing instrument connection."""

    connect_requested = QtCore.Signal(str, str)
    disconnect_requested = QtCore.Signal(str)

    def __init__(self, config: dict, config_path: str):
        super().__init__()

        self.config = config
        self.names = self.config.keys()
        self.config_path = config_path

        self.combos = {}
        self.buttons = {}

        layout = QtWidgets.QFormLayout()
        for name in self.names:
            button = QtWidgets.QPushButton("Connect")
            button.clicked.connect(lambda _, n=name: self._button_clicked(n))
            
            combo = QtWidgets.QComboBox()          
            combo.setEditable(True)
            combo.addItems(self.config[name]["addresses"])
            combo.setCurrentText(self.config[name]["address_preset"])
            combo.setToolTip(self.config[name]["address_pattern"])
            combo.lineEdit().returnPressed.connect(button.click)

            self.combos[name] = combo
            self.buttons[name] = button
            
            sub_layout = QtWidgets.QHBoxLayout()
            sub_layout.addWidget(combo)
            sub_layout.addWidget(button)
            layout.addRow(name, sub_layout)

        self.setLayout(layout)

    def _button_clicked(self, name:str):
        if self.buttons[name].text() == "Connect":
            self._update_combo(name)
            self.connect_requested.emit(name, self.combos[name].currentText().strip())
        else:
            self.disconnect_requested.emit(name)

    def _update_combo(self, name: str):
        combo = self.combos[name]
        text = combo.currentText().strip()

        if combo.findText(text) == -1:
            combo.addItem(text)

    def set_connected(self, name: str, connected: bool):
        self.buttons[name].setText("Disconnect" if connected else "Connect")
        self.combos[name].setEnabled(not connected)