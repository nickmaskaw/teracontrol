from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable


@dataclass(frozen=True)
class DataAtom:
    timestamp: float
    status: dict[str, Any]
    data: Any


def capture_data(
        read_status: Callable[[], dict[str, Any]],
        read_data: Callable[[], Any],
):  
    ts = datetime.now().astimezone().isoformat()
    status = read_status()
    data = read_data()

    return DataAtom(
        timestamp=ts,
        status=status,
        data=data,
    )