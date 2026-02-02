import sys
import logging
from PySide6 import QtWidgets, QtCore

from teracontrol.core.data import Waveform
from teracontrol.gui.monitor.monitor_widget import MonitorWidget
from teracontrol.hal.teraflash import TeraflashTHzSystem
from teracontrol.hal.mercury_itc import MercuryITCController
from teracontrol.utils.logging import setup_logging


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
setup_logging(level=logging.INFO)


# -----------------------------------------------------------------------------
# Worker
# -----------------------------------------------------------------------------
class AcquisitionWorker(QtCore.QObject):
    waveform_ready = QtCore.Signal(object, dict)
    finished = QtCore.Signal()

    def __init__(self, thz, itc, total: int, interval_ms: int = 1000):
        super().__init__()
        self.thz = thz
        self.itc = itc
        self.total = total
        self.interval_ms = interval_ms
        self._running = True

    @QtCore.Slot()
    def run(self):
        counter = 0

        while self._running and counter < self.total:
            trace = self.thz.acquire_trace()
            meta = self.itc.export_temperatures()

            wf = Waveform(
                time=trace["time_abs_ps"],
                signal=trace["signal1_na"],
            )

            self.waveform_ready.emit(wf, meta)
            counter += 1

            QtCore.QThread.msleep(self.interval_ms)

        self.finished.emit()

    def stop(self):
        self._running = False


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    # --- Hardware ---
    thz = TeraflashTHzSystem()
    itc = MercuryITCController()

    thz.connect("127.0.0.1")
    itc.connect("192.168.1.2")

    app = QtWidgets.QApplication(sys.argv)

    # --- UI ---
    monitor = MonitorWidget()
    monitor.show()

    total = 50
    monitor.configure(expected_load_size=total)

    # --- Thread + worker ---
    thread = QtCore.QThread()
    worker = AcquisitionWorker(thz, itc, total=total, interval_ms=1000)
    worker.moveToThread(thread)

    # --- Connections ---
    thread.started.connect(worker.run)
    worker.waveform_ready.connect(monitor.on_new_waveform)

    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    thread.start()

    # --- Graceful shutdown ---
    def cleanup():
        worker.stop()
        thread.quit()
        thread.wait()
        itc.disconnect()
        thz.disconnect()

    app.aboutToQuit.connect(cleanup)

    sys.exit(app.exec())


# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
