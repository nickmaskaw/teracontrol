from __future__ import annotations

import sys
import numpy as np
from typing import Any

from PySide6 import QtWidgets, QtCore

from teracontrol.core.data import Waveform, capture_data
from teracontrol.core.experiment import (
    SweepRunner, SweepConfig, CountAxis, ExperimentWorker,
)
from teracontrol.core.data import Experiment
from teracontrol.gui.monitor.monitor_widget import MonitorWidget

from teracontrol.hal import TeraflashTHzSystem, MercuryITCController, MercuryIPSController
from teracontrol.engines.capture_engine import CaptureEngine

def on_new_data(data, meta):
    monitor.on_new_waveform(data.payload, meta)

thz = TeraflashTHzSystem()
itc = MercuryITCController()
ips = MercuryIPSController()

thz.connect("127.0.0.1")
itc.connect("192.168.1.2")
ips.connect("192.168.1.3")

engine = CaptureEngine(thz, itc, ips)

count = CountAxis()
sweep = SweepConfig(count, 0, 10, 1, 1.0)

experiment = Experiment(metadata=sweep.describe())
runner = SweepRunner(sweep, experiment,engine.capture)

app = QtWidgets.QApplication(sys.argv)

monitor = MonitorWidget()
monitor.show()

total = len(list(runner.sweep.points()))
monitor.configure(expected_load_size=total)

thread = QtCore.QThread()
worker = ExperimentWorker(runner)
worker.moveToThread(thread)

thread.started.connect(worker.run)
worker.signals.data_ready.connect(on_new_data)

worker.signals.finished.connect(thread.quit)
worker.signals.finished.connect(worker.deleteLater)
thread.finished.connect(thread.deleteLater)

thread.start()


def cleanup():
        worker.abort()
        thread.quit()
        thread.wait()
        itc.disconnect()
        ips.disconnect()
        thz.disconnect()

app.aboutToQuit.connect(cleanup)


sys.exit(app.exec())
