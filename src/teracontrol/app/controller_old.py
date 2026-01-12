from teracontrol.hal.thz.simulated import SimulatedTHzSystem
from teracontrol.experiments.live_monitor import LiveMonitorExperiment
from teracontrol.engines.experiment_worker import ExperimentWorker
from teracontrol.engines.connection import ConnectionEngine
from teracontrol.config.loader import load_config, save_config


class AppController:
    """Application-level controller."""

    def __init__(self, config_path: str, on_new_trace, on_status):
        self.config_path = config_path
        self.config = load_config(config_path)

        self.connection_engine = ConnectionEngine(
            instruments={
                "THz System": SimulatedTHzSystem(),
            }
        )

        self.thz = SimulatedTHzSystem()
        self.experiment = None
        self.worker = None

        self.on_new_trace = on_new_trace
        self.on_status = on_status

    # --- Instrument control ---

    def connect_instrument(self, name: str) -> bool:
        ok = self.connection_engine.connect(name)
        self.on_status(
            f"{name} connected" if ok else f"Failed to connect {name}"
        )
        return ok
    
    def disconnect_instrument(self, name: str):
        self.connection_engine.disconnect(name)
        self.on_status(f"{name} disconnected")

    def instrument_status(self):
        return self.connection_engine.status()
    
    # --- Experiment control ---

    def start_livestream(self, livestream_config: dict):
        if self.worker is not None:
            return

        # Update authoritative config and checkpoint preset
        self.config["livestream"] = livestream_config
        save_config(self.config, self.config_path)

        self.experiment = LiveMonitorExperiment(
            thz=self.thz,
            livestream_config=livestream_config,
            on_new_trace=self.on_new_trace,
        )

        self.worker = ExperimentWorker(self.experiment)
        self.worker.finished.connect(self._on_experiment_finished)

        self.on_status("Running livestream")
        self.worker.start()

    def stop_livestream(self):
        if self.worker is None:
            return

        self.worker.stop()
        self.worker.quit()
        self.worker.wait()

        self.worker = None
        self.on_status("Connected")

    def _on_experiment_finished(self):
        self.worker = None
        self.on_status("Connected")