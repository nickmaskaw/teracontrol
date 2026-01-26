from dataclasses import dataclass, field
from typing import Any
from .record import Record


@dataclass
class Experiment:
    metadata: dict[str, Any] = field(default_factory=dict)
    record: Record = field(default_factory=Record)