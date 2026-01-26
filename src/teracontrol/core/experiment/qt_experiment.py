from __future__ import annotations

from PySide6 import QtCore

from teracontrol.core.data import DataAtom
from .runner import SweepRunner


class ExperimentSignals(QtCore.QObject):
    """
    Qt signals emitted during experiment execution.
    """

    # experiment lifecycle
    started = QtCore.Signal(dict)  # sweep metadata
    aborted = QtCore.Signal()
    finished = QtCore.Signal()

    # step lifecycle
    step_started = QtCore.Signal(dict)    # axis.describe(value)
    data_ready = QtCore.Signal(DataAtom)  # streaming acquisition
    step_finished = QtCore.Signal(dict)   # axis.describe(value)


class ExperimentWorker(QtCore.QObject):
    """
    Qt worker that exacutes a SweepRunner ia a separate thread.
    """

    def __init__(self, runner: SweepRunner):
        super().__init__()
        self.runner = runner
        self.signals = ExperimentSignals()
        self._abort = False

    @QtCore.Slot()
    def run(self):
        """
        Entry point for QThread.
        """
        sweep = self.runner.sweep
        axis = sweep.axis

        self.signals.started.emit(sweep.describe())

        try:
            for value in sweep.points():
                if self._abort:
                    self.experiment.abort()
                    self.signals.aborted.emit()
                    return

                axis.goto(value)

                if sweep.dwell_s > 0:
                    QtCore.QThread.msleep(int(sweep.dwell_s * 1000))

                meta = axis.describe(value)
                self.signals.step_started.emit(meta)

                atom = self.runner.capture(meta)
                self.runner.experiment.record.append(atom)

                self.signals.data_ready.emit(atom)
                self.signals.step_finished.emit(meta)

        finally:
            self.signals.finished.emit()

    def abort(self):
        """
        Request cooperative abortion of the experiment.
        """
        self._abort = True