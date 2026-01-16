from PySide6 import QtWidgets, QtCore

class DockWidget(QtWidgets.QDockWidget):
    """
    Thin convenience wrapper around QDockWidget.
    """

    def __init__(
        self,
        name: str,
        parent: QtWidgets.QMainWindow,
        widget: QtWidgets.QWidget,
    ) -> None:
        super().__init__(name, parent)
        
        self.setWidget(widget)
        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)

        parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        parent.window_menu.addAction(self.toggleViewAction())