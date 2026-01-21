import socket
import warnings
from typing import Optional, Any, Callable

from teracontrol.hal.base import BaseHAL


class GenericMercuryController(BaseHAL):
    """
    Hardware Abstraction layer (HAL) for a Generic Mercury controller.

    This class is a generic implementation of the HAL interface.
    It is intended to be subclassed for specific instruments.
    """
    PORT = 7020

    # --- enabled device kinds ---
    enabled_kinds: dict[str, bool] = {
        "TEMP": True,  # Temperatrue controller
        "HTR": True,   # Heater controller
        "PRES": True,  # Pressure controller
        "AUX": True,   # Needle valve controller
        "PSU": True,   # Magnet power supply controller
    }

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

        # --- Ignored devices ---
        self.ignored_devices: dict[str, list[str]] = {
            "TEMP": [],
            "HTR": [],
            "PRES": [],
            "AUX": [],
            "PSU": [],
        }

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self, address_ip: str) -> None:
        if self.sock is not None:
            raise RuntimeError(f"{self.name} is already connected")

        try:
            self.host = address_ip
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.PORT))

            self.devices = self.get_devices()
        
        except Exception:
            if self.sock:
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

    def _send_command(self, cmd: str) -> str:
        if not self.sock:
            raise RuntimeError(f"Not connected to {self.name}")
        
        self.sock.sendall((cmd + "\n").encode("ascii"))

        while b"\n" not in self._rx_buffer:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise RuntimeError(f"{self.name} connection closed by instrument")
            self._rx_buffer += chunk

        line, _, self._rx_buffer = self._rx_buffer.partition(b"\n")
        response = line.decode("ascii").strip()
        return response
    
    def _read(self, cmd: str) -> str:
        response = self._send_command(f"READ:{cmd}")
        return response
    
    def _read_device(
        self,
        device_name: str,
        cmd: str,
        astype: type, 
        unit: str = "",
        expected_kind: Optional[str] = None
    ) -> Any:
        device_id = self._get_device_id(device_name)

        if expected_kind is not None:
            self._check_device_kind(device_id, expected_kind)
            
        response = self._read(f"DEV:{device_id}:{cmd}")
        value = response.split(":")[-1]
        
        if unit:
            value = value.split(unit)[0]
        
        try:
            return astype(value)
        
        except Exception:
            warnings.warn(
                f"Failed to parse response {response} as {astype.__name__}",
                RuntimeWarning,
            )
            return value
        
    def _check_device_kind(self, device_id: str, expected_kind: str) -> None:
        actual_kind = device_id.split(":")[1]
        if actual_kind != expected_kind:
            raise RuntimeError(
                f"Device kind mismatch: expected '{expected_kind}', "
                f"got '{actual_kind}' (device id: {device_id})"
            )
    
    def _get_device_id(self, device_name: str) -> str:
        return self.devices[device_name]
    
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

    def status(self) -> dict[str, Any]:
        """Acquire a snapshot of the instrument status."""

        status: dict[str, Any] = {
            "connected": self.is_connected(),
        }

        if self.enabled_kinds["TEMP"]:
            status["temp.temp_K"] = self._collect(
                self.read_temperature, "TEMP"
            )
        
        if self.enabled_kinds["HTR"]:
            status["htr.power_W"] = self._collect(
                self.read_power, "HTR"
            )
        
        if self.enabled_kinds["PRES"]:
            status["pres.pressure_mbar"] = self._collect(
                self.read_pressure, "PRES"
            )
        
        if self.enabled_kinds["AUX"]:
            status["aux.nvalve_percent"] = self._collect(
                self.read_nvalve, "AUX"
            )

        if self.enabled_kinds["PSU"]:
            status["psu.field_T"] = self._collect(
                self.read_field, "PSU"
            )
            status["psu.rate_A_per_min"] = self._collect(
                self.read_field_rate, "PSU"
            )
            status["psu.heater"] = self._collect(
                self.read_magnet_heater, "PSU"
            )
            status["psu.status"] = self._collect(
                self.read_magnet_status, "PSU"
            )

        return status
    
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
    
    # --- read devices ---    
    
    def read_temperature(self, device_name: str) -> float:
        """Return the temperature of a device in Kelvin."""
        return self._read_device(
            device_name, "SIG:TEMP", astype=float, unit="K", expected_kind="TEMP"
        )  
        
    def read_power(self, device_name: str) -> float:
        """Return the heater power of a device in Watts."""
        return self._read_device(
            device_name, "SIG:POWR", astype=float, unit="W", expected_kind="HTR"
        )
    
    def read_pressure(self, device_name: str) -> float:
        """Return the pressure of a device in millibar."""
        return self._read_device(
            device_name, "SIG:PRES", astype=float, unit="mB", expected_kind="PRES"
        )
    
    def read_nvalve(self, device_name: str) -> float:
        """Return the percent of a device's needle valve."""
        return self._read_device(
            device_name, "SIG:PERC", astype=float, unit="%", expected_kind="AUX"
        )
    
    def read_field(self, device_name: str) -> float:
        """Return the magnet field strength of a power supply in Tesla."""
        return self._read_device(
            device_name, "SIG:FLD", astype=float, unit="T", expected_kind="PSU"
        )
    
    def read_field_rate(self, device_name: str) -> float:
        """Return the current rate of a power supply in Ampere per minute."""
        return self._read_device(
            device_name, "SIG:RCUR", astype=float, unit="A/min", expected_kind="PSU"
        )
    
    def read_magnet_heater(self, device_name: str) -> str:
        """Return the magnet heater state."""
        return self._read_device(
            device_name, "SIG:SWHT", astype=str, expected_kind="PSU"
        )
    
    def read_magnet_status(self, device_name: str) -> str:
        """Return the magnet status."""
        return self._read_device(
            device_name, "ACTN", astype=str, expected_kind="PSU"
        )
    
    # --- get dictionaries ---

    def _collect(self, fn: Callable[[str], Any], kind: str) -> dict[str, Any]:
        return {
            name: fn(name) for name in self.devices
            if self.devices[name].split(":")[1] == kind
            and name not in self.ignored_devices[kind]
        }