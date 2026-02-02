from pathlib import Path
from dataclasses import dataclass
from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.core.experiment import ExperimentStatus
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


@dataclass
class AppContext:
    registry: InstrumentRegistry
    root_dir: Path
    
    # --- Directories ---
    data_dir: Path | None = None
    config_dir: Path | None = None
    export_dir: Path | None = None

    # --- Status ---
    experiment_status: ExperimentStatus = ExperimentStatus.IDLE

    def __post_init__(self):
        self.root_dir = Path(self.root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)
        log.debug("Application context initialized")
        log.info("root directory: %s", self.root_dir)

    def set_dir(
        self,
        name: str,
        path: Path | str,
        relative_to_root: bool = True
    ) -> None:
        if name in ["data", "config", "export"]:
            path = Path(path)
            
            if relative_to_root:
                path = self.root_dir / path
            else:
                path = path.resolve()

            path.mkdir(parents=True, exist_ok=True)
            setattr(self, f"{name}_dir", path)

            log.info("%s directory: %s", name, path)