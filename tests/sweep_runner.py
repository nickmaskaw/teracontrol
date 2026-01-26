import sys
import logging
from datetime import datetime

from PySide6 import QtWidgets, QtCore

from teracontrol.core.data import Waveform, DataAtom, Experiment, capture_data
from teracontrol.core.experiment.sweep_config import SweepConfig
from teracontrol.core.experiment.runner import SweepRunner
from teracontrol.core.experiment.qt_experiment import ExperimentWorker
from teracontrol.core.experiment.sweep_axis import CountAxis

from teracontrol.gui.monitor.monitor_widget import MonitorWidget
from teracontrol.hal.teraflash import TeraflashTHzSystem
from teracontrol.hal.mercury_itc import MercuryITCController
from teracontrol.utils.logging import setup_logging


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
setup_logging(level=logging.INFO)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    # --- Hardware ---
    thz = TeraflashTHzSystem()
    itc = MercuryITCController()

    thz.connect("127.0.0.1")
    itc.connect("192.168.1.2")

    # --- Qt app ---
    app = QtWidgets.QApplication(sys.argv)

    # --- UI ---
    monitor = MonitorWidget()
    monitor.show()

    total = 50
    interval_ms = 1000

    monitor.configure(expected_load_size=total)

    # -----------------------------------------------------------------------------
    # Sweep definition
    # -----------------------------------------------------------------------------
    axis = CountAxis()

    sweep = SweepConfig(
        axis=axis,
        start=0,
        stop=total - 1,
        step=1,
        dwell_s=interval_ms / 1000,
    )

    # -----------------------------------------------------------------------------
    # Experiment container
    # -----------------------------------------------------------------------------
    experiment = Experiment(
        metadata={
            "name": "thz_count_test",
            "axis": "count",
        }
    )

    # -----------------------------------------------------------------------------
    # Runner + Qt worker
    # -----------------------------------------------------------------------------
    def capture(meta):
        trace = thz.acquire_trace()
        wf = Waveform(
            time=trace["time_abs_ps"],
            signal=trace["signal1_na"],
        )
        return capture_data(
            read_status=lambda: {
                "metadata": meta,
                "THz System": thz.status(),
                "Temperature Controller": itc.status(),
            },
            read_data=lambda: wf,
        )

    runner = SweepRunner(
        sweep=sweep,
        experiment=experiment,
        capture=capture,
    )

    thread = QtCore.QThread()
    worker = ExperimentWorker(runner)
    worker.moveToThread(thread)

    # -----------------------------------------------------------------------------
    # Signal wiring
    # -----------------------------------------------------------------------------
    def on_atom(atom: DataAtom):
        # Adapter for existing MonitorWidget API
        monitor.on_new_waveform(atom.payload, atom.status)

    thread.started.connect(worker.run)
    worker.signals.data_ready.connect(on_atom)

    worker.signals.finished.connect(thread.quit)
    worker.signals.aborted.connect(thread.quit)

    thread.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

    # -----------------------------------------------------------------------------
    # Graceful shutdown
    # -----------------------------------------------------------------------------
    def cleanup():
        worker.abort()
        thread.quit()
        thread.wait()
        itc.disconnect()
        thz.disconnect()

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
