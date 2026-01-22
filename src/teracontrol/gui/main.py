import sys
import logging
import numpy as np

from PySide6 import QtWidgets

from teracontrol.app.controller import AppController
from teracontrol.gui.connection_widget import ConnectionWidget
from teracontrol.gui.livemonitor_widget import LiveMonitorWidget
from teracontrol.gui.livestream_experiment_widget import LiveStreamExperimentWidget
from teracontrol.gui.query_widget import QueryWidget
from teracontrol.gui.dock_widget import DockWidget

from teracontrol.utils.logging import setup_logging, get_logger

log = get_logger(__name__)

class MainWindow(QtWidgets.QMainWindow):
    """
    Application main window and entry point.
    """

    APP_NAME = "TeraControl 0.1.0-dev"
    WIN_SIZE = (1200, 800)

    def __init__(self) -> None:
        super().__init__()

        self._setup_window()
        self._setup_controller()
        self._setup_widgets()
        self._setup_docks()
        self._connect_signals()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    
    def _setup_window(self) -> None:
        self.setWindowTitle(self.APP_NAME)
        self.resize(*self.WIN_SIZE)
        
        self.window_menu = self.menuBar().addMenu("&Window")
        self.debug_menu = self.menuBar().addMenu("&Debug")

        self.statusBar().showMessage("Ready")

    def _setup_controller(self) -> None:
        # Parented to the main window to avoid premature garbage collection
        self.controller = AppController(parent=self)

    def _setup_widgets(self) -> None:
        self.connection_widget = ConnectionWidget(
            config=self.controller.instrument_config,
        )
        self.query_widget = QueryWidget(
            config=self.controller.instrument_config,
        )
        self.livemonitor_widget = LiveMonitorWidget()

        self.setCentralWidget(self.livemonitor_widget)

    def _setup_docks(self) -> None:
        self.connection_dock = DockWidget(
            name="Connection",
            parent=self,
            widget=self.connection_widget,
            menu=self.window_menu,
        )
        self.query_dock = DockWidget(
            name="Query",
            parent=self,
            widget=self.query_widget,
            menu=self.debug_menu,
            set_floating=True,
        )

    def _connect_signals(self) -> None:
        # --- Connection ---
        self.connection_widget.connect_requested.connect(self._on_connect)
        self.connection_widget.disconnect_requested.connect(self._on_disconnect)

        # --- Query ---
        self.query_widget.query_requested.connect(self._on_query)

        # --- Controller -> GUI ---
        self.controller.status_updated.connect(self._on_status_updated)
        self.controller.trace_updated.connect(self._on_trace_updated)
        self.controller.query_response_updated.connect(self._on_query_response)

    # ------------------------------------------------------------------
    # GUI -> Controller callbacks (user intent)
    # ------------------------------------------------------------------

    def _on_connect(self, name: str, address: str) -> None:
        ok = self.controller.connect_instrument(name, address)
        self.connection_widget.set_connected(name, ok)

    def _on_disconnect(self, name: str) -> None:
        self.controller.disconnect_instrument(name)
        self.connection_widget.set_connected(name, False)

    def _on_query(self, name: str, query: str) -> None:
        self.controller.send_query(name, query)

    # ------------------------------------------------------------------
    # Controller -> GUI callbacks
    # ------------------------------------------------------------------

    def _on_query_response(self, name: str, query: str, response: str) -> None:
        self.query_widget.update_response(name, query, response)
    
    def _on_status_updated(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_trace_updated(
        self,
        time: np.ndarray,
        signal: np.ndarray,
    ) -> None:
        self.livemonitor_widget.update_trace(time, signal)


def main() -> None:
    setup_logging(
        level=logging.INFO,
        logfile=f"logs/teracontrol.log"
    )
    
    log.info("=== Application started ===")

    try:
        app = QtWidgets.QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())    
    except Exception:
        log.exception("Application crashed", exc_info=True)
        raise
    finally:
        log.info("=== Application exited ===")

if __name__ == "__main__":
    main()