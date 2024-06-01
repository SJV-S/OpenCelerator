from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QGroupBox, QHBoxLayout, QButtonGroup, QLineEdit, QLabel, QPushButton
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


class SaveImageDialog(QDialog):
    def __init__(self, parent=None):
        super(SaveImageDialog, self).__init__(parent)
        self.setWindowTitle('Format & resolution')

        # Create layout
        layout = QVBoxLayout(self)

        # Format selection group
        format_group = QGroupBox('Format')
        format_layout = QVBoxLayout()
        self.radio_png = QRadioButton('PNG')
        self.radio_pdf = QRadioButton('PDF')
        self.radio_jpg = QRadioButton('JPG')
        self.radio_pdf.setChecked(True)  # Default option
        format_layout.addWidget(self.radio_png)
        format_layout.addWidget(self.radio_pdf)
        format_layout.addWidget(self.radio_jpg)
        format_group.setLayout(format_layout)

        # Connect format radio buttons to update resolution state
        self.radio_png.toggled.connect(self.update_resolution_state)
        self.radio_pdf.toggled.connect(self.update_resolution_state)
        self.radio_jpg.toggled.connect(self.update_resolution_state)

        # Resolution selection group
        resolution_group = QGroupBox('Resolution')
        resolution_layout = QVBoxLayout()
        self.radio_high = QRadioButton('High (300 dpi)')
        self.radio_medium = QRadioButton('Medium (200 dpi)')
        self.radio_low = QRadioButton('Low (100 dpi)')
        self.radio_medium.setChecked(True)  # Default option
        resolution_layout.addWidget(self.radio_high)
        resolution_layout.addWidget(self.radio_medium)
        resolution_layout.addWidget(self.radio_low)
        resolution_group.setLayout(resolution_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Add groups to layout
        layout.addWidget(format_group)
        layout.addWidget(resolution_group)
        layout.addWidget(buttons)
        self.setLayout(layout)

        # Store resolution group to enable/disable it
        self.resolution_group = resolution_group

        # Initial state update
        self.update_resolution_state()

    def get_selected_options(self):
        # Get the selected format
        if self.radio_png.isChecked():
            format_selected = 'png'
        elif self.radio_pdf.isChecked():
            format_selected = 'pdf'
        elif self.radio_jpg.isChecked():
            format_selected = 'jpg'

        # Get the selected resolution
        if self.radio_high.isChecked():
            resolution_selected = 300
        elif self.radio_medium.isChecked():
            resolution_selected = 200
        elif self.radio_low.isChecked():
            resolution_selected = 100
        else:
            resolution_selected = None  # For PDF, resolution is not applicable

        return format_selected, resolution_selected

    def update_resolution_state(self):
        # Enable or disable the resolution group based on the selected format
        is_pdf_selected = self.radio_pdf.isChecked()
        self.radio_high.setEnabled(not is_pdf_selected)
        self.radio_medium.setEnabled(not is_pdf_selected)
        self.radio_low.setEnabled(not is_pdf_selected)
