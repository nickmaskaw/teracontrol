import pyqtgraph as pg
from PySide6 import QtWidgets, QtCore


class SignalWidget(QtWidgets.QWidget):
    """Time- and Freq-domain waveform viewer"""

    cursor_moved_signal = QtCore.Signal(float)
    pad_changed_signal = QtCore.Signal(int)

    def __init__(self):
        super().__init__()

        self.time_curves: dict[int, pg.PlotCurveItem] = {}
        self.freq_curves: dict[int, pg.PlotCurveItem] = {}

        self._setup_plots()
        self._setup_controls()

        # --- Layout ---
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.timeplot)
        layout.addWidget(self.controls)
        layout.addWidget(self.freqplot)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _setup_plots(self) -> None:
        self.timeplot = pg.PlotWidget(title="Time-domain signal")
        self.timeplot.setLabel("bottom", "Time", units="ps")
        self.timeplot.setLabel("left", "Signal", units="nA")

        self.freqplot = pg.PlotWidget(title="Spectrum")
        self.freqplot.setLogMode(y=True)
        self.freqplot.setLabel("bottom", "Frequency", units="THz")
        self.freqplot.setLabel("left", "Amplitude", units="arb. units")

    def _setup_controls(self) -> None:
        self.controls = QtWidgets.QWidget()
        self.cursor = None
        self.cursor_visor = QtWidgets.QLineEdit()
        self.pad_entry = QtWidgets.QSpinBox()

        self.cursor_visor.setReadOnly(True)
        self.cursor_visor.setMaximumWidth(100)

        self.pad_entry.setRange(0, 12)
        self.pad_entry.setValue(0)
        self.pad_entry.setToolTip(
            "Enter x to use 2^x as padding. Min=0, Max=12.\n"
            "If x=0, no padding is applied."
        )

        self.pad_entry.editingFinished.connect(self._on_pad_changed)

        layout = QtWidgets.QHBoxLayout()
        layout.addStretch()
        layout.addWidget(QtWidgets.QLabel("Truncation position:"))
        layout.addWidget(self.cursor_visor)
        layout.addSpacing(15)
        layout.addWidget(QtWidgets.QLabel("FFT padding exponent:"))
        layout.addWidget(self.pad_entry)
        self.controls.setLayout(layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_curve(self, curve) -> None:        
        new_idx = len(self.time_curves)
        
        cmap = pg.colormap.get('spectrum')
        color = cmap.map(curve.hue, mode='qcolor')
        pen = pg.mkPen(color, width=2)

        self.time_curves[new_idx] = self.timeplot.plot(
            curve.waveform.time, curve.waveform.signal, pen=pen
        )
        
        self.freq_curves[new_idx] = self.freqplot.plot(
            curve.spectrum.freq, curve.spectrum.amp, pen=pen
        )

        if self.cursor is None:
            self.cursor = pg.InfiniteLine(
                pos=curve.waveform.time[-1],
                angle=90,
                movable=True,
            )
            self.cursor.setPen(width=3)
            self.timeplot.addItem(self.cursor)
            self.cursor.sigPositionChangeFinished.connect(
                self._on_cursor_moved
            )

    def toggle_visibility(self, visible: list[bool]) -> None:
        for idx, v in enumerate(visible):
            self.time_curves[idx].setVisible(v)
            self.freq_curves[idx].setVisible(v)

    def refresh_spectra(self, curves: list[object]) -> None:
        for idx, curve in enumerate(curves):
            self.freq_curves[idx].setData(
                curve.spectrum.freq, curve.spectrum.amp
            )

    def update_cursor_visor(self, t: float) -> None:
        self.cursor_visor.setText(f"{t:.1f}")

    def clear(self) -> None:
        self.timeplot.clear()
        self.freqplot.clear()
        self.time_curves.clear()
        self.freq_curves.clear()
        self.cursor = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_cursor_moved(self, line: pg.InfiniteLine) -> None:
        pos = float(line.getPos()[0])
        self.cursor_moved_signal.emit(pos)

    def _on_pad_changed(self) -> None:
        self.pad_changed_signal.emit(self.pad_entry.value())