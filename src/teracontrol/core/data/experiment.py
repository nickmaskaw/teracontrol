from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from .record import Record


@dataclass
class Experiment:
    created_at: datetime = field(
        default_factory=datetime.now().astimezone().isoformat
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    record: Record = field(default_factory=Record)