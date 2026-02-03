import socket
import warnings
import time
import numpy as np
from typing import Any, Callable

from teracontrol.hal.base import BaseHAL
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


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
        self._channel = channel
        self.host: str = ""
        self._udp_tx = None
        self._udp_rx = None

        log.debug(
            "TeraFlashTHzSystem initialized (timeout: %.2fs, channel: %d)",
            timeout_s, channel
        )

    @property
    def channel(self) -> int:
        return self._channel

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self, address_ip: str = "127.0.0.1") -> None:
        log.info("Connecting to Teraflash THz system at %s", address_ip)

        try: 
            self.host = address_ip
            self._udp_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            log.debug("UDP sockets created")

            self._udp_rx.bind((self.host, self.UDP_RX_PORT))
            self._udp_rx.settimeout(self.timeout)
            log.debug("UDP RX bound to %s:%d", self.host, self.UDP_RX_PORT)

            self._udp_tx.bind((self.host, self.UDP_TX_PORT))
            log.debug("UDP TX bound to %s:%d", self.host, self.UDP_TX_PORT)

            self._probe()  # Ensure connection is active
            log.info("Connection established successfully")

        except Exception:
            log.error("Failed to connect to Teraflash THz system", exc_info=True)
            self.disconnect()
            raise

    def disconnect(self) -> None:
        if self._udp_tx is not None:
            self._udp_tx.close()
            self._udp_tx = None
            log.debug("UDP TX socket closed")

        if self._udp_rx is not None:
            self._udp_rx.close()
            self._udp_rx = None
            log.debug("UDP RX socket closed")

        log.info("Disconnected from Teraflash THz system")

    def _probe(self, short_timeout: float = 1.0) -> None:
        """
        Verify that the instrument is reachable and responding.

        Uses a short timeout to fail fast during connection.
        """
        log.debug("Probing instrument responsiveness (timeout: %.2fs)", short_timeout)

        try:
            self._udp_rx.settimeout(short_timeout)
            
            response = self._send_command("RD-RUN")
            log.debug("Probe response: %r", response)

            if response not in ("ON", "OFF"):
                raise RuntimeError(f"Unexpected probe response: {response}")
            
        finally:
            self._udp_rx.settimeout(self.timeout)
    
    # ------------------------------------------------------------------
    # UDP control layer
    # ------------------------------------------------------------------

    def _send_command(self, cmd: str) -> str:
        """Send a raw RC/RD command and return the response string."""

        if not self.is_connected():
            log.error("Attempted to send command while not connected")
            raise RuntimeError("Not connected to Teraflash THz system.")
        
        log.debug("UDP TX -> %s", cmd)
        self._udp_tx.sendto(cmd.encode("ascii"), (self.host, self.UDP_CMD_PORT))    

        data, _ = self._udp_rx.recvfrom(1024)
        response = data.decode("ascii").strip()
        
        log.debug("UDP RX <- %s", response)
        return response
    
    def _expect_ok(self, response: str):
        """Raise an exception if the response is not OK."""
        if not response.startswith("OK"):
            log.error("Instrument returned error response: %s", response)
            raise RuntimeError(f"Teraflash error: {response}")
        
    def _set(self, cmd: str, value: Any, sep: str = ":"):
        full_cmd = f"{cmd.strip()} {sep} {value}"
        log.debug("Setting parameter: %s", full_cmd)

        try:
            self._expect_ok(self._send_command(full_cmd))
            log.info("Set successful: %s", cmd)

        except Exception as e:
            log.error(
                "Failed to set parameter %s to %s",
                cmd, value, exc_info=True
            )
            raise RuntimeError(f"Failed to set {cmd} to {value}") from e

    def _read(self, cmd: str, astype: type = str) -> Any:
        log.debug("Reading parameter: %s", cmd)

        response = self._send_command(cmd)
        try:
            value = astype(response)
            log.debug("Parsed %s -> %r", cmd, value)
            return value
        
        except Exception:
            log.warning(
                "Failed to parse response %s as %s",
                response, astype.__name__,
            )
            warnings.warn(
                f"Failed to parse response {response} as {astype.__name__}",
                RuntimeWarning,
            )
            return response
    
    # ------------------------------------------------------------------
    # TCP acquisition layer (sync)
    # ------------------------------------------------------------------

    def acquire_trace(self):
        """Acquire a single synchronous time-domain trace."""
        log.info("Acquiring synchronous trace")

        if not self.is_connected():
            log.error("Acquire requested while not connected")
            raise RuntimeError("Teraflash THz system is not connected.")
        
        if not self.is_running():
            log.warning("Acquiring trace while RUN state is OFF")
            warnings.warn(
                "Acquiring trace while RUN state is OFF",
                RuntimeWarning,
            )

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: 
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.TCP_SYNC_PORT))
            log.debug("TCP connected to %s:%d", self.host, self.TCP_SYNC_PORT)

            # first packet: 6-byte length
            length_bytes = self._recv_exact(sock, 6)
            length = int(length_bytes.decode("ascii"))
            log.debug("TCP payload length: %d bytes", length)
            
            # Prevent glitches: reject packets with invalid length
            if length <= 0 or length > 10_000_000:
                raise ValueError(f"Invalid TCP payload length: {length}")

            # second packet: CSV payload
            payload = self._recv_exact(sock, length).decode("utf-8")
            log.debug("TCP payload received (%d bytes)", length)

            trace = self._parse_trace(payload)
            log.info("Trace acquisition complete")
            return trace
        
        finally:
            sock.close()
            log.debug("TCP socket closed")

    def _recv_exact(self, sock, nbytes: int) -> bytes:
        log.debug("Receiving %d bytes (exact)", nbytes)

        data = b""
        while len(data) < nbytes:
            chunk = sock.recv(nbytes - len(data))
            if not chunk:
                log.error("TCP connection closed prematurely")
                raise RuntimeError("TCP connection closed prematurely")
            data += chunk

        return data
    
    def _parse_trace(self, csv_text: str) -> dict:
        log.debug("Parsing CSV trace payload")

        # Split lines (CRLF as per documentation)
        lines = csv_text.strip().splitlines()#.split("\r\n")

        # Parse header
        headers = [h.strip() for h in lines.pop(0).split(",")]

        log.debug("Parsed headers: %s", headers)

        # Parse numeric data
        data = [line.split(",") for line in lines]
        arr = np.array(data, dtype=float)

        if arr.shape[1] != len(headers):
            log.error(
                "Column mismatch: header %d, data %d",
                len(headers), arr.shape[1]
            )
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
        log.debug("Trace parsed successfully (%d samples)", arr.shape[0])
        return result
    
    def _normalize_header(self, header: str) -> str:
        h = header.lower()
        h = h.replace("/", "_")
        return h

    # ------------------------------------------------------------------
    # Debug tools
    # ------------------------------------------------------------------

    def query(self, command: str) -> str:
        log.info(f"Query: {command}")
        response = self._send_command(command)
        log.info(f"Response: {response}")
        return response

    # ------------------------------------------------------------------
    # System control
    # ------------------------------------------------------------------
    
    def set_channel(self, channel: int) -> None:
        if channel not in [1, 2]:
            raise ValueError(
                f"Channel {channel} is not supported by this instrument"
            )
        
        self._channel = channel
    
    def set_laser_on(self) -> None:
        self._set("RC-LASER", "ON")

    def set_laser_off(self) -> None:
        self._set("RC-LASER", "OFF")

    def set_emitter_on(self) -> None:
        self._set(f"RC-VOLT{self.channel}", "ON")

    def set_emitter_off(self) -> None:
        self._set(f"RC-VOLT{self.channel}", "OFF")

    def set_run_on(self) -> None:
        self._set("RC-RUN", "ON")
    
    def set_run_off(self) -> None:
        self._set("RC-RUN", "OFF")

    def set_wait_on(self) -> None:
        self._set("RC-WAIT", "ON")

    def set_wait_off(self) -> None:
        self._set("RC-WAIT", "OFF")

    def set_auto_on(self) -> None:
        self._set("RC-AUTO", "ON")

    def set_auto_off(self) -> None:
        self._set("RC-AUTO", "OFF")
    
    def set_begin_ps(self, value: float) -> None:
        self._set("RC-BEGIN", value, sep="%.1f")
    
    def set_range_ps(self, value: int) -> None:
        self._set("RC-RANGE", value, sep="%d")

    def set_average_points(self, value: int) -> None:
        self._set("RC-AVERAGE", value, sep="%d")

    def set_file_path(self, path: str) -> None:
        self._set("RC-FILEPATH", path, sep="%s")

    def dump_save_trace(self) -> None:
        self._expect_ok(self._send_command("RC-SAVE WO-S"))
        log.info("Saved trace")

    # ------------------------------------------------------------------
    # Read commands
    # ------------------------------------------------------------------

    def read_amplitude_nA(self) -> float:
        return self._read("RD-AMPLITUDE", astype=float)
    
    def read_tactime_s(self) -> float:
        """Return the estimated total aquisition time of averaged traces."""
        return self._read("RD-TAC.TIME", astype=float)
    
    def read_laser_state(self) -> str:
        return self._read("RD-LASER")
    
    def read_emitter_state(self) -> str:
        return self._read(f"RD-VOLT{self.channel}")
    
    def read_run_state(self) -> str:
        return self._read("RD-RUN")
    
    def read_begin_ps(self) -> float:
        return self._read("RD-BEGIN", astype=float)
    
    def read_range_ps(self) -> int:
        return self._read("RD-RANGE", astype=int)
    
    def read_average_points(self) -> int:
        return self._read("RD-AVERAGE", astype=int)

    def read_wait_state(self) -> str:
        return self._read("RD-WAIT")
    
    def read_auto_state(self) -> str:
        return self._read("RD-AUTO")
    
    # ------------------------------------------------------------------
    # High-level methods
    # ------------------------------------------------------------------

    def acquire_averaged_trace(self, timeout_s: float | None = None):
        log.info("Starting averaged trace acquisition")

        # Estimate timeout if not provided
        if timeout_s is None:
            try:
                tac_time = self.read_tactime_s()
                timeout_s = max(self.timeout, 2.0 * tac_time + 3.0)
                log.debug("Estimated timeout: %.2fs", timeout_s)

            except Exception:
                # Fallback if estimation fails
                timeout_s = self.timeout
                log.warning(
                    "Failed to read TAC.TIME; using default timeout"
                )
                warnings.warn(
                    "Failed to read TAC.TIME; falling back to default timeout",
                    RuntimeWarning,
                )

        # Reset averaging and start countdown
        self.set_auto_on()
        log.debug("AUTO mode enabled, waiting for WAIT=ON")

        # Wait until firmware signals completion (WAIT ON)
        t0 = time.monotonic()
        while True:
            try:
                if self.read_wait_state() == "ON":
                    log.debug("WAIT=ON detected")
                    break

            except Exception:
                pass

            if time.monotonic() - t0 > timeout_s:
                log.error("Timeout waiting for WAIT=ON")
                raise TimeoutError(
                    f"Timeout waiting for averaging to complete (WAIT ON)"
                )
            
            time.sleep(0.1)

        # Acquire the completed averaged trace
        trace = self.acquire_trace()

        # Release WAIT state for next acquisition
        self.set_wait_off()

        log.info("Averaged trace acquisition complete")
        return trace
    
    def run(self):
        log.info("Starting system RUN sequence")
        self.set_laser_on()
        self.set_emitter_on()
        self.set_run_on()

    def stop(self):
        log.info("Stopping system RUN squence")
        self.set_laser_off()
        self.set_emitter_off()
        self.set_run_off()

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Acquire a snapshot of the instrument status."""
        log.debug("Querying system status")

        return {
            "connected": self.is_connected(),
            "running": self.is_running(),
            "channel": self.channel,
            "average_points": self._safe(self.read_average_points),
            "tac_time_s": self._safe(self.read_tactime_s),
            "amplitude_nA": self._safe(self.read_amplitude_nA),
        }
    
    def is_connected(self) -> bool:
        """Return True if the instrument is connected."""
        return (self._udp_tx is not None) and (self._udp_rx is not None)
    
    def is_running(self) -> bool:
        """Return true if:
        
        - Laser state is ON
        - Emitter state is ON
        - Run state is ON
        """
        if not self.is_connected():
            return False
        
        return (
            self.read_laser_state() == "ON"
            and self.read_emitter_state() == "ON"
            and self.read_run_state() == "ON"
        )
    
    def _safe(self, fn: Callable[[], Any]) -> Any:
        try:
            return fn()
        except Exception:
            return None
