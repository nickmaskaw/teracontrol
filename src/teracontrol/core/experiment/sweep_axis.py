from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


# =============================================================================
# Sweep axis base class
# =============================================================================

class SweepAxis(ABC):
    """
    Abstract sweep axis.

    A SweepAxis represents one controllable experimental degree of freedom:
    count, magnetic field, temperature, etc.
    """
    
    name: str = "axis"
    unit: str = ""
    decimals: int = 3

    def __init__(self):
        self._current: Optional[float] = None

    @abstractmethod
    def goto(self, value: float) -> None:
        """
        Move the axis to an absolute value.
        """
        ...

    def read(self) -> Optional[float]:
        """
        Read back the current axis value.

        Default implementation returns the last value passed to goto().
        Hardware-backed axes may override this.
        """
        return self._current
    
    def set_current(self, value: float) -> None:
        """
        Update internal cached value.
        
        Intended to be called by subclasses at the end of goto().
        """
        self._current = value

    def describe(self, value: float) -> dict:
        """
        Standardized metadata dictionary for this axis at a given value.
        """
        return {
            "axis": self.name,
            "value": value,
            "unit": self.unit,
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} unit={self.unit!r}>"


# =============================================================================
# Axis implementations
# =============================================================================

class CountAxis(SweepAxis):
    """
    Dummy sweep axis based on measurement count / dwell.
    
    Useful for:
    - averaging
    - stability tests
    - debugging
    """

    name = "count"
    unit = "#"
    decimals = 0

    def goto(self, value: float) -> None:
        # Count has no physical motion; just update state
        self.set_current(int(value))


class TemperatureAxis(SweepAxis):
    name = "temperature"
    unit = "K"
    decimals = 1
