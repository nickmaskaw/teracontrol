from dataclasses import dataclass


@dataclass(frozen=True)
class InstrumentPreset:
    name: str
    address_type: str
    address: str