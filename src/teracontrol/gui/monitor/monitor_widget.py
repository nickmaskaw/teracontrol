from PySide6 import QtWidgets, QtCore
from dataclasses import dataclass

from .signal_widget import SignalWidget
from .trends_widget import TrendsWidget
from .curve_list_widget import CurveListWidget
from teracontrol.core.data import Waveform, WaveSpectrum, waveform_to_wavespectrum


@dataclass
class CurveEntry:
    waveform: Waveform
    spectrum: WaveSpectrum
    visible: bool = True
    meta: dict[str, float] | None = None
    hue: float = 0.0


class MonitorWidget(QtWidgets.QWidget):
    """Tabbed monitor: Signal + Trends + Curves"""

    def __init__(self):
        super().__init__()

        # --- GUI cache / registry ---
        self._curves: list[CurveEntry] = []
        self._expected_load_size: int = 0

        # --- Child widgets ---
        self.signal_widget = SignalWidget()
        self.trends_widget = TrendsWidget()
        self.curve_list_widget = CurveListWidget()

        # wire curve list -> monitor
        self.curve_list_widget.visibility_changed.connect(
            self.set_curve_visible
        )

        # --- GUI layout ---
        self.tabs1 = QtWidgets.QTabWidget()
        self.tabs1.addTab(self.signal_widget, "Signal")
        self.tabs1.addTab(self.trends_widget, "Trends")

        self.tabs2 = QtWidgets.QTabWidget()
        self.tabs2.addTab(self.curve_list_widget, "Curves")

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.tabs1)
        splitter.addWidget(self.tabs2)

        splitter.setStretchFactor(0, 2)    # Tabs area
        splitter.setStretchFactor(1, 1)    # Curve list area
        splitter.setCollapsible(0, False)  # prevent hiding the tabs
        splitter.setCollapsible(1, False)  # prevent hiding the list

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def configure(self, expected_load_size: int) -> None:
        self._expected_load_size = expected_load_size

    def on_new_waveform(self, wf: Waveform, meta: dict | None = None) -> None:
        """Append a new waveform to the monitor"""
        sp = waveform_to_wavespectrum(wf)
        hue = self._get_hue(len(self._curves))

        curve = CurveEntry(waveform=wf, spectrum=sp, visible=True, meta=meta, hue=hue)

        self._curves.append(curve)

        self.curve_list_widget.append_curve(meta, hue)
        self.signal_widget.append_curve(curve)

        self._refresh_views()

    def set_curve_visible(self, index: int, visible: bool) -> None:
        """Toggle the visibility of a curve"""
        if 0 <= index < len(self._curves):
            self._curves[index].visible = visible
            self._refresh_views()

    def clear(self) -> None:
        self._curves.clear()
        self.signal_widget.clear()
        self.trends_widget.clear()
        self.curve_list_widget.set_curves(count=0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    
    def _refresh_views(self) -> None:
        self.signal_widget.toggle_visibility([c.visible for c in self._curves])
        self.trends_widget.update_from_waveforms(self._curves)

    def _get_hue(self, index: int) -> float:
        total = self._expected_load_size
        
        if index >= total:
            return 0.0
        
        if total <= 1:
            return 0.0
        
        return index / max(total - 1, 1)