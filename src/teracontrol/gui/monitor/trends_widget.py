import numpy as np
import pyqtgraph as pg
from typing import Iterable
from PySide6 import QtWidgets


class TrendsWidget(QtWidgets.QWidget):
    """Stacked plots of peak amplitude and peak position"""

    def __init__(self):
        super().__init__()

        self._x: list[int] = []
        self._amp: list[float] = []
        self._pos: list[float] = []

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

    def append_curve(self, curve) -> None:
        i = int(np.argmax(np.abs(curve.waveform.signal)))
        self._x.append(len(self._x))
        self._amp.append(float(curve.waveform.signal[i]))
        self._pos.append(float(curve.waveform.time[i]))

    def toggle_visibility(self, visible: list[bool]) -> None:
        x = [i+1 for i, v in enumerate(visible) if v]
        amp = [self._amp[i-1] for i in x]
        pos = [self._pos[i-1] for i in x]

        self.amp_curve.setData(x, amp)
        self.pos_curve.setData(x, pos)

    def clear(self) -> None:
        self._x.clear()
        self._peak_amp.clear()
        self._peak_pos.clear()
        self.amp_curve.clear()
        self.pos_curve.clear()