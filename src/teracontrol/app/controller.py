from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.engines.experiment_worker import ExperimentWorker

from teracontrol.config.loader import load_config, save_config

from teracontrol.hal.thz.simulated import SimulatedTHzSystem
from teracontrol.hal.thz.teraflash import TeraflashTHzSystem

from teracontrol.experiments.livestream_experiment import LiveStreamExperiment

class AppController:
    """Manages the application state and logic."""

    def __init__(self, instrument_config_path: str, update_status: callable, update_trace: callable):
        self.instrument_config_path = instrument_config_path
        self.instrument_config = load_config(instrument_config_path)

        self.connection_engine = ConnectionEngine(
            instruments={
                "THz System": TeraflashTHzSystem(self.instrument_config["THz System"]["ports"]),
            }
        )

        self.thz_system = self.connection_engine.instruments["THz System"]

        self.experiment = None
        self.worker = None
        self.update_status = update_status
        self.update_trace = update_trace

    # --- Instruments ---

    def connect_instrument(self, name: str, address: str) -> bool:
        ok = self.connection_engine.connect(name, address)
        text = f"{name} ({address}) connected" if ok else f"Failed to connect {name} ({address})"   
        self.update_status(text)
        print(text)
        if ok and address != self.instrument_config[name]["address_preset"]:
            self.instrument_config[name]["address_preset"] = address
            if not address in self.instrument_config[name]["addresses"]:
                self.instrument_config[name]["addresses"].append(address)
            save_config(self.instrument_config, self.instrument_config_path)
            print(f"Saved config to {self.instrument_config_path}")
        return ok

    def disconnect_instrument(self, name: str):
        self.connection_engine.disconnect(name)
        text = f"{name} disconnected"
        self.update_status(text)
        print(text)

    # --- Livestream control ---

    def run_livestream(self):
        if self.worker is not None:
            return
        
        self.experiment = LiveStreamExperiment(
            thz_system=self.thz_system,
            on_new_trace=self.update_trace,
        )

        self.worker = ExperimentWorker(self.experiment)
        self.worker.finished.connect(self._on_experiment_finished)

        self.update_status("Running livestream")
        self.worker.start()

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