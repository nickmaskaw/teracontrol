import time
import numpy as np
import socket

from .base import THzAcquisitionSystem


class SimulatedTHzSystem(THzAcquisitionSystem):
    """
    A minimal simulated THz acquisition system.
    """

    def __init__(self, port_config: dict):
        self.udp_cmd_port: int = port_config["udp_cmd"]
        self.udp_rx_port: int = port_config["udp_rx"]
        self.tcp_sync_port: int = port_config["tcp_sync"]
        self.timeout: float = port_config["timeout"]

        self.host: str = ""
        
        self._udp_tx = None
        self._udp_rx = None

    # --- Connection handling ---

    def connect(self, address: str) -> None:
        try: 
            self.host = address
            self._udp_tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._udp_rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            #self._udp_rx.bind((self.host, self.udp_rx_port))
            self._udp_rx.settimeout(self.timeout)

            print(f"Simulated THz system connected to {address}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to {address}\n{e}")

    def disconnect(self) -> None:
        """Close all sockets."""
        if self._udp_tx is not None:
            self._udp_tx.close()
            self._udp_tx = None
        if self._udp_rx is not None:
            self._udp_rx.close()
            self._udp_rx = None
        print("Simulated THz system disconnected")
    
    # --- UDP control layer ---

    def _send_command(self, cmd: str) -> str:
        """Send a raw RC/RD command and return the response string."""
        if not self._udp_tx or not self._udp_rx:
            raise RuntimeError("Simulated THz system is not connected.")
        
        # --- Simulate sending a command ---
        #self._udp_tx.sendto(cmd.encode("ascii"), (self.host, self.udp_cmd_port))
        print(f"Sending {cmd}")
        time.sleep(0.1)

        # --- Simulate receiving a response ---
        #data, _ = self._udp_rx.recvfrom(1024)
        #return data.decode("ascii").strip()
        return "OK" if np.random.rand() < 0.5 else "ERR"
    
    def _expect_ok(self, response: str):
        """Raise an exception if the response is not OK."""
        if not response.startswith("OK"):
            raise RuntimeError(f"TeraFlash error: {response}")

    def _read(self, cmd: str) -> str:
        """
        Send an RD-* command and return the parsed value.
        
        Returns:
            None              -> for OK with no value
            str / int / float -> parsed value
        """
        
        response = self.send_command(cmd)
        if not response.startswith("OK"):
            raise RuntimeError(f"TeraFlash error: {response}")
        
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

    def start(self):
        self._expect_ok(self._send_command("RC-RUN : ON"))
    
    def stop(self):
        self._expect_ok(self._send_command("RC-RUN : OFF"))

    # --- Acquisition settings ---
    
    def set_begin_ps(self, value: float):
        self._expect_ok(self._send_command(f"RC-BEGIN {value} "))
    
    def set_range_ps(self, value: int):
        self._expect_ok(self._send_command(f"RC-RANGE {value} "))

    def set_average_points(self, value: int):
        self._expect_ok(self._send_command(f"RC-AVERAGE {value} "))

    # --- Read commands ---

    def get_amplitude_nA(self) -> float:
        return float(self._read("RD-AMPLITUDE"))
    
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
    
    # --- TCP acquisition layer (sync) ---

    def acquire_trace(self):
        """Acquire a single synchronous time-domain trace."""

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect((self.host, self.tcp_sync_port))

        # first packet: 6-byte length
        length_bytes = self._recv_exact(sock, 6)
        length = int(length_bytes.decode("ascii"))

        # second packet: CSV payload
        payload = self._recv_exact(sock, length).decode("uft-8")
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

    
    def acquire(self):
        if not self._connected:
            raise RuntimeError("Simulated THz system is not connected.")
        
        time.sleep(0.25)  # simulate acqusition time

        # fake time axis (ps)
        t = np.linspace(-10, 10, self.data_points)
        # fake THz pulse
        noise = 0.02 * np.random.normal(size=self.data_points)
        signal = np.exp(-t**2) * np.cos(2 * np.pi * 0.5 * t)

        return {
            "time_ps": t,
            "signal": signal + noise,
        }



