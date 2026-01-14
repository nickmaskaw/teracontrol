from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.config.loader import load_config, save_config

from teracontrol.hal.thz.simulated import SimulatedTHzSystem

class AppController:
    """Manages the application state and logic."""

    def __init__(self, instrument_config_path: str, update_status: callable):
        self.instrument_config_path = instrument_config_path
        self.instrument_config = load_config(instrument_config_path)

        self.connection_engine = ConnectionEngine(
            instruments={
                "THz System": SimulatedTHzSystem(self.instrument_config["THz System"]["ports"]),
            }
        )

        self.update_status = update_status

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
