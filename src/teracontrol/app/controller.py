from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Any
from PySide6 import QtCore

from teracontrol.app.context import AppContext
from teracontrol.core.instruments import (
    INSTRUMENT_DEFAULTS,
    InstrumentCatalog,
)
from teracontrol.core.experiment import (
    AXIS_CATALOG,
    AXIS_DEFAULTS,
    SweepAxis,
    SweepConfig,
    SweepRunner,
    ExperimentWorker,
    ExperimentStatus,
)
from teracontrol.core.data import DataAtom
from teracontrol.hal import (
    TeraflashTHzSystem,
    MercuryITCController,
    MercuryIPSController,
)
from teracontrol.engines import (
    ConnectionEngine,
    QueryEngine,
    CaptureEngine,
    HDF5RunWriter,
)
from teracontrol.config import load_config, save_config
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class AppController(QtCore.QObject):

    # --- Signals (Controller -> GUI) ---
    experiment_status_updated = QtCore.Signal(ExperimentStatus)
    data_ready = QtCore.Signal(DataAtom, dict)
    experiment_finished = QtCore.Signal()
    sweep_created = QtCore.Signal(int)
    step_finished = QtCore.Signal(int, int)
    step_progress = QtCore.Signal(int, int, str)
    
    def __init__(self, context: AppContext):
        super().__init__()

        self._context = context
        self._registry = context.registry

        self._registry.register(InstrumentCatalog.THZ, TeraflashTHzSystem())
        self._registry.register(InstrumentCatalog.TEMP, MercuryITCController())
        self._registry.register(InstrumentCatalog.FIELD, MercuryIPSController())

        print(InstrumentCatalog.THZ)

        self._presets: dict[str, Any] = {}
        self._load_presets()

        # --- Engines ---
        self._connection = ConnectionEngine(self._registry)
        self._query = QueryEngine(self._registry)
        self._capture = CaptureEngine(self._registry)

        self._reset_experiment_state()
        log.info("=== AppController initialized ===")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_presets(self) -> None:
        try:
            presets_path = self._context.config_dir / "presets.json"
            presets = load_config(presets_path)
            log.info("Loaded presets file: %s", presets_path)
            self._presets.update(presets)
        except Exception:
            log.warning("Failed to load presets file", exc_info=True)

        if "instruments" not in self._presets:
            self._presets["instruments"] = INSTRUMENT_DEFAULTS

        if "axes" not in self._presets:
            self._presets["axes"] = AXIS_DEFAULTS

    def _reset_experiment_state(self) -> None:
        self._axis: SweepAxis | None = None
        self._sweep: SweepConfig | None = None
        self._runner: SweepRunner | None = None
        self._worker: ExperimentWorker | None = None
        self._writer: HDF5RunWriter | None = None
        self._thread: QtCore.QThread | None = None

    def _experiment_running(self) -> bool:
        return self._context.experiment_status in {
            ExperimentStatus.RUNNING,
            ExperimentStatus.PAUSED,
        }
    
    def _set_status(self, status: ExperimentStatus) -> None:
        if self._context.experiment_status == status:
            return
        
        log.debug(
            "Experiment status: %s -> %s",
            self._context.experiment_status,
            status,
        )

        self._context.experiment_status = status
        self.experiment_status_updated.emit(status)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def instrument_names(self) -> list[str]:
        return list(self._registry.names())
    
    def axis_catalog(self) -> dict[str, type[SweepAxis]]:
        return AXIS_CATALOG
    
    def presets(self) -> dict[str, Any]:
        return self._presets
    
    def cleanup(self) -> None:
        self._registry.disconnect_all()
        self._cleanup_experiment()

    def save_presets(self) -> None:
        try:
            presets_path = self._context.config_dir / "presets.json"
            save_config(self._presets, presets_path)
            log.info("Saved presets file: %s", presets_path)
        except Exception:
            log.warning("Failed to save presets file", exc_info=True)

    # ------------------------------------------------------------------
    # Connection API
    # ------------------------------------------------------------------

    def connect(self, name: str, address: str) -> bool:
        try:
            self._presets["instruments"][name]["address"] = address
        except Exception:
            log.error("Failed to update presets", exc_info=True)
        
        return self._connection.connect(name, address)
    
    def disconnect(self, name: str) -> None:
        self._connection.disconnect(name)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def query(self, name: str, cmd: str) -> str:
        return self._query.query(name, cmd)
    
    # ------------------------------------------------------------------
    # Experiment API
    # ------------------------------------------------------------------

    def run_experiment(self, config: dict[str, Any]) -> bool:
        if self._experiment_running():
            log.warning("Experiment already running")
            return False
        
        if config["meta"]["operator"] == "":
            log.warning("Operator name not set")
            return False
        
        if config["meta"]["sample"] == "":
            log.warning("Sample name not set")
            return False
        
        self._presets["axes"][config["axis"]] = config["pars"]

        try:
            self._build_experiment(config)
            self._start_worker_thread()
            self._set_status(ExperimentStatus.RUNNING)
            return True
        
        except Exception:
            log.error("Failed to run experiment", exc_info=True)
            self._set_status(ExperimentStatus.IDLE)
            self._cleanup_experiment()
            return False
        
    def abort_experiment(self) -> bool:
        return self._forward_worker_call("abort")

    def pause_experiment(self) -> bool:
        ok = self._forward_worker_call("pause")
        if ok:
            self._set_status(ExperimentStatus.PAUSED)
        return ok
    
    def resume_experiment(self) -> bool:
        ok = self._forward_worker_call("resume")
        if ok:
            self._set_status(ExperimentStatus.RUNNING)
        return ok

    # ------------------------------------------------------------------
    # Experiment construction
    # ------------------------------------------------------------------

    def _build_experiment(self, config: dict[str, Any]) -> None:
        axis_name = config["axis"]
        pars = config["pars"]
        meta = config["meta"]

        axis_cls = AXIS_CATALOG[axis_name]
        self._axis = axis_cls()

        self._sweep = SweepConfig(
            axis=self._axis,
            start=pars["start"],
            stop=pars["stop"],
            step=pars["step"],
            dwell_s=pars["dwell"],
        )

        self.sweep_created.emit(self._sweep.npoints())

        self._runner = SweepRunner(
            sweep=self._sweep,
            capture_engine=self._capture,
            safe_dump_dir=self._context.data_dir / "safe_dumps",
        )
        self._worker = ExperimentWorker(self._runner)

        self._writer = HDF5RunWriter(
            self._context.data_dir /
            f"{datetime.now():%Y-%m-%d_%H-%M-%S}_"
            f"{meta["operator"]}_{meta["sample"]}_"
            f"{self._axis.name}.h5"
        )
        self._writer.open(
            sweep_meta=self._sweep.describe(),
            user_meta=meta,
        )

    def _start_worker_thread(self) -> None:
        assert self._worker is not None

        self._thread = QtCore.QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
            
        signals = self._worker.signals
        signals.step_progress.connect(self._on_step_progress)
        signals.data_ready.connect(self._on_data_ready)
        signals.data_ready.connect(
            lambda atom, _: self._writer.write(atom.index, atom)
        )
        signals.step_finished.connect(self._on_step_finished)

        signals.started.connect(
            lambda _: self._set_status(ExperimentStatus.RUNNING)
        )
        signals.aborted.connect(
            lambda: self._set_status(ExperimentStatus.IDLE)
        )
        signals.aborted.connect(
            lambda: self._writer.close(status="aborted")
        )
        signals.finished.connect(
            lambda: self._set_status(ExperimentStatus.IDLE)
        )
        signals.finished.connect(
            lambda: self._writer.close(status="completed")
        )

        signals.finished.connect(self.experiment_finished)
        signals.finished.connect(self._thread.quit)
        signals.finished.connect(self._worker.deleteLater)
            
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_experiment)

        self._thread.start()

    # ------------------------------------------------------------------
    # Cleanup and forwarding
    # ------------------------------------------------------------------

    def _cleanup_experiment(self) -> None:
        if self._writer is not None:
            try:
                self._writer.close(status="aborted")
            except Exception:
                pass

        self._reset_experiment_state()
        self._set_status(ExperimentStatus.IDLE)
        log.debug("Experiment state cleaned up")

    def _forward_worker_call(self, method: str) -> bool:
        if not self._experiment_running():
            log.warning("Experiment not running")
            return False
        
        getattr(self._worker, method)()
        return True

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_data_ready(self, data: DataAtom, meta: dict[str, Any]) -> None:
        self.data_ready.emit(data, meta)

    def _on_step_finished(self, index: int, total: int) -> None:
        self.step_finished.emit(index, total)

    def _on_step_progress(self, current: int, total: int, message: str) -> None:
        self.step_progress.emit(current, total, message)