from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
from DataManager import DataManager

class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Credit Lines')

        # Create data manager instance
        self.data_manager = DataManager()

        # Main layout
        layout = QVBoxLayout(self)

        # Create labels and input fields
        row_labels = ['Row I', 'Row II', 'Row III']
        self.inputs = [QLineEdit(self) for _ in row_labels]
        for row_label, input_field in zip(row_labels, self.inputs):
            row_layout = QHBoxLayout()
            label = QLabel(row_label)
            input_field.setFixedWidth(700)  # Set a wider width
            row_layout.addWidget(label)
            row_layout.addWidget(input_field)
            layout.addLayout(row_layout)

        # Button layout
        button_layout = QHBoxLayout()
        self.btn_revise = QPushButton('Revise', self)
        self.btn_cancel = QPushButton('Cancel', self)
        button_layout.addWidget(self.btn_revise)
        button_layout.addWidget(self.btn_cancel)

        # Add button layout to the main layout
        layout.addLayout(button_layout)

        # Connect the Cancel button to close the dialog
        self.btn_cancel.clicked.connect(self.reject)
        # Connect the Revise button to accept the dialog
        self.btn_revise.clicked.connect(self.accept)

    def update_data(self):
        # Fetch the latest data
        row1, row2, row3 = self.data_manager.chart_data['credit']
        for i, row_data in enumerate([row1, row2, row3]):
            self.inputs[i].setText(row_data)

    def showEvent(self, event):
        # Update data each time the dialog is shown
        self.update_data()
        super().showEvent(event)

    def get_inputs(self):
        return tuple(input_field.text() for input_field in self.inputs)
