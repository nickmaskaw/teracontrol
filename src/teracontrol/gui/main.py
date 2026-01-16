import sys
import numpy as np

from PySide6 import QtWidgets

from teracontrol.app.controller import AppController
from teracontrol.gui.connection_widget import ConnectionWidget
from teracontrol.gui.livemonitor_widget import LiveMonitorWidget
from teracontrol.gui.livestream_experiment_widget import LiveStreamExperimentWidget
from teracontrol.gui.dock_widget import DockWidget


class MainWindow(QtWidgets.QMainWindow):
    """
    Application main window and entry point.
    """
    APP_NAME = "TeraControl 0.1.0-dev"
    WIN_SIZE = (1200, 800)

    def __init__(self) -> None:
        super().__init__()

        # --- Window setup ---
        self.setWindowTitle(self.APP_NAME)
        self.resize(*self.WIN_SIZE)
        self.window_menu = self.menuBar().addMenu("&Window")
        self.statusBar().showMessage("Ready")
        
        # --- Controller ---
        self.controller = AppController(
            update_status=self.update_status,
            update_trace=self.update_trace,
        )

        # --- Widgets ---
        self.connection_widget = ConnectionWidget(
            config=self.controller.instrument_config,
        )
        self.livestream_experiment_widget = LiveStreamExperimentWidget()
        self.livemonitor_widget = LiveMonitorWidget()
        
        # --- Docks ---
        self.connection_dock = DockWidget(
            name="Connection",
            parent=self,
            widget=self.connection_widget,
        )
        self.livestream_dock = DockWidget(
            name="Livestream",
            parent=self,
            widget=self.livestream_experiment_widget,
        )

        self.setCentralWidget(self.livemonitor_widget)

        # --- Wiring (signals -> callbacks) ---
        self.connection_widget.connect_requested.connect(self.connection_callback)
        self.connection_widget.disconnect_requested.connect(self.disconnection_callback)

        self.livestream_experiment_widget.run_requested.connect(self.run_callback)
        self.livestream_experiment_widget.stop_requested.connect(self.stop_callback)

    # ------------------------------------------------------------------
    # GUI Callbacks (user intent)
    # ------------------------------------------------------------------

    def connection_callback(self, name: str, address: str) -> None:
        ok = self.controller.connect_instrument(name, address)
        self.connection_widget.set_connected(name, ok)

    def disconnection_callback(self, name: str) -> None:
        self.controller.disconnect_instrument(name)
        self.connection_widget.set_connected(name, False)

    def run_callback(self) -> None:
        ok = self.controller.run_livestream()
        self.livestream_experiment_widget.set_running(ok)

    def stop_callback(self) -> None:
        self.controller.stop_livestream()
        self.livestream_experiment_widget.set_running(False)

    # ------------------------------------------------------------------
    # Controller -> GUI callbacks
    # ------------------------------------------------------------------

    def update_status(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def update_trace(
        self,
        time: np.ndarray,
        signal: np.ndarray,
    ) -> None:
        self.livemonitor_widget.update_trace(time, signal)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()