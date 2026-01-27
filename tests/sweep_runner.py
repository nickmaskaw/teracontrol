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

def read_data(meta):
    value = meta["value"]

    return Waveform(
        time=np.linspace(0, 10, 100),
        signal=value*np.sin(np.linspace(0, 10, 100)),
    )

def read_status(meta):
    status = {
        "place_holder": "placeholder",
    }
    status.update(meta)
    return status

def capture(meta: dict[str, Any]):
    _status = lambda: read_status(meta)   
    _data = lambda: read_data(meta)
    return capture_data(_status, _data)

def on_new_data(data):
    return monitor.on_new_waveform(data.payload)

count = CountAxis()
sweep = SweepConfig(count, 0, 10, 1, 1.0)

experiment = Experiment(metadata=sweep.describe())
runner = SweepRunner(sweep, experiment, capture)

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





sys.exit(app.exec())