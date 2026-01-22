from typing import Iterable
from PySide6 import QtWidgets

from teracontrol.gui.monitor.signal_widget import SignalWidget
from teracontrol.gui.monitor.trends_widget import TrendsWidget

from teracontrol.core.data import Waveform


class MonitorWidget(QtWidgets.QWidget):
    """Tabbed monitor: Signal + trends"""

    def __init__(self):
        super().__init__()

        self.tabs = QtWidgets.QTabWidget()

        self.signal_widget = SignalWidget()
        self.trends_widget = TrendsWidget()

        self.tabs.addTab(self.signal_widget, "Signal")
        self.tabs.addTab(self.trends_widget, "Trends")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def update_from_waveforms(self, waveforms: Iterable[Waveform]) -> None:
        waveforms = list(waveforms)
        if not waveforms:
            return
        
        self.signal_widget.display_waveforms(waveforms)
        self.trends_widget.update_from_waveforms(waveforms)

    def clear(self) -> None:
        self.signal_widget.display_waveforms([])
        self.trends_widget.clear()