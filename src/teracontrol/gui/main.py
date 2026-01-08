import sys
from PySide6 import QtWidgets

from teracontrol.gui.thz_control import THzControlWidget
from teracontrol.gui.live_plot import LivePlotWidget
from teracontrol.app.controller import AppController


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for teracontrol GUI.
    """
    
    def __init__(self):
        super().__init__()

        # --- Controller ---
        self.controller = AppController(
            config_path="configs/experiments/live_monitor.yaml",
            on_new_trace=self.on_new_trace,
            on_status=self.update_status,
        )

        self.setWindowTitle(self.controller.config["gui"]["window_title"])

        # --- GUI widgets ---
        self.thz_control = THzControlWidget()
        self.live_plot = LivePlotWidget(
            initial_config=self.controller.config["livestream"]
        )

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.thz_control)
        layout.addWidget(self.live_plot)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Disconnected")

        # --- Wiring ---
        self.thz_control.connect_requested.connect(self.on_connect)
        self.thz_control.disconnect_requested.connect(self.on_disconnect)

        self.live_plot.run_requested.connect(self.on_run)
        self.live_plot.stop_requested.connect(self.on_stop)

    # --- GUI callbacks ---

    def on_connect(self):
        ok = self.controller.connect_thz()
        self.thz_control.set_connected(ok)

    def on_disconnect(self):
        self.controller.disconnect_thz()
        self.thz_control.set_connected(False)
        self.live_plot.set_running(False)

    def on_run(self):
        self.controller.start_livestream(
            livestream_config=self.live_plot.get_config()
        )
        self.live_plot.set_running(True)

    def on_stop(self):
        self.controller.stop_livestream()
        self.live_plot.set_running(False)

    def update_status(self, message: str):
        self.statusBar().showMessage(message)

    def on_new_trace(self, trace):
        self.live_plot.update_trace(
            trace["time_ps"],
            trace["signal"],
        )


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()