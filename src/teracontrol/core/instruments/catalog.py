from .presets import InstrumentPreset


THZ = "THz System"
TEMP = "Temperature Controller"
FIELD = "Field Controller"

INSTRUMENT_PRESETS = {
    THZ: InstrumentPreset(
        name=THZ,
        address_type="<ip>",
        address="127.0.0.1",
    ),
    TEMP: InstrumentPreset(
        name=TEMP,
        address_type="<ip>",
        address="192.168.1.2",
    ),
    FIELD: InstrumentPreset(
        name=FIELD,
        address_type="<ip>",
        address="192.168.1.3",
    ),
}