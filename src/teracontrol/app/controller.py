from teracontrol.hal.thz.simulated import SimulatedTHzSystem
from teracontrol.experiments.live_monitor import LiveMonitorExperiment
from teracontrol.engines.experiment_worker import ExperimentWorker
from teracontrol.config.loader import load_config, save_config


class AppController:
    """
    Application-level controller.

    Owns:
    - config
    - THz system
    - experiment lifecycle
    - worker thread

    Has no GUI code.
    """

    def __init__(self, config_path: str, on_new_trace, on_status):
        self.config_path = config_path
        self.config = load_config(config_path)

        self.thz = SimulatedTHzSystem()
        self.experiment = None
        self.worker = None

        self.on_new_trace = on_new_trace
        self.on_status = on_status

    # --- THz control ---

    def connect_thz(self):
        try:
            self.thz.connect()
            self.on_status("Connected")
            return True
        except Exception as e:
            self.on_status(f"Connection error: {e}")
            return False
        
    def disconnect_thz(self):
        self.stop_livestream()
        self.thz.disconnect()
        self.on_status("Disconnected")

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