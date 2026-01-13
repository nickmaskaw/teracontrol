from abc import ABC, abstractmethod
from typing import Any

class THzAcquisitionSystem(ABC):
    """Abstract base class for THz acquisition systems."""

    @abstractmethod
    def connect(self) -> None:
        pass

    @abstractmethod
    def disconnect(self) -> None:
        pass

    @abstractmethod
    def acquire(self) -> Any:
        pass