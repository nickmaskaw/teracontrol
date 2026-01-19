import time
from teracontrol.experiments.sweep import SweepAxis
from teracontrol.experiments.sweep_executor import SweepExecutor


class TimeSweepExecutor(SweepExecutor):
    """
    Sweep executor for TIME axis.

    Interprets sweep values as seconds and blocks using time.sleep().
    """

    @property
    def axis(self) -> SweepAxis:
        return SweepAxis.TIME
    
    def apply(self, value: float) -> None:
        if self.sweep.unit != "s":
            raise ValueError(
                f"Time sweep expects unit='s', got {self.sweep.unit}"
            )
        
        if value < 0:
            raise ValueError(f"Time sweep value must be positive, got {value}")
        
        time.sleep(value)