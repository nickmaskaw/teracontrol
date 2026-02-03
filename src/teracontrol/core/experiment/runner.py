from __future__ import annotations

from pathlib import Path

from .sweep_config import SweepConfig
from teracontrol.engines.capture_engine import CaptureEngine


class SweepRunner:
    """
    Executes a 1D sweep and fills an existing Experiment with DataAtom entries.
    """

    def __init__(
        self,
        sweep: SweepConfig,
        capture_engine: CaptureEngine,
        safe_dump_path: Path | None = None,
    ):
        self.sweep = sweep
        self.capture = capture_engine
        self._abort = False

    def abort(self) -> None:
        """
        Request cooperative abortion of the sweep.
        """
        self._abort = True