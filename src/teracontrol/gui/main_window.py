from typing import Any
from PySide6 import QtWidgets

from teracontrol.app.controller import AppController
from teracontrol.core.experiment import ExperimentStatus

from teracontrol.core.data import DataAtom

from .monitor import MonitorWidget
from .instrument import ConnectionWidget, QueryWidget
from .experiment import ExperimentControlWidget
from .misc import DockWidget

from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    APP_NAME = "TeraControl 0.1.0-dev"
    WIN_SIZE = (1200, 800)

    def __init__(self, controller: AppController) -> None:
        super().__init__()

        self._controller = controller
        self._instrument_names = controller.instrument_names()
        self._axis_catalog = controller.axis_catalog()
        self._presets = controller.presets()

        self._setup_window()
        self._setup_menus()
        self._setup_widgets()
        self._load_presets()
        self._setup_layout()
        self._wire_signals()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        self.setWindowTitle(self.APP_NAME)
        self.resize(*self.WIN_SIZE)

    def _setup_menus(self) -> None:
        self.menus = {
            "window": self.menuBar().addMenu("&Window"),
            "debug": self.menuBar().addMenu("&Debug"),
        }
    
    def _setup_widgets(self) -> None:
        self.widgets = {
            "connection": ConnectionWidget(self._instrument_names),
            "query": QueryWidget(self._instrument_names),
            "experiment": ExperimentControlWidget(self._axis_catalog),
            "monitor": MonitorWidget(),
        }
    
    def _load_presets(self) -> None:
        if "instruments" in self._presets:
            preset = self._presets["instruments"]
            self.widgets["connection"].apply_presets(preset)
    
    def _setup_layout(self) -> None:
        self.setCentralWidget(self.widgets["monitor"])
        self.docks = {
            "connection": DockWidget(
                name="Connection",
                parent=self,
                widget=self.widgets["connection"],
                menu=self.menus["window"],
            ),
            "query": DockWidget(
                name="Query",
                parent=self,
                widget=self.widgets["query"],
                menu=self.menus["debug"],
                set_floating=True,
            ),
            "experiment": DockWidget(
                name="Sweep Experiment",
                parent=self,
                widget=self.widgets["experiment"],
                menu=self.menus["window"],
            ),
        }

    def _wire_signals(self) -> None:

        # --- Controller -> GUI ---
        self._controller.data_ready.connect(self._on_new_data)
        self._controller.sweep_created.connect(self._on_sweep_created)
        self._controller.step_finished.connect(self._on_step_finished)

        self._controller.experiment_status_updated.connect(
            self._on_experiment_status_changed
        )
        
        # --- Connection ---
        self.widgets["connection"].connect_requested.connect(
            self._on_connect
        )
        self.widgets["connection"].disconnect_requested.connect(
            self._on_disconnect
        )
        
        # --- Query ---
        self.widgets["query"].query_requested.connect(
            self._on_query
        )

        # --- Experiment ---
        self.widgets["experiment"].run_requested.connect(
            self._controller.run_experiment
        )
        self.widgets["experiment"].pause_requested.connect(
            self._controller.pause_experiment
        )
        self.widgets["experiment"].resume_requested.connect(
            self._controller.resume_experiment
        )
        self.widgets["experiment"].abort_requested.connect(
            self._controller.abort_experiment
        )

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_experiment_status_changed(self, status: ExperimentStatus) -> None:
        self.widgets["experiment"].set_state(status)
        self.widgets["connection"].set_enabled(
            status == ExperimentStatus.IDLE
        )

    def _on_connect(self, name: str, address: str) -> None:
        ok = self._controller.connect(name, address)
        self.widgets["connection"].set_connected(name, ok)
        self.widgets["query"].set_enabled(ok, name)

    def _on_disconnect(self, name: str) -> None:
        self._controller.disconnect(name)
        self.widgets["connection"].set_connected(name, False)
        self.widgets["query"].set_enabled(False, name)

    def _on_query(self, name: str, cmd: str) -> None:
        response = self._controller.query(name, cmd)
        self.widgets["query"].update_response(name, cmd, response)

    def _on_new_data(self, data: DataAtom, meta: dict[str, Any]) -> None:
        self.widgets["monitor"].on_new_waveform(data.payload, meta)

    def _on_sweep_created(self, npoints: int) -> None:
        self.widgets["monitor"].clear()
        self.widgets["monitor"].configure(npoints)

    def _on_step_finished(self, index: int, total: int) -> None:
        self.widgets["experiment"].set_progress(index, total)