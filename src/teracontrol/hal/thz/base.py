from abc import ABC, abstractmethod
from typing import Any

class THzAcquisitionSystem(ABC):
    """Abstract base class for THz acquisition systems."""

    @abstractmethod
    def connect(self) -> None:
        """
        Establish communication with the THz system.

        May later include actions such as:
        - enabling laser
        - enabling emitter voltage
        - preparing acquisition state
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """
        Cleanly shut down communication with the system.

        May later include actions such as:
        - stopping acquisition
        - disabling hardware safely
        """
        pass

    @abstractmethod
    def acquire(self) -> Any:
        """
        Perform one THz acquisition and return the result.

        The meaning of 'one acquisition' is intentionally left open:
        - may correspond to a block-averaged trace
        - may wrap internal WAIT/AUTO/SAVE logic
        - may rely on system configuration done beforehand
        """
        pass