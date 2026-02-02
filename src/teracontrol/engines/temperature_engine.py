from teracontrol.core.instruments import (
    InstrumentRegistry, InstrumentCatalog
)


class TemperatureEngine:
    def __init__(self, registry: InstrumentRegistry):
        self._registry = registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    
