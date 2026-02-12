from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any
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
    run_progress = QtCore.Signal(int, int)  # current, total

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

    # --------------------------------------------------------------------------
    # Abort / pause handling
    # --------------------------------------------------------------------------

    def _check_abort(self) -> bool:
        if self._abort:
            self.runner.abort()
            self.signals.aborted.emit()
            return True
        return False
    
    def _wait_if_paused(self) -> bool:
        while self._paused:
            if self._abort:
                self.runner.abort()
                self.signals.aborted.emit()
                return False
            QtCore.QThread.msleep(self._SLEEP_QUANTUM_MS)
        return True
    
    # --------------------------------------------------------------------------
    # Comparative waiting helpers
    # --------------------------------------------------------------------------

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
    
    # --------------------------------------------------------------------------
    # Step execution
    # --------------------------------------------------------------------------

    def _position_axis(self, axis, value, dwell_s: float) -> bool:
        axis.goto(value)

        if axis.blocking:
            timeout_s = axis.estimate_settle_time_s(value)
            t0 = time.monotonic()

            while not axis.is_ready():
                
                if self._abort:
                    return False
                
                elapsed_s = time.monotonic() - t0
                
                if elapsed_s > timeout_s:
                    raise TimeoutError(
                        f"{axis.name} axis did not stabilize "
                        f"(elapsed={elapsed_s:.1f}s, expected<{timeout_s:.1f}s)"
                )
                
                self.signals.step_progress.emit(
                    int(elapsed_s * 1000),
                    int(timeout_s * 1000),
                    f"{axis.name}: stabilizing...",
                )

                QtCore.QThread.msleep(self._SLEEP_QUANTUM_MS)

        if dwell_s > 0:
            if not self._controlled_sleep(int(dwell_s * 1000)):
                return False
            
        self.signals.step_progress.emit(1, 1, "")
        return True
    
    def _run_averaging(self) -> bool:
        self.runner.capture.begin_averaging()
        timeout_s = self.runner.capture.estimate_timeout_s()

        if not self._wait_for_averaging(timeout_s):
            self.runner.capture.end_averaging()
            return False
        
        self.signals.step_progress.emit(1, 1, "")
        return True
    
    def _capture_data(
        self,
        meta: dict[str, Any],
        index: int,
    ) -> DataAtom:
        atom = self.runner.capture.capture(meta, index=index)
        self.signals.data_ready.emit(atom, meta)
        return atom
    
    def _safe_dump(
        self,
        atom: DataAtom,
        axis_name: str,
        index: int,
        npoints: int,
    ) -> None:
        if self.runner.safe_dump_dir is None:
            return
        
        now = f"{datetime.now():%Y-%m-%d_%H-%M-%S}"
        path = (
            self.runner.safe_dump_dir / 
            f"{now}_{axis_name}_{index}_of_{npoints}"
        )

        self.runner.capture.dump_save(path)

        meta_path = path.with_suffix(".json")
        payload = {
            "timestamp": atom.timestamp,
            "status": atom.status,
            "index": atom.index,
        }

        meta_path.write_text(
            json.dumps(payload, indent=4, sort_keys=True),
            encoding="utf-8",
        )

    # --------------------------------------------------------------------------
    # Qt entry points
    # --------------------------------------------------------------------------

    @QtCore.Slot()
    def run(self):
        """
        Entry point for QThread.
        """
        sweep = self.runner.sweep
        axis = sweep.axis
        npoints = sweep.npoints()

        self.signals.started.emit(sweep.describe())
        self.signals.run_progress.emit(0, npoints)

        try:
            for i, value in enumerate(sweep.points(), start=1):

                if self._check_abort():
                    return
                
                if not self._wait_if_paused():
                    return
                
                # --- Axis positioning and dwell ---
                if not self._position_axis(axis, value, sweep.dwell_s):
                    self.runner.abort()
                    self.signals.aborted.emit()
                    return

                meta = axis.describe(value)
                self.signals.step_started.emit(meta)

                # --- Firmware averaging ---
                if not self._run_averaging():
                    self.runner.abort()
                    self.signals.aborted.emit()
                    return
                
                # --- Capture ---
                atom = self._capture_data(meta, i)

                # --- Optional safe dump ---
                self._safe_dump(atom, axis.name, i, npoints)

                self.runner.capture.end_averaging()

                # --- Progress ---
                self.signals.run_progress.emit(i, npoints)
                self.signals.step_finished.emit(i, npoints)

        finally:
            self.signals.finished.emit()
            self.signals.step_progress.emit(0, 1, "")  # reset step progress
            axis.shutdown()  # cleanup

    @QtCore.Slot()
    def abort(self):
        self._abort = True

    @QtCore.Slot()
    def pause(self):
        self._paused = True

    @QtCore.Slot()
    def resume(self):
        self._paused = False
