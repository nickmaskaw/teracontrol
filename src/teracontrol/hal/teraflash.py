import socket
import warnings
import time
import numpy as np
from typing import Any, Optional

from teracontrol.hal.base import BaseHAL


class TeraflashTHzSystem(BaseHAL):
    """
    Hardware Abstraction Layer (HAL) for the Teraflash THz-TDS system.

    Notes
    -----
    This class intentionally mirrors the Teraflash ASCII control protocol
    verbatim. Some commands include literal printf-style format tokens
    (e.g. '%.1f', '%d') which are required by the instrument firmware and
    must not be interpreted or substituted on the host side.

    See:
        - docs/TF_PRO-RC-Commands-UDP-v22p1.pdf
        - docs/TF_PRO_RemoteDataAcquisition-TCP_v22p1.pdf
    """

    UDP_CMD_PORT = 61234
    UDP_RX_PORT = 61235
    UDP_TX_PORT = 61237
    TCP_SYNC_PORT = 6007

    def __init__(self, timeout_s: float = 15.0, channel: int = 1):
        super().__init__(timeout_s)
        self.channel = channel
        self.host: str = ""
        self._udp_tx = None
        self._udp_rx = None

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self, address_ip: str = "127.0.0.1") -> None:
        """Open UDP sockets and bind to ports."""
        try: 
            self.host = address_ip
            self._udp_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self._udp_rx.bind((self.host, self.UDP_RX_PORT))
            self._udp_rx.settimeout(self.timeout)

            self._udp_tx.bind((self.host, self.UDP_TX_PORT))

            # --- ACTIVE verification ---
            self._probe()

        except Exception:
            # Ensure partial sockets don't linger
            self.disconnect
            raise

    def disconnect(self) -> None:
        """Close all UDP sockets."""
        if self._udp_tx is not None:
            self._udp_tx.close()
            self._udp_tx = None
        if self._udp_rx is not None:
            self._udp_rx.close()
            self._udp_rx = None
        #print("Disconnected from Teraflash THz system")

    def _probe(self, short_timeout: float = 1.0) -> None:
        """
        Verify that the instrument is reachable and responding.

        Uses a short timeout to fail fast during connection.
        """
        try:
            self._udp_rx.settimeout(short_timeout)
            
            response = self._send_command("RD-RUN")
            if response not in ("ON", "OFF"):
                raise RuntimeError(f"Unexpected probe response: {response}")
        finally:
            self._udp_rx.settimeout(self.timeout)
    
    # ------------------------------------------------------------------
    # UDP control layer
    # ------------------------------------------------------------------

    def _send_command(self, cmd: str) -> str:
        """Send a raw RC/RD command and return the response string."""

        if not self._udp_tx or not self._udp_rx:
            raise RuntimeError("Not connected to Teraflash THz system")
        
        # --- Send a command ---
        self._udp_tx.sendto(cmd.encode("ascii"), (self.host, self.UDP_CMD_PORT))    
        #print(f"Sending {cmd} to Teraflash THz system")

        # --- Receive a response ---
        data, _ = self._udp_rx.recvfrom(1024)
        response = data.decode("ascii").strip()
        #print(f"Received {response} from Teraflash THz system")
        return response
    
    def _expect_ok(self, response: str):
        """Raise an exception if the response is not OK."""
        if not response.startswith("OK"):
            raise RuntimeError(f"Teraflash error: {response}")

    def _read(self, cmd: str) -> str:
        # ToDo: implement some kind of parsing
        return self._send_command(cmd)
    
    # ------------------------------------------------------------------
    # Debug tools
    # ------------------------------------------------------------------

    def query(self, command: str) -> str:
        response = self._send_command(command)
        print(f"Query: {command}")
        print(f"Response: {response}")
        return response

    # ------------------------------------------------------------------
    # System control
    # ------------------------------------------------------------------
    
    def laser_on(self):
        self._expect_ok(self._send_command("RC-LASER : ON"))

    def laser_off(self):
        self._expect_ok(self._send_command("RC-LASER : OFF"))

    def emitter_on(self, channel: Optional[int] = None):
        if channel is None:
            channel = self.channel
        self._expect_ok(self._send_command(f"RC-VOLT{channel} : ON"))

    def emitter_off(self, channel: Optional[int] = None):
        if channel is None:
            channel = self.channel
        self._expect_ok(self._send_command(f"RC-VOLT{channel} : OFF"))

    def run(self):
        self._expect_ok(self._send_command("RC-RUN : ON"))
    
    def stop(self):
        self._expect_ok(self._send_command("RC-RUN : OFF"))

    def wait_on(self):
        self._expect_ok(self._send_command("RC-WAIT : ON"))

    def wait_off(self):
        self._expect_ok(self._send_command("RC-WAIT : OFF"))

    def auto_on(self):
        self._expect_ok(self._send_command("RC-AUTO : ON"))

    def auto_off(self):
        self._expect_ok(self._send_command("RC-AUTO : OFF"))

    # ------------------------------------------------------------------
    # Acquisition settings
    # ------------------------------------------------------------------
    
    def set_begin_ps(self, value: float):
        self._expect_ok(self._send_command(f"RC-BEGIN %.1f {value}"))
    
    def set_range_ps(self, value: int):
        self._expect_ok(self._send_command(f"RC-RANGE %d {value}"))

    def set_average_points(self, value: int):
        self._expect_ok(self._send_command(f"RC-AVERAGE %d {value}"))

    # ------------------------------------------------------------------
    # Read commands
    # ------------------------------------------------------------------

    def get_amplitude_nA(self) -> float:
        return float(self._read("RD-AMPLITUDE"))
    
    def get_tactime_s(self) -> float:
        """Return the estimated total aquisition time of averaged traces."""
        return float(self._read("RD-TAC.TIME"))
    
    def get_laser_state(self) -> str:
        return self._read("RD-LASER")
    
    def get_emitter_state(self, channel: int = 1) -> str:
        return self._read(f"RD-VOLT{channel}")
    
    def get_run_state(self) -> str:
        return self._read("RD-RUN")
    
    def get_begin_ps(self) -> float:
        return float(self._read("RD-BEGIN"))
    
    def get_range_ps(self) -> int:
        return int(self._read("RD-RANGE"))
    
    def get_average_points(self) -> int:
        return int(self._read("RD-AVERAGE"))

    def get_wait_state(self) -> str:
        return self._read("RD-WAIT")
    
    def get_auto_state(self) -> str:
        return self._read("RD-AUTO")
    
    # ------------------------------------------------------------------
    # TCP acquisition layer (sync)
    # ------------------------------------------------------------------

    def acquire_trace(self):
        """Acquire a single synchronous time-domain trace."""

        if not self.is_connected:
            raise RuntimeError("Simulated THz system is not connected.")
        
        try:
            run_state = self.get_run_state()
            if run_state != "ON":
                warnings.warn(
                    "Acquiring trace while RUN state is OFF",
                    RuntimeWarning,
                )
        except Exception:
            # Never let warnings break acquisition
            pass

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.TCP_SYNC_PORT))

            # first packet: 6-byte length
            length_bytes = self._recv_exact(sock, 6)
            length = int(length_bytes.decode("ascii"))
            
            # Prevent glitches: reject packets with invalid length
            if length <= 0 or length > 10_000_000:
                raise ValueError(f"Invalid TCP payload length: {length}")

            # second packet: CSV payload
            payload = self._recv_exact(sock, length).decode("utf-8")

            return self._parse_trace(payload)
        
        finally:
            sock.close()
    
    # ------------------------------------------------------------------
    # TCP Helpers
    # ------------------------------------------------------------------

    def _recv_exact(self, sock, nbytes: int) -> bytes:
        data = b""
        while len(data) < nbytes:
            chunk = sock.recv(nbytes - len(data))
            if not chunk:
                raise RuntimeError("TCP connection closed prematurely")
            data += chunk
        return data
    
    def _parse_trace(self, csv_text: str) -> dict:
        # Split lines (CRLF as per documentation)
        lines = csv_text.strip().split("\r\n")

        # Parse header
        headers = [h.strip() for h in lines.pop(0).split(",")]

        # Parse numeric data
        data = [line.split(",") for line in lines[1:]]
        arr = np.array(data, dtype=float)

        if arr.shape[1] != len(headers):
            raise ValueError(
                f"Column mismatch: header has {len(headers)} columns, "
                f"data has {arr.shape[1]}"
            )
        
        # Build result dictionary dinamically
        result = {}
        for i, name in enumerate(headers):
            key = self._normalize_header(name)
            result[key] = arr[:, i]

        # Keep original raw headers for reference
        result["_raw_header"] = headers
        return result
    
    def _normalize_header(self, header: str) -> str:
        h = header.lower()
        h = h.replace("/", "_")
        return h
    
    # ------------------------------------------------------------------
    # Complex methods
    # ------------------------------------------------------------------

    def acquire_averaged_trace(self, timeout_s: float | None = None):
        # Estimate timeout if not provided
        if timeout_s is None:
            try:
                tac_time = self.get_tactime_s()
                timeout_s = max(self.timeout, 2.0 * tac_time + 3.0)
            except Exception:
                # Fallback if estimation fails
                timeout_s = self.timeout
                warnings.warn(
                    "Failed to read TAC.TIME; falling back to default timeout",
                    RuntimeWarning,
                )

        # Reset averaging and start countdown
        self.auto_on()

        # Wait until firmware signals completion (WAIT ON)
        t0 = time.monotonic()
        while True:
            try:
                if self.get_wait_state() == "ON":
                    break
            except Exception:
                pass

            if time.monotonic() - t0 > timeout_s:
                raise TimeoutError(
                    f"Timeout waiting for averaging to complete (WAIT ON)"
                )
            
            time.sleep(0.1)

        # Acquire the completed averaged trace
        trace = self.acquire_trace()

        # Release WAIT state for next acquisition
        self.wait_off()

        return trace
    
    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def get_status(self, channel: Optional[int] = None) -> dict[str, Any]:
        """Return the status of the instrument."""
        if channel is None:
            channel = self.channel
        
        return {
            "connected": self.is_connected(),
            "running": self.is_running(channel=channel),
            "begin_ps": self.get_begin_ps(),
            "range_ps": self.get_range_ps(),
            "average_points": self.get_average_points(),
            "amplitude_nA": self.get_amplitude_nA(),
        }
    
    def is_connected(self) -> bool:
        """Return True if the instrument is connected."""
        return (self._udp_tx is not None) and (self._udp_rx is not None)
    
    def is_running(self, channel: Optional[int] = None) -> bool:
        """Return true if:
        
        - Laser state is ON
        - Emitter state is ON
        - Run state is ON
        """
        if channel is None:
            channel = self.channel

        if not self.is_connected:
            return False
        
        return (
            self.get_laser_state() == "ON"
            and self.get_emitter_state(channel=channel) == "ON"
            and self.get_run_state() == "ON"
        )