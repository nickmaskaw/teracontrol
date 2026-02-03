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
        safe_dump_dir: Path | None = None,
    ):
        self.sweep = sweep
        self.capture = capture_engine
        self._abort = False
        self.safe_dump_dir = safe_dump_dir
        if safe_dump_dir is not None:
            safe_dump_dir.mkdir(parents=True, exist_ok=True)

    def abort(self) -> None:
        """
        Request cooperative abortion of the sweep.
        """
        self._abort = True