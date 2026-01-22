from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable
import numpy as np


# =============================================================================
# Payload
# =============================================================================

@dataclass(frozen=True)
class Waveform:
    time: np.ndarray
    signal: np.ndarray


# =============================================================================
# Data Atom
# =============================================================================

@dataclass(frozen=True)
class DataAtom:
    timestamp: datetime
    status: dict[str, Any]
    payload: Any


# =============================================================================
# Data Cappture helper
# =============================================================================

def capture_data(
        read_status: Callable[[], dict[str, Any]],
        read_data: Callable[[], Any],
):  
    timestamp = datetime.now().astimezone().isoformat()
    status = read_status()
    payload = read_data()

    return DataAtom(
        timestamp=timestamp,
        status=status,
        payload=payload,
    )