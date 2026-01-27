import sys
import logging
from PySide6 import QtWidgets

from teracontrol.utils.logging import setup_logging, get_logger

from teracontrol.core.instruments import InstrumentRegistry, INSTRUMENT_PRESETS
from teracontrol.controllers import AppController
from teracontrol.gui.main_window import MainWindow

log = get_logger(__name__)


def main() -> None:
    setup_logging(
        level=logging.INFO,
        logfile=f"logs/teracontrol.log",
    )

    log.info("=== Application started ===")

    try:
        app = QtWidgets.QApplication(sys.argv)

        registry = InstrumentRegistry()
        controller = AppController(registry)
        window = MainWindow(controller, INSTRUMENT_PRESETS)

        window.show()

        sys.exit(app.exec())

    except Exception:
        log.exception("Application crashed", exc_info=True)
        raise

    finally:
        log.info("=== Application exited ===")


if __name__ == "__main__":
    main()