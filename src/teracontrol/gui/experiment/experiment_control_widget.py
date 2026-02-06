from __future__ import annotations

from typing import Any
from PySide6 import QtWidgets, QtCore

from teracontrol.core.experiment import ExperimentStatus
from teracontrol.utils.logging import get_logger

log = get_logger(__name__)


class ExperimentControlWidget(QtWidgets.QWidget):

    # --- Signals ---
    run_requested = QtCore.Signal(dict)  # Snapshot of config
    pause_requested = QtCore.Signal()
    resume_requested = QtCore.Signal()
    abort_requested = QtCore.Signal()
    axis_selected = QtCore.Signal(str)  # Axis name
    
    def __init__(self, axis_catalog: dict[str, type] | None = None):
        super().__init__()

        self._axis_catalogue = axis_catalog or {}

        self._build_widgets()
        self._setup_layout()
        self._preconfigure_widgets()
        self._wire_signals()

        self.set_state(ExperimentStatus.IDLE)
    
    # ------------------------------------------------------------------
    # Widget construction
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        # --- Axis Selection ---
        self._axis_dropdown = QtWidgets.QComboBox()

        # --- Parameters ---
        self._start = QtWidgets.QDoubleSpinBox()
        self._stop = QtWidgets.QDoubleSpinBox()
        self._step = QtWidgets.QDoubleSpinBox()
        self._dwell = QtWidgets.QDoubleSpinBox(suffix=" s")
        
        # --- Metadata ---
        self._operator = QtWidgets.QLineEdit()
        self._sample = QtWidgets.QLineEdit()
        self._label = QtWidgets.QLineEdit()
        self._comment = QtWidgets.QPlainTextEdit()

        # --- Controls ---
        self._step_progress = QtWidgets.QProgressBar()
        self._run = QtWidgets.QPushButton("Run")
        self._pause = QtWidgets.QPushButton("Pause")
        self._abort = QtWidgets.QPushButton("Abort")
        self._progress = QtWidgets.QProgressBar()

        self._top_widget = self._build_top_widget()
        self._pars_group = self._build_pars_group()
        self._meta_group = self._build_meta_group()
        self._bottom_widget = self._build_bottom_widget()
        
    def _build_top_widget(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(w)
        layout.addRow("Axis", self._axis_dropdown)
        return w

    def _build_pars_group(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Parameters")
        layout = QtWidgets.QGridLayout(box)
        
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

        return box
    
    def _build_meta_group(self) -> QtWidgets.QWidget:
        box = QtWidgets.QGroupBox("Metadata")
        layout = QtWidgets.QFormLayout(box)
        layout.addRow("Operator", self._operator)
        layout.addRow("Sample", self._sample)
        layout.addRow("Label", self._label)
        layout.addRow("Comment", self._comment)
        return box

    def _build_bottom_widget(self) -> QtWidgets.QWidget:
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.addWidget(self._step_progress)
        sub_layout = QtWidgets.QHBoxLayout()
        sub_layout.addWidget(self._run)
        sub_layout.addWidget(self._pause)
        sub_layout.addWidget(self._abort)
        sub_layout.addStretch(1)
        sub_layout.addWidget(self._progress)
        layout.addLayout(sub_layout)
        return w

    def _setup_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._top_widget)
        layout.addWidget(self._pars_group)
        layout.addWidget(self._meta_group)
        layout.addWidget(self._bottom_widget)

    def _preconfigure_widgets(self) -> None:
        if self._axis_catalogue:
            self._axis_dropdown.addItems(self._axis_catalogue)
            self._update_axis(self.current_axis())
        
        for spinbox in (self._start, self._stop, self._step, self._dwell):
            spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            spinbox.setAlignment(QtCore.Qt.AlignRight)
            spinbox.setRange(-10000, 10000)

        self._dwell.setRange(0, 1000)
        self._dwell.setDecimals(1)

        # --- Tooltips ---
        self._operator.setToolTip(
            "Mandatory: Data owner (will be appended to filename)"
        )
        self._sample.setToolTip(
            "Mandatory: brief sample name (will be appended to filename)"
        )
        self._label.setToolTip(
            "Optional: run label (will be appended to filename)"
        )
        self._comment.setToolTip(
            "Optional: run comment / experiment description\n"
            "Saved as plain text in the HDF5 file\n"
            "(Not appended to filename)"
        )

    def _wire_signals(self) -> None:
        self._run.clicked.connect(
            lambda: self.run_requested.emit(self.current_config())
        )
        self._pause.clicked.connect(self._on_pause_clicked)
        self._abort.clicked.connect(
            lambda: self.abort_requested.emit()
        )
        self._axis_dropdown.currentTextChanged.connect(
            self._on_axis_selected
        )

    # ------------------------------------------------------------------
    # UI -> Controller intent
    # ------------------------------------------------------------------

    def _on_pause_clicked(self) -> None:
        if self._pause.text() == "Pause":
            self.pause_requested.emit()
        else:
            self.resume_requested.emit()

    def _on_axis_selected(self, axis_name: str) -> None:
        self._update_axis(axis_name)

    # ------------------------------------------------------------------
    # Controller -> GUI callbacks
    # ------------------------------------------------------------------

    def set_state(self, status: ExperimentStatus) -> None:
        idle = status in (ExperimentStatus.IDLE, ExperimentStatus.ERROR)
        paused = status is ExperimentStatus.PAUSED

        self._top_widget.setEnabled(idle)
        self._pars_group.setEnabled(idle)
        self._meta_group.setEnabled(idle)
        
        self._run.setEnabled(idle)
        self._pause.setEnabled(not idle)
        self._abort.setEnabled(not idle)

        self._pause.setText("Resume" if paused else "Pause")

    def set_progress(self, current: int, total: int) -> None:
        self._progress.setMaximum(total)
        self._progress.setValue(current)

    def set_step_progress(self, current: int, total: int, message: str) -> None:
        self._step_progress.setMaximum(total)
        self._step_progress.setValue(current)
        self._step_progress.setFormat(message)

    def load_presets(self, presets: dict[str, Any]) -> None:
        try:
            self._start.setValue(presets["start"])
            self._stop.setValue(presets["stop"])
            self._step.setValue(presets["step"])
            self._dwell.setValue(presets["dwell"])
        except Exception:
            log.error("Failed to load presets", exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Axis handling
    # ------------------------------------------------------------------

    def _update_axis(self, axis_name: str) -> None:
        axis_cls = self._axis_catalogue[axis_name]
        decimals = axis_cls.decimals
        unit = axis_cls.unit
        minimum = axis_cls.minimum
        maximum = axis_cls.maximum

        for spinbox in (self._start, self._stop, self._step):
            spinbox.setDecimals(decimals)
            spinbox.setSuffix(f" {unit}")
            spinbox.setRange(minimum, maximum)
        
        self.axis_selected.emit(axis_name)

    # ------------------------------------------------------------------
    # Snapshot API
    # ------------------------------------------------------------------

    def current_axis(self) -> str:
        return self._axis_dropdown.currentText() or None
    
    def current_pars(self) -> dict[str, Any]:
        return {
            "start": self._start.value(),
            "stop": self._stop.value(),
            "step": self._step.value(),
            "dwell": self._dwell.value(),
        }
    
    def current_meta(self) -> dict[str, Any]:
        return {
            "operator": self._operator.text(),
            "sample": self._sample.text(),
            "label": self._label.text(),
            "comment": self._comment.toPlainText(),
        }
    
    def current_config(self) -> dict[str, Any]:
        return {
            "axis": self.current_axis(),
            "pars": self.current_pars(),
            "meta": self.current_meta(),
        }