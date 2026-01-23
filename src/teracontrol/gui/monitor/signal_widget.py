import pyqtgraph as pg
from typing import Iterable, Callable
from PySide6 import QtWidgets

# TODO: implement truncation


class SignalWidget(QtWidgets.QWidget):
    """Time- and Freq-domain waveform viewer"""

    def __init__(self):
        super().__init__()

        # --- Plots ---
        self.timeplot = pg.PlotWidget(title="Time-domain signal")
        self.timeplot.setLabel("bottom", "Time", units="ps")
        self.timeplot.setLabel("left", "Signal", units="nA")

        self.freqplot = pg.PlotWidget(title="Spectrum")
        #self.freqplot.getPlotItem().ctrl.fftCheck.setChecked(True)
        self.freqplot.setLogMode(y=True)
        self.freqplot.setLabel("bottom", "Frequency", units="THz")
        self.freqplot.setLabel("left", "Amplitude", units="arb. units")

        # --- Curves ---
        self.time_curves: dict[int, pg.PlotCurveItem] = {}
        self.freq_curves: dict[int, pg.PlotCurveItem] = {}

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.timeplot)
        layout.addWidget(self.freqplot)
        self.setLayout(layout)

    def append_curve(self, curve) -> None:
        new_idx = len(self.time_curves)
        pen = pg.mkPen(pg.hsvColor(curve.hue, 1.0, 1.0), width=2)
        
        self.time_curves[new_idx] = self.timeplot.plot(
            curve.waveform.time, curve.waveform.signal, pen=pen
        )
        
        self.freq_curves[new_idx] = self.freqplot.plot(
            curve.spectrum.freq, curve.spectrum.amp, pen=pen
        )

    def toggle_visibility(self, visible: list[bool]) -> None:
        for idx, v in enumerate(visible):
            self.time_curves[idx].setVisible(v)
            self.freq_curves[idx].setVisible(v)

    def clear(self) -> None:
        self.timeplot.clear()
        self.freqplot.clear()
        self.time_curves.clear()
        self.freq_curves.clear()