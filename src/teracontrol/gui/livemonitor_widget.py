import pyqtgraph as pg
from PySide6 import QtWidgets, QtCore


class LiveMonitorWidget(QtWidgets.QWidget):
    """Live plot monitor widget showing time and frequency domains."""

    def __init__(self):
        super().__init__()

        self.timeplot = pg.PlotWidget(title="Time-domain signal")
        self.timeplot.setLabel("bottom", "Time", units="ps")
        self.timeplot.setLabel("left", "Signal", units="nA")
        self.timecurve = self.timeplot.plot()

        self.freqplot = pg.PlotWidget(title="Spectrum")
        self.freqplot.getPlotItem().ctrl.fftCheck.setChecked(True)
        self.freqplot.setLogMode(y=True)
        self.freqplot.setLabel("bottom", "Frequency", units="THz")
        self.freqplot.setLabel("left", "Amplitude", units="arb. units")
        self.freqcurve = self.freqplot.plot()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.timeplot)
        layout.addWidget(self.freqplot)
        self.setLayout(layout)

    def update_trace(self, time, signal):
        self.timecurve.setData(time, signal)
        self.freqcurve.setData(time, signal)