from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .sweep_axis import SweepAxis


@dataclass(frozen=True)
class SweepConfig:
    """
    Definition of a 1D sweep.

    This class contains no execution logic.
    I only defines what the sweep is.
    """

    axis: SweepAxis
    start: float
    stop: float
    step: float

    # Optional dwell time per point (seconds)
    dwell_s: float = 0.0

    def __post_init__(self):
        if self.step == 0:
            raise ValueError("Sweep step must be non-zero")
        
        if (self.stop - self.start) * self.step < 0:
            raise ValueError(
                "Sweep step sign does not move start toward stop"
            )
        
    def points(self) -> Iterable[float]:
        """
        Generate sweep points including start and stop.
        """
        x = self.start
        eps = abs(self.step) * 1e-12

        if self.step > 0:
            while x <= self.stop + eps:
                yield x
                x += self.step
        else:
            while x >= self.stop - eps:
                yield x
                x += self.step

    def npoints(self) -> int:
        """
        Total number of points in the sweep.
        """
        return sum(1 for _ in self.points())

    def describe(self) -> dict:
        """
        Metadata describing the sweep configuration.
        """
        return {
            "axis": self.axis.name,
            "start": self.start,
            "stop": self.stop,
            "step": self.step,
            "unit": self.axis.unit,
            "dwell_s": self.dwell_s,
        }