import pyqtgraph as pg
from typing import Iterable
from PySide6 import QtWidgets

from teracontrol.core.data import Waveform


class SignalWidget(QtWidgets.QWidget):
    """Time- and Freq-domain waveform viewer"""

    def __init__(self):
        super().__init__()

         # --- Plots ---
        self.timeplot = pg.PlotWidget(title="Time-domain signal")
        self.timeplot.setLabel("bottom", "Time", units="ps")
        self.timeplot.setLabel("left", "Signal", units="nA")

        self.freqplot = pg.PlotWidget(title="Spectrum")
        self.freqplot.getPlotItem().ctrl.fftCheck.setChecked(True)
        self.freqplot.setLogMode(y=True)
        self.freqplot.setLabel("bottom", "Frequency", units="THz")
        self.freqplot.setLabel("left", "Amplitude", units="arb. units")

        # --- Curve storage ---
        self._time_curves = {}
        self._freq_curves = {}

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.timeplot)
        layout.addWidget(self.freqplot)
        self.setLayout(layout)

    def display_waveforms(self, waveforms: Iterable[Waveform]) -> None:
        waveforms = list(waveforms)

        self.timeplot.clear()
        self.freqplot.clear()
        self._time_curves.clear()
        self._freq_curves.clear()

        n = len(waveforms)
        if n == 0:
            return

        for i, wf in enumerate(waveforms):
            hue = (n - 1 - i) / n
            pen = pg.mkPen(pg.hsvColor(hue, 1.0, 1.0), width=2)

            self._time_curves[i] = self.timeplot.plot(
                wf.time, wf.signal, pen=pen
            )
            self._freq_curves[i] = self.freqplot.plot(
                wf.time, wf.signal, pen=pen
            )