from dataclasses import dataclass
from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.core.experiment import ExperimentStatus


@dataclass
class AppContext:
    registry: InstrumentRegistry
    experiment_status: ExperimentStatus = ExperimentStatus.IDLE