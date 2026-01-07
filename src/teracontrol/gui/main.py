import sys
import pyqtgraph as pg
from PySide6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    """
    Main application window for teracontrol GUI.

    For now, this window only hosts a central live plot.
    """
    
    def __init__(self):
        super().__init__()

        self.setWindowTitle("teracontrol GUI")
        self.resize(800, 600)

        # Central pyqtgraph plot
        self.plot = pg.PlotWidget(title="THz Live Stream")
        self.plot.setLabel("bottom", "Time", units="ps")
        self.plot.setLabel("left", "Signal", units="nA")

        self.setCentralWidget(self.plot)


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()