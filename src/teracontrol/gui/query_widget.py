from PySide6 import QtWidgets, QtCore


class QueryWidget(QtWidgets.QWidget):
    
    query_requested = QtCore.Signal(str, str)
    # name, message

    def __init__(self, config: dict):
        super().__init__()

        self.config = config
        self.names = list(self.config.keys())

        self._waiting: dict[str, bool] = {name: False for name in self.names}

        self.queries: dict[str, QtWidgets.QLineEdit] = {}
        self.buttons: dict[str, QtWidgets.QPushButton] = {}
        self.response = QtWidgets.QPlainTextEdit()

        self.response.setReadOnly(True)
        self.response.font().setFamily("Monospace")

        layout = QtWidgets.QFormLayout()

        for name in self.names:
            query = QtWidgets.QLineEdit()
            query.returnPressed.connect(
                lambda n=name: self._on_return_pressed(n)
            )

            button = QtWidgets.QPushButton("Query")
            button.clicked.connect(
                lambda _, n=name: self._on_button_clicked(n)
            )

            self.queries[name] = query
            self.buttons[name] = button

            query_row = QtWidgets.QHBoxLayout()
            query_row.addWidget(query)
            query_row.addWidget(button)

            layout.addRow(name, query_row)

        layout.addRow("Response", self.response)

        self.setLayout(layout)

    def _on_button_clicked(self, name:str):
        if self._waiting[name]:
            return # Ignore clicks while waiting
        
        self._waiting[name] = True
        self.query_requested.emit(name, self.queries[name].text())

    def _on_return_pressed(self, name: str):
        self._on_button_clicked(name)

    def update_response(self, name: str, query: str,response: str):
        self.response.appendPlainText(f"{name}:\n    Query: {query}\n    Response: {response}\n")
        self._waiting[name] = False

            

