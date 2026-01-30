from typing import Dict, Any
from teracontrol.hal import BaseHAL


class InstrumentRegistry:
    """
    Authoritative owner of all HAL instances.
    """

    def __init__(self):
        self._instruments: Dict[str, BaseHAL] = {}

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------

    def register(self, name: str, instrument: BaseHAL) -> None:
        if name in self._instruments:
            raise ValueError(f"Instrument {name} already registered")
        self._instruments[name] = instrument

    def get(self, name: str) -> BaseHAL:
        try:
            return self._instruments[name]
        except KeyError:
            raise KeyError(f"Instrument {name} not registered")
    
    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def names(self) -> list[str]:
        return list(self._instruments.keys())
    
    def types(self) -> dict[str, type[BaseHAL]]:
        return {
            name: inst.__class__
            for name, inst in self._instruments.items()
        }
    
    def is_connected(self, name: str) -> bool:
        inst = self.get(name)
        return inst.is_connected()
    
    def describe(self, name: str) -> dict[str, Any]:
        """
        Retrieve instrument status.

        Maybe not a good name.
        """
        inst = self.get(name)
        return inst.status()
    
    def disconnect_all(self) -> None:
        for name in self.names():
            inst = self.get(name)
            inst.disconnect()