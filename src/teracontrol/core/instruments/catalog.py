from dataclasses import dataclass


# =============================================================================
# Instrument Catalog
# =============================================================================

@dataclass(frozen=True)
class InstrumentCatalog:
    THZ = "THz System"
    TEMP = "Temperature Controller"
    FIELD = "Field Controller"

# =============================================================================
# Instrument Defaults
# =============================================================================

INSTRUMENT_DEFAULTS = {
    InstrumentCatalog.THZ: {
        "address_type": "<ip>",
        "address": "127.0.0.1",
    },
    InstrumentCatalog.TEMP: {
        "address_type": "<ip>",
        "address": "192.168.1.2",
    },
    InstrumentCatalog.FIELD: {
        "address_type": "<ip>",
        "address": "192.168.1.3",
    },
}