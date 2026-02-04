import socket
import warnings
from typing import Optional, Any, Callable

from teracontrol.hal.base import BaseHAL
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


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
    
    def _expect_valid(self, response: str) -> None:
        """Raise an exception if the response is not VALID."""
        if not response.endswith("VALID"):
            log.error("Instrument returned error response: %s", response)
            raise RuntimeError(f"Invalid response: {response}")
        
    def _set(self, cmd: str, value: Any) -> None:
        full_cmd = f"SET:{cmd}:{value}"
        log.debug("Setting parameter: %s", full_cmd)

        try:
            self._expect_valid(self._send_command(full_cmd))
            log.info("Set successful: %s", cmd)

        except Exception as e:
            log.error(
                "Failed to set parameter %s to %s",
                cmd, value, exc_info=True
            )
            raise RuntimeError(f"Failed to set {cmd} to {value}") from e
    
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
        
    def _set_device(
        self,
        device_name: str,
        cmd: str,
        value: Any,
        expected_kind: Optional[str] = None,
    ) -> None:
        device_id = self._get_device_id(device_name)

        if expected_kind is not None:
            self._check_device_kind(device_id, expected_kind)

        self._set(f"DEV:{device_id}:{cmd}", value)
        
    def _check_device_kind(self, device_id: str, expected_kind: str) -> None:
        actual_kind = device_id.split(":")[1]
        if actual_kind != expected_kind:
            raise RuntimeError(
                f"Device kind mismatch: expected '{expected_kind}', "
                f"got '{actual_kind}' (device id: {device_id})"
            )
    
    def _get_device_id(self, device_name: str) -> str:
        return self.devices[device_name]
    
    # ==========================================================================
    # Debug tools
    # ==========================================================================

    def query(self, command: str) -> str:
        response = self._send_command(command)
        print(f"Query: {command}")
        print(f"Response: {response}")
        return response
    
    # ==========================================================================
    # System commands
    # ==========================================================================

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
    
    # ==========================================================================
    # Temperature control
    # ==========================================================================

    # --- getters ---

    def read_temperature(self, device_name: str) -> float:
        """Return the temperature of a device in Kelvin."""
        return self._read_device(
            device_name, "SIG:TEMP", astype=float, unit="K", expected_kind="TEMP"
        )
    
    def read_temperature_setpoint(self, device_name: str) -> float:
        """ Return the temperature set point of a device in Kelvin. """
        return self._read_device(
            device_name, "LOOP:TSET", astype=float, unit="K", expected_kind="TEMP"
        )
    
    def read_power(self, device_name: str) -> float:
        """Return the heater power of a device in Watts."""
        return self._read_device(
            device_name, "SIG:POWR", astype=float, unit="W", expected_kind="HTR"
        )
    
    def read_temperature_control_status(self, device_name: str) -> str:
        """ Return the temperature control status of a device. """
        return self._read_device(
            device_name, "LOOP:ENAB", astype=str, expected_kind="TEMP"
        )
    
    # --- setters ---

    def set_temperature_setpoint(self, device_name: str, value: float) -> None:
        """ Set the temperature set point of a device in Kelvin. """
        if value > 300 or value < 0:
            raise ValueError("Temperature set point must be between 0 and 300 K")
        
        self._set_device(device_name, "LOOP:TSET", value, expected_kind="TEMP")

    def enable_temperature_control(self, device_name: str) -> None:
        """ Enable temperature auto control for a device. """
        self._set_device(device_name, "LOOP:ENAB", "ON", expected_kind="TEMP")

    def disable_temperature_control(self, device_name: str) -> None:
        """ Disable temperature auto control for a device. """
        self.set_temperature_setpoint(device_name, 0)
        self._set_device(device_name, "LOOP:ENAB", "OFF", expected_kind="TEMP")

    # ==========================================================================
    # Pressure controller
    # ==========================================================================

    # --- getters ---

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
    
    # ==========================================================================
    # Magnet controller
    # ==========================================================================

    # --- getters ---

    def read_voltage(self, device_name: str) -> float:
        """Return the voltage of a power supply in Volts."""
        return self._read_device(
            device_name, "SIG:VOLT", astype=float, unit="V", expected_kind="PSU"
        )
    
    def read_current(self, device_name: str) -> float:
        """Return the current of a power supply in Amperes."""
        return self._read_device(
            device_name, "SIG:CURR", astype=float, unit="A", expected_kind="PSU"
        )

    def read_field(self, device_name: str) -> float:
        """Return the magnet field strength of a power supply in Tesla."""
        return self._read_device(
            device_name, "SIG:FLD", astype=float, unit="T", expected_kind="PSU"
        )
    
    def read_target_current(self, device_name: str) -> float:
        """Return the target current of a power supply in Amperes."""
        return self._read_device(
            device_name, "SIG:CSET", astype=float, unit="A", expected_kind="PSU"
        )
    
    def read_target_field(self, device_name: str) -> float:
        """Return the target magnet field strength of a power supply in Tesla."""
        return self._read_device(
            device_name, "SIG:FSET", astype=float, unit="T", expected_kind="PSU"
        )
    
    def read_current_rate(self, device_name: str) -> float:
        """Return the current rate of a power supply in Ampere per minute."""
        return self._read_device(
            device_name, "SIG:RCUR", astype=float, unit="A/min", expected_kind="PSU"
        )
    
    def read_field_rate(self, device_name: str) -> float:
        """Return the current rate of a power supply in Tesla per minute."""
        return self._read_device(
            device_name, "SIG:RFLD", astype=float, unit="T/min", expected_kind="PSU"
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

    # ==========================================================================
    # Dictionary helpers
    # ==========================================================================

    def _collect(self, fn: Callable[[str], Any], kind: str) -> dict[str, Any]:
        return {
            name: fn(name) for name in self.devices
            if self.devices[name].split(":")[1] == kind
            and name not in self.ignored_devices[kind]
        }
    
    def export_temperatures(self) -> dict[str, float]:
        return self._collect(self.read_temperature, "TEMP")
    
    def export_pressures(self) -> dict[str, float]:
        return self._collect(self.read_pressure, "PRES")
    
    def export_nvalves(self) -> dict[str, float]:
        return self._collect(self.read_nvalve, "AUX")

    # ==========================================================================
    # Status
    # ==========================================================================
    
    def is_connected(self) -> bool:
        """Return True if the instrument is connected."""
        return (self.sock is not None)
    
    def status(self) -> dict[str, Any]:
        status: dict[str, Any] = {
            "connected": self.is_connected(),
        }

        for enabled_kind in self.enabled_kinds:
            status[enabled_kind] = {}

        for name in self.devices:
            kind = self.devices[name].split(":")[1]
            if kind not in self.enabled_kinds:
                continue

            if name in self.ignored_devices[kind]:
                continue

            status[kind][name] = {}

            if kind == "TEMP":
                status[kind][name]["reading_K"] = self.read_temperature(name)
                status[kind][name]["setpoint_K"] = self.read_temperature_setpoint(name)
                status[kind][name]["auto"] = self.read_temperature_control_status(name)
            
            if kind == "HTR":
                status[kind][name]["power_W"] = self.read_power(name)

            if kind == "PRES":
                status[kind][name]["reading_mbar"] = self.read_pressure(name)

            if kind == "AUX":
                status[kind][name]["nvalve_percent"] = self.read_nvalve(name)

            if kind == "PSU":
                status[kind][name]["voltage_V"] = self.read_voltage(name)
                status[kind][name]["current_A"] = self.read_current(name)
                status[kind][name]["field_T"] = self.read_field(name)
                status[kind][name]["current_target_A"] = self.read_target_current(name)
                status[kind][name]["field_target_T"] = self.read_target_field(name)
                status[kind][name]["current_rate_A_per_min"] = self.read_current_rate(name)
                status[kind][name]["field_rate_T_per_min"] = self.read_field_rate(name)
                status[kind][name]["heater"] = self.read_magnet_heater(name)
                status[kind][name]["magnet"] = self.read_magnet_status(name)

        return status