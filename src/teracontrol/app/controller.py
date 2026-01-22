from typing import Callable
import numpy as np

from PySide6 import QtCore

from teracontrol.hal.teraflash import TeraflashTHzSystem
from teracontrol.hal.generic_mercury import GenericMercuryController

from teracontrol.engines.connection_engine import ConnectionEngine
from teracontrol.engines.query_engine import QueryEngine
from teracontrol.workers.experiment_worker_old import ExperimentWorker

from teracontrol.config.loader import load_config, save_config


class AppController(QtCore.QObject):
    """
    Central application controller.
    Owns experiment state and mediates between GUI and HAL.
    """
    INSTRUMENT_CONFIG_PATH = "./configs/instruments.yaml"

    THZ = "THz System"
    TEMP = "Temperature Controller"
    FIELD = "Field Controller"

    # --- Signals (Controller -> GUI) ---
    status_updated = QtCore.Signal(str)
    query_response_updated = QtCore.Signal(str, str, str)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent)
        # --- Configuration ---
        self.instrument_config = load_config(self.INSTRUMENT_CONFIG_PATH)

        # --- HAL instances ---
        self.instruments = {
            self.THZ: TeraflashTHzSystem(),
            self.TEMP: GenericMercuryController(name="ITC"),
            self.FIELD: GenericMercuryController(name="IPS"),
        }

        # --- Engines ---
        self.connection_engine = ConnectionEngine(self.instruments)
        self.query_engine = QueryEngine(
            self.instruments,
            self._on_query_response,
        )

        self.experiment = None
        self.worker = None

        # --- Guard flag ---
        self._connecting: set[str] = set()

    # --- Controller API ---

    def connect_instrument(self, name: str, address: str) -> bool:
        # Guard against simultaneous connection attempts
        if name in self._connecting:
            self.status_updated.emit(f"{name}: connection already in progress")
            return False

        self._connecting.add(name)
        try:
            self.status_updated.emit(f"{name}: connecting to {address}...")
            ok = self.connection_engine.connect(name, address)

            self.status_updated.emit(
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
            self.status_updated.emit(f"{name}: cannot disconnect while connecting")
            return
        
        self.connection_engine.disconnect(name)
        self.status_updated.emit(f"{name} disconnected")

    # ------------------------------------------------------------------
    # ITC query test
    # ------------------------------------------------------------------

    def send_query(self, name: str, query: str) -> None:
        self.query_engine.query(name, query)

    def _on_query_response(self, name: str, query: str,response: str) -> None:
        self.query_response_updated.emit(name, query, response)