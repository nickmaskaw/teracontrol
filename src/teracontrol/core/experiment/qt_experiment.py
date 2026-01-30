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
    step_started = QtCore.Signal(dict)          # axis.describe(value)
    data_ready = QtCore.Signal(DataAtom, dict)  # streaming acquisition
    step_finished = QtCore.Signal(int, int)     # step index, total steps


class ExperimentWorker(QtCore.QObject):
    """
    Qt worker that exacutes a SweepRunner ia a separate thread.
    """

    def __init__(self, runner: SweepRunner):
        super().__init__()
        self.runner = runner
        self.signals = ExperimentSignals()
        self._abort = False
        self._paused = False

    @QtCore.Slot()
    def run(self):
        """
        Entry point for QThread.
        """
        sweep = self.runner.sweep
        axis = sweep.axis
        npoints = sweep.npoints()

        self.signals.started.emit(sweep.describe())

        try:
            for i, value in enumerate(sweep.points()):
                
                # --- Abort check ---
                if self._abort:
                    self.runner.abort()
                    self.signals.aborted.emit()
                    return
                
                # --- Pause loop ---
                while self._paused:
                    if self._abort:
                        self.runner.abort()
                        self.signals.aborted.emit()
                        return
                    QtCore.QThread.msleep(50)

                axis.goto(value)

                if sweep.dwell_s > 0:
                    QtCore.QThread.msleep(int(sweep.dwell_s * 1000))

                meta = axis.describe(value)
                self.signals.step_started.emit(meta)

                atom = self.runner.capture(meta)
                self.runner.experiment.record.append(atom)

                self.signals.data_ready.emit(atom, meta)
                self.signals.step_finished.emit(i+1, npoints)

        finally:
            self.signals.finished.emit()

    @QtCore.Slot()
    def abort(self):
        self._abort = True

    @QtCore.Slot()
    def pause(self):
        self._paused = True

    @QtCore.Slot()
    def resume(self):
        self._paused = False