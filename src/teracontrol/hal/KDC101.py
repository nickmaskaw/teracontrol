import serial
import time
from typing import Any, Callable

from teracontrol.hal.base import BaseHAL
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class KDC101Commands:
    move_abs_angle = "53 04 06 00 D0 01 01 00" # move absolute (+4 byte)
    move_home = "43 04 01 00 50 01"            # move home
    req_poscounter = "11 04 01 00 50 01"       # get position count


class KDC101Controller(BaseHAL):
    """
    Hardware Abstraction Layer (HAL) for the Thorlbas KDC101 driver.
    """

    ENC_CNT_PER_DEG = 1919.6418578623391

    def __init__(self, timeout_s: float = 15.0):
        super().__init__(timeout_s)
        self._serial: serial.Serial | None = None

        log.debug(
            "KDC101Controller initialized (timeout: %.2fs)",
            timeout_s
        )

    # -------------------------------------------------------------------------
    # Connection handling
    # -------------------------------------------------------------------------

    def connect(self, port: str) -> None:
        log.info("Connecting to KDC101 at %s", port)

        if self._serial is not None:
            log.warning("KDC101 controller already connected")
            return

        try:
            self._serial = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=5,
                rtscts=True,
            )
            log.info("KDC101 connected")
        except Exception:
            log.error("Failed to connect to KDC101", exc_info=True)
            self.disconnect()
            raise

    def disconnect(self) -> None:
        if self._serial is not None:
            self._serial.close()
            self._serial = None

        log.info("Disconnected from KDC101")

    # -------------------------------------------------------------------------
    # BaseHAL API
    # -------------------------------------------------------------------------

    def is_connected(self) -> bool:
        return self._serial is not None
    
    def query(self, command: str) -> str:
        NotImplementedError("KDC101 queries not implemented")

    def status(self) -> dict[str, Any]:
        return {
            "connected": self.is_connected(),
            "position_deg": self._safe(self.get_position),
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _safe(self, fn: Callable[[], Any]) -> Any:
        try:
            return fn()
        except Exception:
            return None
    
    def _send(self, hex_string: str):
        cmd = bytes(int(x, 16) for x in hex_string.split())
        self._serial.write(cmd)

    def _recv(self):
        time.sleep(0.05)
        reply = b""
        while self._serial.in_waiting:
            reply += self._serial.read()
        return reply.hex(" ")

    def _angle_to_hex(self, angle_deg: float):
        enc = int(angle_deg * self.ENC_CNT_PER_DEG)
        b = enc.to_bytes(4, byteorder="little", signed=True)
        return " " + " ".join(f"{byte:02X}" for byte in b)
    
    def _wait_until_done(self):
        while True:
            reply = self._recv()
            if reply.startswith("64 04") or reply.startswith("44 04"):
                break
            time.sleep(0.1)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def move_to(self, angle_deg: float, wait: bool = True) -> None:
        cmd = KDC101Commands.move_abs_angle + self._angle_to_hex(angle_deg)
        
        self._send(cmd)
        if wait:
            self._wait_until_done()

    def home(self, wait: bool = True) -> None:
        self._send(KDC101Commands.move_home)
        if wait:
            self._wait_until_done()

    def get_position(self) -> float:
        self._send(KDC101Commands.req_poscounter)
        reply = self._recv()

        if not reply:
            return None
        
        msg_id = reply[0:5]

        if msg_id != "12 04":
            return None
        
        payload = reply[18:]
        pos_hex = payload[6:17]

        enc = int.from_bytes(bytes.fromhex(pos_hex), "little", signed=True)
        return enc / self.ENC_CNT_PER_DEG