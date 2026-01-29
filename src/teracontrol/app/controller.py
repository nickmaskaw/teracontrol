from __future__ import annotations

from typing import Any
from PySide6 import QtCore

from teracontrol.core.instruments import (
    InstrumentRegistry,
    INSTRUMENT_PRESETS,
    THZ,
    TEMP,
    FIELD,
)
from teracontrol.core.experiment import (
    AXIS_CATALOG,
    SweepAxis,
    SweepConfig,
    SweepRunner,
    ExperimentWorker,
)
from teracontrol.core.data import Experiment, DataAtom
from teracontrol.hal import (
    TeraflashTHzSystem,
    MercuryITCController,
    MercuryIPSController,
)
from teracontrol.engines import ConnectionEngine, QueryEngine, CaptureEngine
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class AppController(QtCore.QObject):

    # --- Signals (Controller -> GUI) ---
    data_ready = QtCore.Signal(DataAtom, dict)
    experiment_finished = QtCore.Signal()
    sweep_created = QtCore.Signal(int)
    step_finished = QtCore.Signal(int, int)
    
    def __init__(self, registry: InstrumentRegistry):
        super().__init__()

        # --- Registry ---
        self._registry = registry
        self._register_instruments()

        # --- Presets ---
        self._presets: dict[str, Any] = {}
        self._load_presets()

        # --- Engines ---
        self._connection = ConnectionEngine(self._registry)
        self._query = QueryEngine(self._registry)
        self._capture = CaptureEngine(self._registry)

        self._reset_experiment_state()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _register_instruments(self) -> None:
        self._registry.register(THZ, TeraflashTHzSystem())
        #self._registry.register(TEMP, MercuryITCController())
        #self._registry.register(FIELD, MercuryIPSController())

    def _load_presets(self) -> None:
        self._presets["instruments"] = {
            name: INSTRUMENT_PRESETS[name]
            for name in self.instrument_names()
        }

    def _reset_experiment_state(self) -> None:
        self._experiment: Experiment | None = None
        self._axis: SweepAxis | None = None
        self._sweep: SweepConfig | None = None
        self._runner: SweepRunner | None = None
        self._worker: ExperimentWorker | None = None
        self._thread: QtCore.QThread | None = None

    def _experiment_running(self) -> bool:
        return self._worker is not None

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

    # ------------------------------------------------------------------
    # Connection API
    # ------------------------------------------------------------------

    def connect(self, name: str, address: str) -> bool:
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

        try:
            self._build_experiment(config)
            self._start_worker_thread()
            return True
        
        except Exception:
            log.error("Failed to run experiment", exc_info=True)
            self._cleanup_experiment()
            return False
        
    def abort_experiment(self) -> bool:
        return self._forward_worker_call("abort")
    
    def pause_experiment(self) -> bool:
        return self._forward_worker_call("pause")
    
    def resume_experiment(self) -> bool:
        return self._forward_worker_call("resume")

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

        npoints = len(list(self._sweep.points()))
        self.sweep_created.emit(npoints)
            
        self._experiment = Experiment(
            metadata={
                "sweep": self._sweep.describe(),
                "user": meta,
            }
        )

        self._runner = SweepRunner(
            self._sweep,
            self._experiment,
            self._capture.capture,
        )

        self._worker = ExperimentWorker(self._runner)

    def _start_worker_thread(self) -> None:
        assert self._worker is not None

        self._thread = QtCore.QThread()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
            
        signals = self._worker.signals
        signals.data_ready.connect(self._on_data_ready)
        signals.finished.connect(self.experiment_finished)
        signals.step_finished.connect(self._on_step_finished)

        signals.finished.connect(self._thread.quit)
        signals.finished.connect(self._worker.deleteLater)
            
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_experiment)

        self._thread.start()

    # ------------------------------------------------------------------
    # Cleanup and forwarding
    # ------------------------------------------------------------------

    def _cleanup_experiment(self) -> None:
        self._reset_experiment_state()
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