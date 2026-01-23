import numpy as np
import pyqtgraph as pg
from typing import Iterable
from PySide6 import QtWidgets


class TrendsWidget(QtWidgets.QWidget):
    """Stacked plots of peak amplitude and peak position"""

    def __init__(self):
        super().__init__()

        self._x: list[int] = []
        self._peak_amp: list[float] = []
        self._peak_pos: list[float] = []

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

    def update_from_waveforms(self, curves) -> None:
        self.clear()

        indices = [i for i, c in enumerate(curves) if c.visible]
        indices.sort()

        if not indices:
            return

        wf = [c.waveform for c in curves]

        for idx in indices:
            i = int(np.argmax(np.abs(wf[idx].signal)))
            self._x.append(idx + 1)
            self._peak_amp.append(float(wf[idx].signal[i]))
            self._peak_pos.append(float(wf[idx].time[i]))

        if self._x:
            self.amp_curve.setData(self._x, self._peak_amp)
            self.pos_curve.setData(self._x, self._peak_pos)

    def clear(self) -> None:
        self._x.clear()
        self._peak_amp.clear()
        self._peak_pos.clear()
        self.amp_curve.clear()
        self.pos_curve.clear()