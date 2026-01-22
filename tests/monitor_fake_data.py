import sys
import numpy as np
from PySide6 import QtWidgets, QtCore

from teracontrol.core.data import Waveform
from teracontrol.gui.monitor.monitor_widget import MonitorWidget


def fake_waveform(
    delay_ps: float = 0.0,
    amplitude_nA: float = 1.0,
    noise: float = 0.0,
    n: int = 1024,
):
    t = np.linspace(-10, 10, n)  # ps
    signal = amplitude_nA * np.exp(-(t) ** 2) * np.cos(2 * np.pi * 0.5 * (t + delay_ps))

    if noise > 0:
        signal += noise * np.random.randn(n)

    return Waveform(time=t, signal=signal)


app = QtWidgets.QApplication(sys.argv)

monitor = MonitorWidget()
monitor.show()

waveforms: list[Waveform] = []
counter = 0


def update():
    global counter
    wf = fake_waveform(delay_ps=counter * 0.05, amplitude_nA=counter * 0.05, noise=0.)
    waveforms.append(wf)
    monitor.update_from_waveforms(waveforms)
    counter += 1

    if counter >= 40:
        timer.stop()

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(500)

sys.exit(app.exec())