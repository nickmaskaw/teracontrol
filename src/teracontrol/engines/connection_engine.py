from typing import Any
from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class ConnectionEngine:
    """Manages connection state for a set of instruments."""

    def __init__(self, registry: InstrumentRegistry):
        self._registry = registry

    def connect(self, name: str, address: str) -> bool:
        try:
            inst = self._registry.get(name)
            inst.connect(address)
            log.info("Connected %s", name)
            return True
        
        except Exception:
            log.error("Failed to connect %s", name, exc_info=True)
            return False
        
    def disconnect(self, name: str) -> None:
        try:
            inst = self._registry.get(name)
            inst.disconnect()
            log.info("Disconnected %s", name)

        except Exception:
            log.error("Failed to disconnect %s", name, exc_info=True)
            raise