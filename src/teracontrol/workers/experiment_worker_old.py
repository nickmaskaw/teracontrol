from PySide6 import QtCore


class ExperimentWorker(QtCore.QThread):
    """
    Qt worker that runs a headless experiment.
    """

    finished = QtCore.Signal()

    def __init__(self, experiment):
        super().__init__()
        self.experiment = experiment

    def run(self):
        self.experiment.run()
        self.finished.emit()

    def stop(self):
        self.experiment.stop()