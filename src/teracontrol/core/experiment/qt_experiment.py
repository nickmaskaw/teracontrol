from __future__ import annotations

import time
from datetime import datetime
from PySide6 import QtCore

from teracontrol.core.data import DataAtom
from .runner import SweepRunner

# =============================================================================
# Signals
# =============================================================================

class ExperimentSignals(QtCore.QObject):
    """
    Qt signals emitted during experiment execution.
    """

    # experiment lifecycle
    started = QtCore.Signal(dict)  # sweep metadata
    aborted = QtCore.Signal()
    finished = QtCore.Signal()

    # step lifecycle
    step_started = QtCore.Signal(dict)            # axis.describe(value)
    step_progress = QtCore.Signal(int, int, str)  # current, total, message
    data_ready = QtCore.Signal(DataAtom, dict)    # streaming acquisition
    step_finished = QtCore.Signal(int, int)       # step index, total steps
    
# =============================================================================
# Worker
# =============================================================================

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
        elapsed = 0

        while remaining > 0:
            if self._abort:
                return False
            
            step = min(self._SLEEP_QUANTUM_MS, remaining)
            QtCore.QThread.msleep(step)

            remaining -= step
            elapsed += step

            self.signals.step_progress.emit(elapsed, total_ms, "waiting...")

        return True
    
    def _wait_for_averaging(self, timeout_s: float) -> bool:
        """
        Wait cooperatively for firmware averaging to complete.
        Returns False if aborted, raises TimeoutError otherwise.
        """
        t0 = time.monotonic()

        while not self.runner.capture.is_averaging_done():
            
            if self._abort:
                return False

            elapsed = time.monotonic() - t0
            if elapsed > timeout_s:
                raise TimeoutError("Averaging timeout")
            
            self.signals.step_progress.emit(
                int(elapsed * 1000),
                int(timeout_s * 1000),
                "averaging...",
            )

            QtCore.QThread.msleep(self._SLEEP_QUANTUM_MS)
        
        return True
    
    # ------------------------------------------------------------------
    # Qt entry points
    # ------------------------------------------------------------------

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
                
                if self._abort:
                    self.runner.abort()
                    self.signals.aborted.emit()
                    return
                
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
                    if not self._controlled_sleep(int(sweep.dwell_s * 1000)):
                        self.runner.abort()
                        self.signals.aborted.emit()
                        return
                self.signals.step_progress.emit(1, 1, "waiting...")

                meta = axis.describe(value)
                self.signals.step_started.emit(meta)

                # --- Firmware averaging ---
                self.runner.capture.begin_averaging()
                timeout_s = self.runner.capture.estimate_timeout_s()

                if not self._wait_for_averaging(timeout_s):
                    self.runner.capture.end_averaging()
                    self.runner.abort()
                    self.signals.aborted.emit()
                    return
                self.signals.step_progress.emit(1, 1, "averaging...")
                
                # --- Capture data ---
                atom = self.runner.capture.capture(meta, index=i)
                self.signals.data_ready.emit(atom, meta)

                if self.runner.safe_dump_dir is not None:
                    now = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
                    path = (
                        self.runner.safe_dump_dir / 
                        f"{now}_{axis.name}_{i}_of_{npoints}"
                    )
                    print(path)
                    self.runner.capture.dump_save(path)

                self.runner.capture.end_averaging()
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