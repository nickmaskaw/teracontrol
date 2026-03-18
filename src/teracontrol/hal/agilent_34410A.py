from __future__ import annotations

import socket
from typing import Optional, Any

from teracontrol.hal.base import BaseHAL
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class Agilent34410A(BaseHAL):
    
    PORT = 5025

    def __init__(self, name: str = "Agilent 34410A", timeout_s: float = 5.0):
        self.name = name
        self.timeout = timeout_s
        self.host: str = ""
        self.sock: Optional[socket.socket] = None
        self._rx_buffer = b""

        log.debug(
            "Agilent34410A initialized (timeout: %.2fs)",
            timeout_s
        )

    # -------------------------------------------------------------------------
    # Connection handling
    # -------------------------------------------------------------------------

    def connect(self, address_ip: str) -> None:
        if self.sock is not None:
            raise RuntimeError(f"{self.name} is already connected")
        
        try:
            self.host = address_ip
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.PORT))

        except Exception:
            log.error(
                "Failed to connect to %s",
                self.name, exc_info=True
            )
            if self.sock:
                self.sock.close()
            self.sock = None
            raise

    def disconnect(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None
            log.info("Disconnected from %s", self.name)

    # -------------------------------------------------------------------------
    # Low-level I/O
    # -------------------------------------------------------------------------

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
        response = self._send_command(cmd)
        return response
    
    # -------------------------------------------------------------------------
    # Debug tools
    # -------------------------------------------------------------------------

    def query(self, command: str) -> str:
        response = self._send_command(command)
        print(f"Query: {command}")
        print(f"Response: {response}")
        return response
    
    # -------------------------------------------------------------------------
    # Basic read commands
    # -------------------------------------------------------------------------

    def read_voltage(self) -> float:
        volt = self._read("MEAS?")
        return float(volt)
    
    def read_current(self) -> float:
        curr = self._read("MEAS:CURR?")
        return float(curr)
    
    def read_4wire_resistance(self) -> float:
        fres = self._read("MEAS:FRES?")
        return float(fres)
    
    def read_2wire_resistance(self) -> float:
        res = self._read("MEAS:RES?")
        return float(res)

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    def is_connected(self):
        return (self.sock is not None)
    
    def status(self) -> dict[str, Any]:
        return {
            "connected": self.is_connected(),
        }