from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class ExperimentRecord:
    """
    Atomic result of an experiment iteration.
    """
    sweep_value: float
    timestamp: float
    status: Optional[dict[str, Any]]
    waveform: Any