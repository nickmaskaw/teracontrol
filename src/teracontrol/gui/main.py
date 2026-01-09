import sys
from PySide6 import QtWidgets

class MainWindow(QtWidgets.QMainWindow):
    """Application main window and entry point."""
    
    APP_NAME = "TeraControl 0.1.0"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.APP_NAME)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()