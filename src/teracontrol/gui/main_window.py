from typing import Any
from PySide6 import QtWidgets

from teracontrol.utils.logging import get_logger
from teracontrol.controllers import AppController
from teracontrol.core.instruments import InstrumentPreset

from .monitor import MonitorWidget
from .instrument import ConnectionWidget, QueryWidget
from .dock_widget import DockWidget

log = get_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    APP_NAME = "TeraControl 0.1.0-dev"
    WIN_SIZE = (1200, 800)

    def __init__(
        self,
        controller: AppController,
        instrument_presets: dict[str, InstrumentPreset] | None = None,
    ) -> None:
        super().__init__()

        self._controller: AppController = controller
        self._instrument_presets: dict[str, InstrumentPreset] = dict(
            instrument_presets
        )

        self._setup_window()
        self._setup_menus()
        self._setup_widgets()
        self._setup_layout()
        self._wire_signals()

    # --- Setups ------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle(self.APP_NAME)
        self.resize(*self.WIN_SIZE)

    def _setup_menus(self) -> None:
        self.menus = {
            "window": self.menuBar().addMenu("&Window"),
            "debug": self.menuBar().addMenu("&Debug"),
        }
    
    def _setup_widgets(self) -> None:
        self.widgets = {
            "connection": ConnectionWidget(self._instrument_presets),
            #"query": QueryWidget(),
            "monitor": MonitorWidget(),
        }
    
    def _setup_layout(self) -> None:
        self.setCentralWidget(self.widgets["monitor"])
        self.docks = {
            "connection": DockWidget(
                name="Connection",
                parent=self,
                widget=self.widgets["connection"],
                menu=self.menus["window"],
            ),
        }

    def _wire_signals(self) -> None:
        self.widgets["connection"].connect_requested.connect(
            self._on_connect
        )
        self.widgets["connection"].disconnect_requested.connect(
            self._on_disconnect
        )

    # --- GUI -> Controller callbacks -------------------------------------

    def _on_connect(self, name: str, address: str) -> None:
        ok = self._controller.connect(name, address)
        self.widgets["connection"].set_connected(name, ok)

    def _on_disconnect(self, name: str) -> None:
        self._controller.disconnect(name)
        self.widgets["connection"].set_connected(name, False)

