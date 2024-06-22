from resources.resources_rc import *

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QGroupBox, QHBoxLayout, QLineEdit, QLabel, QPushButton, QGridLayout, QSpinBox, QScrollArea, QComboBox, QListWidget,
                             QColorDialog, QListWidgetItem, QDoubleSpinBox, QApplication, QFrame)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QPixmap, QClipboard
from DataManager import DataManager
import calendar


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


class StartDateDialog(QDialog):
    def __init__(self, parent=None):
        super(StartDateDialog, self).__init__(parent)
        self.setWindowTitle('Set Start Date')

        # Create data manager instance
        self.data_manager = DataManager()

        # Initialize dialog layout
        layout = QVBoxLayout(self)

        # Create a grid layout for selection controls
        grid_layout = QGridLayout()

        # Assume start_date is a pandas Timestamp object
        start_date = self.data_manager.chart_data['start_date'].to_pydatetime()
        start_date_day = start_date.day
        current_month = start_date.month
        current_year = start_date.year

        # SpinBox for selecting Day (nearest Sunday)
        sunday_label = QLabel('Day')
        self.sunday_spinbox = QSpinBox()
        self.sunday_spinbox.setRange(1, 31)
        self.sunday_spinbox.setValue(start_date_day)
        grid_layout.addWidget(sunday_label, 0, 0)
        grid_layout.addWidget(self.sunday_spinbox, 0, 1)

        # SpinBox for selecting Month
        month_label = QLabel('Month')
        self.month_spinbox = QSpinBox()
        self.month_spinbox.setRange(1, 12)
        self.month_spinbox.setValue(current_month)
        grid_layout.addWidget(month_label, 1, 0)
        grid_layout.addWidget(self.month_spinbox, 1, 1)

        # SpinBox for selecting Year
        year_label = QLabel('Year')
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setRange(current_year - 300, current_year + 300)
        self.year_spinbox.setValue(current_year)
        grid_layout.addWidget(year_label, 2, 0)
        grid_layout.addWidget(self.year_spinbox, 2, 1)

        # Add grid
        layout.addLayout(grid_layout)

        # Buttons for OK and Cancel
        self.btn_ok = QPushButton('OK', self)
        self.btn_cancel = QPushButton('Cancel', self)
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_cancel)

    def get_date(self):
        day = self.sunday_spinbox.value()
        month = self.month_spinbox.value()
        year = self.year_spinbox.value()

        # Get the maximum number of days in the given month and year
        max_day = calendar.monthrange(year, month)[1]
        # Adjust day if it exceeds the maximum days in the month
        if day > max_day:
            day = max_day

        return f'{day}-{month}-{year}'


class ConfigureTemplateDialog(QDialog):
    def __init__(self, figure_manager, data_key, title, default_item, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(300, 300, 400, 300)
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.items = self.data_manager.chart_data[data_key]
        self.default_item = default_item
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Group box for configuration options
        config_group_box = QGroupBox('Styles')
        config_layout = QVBoxLayout(config_group_box)

        # Line text
        self.line_text = QLineEdit('')
        config_layout.addWidget(QLabel('Text'))
        config_layout.addWidget(self.line_text)

        # Font color picker
        self.font_color_button = QPushButton("Choose Font Color")
        self.font_color_button.clicked.connect(self.choose_font_color)
        config_layout.addWidget(QLabel("Font Color"))
        config_layout.addWidget(self.font_color_button)

        # Font size selector
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 32)  # Example range
        config_layout.addWidget(QLabel("Font Size"))
        config_layout.addWidget(self.font_size_spinbox)

        # Box background color picker
        self.box_bg_color_button = QPushButton("Choose Background Color")
        self.box_bg_color_button.clicked.connect(self.choose_bg_color)
        config_layout.addWidget(QLabel("Box Background Color"))
        config_layout.addWidget(self.box_bg_color_button)

        # Box edge color picker
        self.box_edge_color_button = QPushButton("Choose Edge Color")
        self.box_edge_color_button.clicked.connect(self.choose_edge_color)
        config_layout.addWidget(QLabel("Box Edge Color"))
        config_layout.addWidget(self.box_edge_color_button)

        # Line color picker
        self.line_color_button = QPushButton("Choose Line Color")
        self.line_color_button.clicked.connect(self.choose_line_color)
        config_layout.addWidget(QLabel("Line Color"))
        config_layout.addWidget(self.line_color_button)

        # Line width selector
        self.line_width_spinbox = QDoubleSpinBox()
        self.line_width_spinbox.setRange(0.1, 10.0)
        self.line_width_spinbox.setSingleStep(0.1)
        config_layout.addWidget(QLabel("Line Width"))
        config_layout.addWidget(self.line_width_spinbox)

        # Line style selector
        self.line_style_combobox = QComboBox()
        self.line_style_map = {"Solid": "-", "Dashed": "--", "Dotted": ":", "DashDot": "-."}
        self.line_style_combobox.addItems(self.line_style_map.keys())
        config_layout.addWidget(QLabel("Line Style"))
        config_layout.addWidget(self.line_style_combobox)

        # Styles buttons
        self.update_btn = QPushButton("Update")
        self.update_btn.setToolTip('Item in list must be selected.')
        self.update_btn.clicked.connect(lambda: self.update_item_styles(self.list_widget.currentRow()))
        self.update_btn.setEnabled(False)  # Initially disable the button
        config_layout.addWidget(self.update_btn)

        # Update button
        set_default_btn = QPushButton("Set as default")
        set_default_btn.clicked.connect(self.set_default_style)
        config_layout.addWidget(set_default_btn)

        layout.addWidget(config_group_box)

        # List box and buttons
        right_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.populate_fields)
        self.list_widget.itemSelectionChanged.connect(self.update_button_state)  # Connect to update_button_state method
        right_layout.addWidget(self.list_widget)

        self.populate_fields_with_defaults()

        # Buttons below list box
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("Delete")
        remove_btn.clicked.connect(lambda: self.delete_selected_item(self.list_widget.currentRow()))
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(exit_btn)
        right_layout.addLayout(btn_layout)

        layout.addLayout(right_layout)
        self.setLayout(layout)

    def update_button_state(self):
        """Enable the update button only if an item is selected."""
        selected_items = self.list_widget.selectedItems()
        self.update_btn.setEnabled(len(selected_items) > 0)

    def set_default_style(self):
        self.default_item['font_size'] = self.font_size_spinbox.value()
        self.default_item['font_color'] = self.font_color_button.text()
        self.default_item['bg_color'] = self.box_bg_color_button.text()
        self.default_item['edge_color'] = self.box_edge_color_button.text()
        self.default_item['line_color'] = self.line_color_button.text()
        self.default_item['linewidth'] = self.line_width_spinbox.value()
        self.default_item['linestyle'] = self.line_style_map[self.line_style_combobox.currentText()]
        self.accept()

    def delete_selected_item(self, selected_item):
        if selected_item != -1:
            self.list_widget.takeItem(selected_item)
            self.figure_manager.selective_item_removal(item_type=self.data_key, selected=selected_item)

    def populate_fields(self, current):
        if current:
            item_data = current.data(Qt.UserRole)
            self.font_size_spinbox.setValue(item_data.get('font_size', 12))
            self.line_text.setText(item_data.get('text', ''))
            self.set_color_button_style(self.font_color_button, item_data.get('font_color', '#000000'))
            self.set_color_button_style(self.box_bg_color_button, item_data.get('bg_color', '#FFFFFF'))
            self.set_color_button_style(self.box_edge_color_button, item_data.get('edge_color', '#000000'))
            self.set_color_button_style(self.line_color_button, item_data.get('line_color', '#000000'))
            self.line_width_spinbox.setValue(item_data.get('linewidth', 1))
            style_value = item_data.get('linestyle', '-')
            style_key = next(key for key, value in self.line_style_map.items() if value == style_value)
            index = self.line_style_combobox.findText(style_key)
            self.line_style_combobox.setCurrentIndex(index)

    def populate_fields_with_defaults(self):
        self.font_size_spinbox.setValue(self.default_item['font_size'])
        self.line_text.setText(self.default_item['text'])
        self.set_color_button_style(self.font_color_button, self.default_item['font_color'])
        self.set_color_button_style(self.box_bg_color_button, self.default_item['bg_color'])
        self.set_color_button_style(self.box_edge_color_button, self.default_item['edge_color'])
        self.set_color_button_style(self.line_color_button, self.default_item['line_color'])
        self.line_width_spinbox.setValue(self.default_item['linewidth'])
        style_value = self.default_item['linestyle']
        style_key = next(key for key, value in self.line_style_map.items() if value == style_value)
        index = self.line_style_combobox.findText(style_key)
        self.line_style_combobox.setCurrentIndex(index)

    def update_item_styles(self, selected_item, item_type):
        if selected_item == -1:
            return
        old_item = self.items[selected_item]
        new_item = {
            **old_item,
            'text': self.line_text.text(),
            'font_size': self.font_size_spinbox.value(),
            'font_color': self.font_color_button.text(),
            'bg_color': self.box_bg_color_button.text(),
            'edge_color': self.box_edge_color_button.text(),
            'line_color': self.line_color_button.text(),
            'linewidth': self.line_width_spinbox.value(),
            'linestyle': self.line_style_map[self.line_style_combobox.currentText()],
        }
        self.delete_selected_item(selected_item)
        self.figure_manager.replot(new_item, self.data_key)
        self.figure_manager.refresh()
        self.items.append(new_item)
        self.refresh_list_box(item_type=item_type)

    def choose_font_color(self):
        self.select_color(self.font_color_button)

    def choose_bg_color(self):
        self.select_color(self.box_bg_color_button)

    def choose_edge_color(self):
        self.select_color(self.box_edge_color_button)

    def choose_line_color(self):
        self.select_color(self.line_color_button)

    def refresh_list_box(self, item_type):
        self.list_widget.clear()
        for item in self.items:

            if item_type == 'trend':
                to_display = f"{item['text']}, {item['date1']} -- {item['date2']}"
            elif item_type == 'aim':
                to_display = f"{item['text']}, {item['date1']} -- {item['date2']}"
            elif item_type == 'phase':
                to_display = f"{item['text']}, {item['date']}, {item['y']}"

            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)

    def select_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color_button_style(button, color.name())

    def set_color_button_style(self, button, color):
        button.setStyleSheet(f'border: 3px solid {color};')
        button.setText(color)


class ConfigurePhaseLinesDialog(ConfigureTemplateDialog):
    def __init__(self, figure_manager, parent=None):
        super().__init__(figure_manager, 'phase', "Phase Line Configuration", figure_manager.default_phase_item, parent)
        self.refresh_list_box()  # Populate the list box immediately after initialization

    def update_item_styles(self, selected_item):
        if selected_item == -1:
            return
        old_phase_line = self.items[selected_item]
        new_phase_line = {
            **old_phase_line,
            'text': self.line_text.text(),
            'font_size': self.font_size_spinbox.value(),
            'font_color': self.font_color_button.text(),
            'bg_color': self.box_bg_color_button.text(),
            'edge_color': self.box_edge_color_button.text(),
            'line_color': self.line_color_button.text(),
            'linewidth': self.line_width_spinbox.value(),
            'linestyle': self.line_style_map[self.line_style_combobox.currentText()],
        }
        self.delete_selected_item(selected_item)
        self.figure_manager.phase_replot(new_phase_line)
        self.figure_manager.refresh()
        self.items.append(new_phase_line)
        self.refresh_list_box()

    def delete_selected_item(self, selected_item):
        if selected_item != -1:
            self.list_widget.takeItem(selected_item)
            self.figure_manager.selective_item_removal(item_type='phase', selected=selected_item)

    def refresh_list_box(self):
        self.list_widget.clear()
        for item in self.items:
            to_display = f"{item['text']}, {item['date']}, {item['y']}"
            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)


class ConfigureAimLinesDialog(ConfigureTemplateDialog):
    def __init__(self, figure_manager, parent=None):
        super().__init__(figure_manager, 'aim', "Aim Configuration", figure_manager.default_aim_item, parent)
        self.refresh_list_box()  # Populate the list box immediately after initialization

    def update_item_styles(self, selected_item):
        if selected_item == -1:
            return
        old_aim = self.items[selected_item]
        new_aim = {
            **old_aim,
            'text': self.line_text.text(),
            'font_size': self.font_size_spinbox.value(),
            'font_color': self.font_color_button.text(),
            'bg_color': self.box_bg_color_button.text(),
            'edge_color': self.box_edge_color_button.text(),
            'line_color': self.line_color_button.text(),
            'linewidth': self.line_width_spinbox.value(),
            'linestyle': self.line_style_map[self.line_style_combobox.currentText()],
        }
        self.delete_selected_item(selected_item)
        self.figure_manager.aim_replot(new_aim)
        self.figure_manager.refresh()
        self.items.append(new_aim)
        self.refresh_list_box()

    def delete_selected_item(self, selected_item):
        if selected_item != -1:
            self.list_widget.takeItem(selected_item)
            self.figure_manager.selective_item_removal(item_type='aim', selected=selected_item)

    def refresh_list_box(self):
        self.list_widget.clear()
        for item in self.items:
            to_display = f"{item['text']}, {item['date1']}, {item['date2']}, {item['y']}"
            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)


class ConfigureTrendLinesDialog(ConfigureTemplateDialog):
    def __init__(self, corr, figure_manager, parent=None):
        self.corr = corr
        title = 'Dot' if self.corr else 'X'
        super().__init__(figure_manager, 'trend_corr' if self.corr else 'trend_err', f"{title} Trend Configuration",
                         figure_manager.default_trend_corr_item if self.corr else figure_manager.default_trend_err_item, parent)
        self.refresh_list_box()  # Populate the list box immediately after initialization

    def update_item_styles(self, selected_item):
        if selected_item == -1:
            return
        old_trend = self.items[selected_item]
        new_trend = {
            **old_trend,
            'text': self.line_text.text(),
            'font_size': self.font_size_spinbox.value(),
            'font_color': self.font_color_button.text(),
            'line_color': self.line_color_button.text(),
            'linewidth': self.line_width_spinbox.value(),
            'linestyle': self.line_style_map[self.line_style_combobox.currentText()],
        }
        self.delete_selected_item(selected_item)
        self.figure_manager.trend_replot(new_trend, self.corr)
        self.figure_manager.refresh()
        self.items.append(new_trend)
        self.refresh_list_box()

    def delete_selected_item(self, selected_item):
        if selected_item != -1:
            self.list_widget.takeItem(selected_item)
            self.figure_manager.selective_item_removal(item_type='trend', selected=selected_item, corr=self.corr)

    def refresh_list_box(self):
        self.list_widget.clear()
        for item in self.items:
            to_display = f"{item['text']}, {item['date1']} -- {item['date2']}"
            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.UserRole, item)
            self.list_widget.addItem(list_item)


class SupportDevDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(600, 400)  # Resize the dialog to be larger
        layout = QVBoxLayout()

        # Scroll area to handle longer text inside a QLabel
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        contentWidget = QLabel()
        contentWidget.setWordWrap(True)
        contentWidget.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        contentWidget.setTextFormat(Qt.RichText)
        # Adding margins around the text
        contentWidget.setStyleSheet("padding: 20px;")
        contentWidget.setText(
        "<style>"
        "p, li { font-size: 14px; font-style: normal}" 
        "li { margin-bottom: 10px; }"
        "p.center { text-align: center; }"
        "</style>"
        "<p class='center'><b>iChart will forever remain free and open-source </b></p>"
        "<p> The project has accumulated an extensive number of hours. "
        "If you find iChart useful and would like for me to continue working on the project, please consider donating.</p>"
        "<p>Other ways to contribute:</p>"
        "<ul>"
        "<li>Provide feedback. Let me know what you like and what can be improved, report bugs, etc. Contact: "
        "<a href='mailto:ichart.wopak@simplelogin.com'>ichart.wopak@simplelogin.com</a></li>"
        "<li>Share this tool with others who might find it useful.</li>"
        "<li>Help me get a job. Any help with networking would be much appreciated. I hold a PhD in behavior analysis. Will share CV upon request.</li>"
        "</ul>"
        )

        scrollArea.setWidget(contentWidget)
        layout.addWidget(scrollArea)

        # Button to perform an action, e.g., open a link or close the dialog
        btn_layout = QHBoxLayout()

        patreon_btn = QPushButton('Patreon')
        patreon_icon = QIcon(':/images/patreon_logo.png')
        patreon_btn.setIcon(patreon_icon)
        patreon_btn.clicked.connect(self.patreon_btn_clicked)

        bitcoin_btn = QPushButton('Bitcoin')
        bitcoin_icon = QIcon(':/images/bitcoin_logo.png')
        bitcoin_btn.setIcon((bitcoin_icon))
        bitcoin_btn.clicked.connect(self.bitcoin_btn_clicked)

        # exit_btn = QPushButton('Exit')
        # exit_btn.clicked.connect(self.exit_btn_clicked)

        btn_layout.addWidget(patreon_btn)
        btn_layout.addWidget(bitcoin_btn)
        # btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setWindowTitle('Support iChart')

    def patreon_btn_clicked(self):
        QDesktopServices.openUrl(QUrl('https://www.patreon.com/johanpigeon/membership'))
        self.accept()

    def bitcoin_btn_clicked(self):
        self.close()
        popup = BitcoinDonationPopup(self)
        popup.exec_()  # Use exec_() to show the dialog modally

    def exit_btn_clicked(self):
        self.accept()  # Closes the dialog


class BitcoinDonationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bitcoin")
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout(self)  # Use QHBoxLayout for horizontal arrangement
        self.layout.setSpacing(20)  # Increase horizontal spacing

        # First image and button layout with frame
        first_frame = QFrame(self)
        first_frame.setFrameShape(QFrame.StyledPanel)
        first_layout = QVBoxLayout(first_frame)
        first_layout.setContentsMargins(0, 0, 0, 0)  # Reduce padding around the label and image
        first_layout.setSpacing(5)  # Minimal spacing between widgets

        first_label = QLabel("Bitcoin (Base chain)", self)
        first_label.setAlignment(Qt.AlignCenter)  # Center the label horizontally
        first_label.setStyleSheet("font: normal 10pt Arial; margin: 0; padding: 0; font-size: 15px")  # Ensure the font is not italic
        first_layout.addWidget(first_label)

        self.imageLabel1 = QLabel(self)
        pixmap1 = QPixmap(':/images/base_chain_qr.png')
        self.imageLabel1.setPixmap(pixmap1)
        first_layout.addWidget(self.imageLabel1)

        self.copyButton1 = QPushButton("Copy Address", self)
        self.copyButton1.clicked.connect(lambda: self.copyAddress("bc1qg8y5pxv5g86mhj59xdk89r6tr70zdw6rh6rwh4", self.copyButton1))
        first_layout.addWidget(self.copyButton1)

        # Second image and button layout with frame
        second_frame = QFrame(self)
        second_frame.setFrameShape(QFrame.StyledPanel)
        second_layout = QVBoxLayout(second_frame)
        second_layout.setContentsMargins(0, 0, 0, 0)  # Reduce padding around the label and image
        second_layout.setSpacing(5)  # Minimal spacing between widgets

        second_label = QLabel("Lightning (LNURL)", self)
        second_label.setAlignment(Qt.AlignCenter)  # Center the label horizontally
        second_label.setStyleSheet("font: normal 10pt Arial; margin: 0; padding: 0; font-size: 15px")
        second_layout.addWidget(second_label)

        self.imageLabel2 = QLabel(self)
        pixmap2 = QPixmap(':/images/lightning_qr.png')
        self.imageLabel2.setPixmap(pixmap2)
        second_layout.addWidget(self.imageLabel2)

        self.copyButton2 = QPushButton("Copy Address", self)
        self.copyButton2.clicked.connect(lambda: self.copyAddress("pigeon@getalby.com", self.copyButton2))
        second_layout.addWidget(self.copyButton2)

        # Add the individual frames to the main horizontal layout
        self.layout.addWidget(first_frame)
        self.layout.addWidget(second_frame)

        # Set the geometry of the window
        total_width = pixmap1.width() + pixmap2.width() + 60  # Add more padding
        max_height = max(pixmap1.height(), pixmap2.height()) + 100  # Add space for labels and buttons
        self.setGeometry(300, 300, total_width, max_height)

    def copyAddress(self, address, button):
        clipboard = QApplication.clipboard()
        clipboard.setText(address)
        button.setText("Copied!")
        QTimer.singleShot(3000, lambda: button.setText("Copy Address"))

