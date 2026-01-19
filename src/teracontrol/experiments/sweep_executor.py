from abc import ABC, abstractmethod
from teracontrol.experiments.sweep import SweepAxis, SweepDefinition


class SweepExecutor(ABC):
    """
    Abstract interface responsible for applying one sweep value.

    One executor exists per sweep axis.
    """

    def __init__(self, sweep: SweepDefinition):
        self.sweep = sweep

    @property
    @abstractmethod
    def axis(self) -> SweepAxis:
        """Which sweep axis is this executor responsible for."""
        pass

    @abstractmethod
    def apply(self, value: float) -> None:
        """
        Apply the sweep value.
        
        This method blocks until the value has been applied
        (e.g. sleep finished, field set).
        """
        pass