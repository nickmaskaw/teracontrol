from typing import Dict, Any
from teracontrol.hal import BaseHAL


class InstrumentRegistry:
    """
    Authoritative owner of all HAL instances.

    Responsibilities:
    - Own HAL lifetimes
    - Mediate connection/disconnection
    - Provide access to instruments

    This class does NOT:
    - Decide connection parameters
    - Implement retry or policy
    - Know about GUI or experiments
    """
    
    def __init__(self):
        self._instruments: Dict[str, BaseHAL] = {}

    # --- Ownership --------------------------------------------------------

    def register(self, name: str, instrument: BaseHAL) -> None:
        if name in self._instruments:
            raise ValueError(f"Instrument {name} already registered")
        self._instruments[name] = instrument

    def get(self, name: str) -> BaseHAL:
        try:
            return self._instruments[name]
        except KeyError:
            raise KeyError(f"Instrument {name} not registered")
        
    def names(self) -> list[str]:
        return list(self._instruments.keys())
    
    # --- Status ----------------------------------------------------------

    def is_connected(self, name: str) -> bool:
        inst = self.get(name)
        return inst.is_connected()
    
    def describe(self, name: str) -> dict[str, Any]:
        inst = self.get(name)
        return inst.status()