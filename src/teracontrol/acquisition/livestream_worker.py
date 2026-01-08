from PySide6 import QtCore
from teracontrol.acquisition.livestream import THzLiveStream


class LiveStreamWorker(QtCore.QThread):
    """
    QThread wrapper around THzLiveStream
    """

    new_trace = QtCore.Signal(object)
    finished = QtCore.Signal()

    def __init__(self, thz):
        super().__init__()
        self.thz = thz
        self._engine = None

    def run(self):
        """
        Entry point of the worker thread.
        """
        self._engine = THzLiveStream(
            thz=self.thz,
            on_new_trace=self._emit_trace,
        )

        self._engine.start()
        self.finished.emit()

    def stop(self):
        """
        Stop the livestream safely.
        """
        if self._engine is not None:
            self._engine.stop()

    def _emit_trace(self, trace):
        self.new_trace.emit(trace)