from abc import ABC, abstractmethod
from typing import Any


class BaseHAL(ABC):
    """
    Abstract class for all hardware abstraction layers.
    """

    def __init__(self, timeout_s: float = 5.0):
        self.timeout = timeout_s

    @abstractmethod
    def connect(self, address_ip: str) -> None:
        """Connect to the instrument."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the instrument."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the instrument is connected."""
        pass

    @abstractmethod
    def query(self, command: str) -> str:
        """Send a query to the instrument and return the response."""
        pass

    @property
    @abstractmethod
    def status(self) -> dict[str, Any]:
        """Return the status of the instrument."""
        pass