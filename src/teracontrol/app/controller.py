from typing import Callable
import numpy as np

from teracontrol.hal.thz.teraflash import TeraflashTHzSystem

from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.workers.experiment_worker import ExperimentWorker

from teracontrol.config.loader import load_config, save_config

from teracontrol.experiments.livestream_experiment import LiveStreamExperiment

class AppController:
    """Manages the application state and logic."""
    INSTRUMENT_CONFIG_PATH = "./configs/instruments.yaml"

    THZ = "THz System"

    def __init__(
            self,
            update_status: Callable[[str], None],
            update_trace: Callable[[np.ndarray, np.ndarray], None],
        ):
        """
        Parameters
        ----------
        instrument_config_path : str
            Path to the instrument configuration file.
        update_status : Callable[[str], None]
            Callback to update the status bar.
        update_trace : Callable[[np.ndarray, np.ndarray], None]
            Callback to update the live monitor.
        """
        
        # --- Configuration ---
        self.instrument_config = load_config(self.INSTRUMENT_CONFIG_PATH)

        # --- UI callbacks ---
        self.update_status = update_status
        self.update_trace = update_trace

        # --- HAL instances ---
        self.instruments = {
            self.THZ: TeraflashTHzSystem(),
        }

        # --- Engines ---
        self.connection_engine = ConnectionEngine(self.instruments)

        self.experiment = None
        self.worker = None

        # --- Guard flag ---
        self._connecting: set[str] = set()

    # --- Controller API ---

    def connect_instrument(self, name: str, address: str) -> bool:
        # Guard against simultaneous connection attempts
        if name in self._connecting:
            self.update_status(f"{name}: connection already in progress")
            return False

        self._connecting.add(name)
        try:
            self.update_status(f"{name}: connecting to {address}...")
            ok = self.connection_engine.connect(name, address)

            self.update_status(
                f"{name} (address: {address}) connected"
                if ok
                else f"Failed to connect {name} (address: {address})\n"
                + f"{self.connection_engine.get_last_error(name)}"
            )

            if ok and address != self.instrument_config[name]["address"]:
                self.instrument_config[name]["address"] = address
                save_config(self.instrument_config, self.INSTRUMENT_CONFIG_PATH)
            
            return ok
        
        finally:
            # Aways release the guard\
            self._connecting.remove(name)

    def disconnect_instrument(self, name: str) -> None:
        if name in self._connecting:
            self.update_status(f"{name}: cannot disconnect while connecting")
            return
        
        self.connection_engine.disconnect(name)
        self.update_status(f"{name} disconnected")

    # --- Livestream control ---

    def run_livestream(self):
        if self.worker is not None:
            return
        
        self.experiment = LiveStreamExperiment(
            thz_system=self.instruments[self.THZ],
            on_new_trace=self.update_trace,
        )

        self.worker = ExperimentWorker(self.experiment)
        self.worker.finished.connect(self._on_experiment_finished)

        self.update_status("Running livestream")
        self.worker.start()
        return True

    def stop_livestream(self):
        if self.worker is None:
            return
        
        self.worker.stop()
        self.worker.quit()
        self.worker.wait()

        self.worker = None
        self.update_status("Connected")

    def _on_experiment_finished(self):
        self.worker = None
        self.update_status("Connected")