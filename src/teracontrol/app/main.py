import sys
import logging
from pathlib import Path
from PySide6 import QtWidgets

from teracontrol.core.instruments import InstrumentRegistry
from teracontrol.app.context import AppContext
from teracontrol.app.controller import AppController
from teracontrol.gui.main_window import MainWindow
from teracontrol.utils.logging import setup_logging, get_logger

log = get_logger(__name__)

PACKAGE_ROOT = Path(__file__).resolve().parents[3]
LOG_FILE = PACKAGE_ROOT / "logs/teracontrol.log"


def main() -> None:
    setup_logging(
        level=logging.INFO,
        logfile=LOG_FILE,
    )

    log.info("=== Application started ===")

    try:
        app = QtWidgets.QApplication(sys.argv)

        registry = InstrumentRegistry()
        context = AppContext(registry=registry)

        controller = AppController(context)
        window = MainWindow(controller)

        window.show()

        app.aboutToQuit.connect(controller.cleanup)

        sys.exit(app.exec())

    except Exception:
        log.exception("Application crashed", exc_info=True)
        raise

    finally:
        log.info("=== Application exited ===")


if __name__ == "__main__":
    main()