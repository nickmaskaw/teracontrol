from dataclasses import dataclass
from enum import Enum
from typing import List


class SweepAxis(Enum):
    """
    Identifies which physical parameter is being varied.

    Only TIME will be implemented initially, but others are
    listed to keep the experiment loop generic.
    """
    TIME = "time"
    FIELD = "field"
    TEMPERATURE = "temperature"


@dataclass(frozen=True)
class SweepDefinition:
    """
    Declarative definition of a sweep.

    This object contains NO execution logic.
    It only describes the intended variation.
    """
    axis: SweepAxis
    start: float
    stop: float
    step: float
    unit: str


def generate_sweep_values(sweep: SweepDefinition) -> List[float]:
    """
    Generate the list of sweep values.

    Kept explicit (no numpy) to avoid hidden floating-point
    behavior and to remain fully deterministic.
    """
    values: List[float] = []

    v = sweep.start
    while v <= sweep.stop:
        values.append(v)
        v += sweep.step

    return values