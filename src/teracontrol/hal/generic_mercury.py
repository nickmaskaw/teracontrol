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

    # --- Expected capabilities ---
    capabilities: dict[str, bool] = {
        "temperature": True,
        "heater": True,
        "pressure": True,
        "nvalve": True,
        "magnet": True,
    }

    # --- Ignored devices ---
    ignored_devices: dict[str, list[str]] = {
        "temperature": [],
        "heater": [],
        "pressure": [],
        "nvalve": [],
        "magnet": [],
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
    
    def _read(self, cmd: str) -> Any:
        response = self._send_command(f"READ:{cmd}")
        return response
    
    def _read_value(self, cmd: str, astype: type, unit: str = "") -> Any:
        response = self._read(cmd)
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
        
    def _wrong_device_kind_warning(self, device_id: str, kind: str) -> bool:
        """Return True if a warning should be raised for a device."""
        if device_id.split(":")[1] != kind:
            warnings.warn(
                f"Device {device_id} is not '{kind}'",
                RuntimeWarning,
            )
            return True
    
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

        if self.capabilities["temperature"]:
            status["temperatures_K"] = self.dict_temp_temperatures_K()
        
        if self.capabilities["heater"]:
            status["heaters_W"] = self.dict_htr_powers_W()
        
        if self.capabilities["pressure"]:
            status["pressures_mbar"] = self.dict_pres_pressures_mbar()
        
        if self.capabilities["nvalve"]:
            status["nvalves_percent"] = self.dict_aux_nvalves_percent()

        if self.capabilities["magnet"]:
            status["fields_T"] = self.dict_psu_fields_T()
            status["rates_A_per_min"] = self.dict_psu_rates_A_per_min()

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
    
    def read_temp_temperature_K(self, device_id: str) -> float:
        """Return the temperature of a device in Kelvin."""
        if self._wrong_device_kind_warning(device_id, "TEMP"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:TEMP", astype=float, unit="K")
        
    def read_htr_power_W(self, device_id: str) -> float:
        """Return the heater power of a device in Watts."""
        if self._wrong_device_kind_warning(device_id, "HTR"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:POWR", astype=float, unit="W")
    
    def read_pres_pressure_mbar(self, device_id: str) -> float:
        """Return the pressure of a device in millibar."""
        if self._wrong_device_kind_warning(device_id, "PRES"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:PRES", astype=float, unit="mB")
    
    def read_aux_nvalve_percent(self, device_id: str) -> float:
        """Return the percent of a device's needle valve."""
        if self._wrong_device_kind_warning(device_id, "AUX"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:PERC", astype=float, unit="%")
    
    def read_psu_field_T(self, device_id: str) -> float:
        """Return the magnet field strength of a power supply in Tesla."""
        if self._wrong_device_kind_warning(device_id, "PSU"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:FLD", astype=float, unit="T")
    
    def read_psu_rate_A_per_min(self, device_id: str) -> float:
        """Return the current rate of a power supply in Ampere per minute."""
        if self._wrong_device_kind_warning(device_id, "PSU"):
            return None
        
        return self._read_value(f"DEV:{device_id}:SIG:RCUR", astype=float, unit="A/min")
    
    # --- get dictionaries ---

    def dict_temp_temperatures_K(self) -> dict[str, float]:
        """Return a dictionary of temperature sensors and their values."""
        return {
            name: self.read_temp_temperature_K(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "TEMP"
            and name not in self.ignored_devices["temperature"]
        }
    
    def dict_htr_powers_W(self) -> dict[str, float]:
        """Return a dictionary of heater sensors and their values."""
        return {
            name: self.read_htr_power_W(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "HTR"
            and name not in self.ignored_devices["heater"]
        }
    
    def dict_pres_pressures_mbar(self) -> dict[str, float]:
        """Return a dictionary of pressure sensors and their values."""
        return {
            name: self.read_pres_pressure_mbar(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "PRES"
            and name not in self.ignored_devices["pressure"]
        }
    
    def dict_aux_nvalves_percent(self) -> dict[str, float]:
        """Return a dictionary of needle valve sensors and their values."""
        return {
            name: self.read_aux_nvalve_percent(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "AUX"
            and name not in self.ignored_devices["nvalve"]
        }
    
    def dict_psu_fields_T(self) -> dict[str, float]:
        """Return a dictionary of magnet sensors and their values."""
        return {
            name: self.read_psu_field_T(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "PSU"
            and name not in self.ignored_devices["magnet"]
        }
    
    def dict_psu_rates_A_per_min(self) -> dict[str, float]:
        """Return a dictionary of power supply sensors and their values."""
        return {
            name: self.read_psu_rate_A_per_min(self.devices[name])
            for name in self.devices
            if self.devices[name].split(":")[1] == "PSU"
            and name not in self.ignored_devices["magnet"]
        }