import pyqtgraph as pg
from PySide6 import QtWidgets, QtCore


class LivePlotWidget(QtWidgets.QWidget):
    """
    Live THz plot with run/stop control.
    """

    run_requested = QtCore.Signal()
    stop_requested = QtCore.Signal()

    def __init__(self, initial_config: dict):
        super().__init__()

        self._running = False

        self.plot = pg.PlotWidget(title="Live THz Trace")
        self.plot.setLabel("bottom", "Time", units="ps")
        self.plot.setLabel("left", "Signal", units="nA")
        self.curve = self.plot.plot()

        self.period_input = QtWidgets.QDoubleSpinBox()
        self.period_input.setDecimals(3)
        self.period_input.setRange(0.0, 10.0)
        self.period_input.setSuffix(" s")

        self.period_input.setValue(
            initial_config.get("period_s", 0.0)
        )

        form = QtWidgets.QFormLayout()
        form.addRow("Acquisition period:", self.period_input)

        self.button = QtWidgets.QPushButton("Run")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.plot)
        layout.addLayout(form)
        layout.addWidget(self.button)
        self.setLayout(layout)

        self.button.clicked.connect(self._on_clicked)

    def get_config(self) -> dict:
        """
        Return current parameters as a config dict.
        """
        return {
            "period_s": self.period_input.value(),
        }

    def _on_clicked(self):
        if not self._running:
            self.run_requested.emit()
            self.set_running(True)
        else:
            self.stop_requested.emit()
            self.set_running(False)

    def set_running(self, running: bool):
        """
        Update UI state to reflect acquisition status.
        """
        self._running = running
        self.button.setText("Stop" if running else "Run")

    def update_trace(self, time, signal):
        self.curve.setData(time, signal)