import sys
from PySide6 import QtWidgets

from teracontrol.gui.thz_control import THzControlWidget
from teracontrol.gui.live_plot import LivePlotWidget

from teracontrol.hal.thz.simulated import SimulatedTHzSystem
from teracontrol.acquisition.livestream import THzLiveStream
from teracontrol.acquisition.livestream_worker import LiveStreamWorker


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for teracontrol GUI.

    For now, this window only hosts a central live plot.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("teracontrol")

        # --- Core objects ---
        self.thz = SimulatedTHzSystem()
        self.worker = None

        # --- GUI widgets ---
        self.thz_control = THzControlWidget()
        self.live_plot = LivePlotWidget()

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.thz_control)
        layout.addWidget(self.live_plot)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Disconnected")

        # --- Wiring ---
        self.thz_control.connect_requested.connect(self.connect_thz)
        self.thz_control.disconnect_requested.connect(self.disconnect_thz)

        self.live_plot.run_requested.connect(self.start_livestream)
        self.live_plot.stop_requested.connect(self.stop_livestream)

        # --- THz control ---

    def connect_thz(self):
        try:
            self.thz.connect()
            self.statusBar().showMessage("Connected")
            self.thz_control.set_connected(True)
        except Exception as e:
            self.statusBar().showMessage(f"Connection error: {e}")
            self.thz_control.set_connected(False)

    def disconnect_thz(self):
        self.stop_livestream()
        self.thz.disconnect()
        self.statusBar().showMessage("Disconnected")
        self.thz_control.set_connected(False)

    # --- Livestream control ---

    def start_livestream(self):
        if self.worker is not None:
            return
        
        self.worker = LiveStreamWorker(thz=self.thz)
        self.worker.new_trace.connect(self.on_new_trace)
        self.worker.finished.connect(self.on_livestream_finished)

        self.statusBar().showMessage("Running livestream")
        self.live_plot.set_running(True)

        self.worker.start()

    def stop_livestream(self):
        if self.worker is None:
            return

        self.worker.stop()
        self.worker.quit()
        self.worker.wait()

        self.worker = None

        self.statusBar().showMessage("Connected")
        self.live_plot.set_running(False)

    def on_livestream_finished(self):
        self.worker = None
        self.statusBar().showMessage("Connected")
        self.live_plot.set_running(False)

    # --- Data Sink ---

    def on_new_trace(self, trace):
        self.live_plot.update_trace(trace["time_ps"], trace["signal"])


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()