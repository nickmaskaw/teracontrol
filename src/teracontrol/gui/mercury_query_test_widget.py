from PySide6 import QtWidgets, QtCore

class MercuryQueryTestWidget(QtWidgets.QWidget):

    query_requested = QtCore.Signal(str)

    def __init__(self):
        super().__init__()
        self._waiting_response = False

        self.query = QtWidgets.QLineEdit()
        self.button = QtWidgets.QPushButton("Query")
        self.response = QtWidgets.QLineEdit()
        
        self.response.setReadOnly(True)

        query_row = QtWidgets.QHBoxLayout()
        query_row.addWidget(self.query)
        query_row.addWidget(self.button)

        layout = QtWidgets.QFormLayout()
        layout.addRow("Query", query_row)
        layout.addRow("Response", self.response)

        self.setLayout(layout)

        self.button.clicked.connect(self._on_button_clicked)
        self.query.returnPressed.connect(self._on_return_pressed)

        #self.setEnabled(False)

    def _on_button_clicked(self):
        if self._waiting_response:
            return # Ignore clicks while waiting
        
        self._waiting_response = True
        self.query_requested.emit(self.query.text())

    def _on_return_pressed(self):
        self._on_button_clicked()

    def set_response(self, response: str):
        self.response.setText(response)
        self._waiting_response = False