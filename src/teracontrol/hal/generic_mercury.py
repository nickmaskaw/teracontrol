import socket
import warnings
from typing import Optional, Any

from teracontrol.hal.base import BaseHAL


class GenericMercuryController(BaseHAL):
    """
    Hardware Abstraction layer (HAL) for a Generic Mercury controller.

    This class is a generic implementation of the HAL interface.
    It is intended to be subclassed for specific instruments.
    """
    PORT = 7020

    def __init__(
        self,
        name: str = "Generic Mercury Controller",
        timeout_s: float = 5.0
    ):
        self.name = name
        self.timeout = timeout_s
        self.host: str = ""
        self.sock: Optional[socket.socket] = None
        self._rx_buffer = b""
        self.devices: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self, address_ip: str) -> None:
        if self.sock is not None:
            raise RuntimeError("{self.name} is already connected")

        try:
            self.host = address_ip
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.PORT))

            self.devices = self.get_devices()
        
        except Exception:
            self.sock.close()
            self.sock = None
            raise

    def disconnect(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
            self.devices = {}

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def _send_command(self, cmd: str) -> None:
        if not self.sock:
            raise RuntimeError("Not connected to {self.name}")
        
        self.sock.sendall((cmd + "\n").encode("ascii"))

        while b"\n" not in self._rx_buffer:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise RuntimeError("{self.name} connection closed by instrument")
            self._rx_buffer += chunk

        line, _, self._rx_buffer = self._rx_buffer.partition(b"\n")
        response = line.decode("ascii").strip()
        return response
    
    # ------------------------------------------------------------------
    # Debug tools
    # ------------------------------------------------------------------

    def query(self, command: str) -> str:
        response = self._send_command(command)
        print(f"Query: {command}")
        print(f"Response: {response}")
        return response
    
    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def status(self) -> dict[str, Any]:
        """Return the status of the instrument."""
        return {
            "connected": self.is_connected(),
            "temperatures": self.get_temperature_dict(),
        }
    
    def is_connected(self) -> bool:
        """Return True if the instrument is connected."""
        return (self.sock is not None)
    
    # ------------------------------------------------------------------
    # Read commands
    # ------------------------------------------------------------------

    def idn(self) -> str:
        """Return the instrument IDN."""
        response = self._send_command("*IDN?").split(":")
        return {
            "manufacturer": response[1].strip(),
            "instrument": response[2].strip(),
            "serial_number": response[3].strip(),
            "firmware_version": response[4].strip(),
        }

    def get_devices(self) -> dict[str, str]:
        """Return a dictionary of device names and IDS."""
        ids = self._send_command("READ:SYS:CAT").split(":DEV:")[1:]
        names = [
            self._send_command(f"READ:DEV:{id}:NICK").split(":")[-1] for id in ids
        ]
        return dict(zip(names, ids))
    
    def read_device_temperature_K(self, device_id: str) -> float:
        """Return the temperature of a device in Kelvin."""
        if device_id.split(":")[1] != "TEMP":
            warnings.warn(
                f"Device {device_id} is not a temperature sensor",
                RuntimeWarning,
            )
            return None
        
        response = self._send_command(f"READ:DEV:{device_id}:SIG:TEMP")
        return float(response.split(":")[-1].split('K')[0])
    
    def get_temperature_dict(self) -> dict[str, float]:
        """Return a dictionary of temperature sensors and their values."""
        return {
            name: self.read_device_temperature_K(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "TEMP"
        }
