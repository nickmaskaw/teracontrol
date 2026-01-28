from PySide6 import QtWidgets, QtCore
from teracontrol.core.instruments import InstrumentPreset
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class ConnectionWidget(QtWidgets.QWidget):
    
    # --- Signals ---
    connect_requested = QtCore.Signal(str, str)  # name, address
    disconnect_requested = QtCore.Signal(str)    # name

    def __init__(self, instrument_names: list[str]) -> None:
        super().__init__()

        self._names = list(instrument_names)
        
        self._edits: dict[str, QtWidgets.QLineEdit] = {}
        self._buttons: dict[str, QtWidgets.QPushButton] = {}
        self._status_leds: dict[str, QtWidgets.QLabel] = {}
        self._connected: dict[str, bool] = {
            name: False for name in self._names
        }

        self._setup_widgets()
        
    # --- Internal Helpers ------------------------------------------------        

    def _setup_widgets(self) -> None:
        layout = QtWidgets.QFormLayout()

        for name in self._names:            
            led = self._make_status_led()
            
            edit = QtWidgets.QLineEdit()

            button = QtWidgets.QPushButton("Connect")
            button.clicked.connect(
                lambda _, n=name: self._on_button_clicked(n)
            )

            self._status_leds[name] = led
            self._edits[name] = edit
            self._buttons[name] = button

            inner_layout = QtWidgets.QHBoxLayout()
            inner_layout.addWidget(edit)
            inner_layout.addWidget(led)
            inner_layout.addWidget(button)

            layout.addRow(name, inner_layout)

        self.setLayout(layout)

    def _normalize_input(self, name: str) -> None:
        edit = self._edits[name]
        edit.setText(edit.text().strip())

    def _set_pending(self, name: str, pending: bool):
        self._buttons[name].setEnabled(not pending)

    def _check_name(self, name: str) -> bool:
        if name not in self._names:
            log.warning(f"Unknown instrument name: {name}")
            return False
        
        return True
    
    def _make_status_led(self) -> QtWidgets.QLabel:
        led = QtWidgets.QLabel()
        led.setFixedSize(10, 10)
        self._set_led_color(led, "red")
        return led
    
    def _set_led_color(self, led: QtWidgets.QLabel, color: str) -> None:
        gradients = {
            "red": """
                background-color: qradialgradient(
                    cx:0.3, cy:0.3, radius:0.8,
                    fx:0.3, fy:0.3,
                    stop:0 #ffcccc,
                    stop:0.4 #ff3333,
                    stop:1 #880000
                );
            """,
            "green": """
                background-color: qradialgradient(
                    cx:0.3, cy:0.3, radius:0.8,
                    fx:0.3, fy:0.3,
                    stop:0 #ccffcc,
                    stop:0.4 #33cc33,
                    stop:1 #006600
                );
            """,
        }

        led.setStyleSheet(f"""
            border-radius: 5px;
            {gradients[color]}
        """)

    def _update_status_led(self, name: str) -> None:
        color = "green" if self._connected[name] else "red"
        self._set_led_color(self._status_leds[name], color)

    # --- Public API ------------------------------------------------------

    def apply_presets(self, presets: dict[str, InstrumentPreset]) -> None:
        for name, preset in presets.items():
            if name not in self._edits:
                continue

            edit = self._edits[name]

            if preset.address and not edit.text():
                edit.setText(preset.address)
                log.debug(
                    "Load %s preset address (%s)",
                    name, preset.address
                )

            if preset.address_type:
                edit.setToolTip(preset.address_type)
                log.debug(
                    "Load %s preset address type (%s)",
                    name, preset.address_type
                )

    # ------------------------------------------------------------------
    # UI -> Controller intent
    # ------------------------------------------------------------------

    def _on_button_clicked(self, name:str) -> None:        
        if not self._check_name(name):
            return
        
        if not self._connected[name]:
            self._set_pending(name, True)
            self._normalize_input(name)
            address = self._edits[name].text()
            log.info("Connect requested: %s @ %s", name, address)
            self.connect_requested.emit(name, address)

        else:
            log.info("Disconnect requested: %s", name)
            self.disconnect_requested.emit(name)

    # ------------------------------------------------------------------
    # Controller -> UI state updates
    # ------------------------------------------------------------------

    def set_connected(self, name: str, connected: bool):
        """Must be called by the controller on both success and failure."""
        
        if not self._check_name(name):
            return

        self._set_pending(name, False)
        self._connected[name] = connected

        button = self._buttons[name]
        edit = self._edits[name]

        button.setText("Disconnect" if connected else "Connect")
        edit.setEnabled(not connected)

        self._update_status_led(name)

        log.info(
            "Connection state updated: %s -> %s",
            name,
            "CONNECTED" if connected else "DISCONNECTED",
        )

    def set_enabled(self, enabled: bool) -> None:
        for name in self._names:
            button = self._buttons[name]
            edit = self._edits[name]

            if not enabled:
                button.setEnabled(False)
                edit.setEnabled(False)
            else:
                connected = self._connected[name]
                button.setEnabled(True)
                edit.setEnabled(not connected)