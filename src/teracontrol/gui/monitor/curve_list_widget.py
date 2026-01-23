from PySide6 import QtWidgets, QtCore, QtGui
from typing import Optional, Callable


class CurveListWidget(QtWidgets.QWidget):
    """
    Lists curves with checkboxes and optional metadata display.
    Emits intent; does not modify plots directly.
    """

    visibility_changed = QtCore.Signal(int, bool)

    def __init__(self):
        super().__init__()

        self._list = QtWidgets.QListWidget()
        self._list.itemChanged.connect(self._on_item_changed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._list)
        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append_curve(self, meta: dict | None = None, hue: float = 0.0) -> None:
        index = self._list.count()
        label = self._make_label(index, meta or {})

        item = QtWidgets.QListWidgetItem(label)
        item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
        item.setCheckState(QtCore.Qt.Checked)

        color = QtGui.QColor.fromHsvF(hue, 1.0, 1.0)
        pix = QtGui.QPixmap(8, 8)
        pix.fill(color)
        item.setData(QtCore.Qt.DecorationRole, pix)

        self._list.addItem(item)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_item_changed(self, item: QtWidgets.QListWidgetItem) -> None:
        index = self._list.row(item)
        visible = item.checkState() == QtCore.Qt.Checked
        self.visibility_changed.emit(index, visible)

    @staticmethod
    def _make_label(index: int, meta: dict) -> str:
        if not meta:
            return f"Curve {index + 1}"
        
        parts = [f"{k}={v:.2f}" for k, v in meta.items()]
        return f"Curve {index + 1} | " + " | ".join(parts)