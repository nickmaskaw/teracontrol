from typing import Callable
import numpy as np

from teracontrol.hal.thz.teraflash import TeraflashTHzSystem

from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.engines.experiment_worker import ExperimentWorker

from teracontrol.config.loader import load_config, save_config

from teracontrol.experiments.livestream_experiment import LiveStreamExperiment

class AppController:
    """Manages the application state and logic."""

    THZ = "THz System"

    def __init__(
            self,
            instrument_config_path: str,
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
        self.instrument_config_path = instrument_config_path
        self.instrument_config = load_config(instrument_config_path)

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

    # --- Controller API ---

    def connect_instrument(self, name: str, address: str) -> bool:
        ok = self.connection_engine.connect(name, address)
        
        self.update_status(
            f"{name} (address: {address}) connected"
            if ok
            else f"Failed to connect {name} (address: {address})"
        )

        

        '''
        if ok and address != self.instrument_config[name]["address_preset"]:
            self.instrument_config[name]["address_preset"] = address
            
            if not address in self.instrument_config[name]["addresses"]:
                self.instrument_config[name]["addresses"].append(address)
            
            save_config(self.instrument_config, self.instrument_config_path)
            print(f"Saved config to {self.instrument_config_path}")
        '''

    def disconnect_instrument(self, name: str) -> None:
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