import socket
import numpy as np


class TeraflashTHzSystem:

    UDP_CMD_PORT = 61234
    UDP_RX_PORT = 61235
    UDP_TX_PORT = 61237
    TCP_SYNC_PORT = 6007

    def __init__(self, timeout_s: float = 15.0):
        self.timeout = timeout_s
        self.host: str = ""
        self._udp_tx = None
        self._udp_rx = None

    # --- Connection handling ---

    def connect(self, address_ip: str = "127.0.0.1") -> None:
        """Open UDP sockets and bind to ports."""
        try: 
            self.host = address_ip
            self._udp_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            self._udp_rx.bind((self.host, self.UDP_RX_PORT))
            self._udp_rx.settimeout(self.timeout)

            self._udp_tx.bind((self.host, self.UDP_TX_PORT))

            print(f"Connected to Teraflash THz system")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Teraflash THz system\n{e}")

    def disconnect(self) -> None:
        """Close all UDP sockets."""
        if self._udp_tx is not None:
            self._udp_tx.close()
            self._udp_tx = None
        if self._udp_rx is not None:
            self._udp_rx.close()
            self._udp_rx = None
        print("Disconnected from Teraflash THz system")
    
    # --- UDP control layer ---

    def _send_command(self, cmd: str) -> str:
        """Send a raw RC/RD command and return the response string."""

        if not self._udp_tx or not self._udp_rx:
            raise RuntimeError("Not connected to Teraflash THz system")
        
        # --- Send a command ---
        self._udp_tx.sendto(cmd.encode("ascii"), (self.host, self.UDP_CMD_PORT))
        print(f"Sending {cmd} to Teraflash THz system")

        # --- Receive a response ---
        data, _ = self._udp_rx.recvfrom(1024)
        response = data.decode("ascii").strip()
        print(f"Received {response} from Teraflash THz system")
        return response
    
    def _expect_ok(self, response: str):
        """Raise an exception if the response is not OK."""
        if not response.startswith("OK"):
            raise RuntimeError(f"Teraflash error: {response}")

    def _read(self, cmd: str) -> str:
        """
        Send an RD-* command and return the parsed value.
        
        Returns:
            None              -> for OK with no value
            str / int / float -> parsed value
        """
        
        response = self._send_command(cmd)
        parts = response.split(maxsplit=1)
        if len(parts) == 1:
            return None
        else:
            return parts[1]

    # --- System control ---
    
    def laser_on(self):
        self._expect_ok(self._send_command("RC-LASER : ON"))

    def laser_off(self):
        self._expect_ok(self._send_command("RC-LASER : OFF"))

    def emitter_on(self, channel: int = 1):
        self._expect_ok(self._send_command(f"RC-VOLT{channel} : ON"))

    def emitter_off(self, channel: int = 1):
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

    # --- Acquisition settings ---
    
    def set_begin_ps(self, value: float):
        self._expect_ok(self._send_command(f"RC-BEGIN %.1f {value}"))
    
    def set_range_ps(self, value: int):
        self._expect_ok(self._send_command(f"RC-RANGE %d {value}"))

    def set_average_points(self, value: int):
        self._expect_ok(self._send_command(f"RC-AVERAGE %d {value}"))

    # --- Read commands ---

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
    
    # --- TCP acquisition layer (sync) ---

    def acquire_trace(self):
        """Acquire a single synchronous time-domain trace."""

        if not self._udp_tx or not self._udp_rx:
            raise RuntimeError("Simulated THz system is not connected.")

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.TCP_SYNC_PORT))

        # first packet: 6-byte length
        length_bytes = self._recv_exact(sock, 6)
        length = int(length_bytes.decode("ascii"))

        # second packet: CSV payload
        payload = self._recv_exact(sock, length).decode("utf-8")
        sock.close()

        return self._parse_trace(payload)
    
    def _recv_exact(self, sock, nbytes: int) -> bytes:
        data = b""
        while len(data) < nbytes:
            chunck = sock.recv(nbytes - len(data))
            if not chunck:
                raise RuntimeError("TCP connection closed prematurely")
            data += chunck
        return data
    
    # --- Data parsing ---

    def _parse_trace(self, csv_text: str) -> dict:
        lines = csv_text.strip().split("\r\n")
        header = lines.pop(0)

        cols = [line.split(",") for line in lines]
        arr = np.array(cols, dtype=float)

        result = {
            "header": header,
            "time_ps": arr[:, 0],
            "signal_ch1": arr[:, 1],
        }

        if arr.shape[1] > 2:
            result["ref_ch1"] = arr[:, 2]
        if arr.shape[1] > 3:
            result["signal_ch2"] = arr[:, 3]
        if arr.shape[1] > 4:
            result["ref_ch2"] = arr[:, 4]

        return result