from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

from teracontrol.engines import TemperatureEngine, FieldEngine


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
    blocking: bool = False
    minimum = 0
    maximum = 1000

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
    
    def is_ready(self) -> bool:
        """
        Return True if the axis is settled.
        """
        return True  # default: always ready
    
    def estimate_settle_time_s(self) -> float:
        return 0.0  # default: no settling
    
    def shutdown(self) -> None:
        """
        Put the axis into a safe state.
        Called if the experiment is aborted mid-motion.
        Defualt: do nothing.
        """
        pass
    
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
    blocking = False
    minimum = 1
    maximum = 1000

    def goto(self, value: float) -> None:
        # Count has no physical motion; just update state
        self.set_current(int(value))


class TemperatureAxis(SweepAxis):
    name = "temperature"
    unit = "K"
    decimals = 1
    blocking = False
    minimum = 0.0
    maximum = 300.0

    def __init__(self, engine: TemperatureEngine):
        super().__init__()
        self._engine = engine

    # ------------------------------------------------------------------
    # Sweep axis API
    # ------------------------------------------------------------------

    def goto(self, value: float) -> None:
        """
        Set the temperature setpoint and enable temperature control.
        """
        self._engine.begin_temperature_control(value)
        self.set_current(value)

    def read(self) -> float:
        """
        Read the current measured temperature.
        """
        return self._engine.read_temperature()
    
    def shutdown(self) -> None:
        """
        Disable temperature control.

        Intended to be called by experiment cleanup logic.
        """
        pass  # do nothing right now
    
    # ------------------------------------------------------------------
    # Optional helpers (not required by SweepAxis)
    # ------------------------------------------------------------------

    def read_setpoint(self) -> float:
        """
        Read back the temperature setpoint
        """
        return self._engine.read_temperature_setpoint()


class FieldAxis(SweepAxis):
    name = "field"
    unit = "T"
    decimals = 3
    blocking = True
    minimum = -7.0
    maximum = 7.0

    def __init__(self, engine: FieldEngine):
        super().__init__()
        self._engine = engine

    # ------------------------------------------------------------------
    # Sweep axis API
    # ------------------------------------------------------------------

    def goto(self, value: float) -> None:
        """
        Set the magnet field setpoint and enable magnet control.
        """
        self._engine.set_target_field(value)
        self._engine.goto_set()
        self._current = value

    def read(self) -> float:
        """
        Read the current measured field
        """
        return self._engine.read_field()

    def is_ready(self) -> bool:
        return self._engine.is_holding()
    
    def estimate_settle_time_s(self, value: float) -> float:
        current = self._engine.read_field()    # T
        rate = self._engine.read_field_rate()  # T/min

        delta_field = abs(value - current)     # T
        ramp_s = (delta_field / rate) * 60     

        TIMEOUT_S = 500.0                 # max settling time
        POST_RAMP_STABILIZATION_S = 15.0  # HOLD qualification, correction
        BASE_OVERHEAD_S = 1.0             # command + state latency

        estimated_s = ramp_s + POST_RAMP_STABILIZATION_S + BASE_OVERHEAD_S

        estimated_s *= 1.3                   # safety margin
        estimated_s = max(estimated_s, 2.0)  # never absurdly small
        estimated_s = min(estimated_s, TIMEOUT_S)

        return estimated_s
    
    def shutdown(self) -> None:
        self._engine.hold()