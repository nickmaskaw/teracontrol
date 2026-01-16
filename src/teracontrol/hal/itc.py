import socket
from typing import Optional


# Implement dataclass??

class ITCTempController:
    """
    Hardware Abstraction layer (HAL) for the ITC Temperature Controller.
    """
    PORT = 7020

    def __init__(self, timeout_s: float = 15.0):
        self.timeout = timeout_s
        self.host: str = ""
        self.sock: Optional[socket.socket] = None
        self._rx_buffer = b""

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self, address_ip: str) -> None:
        if self.sock is not None:
            raise RuntimeError("ITC controller is already connected")

        try:
            self.host = address_ip
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            self.sock.connect((self.host, self.PORT))
            print(self.idn())
        
        except Exception:
            self.sock.close()
            self.sock = None
            raise

    def disconnect(self) -> None:
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    # ------------------------------------------------------------------
    # Low-level I/O
    # ------------------------------------------------------------------

    def _send_command(self, cmd: str) -> None:
        if not self.sock:
            raise RuntimeError("Not connected to ITC controller")
        
        self.sock.sendall((cmd + "\n").encode("ascii"))

        while b"\n" not in self._rx_buffer:
            chunk = self.sock.recv(1024)
            if not chunk:
                raise RuntimeError("ITC connection closed by instrument")
            self._rx_buffer += chunk

        line, _, self._rx_buffer = self._rx_buffer.partition(b"\n")
        return line.decode("ascii").strip()
    
    # ------------------------------------------------------------------
    # Core commands API
    # ------------------------------------------------------------------

    def query(self, command: str) -> str:
        # ToDo: parsing
        return self._send_command(command)
    
    # ------------------------------------------------------------------
    # High-level helpers
    # ------------------------------------------------------------------

    def idn(self) -> str:
        return self.query("*IDN?")