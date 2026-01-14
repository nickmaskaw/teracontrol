from PySide6 import QtWidgets, QtCore

class LiveStreamExperimentWidget(QtWidgets.QWidget):
    """Live stream experiment widget."""

    run_requested = QtCore.Signal()
    stop_requested = QtCore.Signal()

    def __init__(self):
        super().__init__()

        self.button = QtWidgets.QPushButton("Run")
        self.button.clicked.connect(self._button_clicked)

        layout = QtWidgets.QFormLayout()
        layout.addRow("Livestream", self.button)
        self.setLayout(layout)

    def _button_clicked(self):
        if self.button.text() == "Run":
            self.run_requested.emit()
        else:
            self.stop_requested.emit()

    def set_running(self, running: bool):
        self.button.setText("Stop" if running else "Run")