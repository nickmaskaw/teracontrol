from PySide6 import QtWidgets, QtCore

from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class ExperimentControlWidget(QtWidgets.QWidget):

    # --- Signals ---
    axis_selected = QtCore.Signal(str)  # name

    
    def __init__(self):
        super().__init__()

        self._axis_dropdown = QtWidgets.QComboBox()

        self._start = QtWidgets.QDoubleSpinBox(suffix="  ")
        self._stop = QtWidgets.QDoubleSpinBox(suffix="  ")
        self._step = QtWidgets.QDoubleSpinBox(suffix="  ")
        self._dwell = QtWidgets.QDoubleSpinBox(suffix=" s")
        
        self._operator = QtWidgets.QLineEdit()
        self._sample = QtWidgets.QLineEdit()
        self._comment = QtWidgets.QPlainTextEdit()

        self._setup_top_widget()
        self._setup_pars_group()
        self._setup_meta_group()

        self._preconfigure_widgets()

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self._top_widget)
        layout.addWidget(self._pars_group)
        layout.addWidget(self._meta_group)
        self.setLayout(layout)
    
    # --- Internal Helpers ------------------------------------------------

    def _setup_top_widget(self) -> None:
        self._top_widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        layout.addRow("Axis", self._axis_dropdown)
        self._top_widget.setLayout(layout)
    
    def _setup_pars_group(self) -> None:
        self._pars_group = QtWidgets.QGroupBox("Parameters")
        
        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)
        
        layout.addWidget(QtWidgets.QLabel("Start"), 0, 0)
        layout.addWidget(self._start,               0, 1)

        layout.addWidget(QtWidgets.QLabel("Stop"),  1, 0)
        layout.addWidget(self._stop,                1, 1)

        layout.addWidget(QtWidgets.QLabel("Step"),  0, 3)

        layout.addWidget(self._step,                0, 4)
        layout.addWidget(QtWidgets.QLabel("Dwell"), 1, 3)
        layout.addWidget(self._dwell,               1, 4)

        layout.setColumnMinimumWidth(2, 16)
        layout.setColumnStretch(5, 1)

        self._pars_group.setLayout(layout)

    def _setup_meta_group(self) -> None:
        self._meta_group = QtWidgets.QGroupBox("Metadata")
        layout = QtWidgets.QFormLayout()
        layout.addRow("Operator", self._operator)
        layout.addRow("Sample", self._sample)
        layout.addRow("Comment", self._comment)
        self._meta_group.setLayout(layout)        

    def _preconfigure_widgets(self) -> None:
        for spinbox in [self._start, self._stop, self._step, self._dwell]:
            spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            spinbox.setAlignment(QtCore.Qt.AlignRight)
            spinbox.setDecimals(3)
            spinbox.setRange(-10000, 10000)

    # --- Public API ------------------------------------------------------

    def load_axis_list(self, axis_names: list[str]) -> None:
        self._axis_dropdown.clear()
        self._axis_dropdown.addItems(axis_names)

    def current_axis(self) -> str | None:
        return self._axis_dropdown.currentText() or None