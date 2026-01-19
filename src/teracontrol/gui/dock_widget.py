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
        menu: QtWidgets.QMenu | None = None,
        set_floating: bool = False,
    ) -> None:
        super().__init__(name, parent)
        
        self.setWidget(widget)
        if set_floating:
            self.setFloating(True)
            self.hide()
            self.setAllowedAreas(QtCore.Qt.NoDockWidgetArea)
        else:
            self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea)
            parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        
        if menu is not None:
            menu.addAction(self.toggleViewAction())