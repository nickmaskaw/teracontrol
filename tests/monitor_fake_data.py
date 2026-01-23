import sys
import numpy as np
import logging
from PySide6 import QtWidgets, QtCore

from teracontrol.core.data import Waveform
from teracontrol.gui.monitor.monitor_widget import MonitorWidget
from teracontrol.hal.teraflash import TeraflashTHzSystem
from teracontrol.hal.mercury_itc import MercuryITCController

from teracontrol.utils.logging import setup_logging
setup_logging(level=logging.INFO)

def fake_waveform(
    delay_ps: float = 0.0,
    amplitude_nA: float = 1.0,
    noise: float = 0.0,
    n: int = 1024,
):
    t = np.linspace(-10, 10, n)  # ps
    signal = amplitude_nA * np.exp(-(t) ** 2) * np.cos(
        2 * np.pi * 0.5 * (t + delay_ps)
    )

    if noise > 0:
        signal += noise * np.random.randn(n)

    return Waveform(time=t, signal=signal)

try: 
    thz = TeraflashTHzSystem()
    itc = MercuryITCController()

    thz.connect("127.0.0.1")
    itc.connect("192.168.1.2")

    app = QtWidgets.QApplication(sys.argv)

    monitor = MonitorWidget()
    monitor.show()

    total = 50
    monitor.configure(expected_load_size=total)

    counter = 0


    def update():
        global counter

        #wf = fake_waveform(
        #    delay_ps=counter * 0.05,
        #    amplitude_nA=counter * 0.05,
        #    noise=0.0,
        #)

        #meta = {
        #    "index": counter,
        #    "delay_ps": counter * 0.05,
        #    "amplitude_nA": counter * 0.05,
        #}

        trace = thz.acquire_trace()
        meta = itc.export_temperatures()

        #print(trace)

        wf = Waveform(
            time = trace["time_abs_ps"],
            signal = trace["signal1_na"],
        )

        monitor.on_new_waveform(wf, meta=meta)
        counter += 1

        if counter >= total:
            timer.stop()

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(1000)

    sys.exit(app.exec())

finally:
    itc.disconnect()
    thz.disconnect()