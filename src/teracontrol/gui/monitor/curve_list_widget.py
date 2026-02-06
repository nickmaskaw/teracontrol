from PySide6 import QtWidgets, QtCore, QtGui


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

        self._show_all = QtWidgets.QPushButton("Show All")
        self._show_all.clicked.connect(self._on_show_all)

        self._hide_all = QtWidgets.QPushButton("Hide All")
        self._hide_all.clicked.connect(self._on_hide_all)

        self._buttons = QtWidgets.QHBoxLayout()
        self._buttons.addWidget(self._show_all)
        self._buttons.addWidget(self._hide_all)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._list)
        layout.addLayout(self._buttons)
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

    def clear(self):
        self._list.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _on_item_changed(self, item: QtWidgets.QListWidgetItem) -> None:
        index = self._list.row(item)
        visible = item.checkState() == QtCore.Qt.Checked
        self.visibility_changed.emit(index, visible)

    def _on_show_all(self) -> None:
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(QtCore.Qt.Checked)

    def _on_hide_all(self) -> None:
        for i in range(self._list.count()):
            self._list.item(i).setCheckState(QtCore.Qt.Unchecked)

    @staticmethod
    def _make_label(index: int, meta: dict) -> str:
        if not meta:
            return f"Curve {index + 1}"
        
        parts = [
            f"{k}={v:.2f}"
            if isinstance(v, (int, float))
            else f"{k}={v}"
            for k, v in meta.items()
        ]
        return f"Curve {index + 1} | " + " | ".join(parts)