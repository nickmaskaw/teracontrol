from typing import Any
from PySide6 import QtWidgets

from teracontrol.app.controller import AppController
from teracontrol.core.instruments import InstrumentPreset

from .monitor import MonitorWidget
from .instrument import ConnectionWidget, QueryWidget
from .dock_widget import DockWidget

from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    APP_NAME = "TeraControl 0.1.0-dev"
    WIN_SIZE = (1200, 800)

    def __init__(
        self,
        controller: AppController,
        instrument_presets: dict[str, InstrumentPreset],
    ) -> None:
        super().__init__()

        self._controller: AppController = controller
        self._instrument_names: list[str] = controller.instrument_names()
        self._filtered_presets: dict[str, InstrumentPreset] = {
            name: instrument_presets[name]
            for name in self._instrument_names
            if name in instrument_presets
        }

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
            "connection": ConnectionWidget(self._filtered_presets),
            "query": QueryWidget(self._instrument_names),
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
            "query": DockWidget(
                name="Query",
                parent=self,
                widget=self.widgets["query"],
                menu=self.menus["debug"],
                set_floating=True,
            ),
        }

    def _wire_signals(self) -> None:
        self.widgets["connection"].connect_requested.connect(
            self._on_connect
        )
        self.widgets["connection"].disconnect_requested.connect(
            self._on_disconnect
        )
        
        self.widgets["query"].query_requested.connect(
            self._on_query
        )

    # --- GUI -> Controller callbacks -------------------------------------

    def _on_connect(self, name: str, address: str) -> None:
        ok = self._controller.connect(name, address)
        self.widgets["connection"].set_connected(name, ok)
        self.widgets["query"].set_enabled(ok, name)

    def _on_disconnect(self, name: str) -> None:
        self._controller.disconnect(name)
        self.widgets["connection"].set_connected(name, False)
        self.widgets["query"].set_enabled(False, name)

    def _on_query(self, name: str, cmd: str) -> None:
        response = self._controller.query(name, cmd)
        self.widgets["query"].update_response(name, cmd, response)
