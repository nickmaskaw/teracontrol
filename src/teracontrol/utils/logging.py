import logging
from pathlib import Path
from typing import Union
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: int = logging.INFO,
    logfile: Union[str, Path, None] = None,
    max_bytes: int = 5_000_000,  # ~5 MB
    backup_count: int = 5,
) -> None:
    """
    Configure application-wide logging.

    - Console output always enabled
    - Optional rotating file logging
    - Safe against double configuration
    """
    root = logging.getLogger()

    # Prevent double configuration
    if root.handlers:
        return
    
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    root.setLevel(level)

    # --- Console handler ---
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(formatter)
    root.addHandler(console)

    # --- Rotating file handler ---
    if logfile is not None:
        logfile = Path(logfile)
        logfile.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            logfile,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)