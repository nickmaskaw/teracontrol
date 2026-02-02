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

    _SLEEP_QUANTUM_MS = 50

    def __init__(self, runner: SweepRunner):
        super().__init__()
        self.runner = runner
        self.signals = ExperimentSignals()
        self._abort = False
        self._paused = False

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _controlled_sleep(self, total_ms: int) -> bool:
        """
        Sleep cooperatively, allowing pause and abort.

        Returns False if aborted, True otherwise.
        """
        remaining = total_ms
        while remaining > 0:

            # --- Abort check ---
            if self._abort:
                return False
            
            # --- Pause loop ---
            while self._paused:
                if self._abort:
                    return False
                QtCore.QThread.msleep(self._SLEEP_QUANTUM_MS)
            
            step = min(self._SLEEP_QUANTUM_MS, remaining)
            QtCore.QThread.msleep(step)
            remaining -= step

        return True

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
            for i, value in enumerate(sweep.points(), start=1):
                
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
                    QtCore.QThread.msleep(self._SLEEP_QUANTUM_MS)

                # --- Move axis ---
                axis.goto(value)

                # --- Dwell (cooperative) ---
                if sweep.dwell_s > 0:
                    ok = self._controlled_sleep(int(sweep.dwell_s * 1000))
                    if not ok:
                        self.runner.abort()
                        self.signals.aborted.emit()
                        return

                meta = axis.describe(value)
                self.signals.step_started.emit(meta)

                atom = self.runner.capture(meta, index=i)

                self.signals.data_ready.emit(atom, meta)
                self.signals.step_finished.emit(i, npoints)

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