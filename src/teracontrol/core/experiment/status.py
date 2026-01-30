from enum import Enum, auto


class ExperimentStatus(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ERROR = auto()