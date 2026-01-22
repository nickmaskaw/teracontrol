import numpy as np
import pyqtgraph as pg
from typing import Iterable
from PySide6 import QtWidgets

from teracontrol.core.data import Waveform


class TrendsWidget(QtWidgets.QWidget):
    """Stacked plots of peak amplitude and peak position"""

    def __init__(self):
        super().__init__()

        self._x: list[int] = []
        self._peak_amp: list[float] = []
        self._peak_pos: list[float] = []
        self._counter: int = 0

        # --- Plots ---
        self.amp_plot = pg.PlotWidget(title="Peak amplitude")
        self.amp_plot.setLabel("left", "Amplitude", units="nA")
        self.amp_plot.setLabel("bottom", "Index")

        self.pos_plot = pg.PlotWidget(title="Peak position")
        self.pos_plot.setLabel("left", "Time", units="ps")
        self.pos_plot.setLabel("bottom", "Index")

        # --- Curves ---
        self.amp_curve = self.amp_plot.plot()
        self.pos_curve = self.pos_plot.plot()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.amp_plot)
        layout.addWidget(self.pos_plot)
        self.setLayout(layout)

    def update_from_waveforms(self, waveforms: Iterable[Waveform]) -> None:
        self.clear()
        
        for wf in waveforms:
            i = int(np.argmax(wf.signal))
            peak_amp = float(wf.signal[i])
            peak_pos = float(wf.time[i])

            self._x.append(self._counter)
            self._peak_amp.append(peak_amp)
            self._peak_pos.append(peak_pos)
            self._counter += 1

        if self._x:
            self.amp_curve.setData(self._x, self._peak_amp)
            self.pos_curve.setData(self._x, self._peak_pos)

    def clear(self) -> None:
        self._x.clear()
        self._peak_amp.clear()
        self._peak_pos.clear()
        self._counter = 0

        self.amp_curve.clear()
        self.pos_curve.clear()