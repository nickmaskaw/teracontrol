import sys
import numpy as np
from PySide6 import QtWidgets, QtCore

from teracontrol.app.controller import AppController

from teracontrol.gui.connection_widget import ConnectionWidget
from teracontrol.gui.livemonitor_widget import LiveMonitorWidget
from teracontrol.gui.livestream_experiment_widget import LiveStreamExperimentWidget

class MainWindow(QtWidgets.QMainWindow):
    """Application main window and entry point."""
    
    APP_NAME = "TeraControl 0.1.0"
    INSTRUMENT_CONFIG_PATH = "./configs/instruments.yaml"

    def __init__(self):
        super().__init__()

        # --- Definitions ---
        self.setWindowTitle(self.APP_NAME)
        self.resize(1200, 800)
        self.window_menu = self.menuBar().addMenu("&Window")
        
        # --- Controller ---
        self.controller = AppController(
            instrument_config_path=self.INSTRUMENT_CONFIG_PATH,
            update_status=self.update_status,
            update_trace=self.update_trace,
        )

        # --- Widgets ---
        self.connection_widget = ConnectionWidget(
            config=self.controller.instrument_config,
            config_path=self.INSTRUMENT_CONFIG_PATH,
        )
        self.livestream_experiment_widget = LiveStreamExperimentWidget()
        self.livemonitor_widget = LiveMonitorWidget()
        
        # --- Placement ---
        self.connection_dock = DockWidget(
            name='Connection',
            parent=self,
            widget=self.connection_widget,
        )
        self.livestream_dock = DockWidget(
            name='Livestream',
            parent=self,
            widget=self.livestream_experiment_widget,
        )
        self.setCentralWidget(self.livemonitor_widget)

        # --- Wiring ---
        self.connection_widget.connect_requested.connect(self.connection_callback)
        self.connection_widget.disconnect_requested.connect(self.disconnection_callback)

        self.livestream_experiment_widget.run_requested.connect(self.run_callback)
        self.livestream_experiment_widget.stop_requested.connect(self.stop_callback)

        # --- Fake test data ---
        t = np.linspace(-10, 10, 1024)
        # fake THz pulse
        noise = 0.02 * np.random.normal(size=1024)
        signal = np.exp(-t**2) * np.cos(2 * np.pi * 0.5 * t)
        self.livemonitor_widget.update_trace(t, signal+noise)

    # --- GUI callbacks ---

    def connection_callback(self, name: str, address: str):
        ok = self.controller.connect_instrument(name, address)
        self.connection_widget.set_connected(name, ok)

    def disconnection_callback(self, name: str):
        self.controller.disconnect_instrument(name)
        self.connection_widget.set_connected(name, False)

    def run_callback(self):
        ok = self.controller.run_livestream()
        self.livestream_experiment_widget.set_running(ok)

    def stop_callback(self):
        self.controller.stop_livestream()
        self.livestream_experiment_widget.set_running(False)

    # --- GUI helpers ---

    def update_status(self, message: str):
        self.statusBar().showMessage(message)

    def update_trace(self, time, signal):
        self.livemonitor_widget.update_trace(time, signal)


class DockWidget(QtWidgets.QDockWidget):
    def __init__(self, name, parent, widget):
        super().__init__(name, parent)
        self.name = name
        self.parent = parent
        self.widget = widget

        self.setWidget(self.widget)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
        self.parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        self.parent.window_menu.addAction(self.toggleViewAction())


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()