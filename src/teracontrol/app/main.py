import sys
import logging
from pathlib import Path
from datetime import datetime
from PySide6 import QtWidgets

from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.app.context import AppContext
from teracontrol.app.controller import AppController
from teracontrol.gui.main_window import MainWindow
from teracontrol.utils.logging import setup_logging, get_logger

log = get_logger(__name__)


def main() -> None:
    PACKAGE_ROOT = Path(__file__).resolve().parents[3]
    
    log_dir = PACKAGE_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(
        level=logging.INFO,
        logfile=log_dir / "teracontrol.log",
    )

    log.info("=== Application started ===")

    try:
        app = QtWidgets.QApplication(sys.argv)

        registry = InstrumentRegistry()
        context = AppContext(
            root_dir=PACKAGE_ROOT,
            registry=registry,
        )

        today = datetime.now().strftime("%Y-%m-%d")
        context.set_dir("data", f"data/{today}")
        context.set_dir("config", "config")

        controller = AppController(context)
        window = MainWindow(controller)

        window.show()

        app.aboutToQuit.connect(controller.save_presets)
        app.aboutToQuit.connect(controller.cleanup)

        sys.exit(app.exec())

    except Exception:
        log.exception("Application crashed", exc_info=True)
        raise

    finally:
        log.info("=== Application exited ===")


if __name__ == "__main__":
    main()