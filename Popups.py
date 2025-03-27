from resources.resources_rc import *

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox, QGroupBox, QHBoxLayout, QLineEdit, QLabel, QPushButton, QGridLayout, QSpinBox, QScrollArea, QComboBox, QListWidget,
                               QColorDialog, QListWidgetItem, QDoubleSpinBox, QApplication, QFrame, QStackedLayout, QTextEdit, QMessageBox, QFormLayout, QWidget, QSizePolicy)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QPixmap
from EventBus import EventBus
import pandas as pd
import re
import warnings

from DataManager import DataManager
import calendar


class InputDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Credit Lines')
        self.setFixedSize(900, 150)

        # Create data manager instance
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Main layout
        layout = QVBoxLayout(self)

        # Create labels and input fields
        row_labels = ['Row I', 'Row II']  # Reduced to 2 rows
        self.inputs = [QLineEdit(self) for _ in row_labels]
        for row_label, input_field in zip(row_labels, self.inputs):
            row_layout = QHBoxLayout()
            label = QLabel(row_label)
            input_field.setFixedWidth(900)
            row_layout.addWidget(label)
            row_layout.addWidget(input_field)
            layout.addLayout(row_layout)

        # Button layout
        button_layout = QHBoxLayout()
        self.btn_revise = QPushButton('Revise', self)
        self.btn_cancel = QPushButton('Cancel', self)
        button_layout.addWidget(self.btn_revise)
        button_layout.addWidget(self.btn_cancel)
        layout.addLayout(button_layout)

        self.btn_cancel.clicked.connect(self.reject)
        self.btn_revise.clicked.connect(self.accept)

    def update_data(self):
        # Fetch only first two rows
        row1, row2 = self.data_manager.chart_data['credit']
        for i, row_data in enumerate([row1, row2]):
            self.inputs[i].setText(row_data)

    def showEvent(self, event):
        self.update_data()
        super().showEvent(event)

    def get_inputs(self):
        return tuple(input_field.text() for input_field in self.inputs)


class SaveImageDialog(QDialog):
    def __init__(self, parent=None):
        super(SaveImageDialog, self).__init__(parent)
        self.setWindowTitle('Format')

        # Create layout
        layout = QVBoxLayout(self)

        # Format selection group
        format_group = QGroupBox('Format')
        format_layout = QVBoxLayout()
        self.radio_pdf = QRadioButton('PDF')
        self.radio_png = QRadioButton('PNG')
        self.radio_jpg = QRadioButton('JPG')
        self.radio_svg = QRadioButton('SVG')
        self.radio_pdf.setChecked(True)  # Default option
        format_layout.addWidget(self.radio_pdf)
        format_layout.addWidget(self.radio_png)
        format_layout.addWidget(self.radio_jpg)
        format_layout.addWidget(self.radio_svg)
        format_group.setLayout(format_layout)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        # Add groups to layout
        layout.addWidget(format_group)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_selected_options(self):
        # Get the selected format
        if self.radio_png.isChecked():
            format_selected = 'png'
            resolution_selected = 300  # Default for raster formats
        elif self.radio_pdf.isChecked():
            format_selected = 'pdf'
            resolution_selected = None  # Not applicable for vector formats
        elif self.radio_jpg.isChecked():
            format_selected = 'jpg'
            resolution_selected = 300  # Default for raster formats
        elif self.radio_svg.isChecked():
            format_selected = 'svg'
            resolution_selected = None  # Not applicable for vector formats

        return format_selected, resolution_selected


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
        self.year_spinbox.setRange(1679, 2261)
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

        return f'{year}-{month}-{day}'


class ConfigureTemplateDialog(QDialog):
    def __init__(self, figure_manager, data_key, title, default_item, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setGeometry(300, 300, 400, 300)
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.items = self.data_manager.chart_data[data_key]
        self.default_item = default_item
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Group box for configuration options
        config_layout = QVBoxLayout()

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
        self.line_style_map = {"Solid": "-", "Dashed": "--", "Dotted": ":"}
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

        layout.addLayout(config_layout)

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
            item_data = current.data(Qt.ItemDataRole.UserRole)
            self.font_size_spinbox.setValue(item_data.get('font_size', 12))
            self.line_text.setText(item_data.get('text', ''))
            self.set_color_button_style(self.font_color_button, item_data.get('font_color', '#000000'))
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
            to_display = f"{item['text']}, {item['date']}"
            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
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
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)


class ConfigureTrendLinesDialog(QDialog):
    def __init__(self, user_col, trend_style, figure_manager, parent=None):
        super().__init__(parent)
        self.user_col = user_col
        self.trend_style = trend_style
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.items = self.data_manager.chart_data[trend_style]
        self.default_item = self.data_manager.user_preferences[trend_style + "_style"]
        self.line_style_map = {"Solid": "-", "Dashed": "--", "Dotted": ":"}

        self.setWindowTitle(f"{user_col} Configuration")
        self.setGeometry(300, 300, 400, 300)
        self.init_ui()
        self.refresh_list_box()
        self.populate_fields_with_defaults()

    def init_ui(self):
        layout = QHBoxLayout(self)

        # Left side - Configuration options
        config_group_box = QGroupBox('Styles')
        config_layout = QVBoxLayout(config_group_box)

        # Line text input
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
        self.font_size_spinbox.setRange(8, 32)
        config_layout.addWidget(QLabel("Font Size"))
        config_layout.addWidget(self.font_size_spinbox)

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
        self.line_style_combobox.addItems(self.line_style_map.keys())
        config_layout.addWidget(QLabel("Line Style"))
        config_layout.addWidget(self.line_style_combobox)

        # Update button
        self.update_btn = QPushButton("Update")
        self.update_btn.setToolTip('Item in list must be selected.')
        self.update_btn.clicked.connect(lambda: self.update_item_styles(self.list_widget.currentRow()))
        self.update_btn.setEnabled(False)
        config_layout.addWidget(self.update_btn)

        # Set default button
        set_default_btn = QPushButton("Set as default")
        set_default_btn.clicked.connect(self.set_default_style)
        config_layout.addWidget(set_default_btn)

        layout.addWidget(config_group_box)

        # Right side - List and buttons
        right_layout = QVBoxLayout()

        # List widget
        self.list_widget = QListWidget()
        self.list_widget.currentItemChanged.connect(self.populate_fields)
        self.list_widget.itemSelectionChanged.connect(self.update_button_state)
        right_layout.addWidget(self.list_widget)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        remove_btn = QPushButton("Delete")
        remove_btn.clicked.connect(lambda: self.delete_selected_item(self.list_widget.currentRow()))
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(exit_btn)
        right_layout.addLayout(btn_layout)

        layout.addLayout(right_layout)

    def update_button_state(self):
        self.update_btn.setEnabled(len(self.list_widget.selectedItems()) > 0)

    def populate_fields(self, current):
        if current:
            item_data = current.data(Qt.ItemDataRole.UserRole)
            self.font_size_spinbox.setValue(item_data.get('font_size', 12))
            self.line_text.setText(item_data.get('text', ''))
            self.set_color_button_style(self.font_color_button, item_data.get('font_color', '#000000'))
            self.set_color_button_style(self.line_color_button, item_data.get('line_color', '#000000'))
            self.line_width_spinbox.setValue(item_data.get('linewidth', 1))
            style_value = item_data.get('linestyle', '-')
            style_key = next(key for key, value in self.line_style_map.items() if value == style_value)
            self.line_style_combobox.setCurrentIndex(self.line_style_combobox.findText(style_key))

    def populate_fields_with_defaults(self):
        self.font_size_spinbox.setValue(self.default_item['font_size'])
        self.line_text.setText(self.default_item['text'])
        self.set_color_button_style(self.font_color_button, self.default_item['font_color'])
        self.set_color_button_style(self.line_color_button, self.default_item['line_color'])
        self.line_width_spinbox.setValue(self.default_item['linewidth'])
        style_value = self.default_item['linestyle']
        style_key = next(key for key, value in self.line_style_map.items() if value == style_value)
        self.line_style_combobox.setCurrentIndex(self.line_style_combobox.findText(style_key))

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

        user_col = self.event_bus.emit('get_current_trend_column')
        col_instance = self.data_manager.plot_columns[user_col]
        trend_set = col_instance.get_trend_set()
        if trend_set:
            trend_elements, trend_data = trend_set[selected_item]

            # Update trend elements styling
            trend_elements['trend_line'].set_color(new_trend['line_color'])
            trend_elements['trend_line'].set_linewidth(new_trend['linewidth'])
            trend_elements['trend_line'].set_linestyle(new_trend['linestyle'])
            if trend_elements['upper_line']:
                trend_elements['upper_line'].set_linestyle(new_trend['linestyle'])
            if trend_elements['lower_line']:
                trend_elements['lower_line'].set_linestyle(new_trend['linestyle'])
            trend_elements['cel_label'].set_color(new_trend['font_color'])
            trend_elements['cel_label'].set_size(new_trend['font_size'])
            trend_elements['cel_label'].set_text(new_trend['text'])

            # Update trend data dictionary
            trend_data.update(new_trend)

            self.figure_manager.refresh()
            self.refresh_list_box()

    def refresh_list_box(self):
        self.list_widget.clear()
        for item in self.items:
            to_display = f"{item['text']}\n{item['date1']} --> {item['date2']}"
            list_item = QListWidgetItem(to_display)
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.list_widget.addItem(list_item)

    def set_default_style(self):
        self.default_item.update({
            'font_size': self.font_size_spinbox.value(),
            'font_color': self.font_color_button.text(),
            'line_color': self.line_color_button.text(),
            'linewidth': self.line_width_spinbox.value(),
            'linestyle': self.line_style_map[self.line_style_combobox.currentText()]
        })
        self.accept()

    def choose_font_color(self):
        self.select_color(self.font_color_button)

    def choose_line_color(self):
        self.select_color(self.line_color_button)

    def select_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_color_button_style(button, color.name())

    def set_color_button_style(self, button, color):
        button.setStyleSheet(f'border: 3px solid {color};')
        button.setText(color)

    def delete_selected_item(self, selected_item):
        if selected_item != -1:
            col_instance = self.data_manager.plot_columns[self.user_col]
            col_instance.remove_trend(selected_item)
            self.list_widget.takeItem(selected_item)
            self.setGeometry(300, 300, 400, 300)
            self.figure_manager.refresh()


class SupportDevDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.resize(600, 450)  # Resize the dialog to be larger
        layout = QVBoxLayout()

        # Scroll area to handle longer text inside a QLabel
        scrollArea = QScrollArea()
        scrollArea.setWidgetResizable(True)
        contentWidget = QLabel()
        contentWidget.setWordWrap(True)
        contentWidget.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        contentWidget.setTextFormat(Qt.TextFormat.RichText)
        # Adding margins around the text
        contentWidget.setStyleSheet("padding: 20px;")
        contentWidget.setText(
            "<style>"
            "p, li { font-size: 14px; font-style: normal; }"
            "li { margin-bottom: 10px; }"
            "p.center { text-align: center; }"
            "</style>"
            "<p class='center'><b>OpenCelerator will forever remain free and open-source </b></p>"
            "<p> An incredible amount of work has gone into this project. If you find the app useful and would like to see its development continue, please consider donating. The project is only kept alive thanks to your support.</p>"
            "<p>Other ways to contribute:</p>"
            "<ul>"
            "<li>Provide feedback. Let me know what you like, what can be improved, report bugs, do testing, and so on. The software is still in alpha. </li>"
            "<li>Share this tool with others who might find it useful.</li>"
            "<li>If you use this in an official capacity, please acknowledge by linking to my GitHub: "
            "<a href='https://github.com/SJV-S/OpenCelerator'>https://github.com/SJV-S/OpenCelerator</a></li>"
            "</ul>"
            "<p>The email below can also be used to contact me about job opportunities.</p>"
            "<p>Contact: <a href='mailto:opencelerator.9qpel@simplelogin.com'>opencelerator.9qpel@simplelogin.com</a></p>"
        )

        scrollArea.setWidget(contentWidget)
        layout.addWidget(scrollArea)

        # Button to perform an action, e.g., open a link or close the dialog
        btn_layout = QHBoxLayout()

        # Add the PayPal button
        paypal_btn = QPushButton('PayPal')
        paypal_icon = QIcon(':/images/PayPal_icon.png')
        paypal_btn.setIcon(paypal_icon)
        paypal_btn.clicked.connect(self.paypal_btn_clicked)

        patreon_btn = QPushButton('Patreon')
        patreon_icon = QIcon(':/images/patreon_logo.png')
        patreon_btn.setIcon(patreon_icon)
        patreon_btn.clicked.connect(self.patreon_btn_clicked)

        bitcoin_btn = QPushButton('Bitcoin')
        bitcoin_icon = QIcon(':/images/bitcoin_logo.png')
        bitcoin_btn.setIcon(bitcoin_icon)
        bitcoin_btn.clicked.connect(self.bitcoin_btn_clicked)

        # exit_btn = QPushButton('Exit')
        # exit_btn.clicked.connect(self.exit_btn_clicked)

        btn_layout.addWidget(paypal_btn)
        btn_layout.addWidget(patreon_btn)
        btn_layout.addWidget(bitcoin_btn)
        # btn_layout.addWidget(exit_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)
        self.setWindowTitle('Support OpenCelerator')

    def patreon_btn_clicked(self):
        url = QUrl('https://www.patreon.com/johanpigeon/membership')
        if not QDesktopServices.openUrl(url):
            print("Failed to open URL")

    def paypal_btn_clicked(self):
        url = QUrl('https://paypal.me/devpigeon')
        if not QDesktopServices.openUrl(url):
            print("Failed to open URL")

    def bitcoin_btn_clicked(self):
        self.close()
        popup = BitcoinDonationPopup(self)
        popup.exec()  # Use exec_() to show the dialog modally

    def exit_btn_clicked(self):
        self.accept()  # Closes the dialog


class BitcoinDonationPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bitcoin")
        self.initUI()
        self.timer = None  # Initialize the timer as None

    def initUI(self):
        self.layout = QVBoxLayout(self)

        self.toggleButton = QPushButton("Lightning", self)
        self.toggleButton.clicked.connect(self.toggleView)
        self.layout.addWidget(self.toggleButton)

        self.stackedLayout = QStackedLayout()

        self.first_frame = QFrame(self)
        self.first_layout = QVBoxLayout(self.first_frame)

        first_label = QLabel("Bitcoin (Base chain)", self)
        first_label.setStyleSheet('font-size: 16px; font-style: normal')
        first_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.first_layout.addWidget(first_label)

        self.imageLabel1 = QLabel(self)
        pixmap1 = QPixmap(':/images/base_chain_qr.png')
        self.imageLabel1.setPixmap(pixmap1)
        self.first_layout.addWidget(self.imageLabel1)

        self.copyButton1 = QPushButton("Copy Address", self)
        self.copyButton1.clicked.connect(lambda: self.copyAddress("bc1qg8y5pxv5g86mhj59xdk89r6tr70zdw6rh6rwh4", self.copyButton1))
        self.first_layout.addWidget(self.copyButton1)

        self.stackedLayout.addWidget(self.first_frame)

        self.second_frame = QFrame(self)
        self.second_layout = QVBoxLayout(self.second_frame)

        second_label = QLabel("Lightning (LNURL)", self)
        second_label.setStyleSheet('font-size: 16px; font-style: normal')
        second_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.second_layout.addWidget(second_label)

        self.imageLabel2 = QLabel(self)
        pixmap2 = QPixmap(':/images/lightning_qr.png')
        self.imageLabel2.setPixmap(pixmap2)
        self.second_layout.addWidget(self.imageLabel2)

        self.copyButton2 = QPushButton("Copy Address", self)
        self.copyButton2.clicked.connect(lambda: self.copyAddress("pigeon@getalby.com", self.copyButton2))
        self.second_layout.addWidget(self.copyButton2)

        self.stackedLayout.addWidget(self.second_frame)

        self.layout.addLayout(self.stackedLayout)

        # Set the geometry of the window
        total_width = max(pixmap1.width(), pixmap2.width()) + 40  # Add some padding
        max_height = max(pixmap1.height(), pixmap2.height()) + 100  # Add space for labels and buttons
        self.setGeometry(300, 300, total_width, max_height)

        # Show the base chain QR code by default
        self.stackedLayout.setCurrentIndex(0)

    def toggleView(self):
        current_index = self.stackedLayout.currentIndex()
        new_index = 1 - current_index
        self.stackedLayout.setCurrentIndex(new_index)
        self.toggleButton.setText("Lightning" if new_index == 0 else "Base chain")

    def copyAddress(self, address, button):
        clipboard = QApplication.clipboard()
        clipboard.setText(address)
        button.setText("Copied!")

        # Cancel any existing timer
        if self.timer:
            self.timer.stop()

        # Create and start a new timer
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self.resetButtonText(button))
        self.timer.start(3000)

    def resetButtonText(self, button):
        if self.isVisible():  # Check if the dialog is still visible
            button.setText("Copy Address")

    def closeEvent(self, event):
        # Stop the timer when the dialog is closing
        if self.timer:
            self.timer.stop()
        super().closeEvent(event)


class NoteDialog(QDialog):
    def __init__(self, x_date, y, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Note")
        self.setGeometry(500, 500, 300, 200)  # Set the dialog dimensions
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.x_date = x_date
        self.y = y

        self.setStyleSheet("""
            QDialog {
                background-color: #fff8b8;
                border: 3px solid #e6d180;
                border-radius: 5px;
            }
            QTextEdit {
                background-color: transparent;
                border: none;
                font-size: 12pt;
                padding: 10px;
            }
            QPushButton {
                background-color: transparent;
                border: 2px solid #e6d180;
                border-radius: 15px;
                padding: 5px 15px;
                color: #756319;
                min-width: 80px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #fff4a1;
            }
            QPushButton:pressed {
                background-color: #e6d180;
            }
        """)

        # Create data manager instance
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Layout
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        # Text Box
        self.text_edit = QTextEdit(self)
        main_layout.addWidget(self.text_edit)

        # Buttons
        save_button = QPushButton("Save", self)
        cancel_button = QPushButton('Cancel', self)
        save_button.clicked.connect(self.save_note)
        cancel_button.clicked.connect(self.cancel_note)

        # Add buttons to layout
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        # Nested layouts
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def save_note(self):
        note_content = self.text_edit.toPlainText()
        note_content = note_content.replace('|', '')  # If the user used pipe character
        note_data = f"{note_content}|{self.x_date}|{self.y}"  # Pipe as separator
        self.data_manager.chart_data['notes'].append(note_data)
        self.event_bus.emit('refresh_note_listbox')
        self.event_bus.emit('refresh_note_locations')
        self.accept()

    def cancel_note(self):
        self.accept()


class DataColumnMappingDialog(QDialog):
    column_placeholder = "-- Select Column --"
    date_pattern = r'^(?=.*\d{2})(?:[^-/.\n]*[-/.]){2}[^-/.\n]*$'
    numeric_pattern = r'^\s*-?\d+(\.\d+)?\s*$'

    date_format_map = {
        'YYYY-MM-DD': '%Y-%m-%d',
        'YY-MM-DD': '%y-%m-%d',
        'MM-DD-YYYY': '%m-%d-%Y',
        'MM-DD-YY': '%m-%d-%y',
        'DD-MM-YYYY': '%d-%m-%Y',
        'DD-MM-YY': '%d-%m-%y'
    }

    def __init__(self, parent, file_path):
        super().__init__(parent)
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.file_path = file_path
        self.dropdowns_dict = {}
        self.misc_dropdowns = []

        # Control variables
        self.is_minute_chart = 'Minute' in self.data_manager.chart_data['type']
        minute_chart_msg = 'Expected to be raw counts. Will be divided by the timing floor automatically.'

        self.field_explanations = {
            'Date': 'Must contain complete dates – day, month, and year. The exact date format should be handled automatically in most cases.',
            'Dot': f'Something to increase. {minute_chart_msg if self.is_minute_chart else ""}',
            'X': f'Something to decrease. {minute_chart_msg if self.is_minute_chart else ""}',
            'Floor': 'Expected to be minutes. Decimal values work fine. The inverse is charted automatically.',
            'date_format': "The date format could not be inferred. A qualified guess has been made.",
        }

        self._setup_ui()
        self._load_data()
        self._setup_column_filters()
        self._create_date_controls()
        self._create_field_dropdowns()

    def _setup_ui(self):
        self.setStyleSheet("""QWidget {font-size: 12pt; font-style: normal;}""")
        self.setWindowTitle("Column Mapping")
        self.setMinimumSize(350, 450)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("What data columns will you be using?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        scroll_layout = QVBoxLayout(container)

        self.form_layout = QFormLayout()
        self.form_layout.setSpacing(10)
        self.form_layout.setContentsMargins(0, 10, 0, 10)
        scroll_layout.addLayout(self.form_layout)

        self.misc_layout = QVBoxLayout()
        scroll_layout.addLayout(self.misc_layout)

        # Plus button inside scroll area
        self.add_misc_button = QPushButton()
        self.add_misc_button.setToolTip('Add column')
        self.add_misc_button.setIcon(QIcon(':/images/plus-solid.svg'))
        self.add_misc_button.setStyleSheet("""
           QPushButton {
               border: 1px solid #ccc !important;
               border-radius: 16px !important;
               margin: 0px !important;
               padding: 0px !important;
               min-width: 32px !important;
               min-height: 32px !important;
               max-width: 32px !important; 
               max-height: 32px !important;
           }
           QPushButton:hover {
               background-color: #f0f0f0;
           }
        """)
        self.add_misc_button.clicked.connect(self.add_misc_dropdown)
        scroll_layout.addWidget(self.add_misc_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        self._add_button_row(main_layout)
        self.setLayout(main_layout)

    def _load_data(self):
        try:
            if self.file_path.endswith('.csv'):
                self.df = pd.read_csv(self.file_path)
            elif self.file_path.endswith(('.xls', '.xlsx', '.ods')):
                self.df = pd.read_excel(self.file_path)
            else:
                raise ValueError("Unsupported file format")

            self.df = self.df.loc[:, ~self.df.columns.str.contains('^Unnamed')]
            self.df = self.df[self.df.columns[:20]]
            self.df = self.df.fillna(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import data file: {str(e)}")
            self.reject()

    def _setup_column_filters(self):
        self.date_columns = self._lazy_check(self.df, pattern=self.date_pattern, date_check=True)
        self.numeric_columns = self._lazy_check(self.df, pattern=self.numeric_pattern)

    def _create_info_label(self, tooltip_text):
        info_label = QLabel()
        info_label.setPixmap(
            QPixmap(":/images/circle-question-regular.svg").scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio,
                                                                   Qt.TransformationMode.SmoothTransformation))
        info_label.setToolTip(f"<p style='white-space: normal; width: 300px;'>{tooltip_text}</p>")
        return info_label

    def _create_dropdown_row(self, field_name, items, on_change=None):
        dropdown = QComboBox()
        dropdown.setStyleSheet("QComboBox { background-color: white;}")
        dropdown.addItem(self.column_placeholder)
        dropdown.addItems(items)
        if on_change:
            dropdown.currentTextChanged.connect(on_change)

        tooltip_text = self.field_explanations.get(field_name.split()[0], "Additional data column")
        info_label = self._create_info_label(tooltip_text)

        row_layout = QHBoxLayout()
        row_layout.addWidget(dropdown)
        row_layout.addWidget(info_label)

        self.form_layout.addRow(QLabel(f"{field_name}: "), row_layout)
        return dropdown

    def _create_date_controls(self):
        self.date_dropdown = self._create_dropdown_row('Date', self.date_columns, self.check_date_format_warning)

        self.date_format_row = QWidget()
        date_format_layout = QHBoxLayout(self.date_format_row)
        date_format_layout.setContentsMargins(0, 0, 0, 0)

        self.date_format_dropdown = QComboBox()
        self.date_format_dropdown.setStyleSheet("QComboBox { background-color: white;}")
        self.date_format_dropdown.addItem("Automatic")
        self.date_format_dropdown.addItems(list(self.date_format_map.keys()))

        date_format_info = self._create_info_label(self.field_explanations['date_format'])

        date_format_layout.addWidget(self.date_format_dropdown)
        date_format_layout.addWidget(date_format_info)

        self.format_label = QLabel("Format:")
        self.form_layout.addRow(self.format_label, self.date_format_row)

        self.format_label.hide()
        self.date_format_row.hide()

        # Auto-select first date column if any exist
        if self.date_columns:
            self.date_dropdown.setCurrentText(self.date_columns[0])

    def _create_field_dropdowns(self):
        if self.is_minute_chart:
            dropdown = self._create_dropdown_row('Floor', self.numeric_columns, lambda *args: self.on_dropdown_changed('Floor'))
            self.dropdowns_dict['Floor'] = dropdown

        for field in ['Dot', 'X']:
            dropdown = self._create_dropdown_row(field, self.numeric_columns,
                                                 lambda *args, f=field: self.on_dropdown_changed(f))
            self.dropdowns_dict[field] = dropdown

    def add_misc_dropdown(self):
        misc_idx = len(self.misc_dropdowns)
        dropdown = self._create_dropdown_row(f'M{misc_idx + 1}', self.numeric_columns,
                                             lambda *args: self.on_dropdown_changed(f'M{misc_idx + 1}'))
        self.misc_dropdowns.append(dropdown)
        self.dropdowns_dict[f'Misc {misc_idx + 1}'] = dropdown

    def _add_button_row(self, layout):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_mapping)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def _lazy_check(self, df, pattern, threshold=0.8, check_limit=20, date_check=False):
        matching_columns = []
        cols_to_check = df.columns if date_check else [col for col in df.columns if col not in self.date_columns]
        for col in cols_to_check:
            matches = 0
            to_check = df[col].dropna()[:check_limit]
            total = len(to_check)

            for cell in to_check.astype(str):
                if re.search(pattern, cell):
                    matches += 1

            if matches / total > threshold:
                matching_columns.append(col)

        # If no matches found, try partial date detection
        if not matching_columns and date_check:
            min_valid_year = pd.Timestamp.min.year
            max_valid_year = pd.Timestamp.max.year

            for col in df.columns:
                matches = 0
                to_check = df[col].dropna()[:check_limit]
                total = len(to_check)

                for cell in to_check.astype(str):
                    value_str = str(cell).strip()

                    # Try year-only format
                    if value_str.isdigit() and len(value_str) == 4:
                        year = int(value_str)
                        if min_valid_year <= year <= max_valid_year:
                            matches += 1
                            continue

                    # Try year/month or month/year format
                    parts = value_str.replace('/', '-').replace('.', '-').split('-')
                    if len(parts) == 2:
                        try:
                            if len(parts[0]) == 4:  # YYYY/MM
                                year, month = int(parts[0]), int(parts[1])
                                if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                                    matches += 1
                            elif len(parts[1]) == 4:  # MM/YYYY
                                month, year = int(parts[0]), int(parts[1])
                                if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                                    matches += 1
                        except ValueError:
                            continue

                if matches / total > threshold:
                    matching_columns.append(col)

        return matching_columns

    def on_dropdown_changed(self, field_changed):
        for dropdown in self.dropdowns_dict.values():
            dropdown.blockSignals(True)

        all_selected_columns = []
        for field in self.dropdowns_dict.keys():
            selected_column = self.dropdowns_dict[field].currentText()
            if selected_column != self.column_placeholder:
                all_selected_columns.append(selected_column)

        for field in self.dropdowns_dict.keys():
            if field != field_changed:
                dropdown = self.dropdowns_dict[field]
                selected = dropdown.currentText()
                if selected == self.column_placeholder:
                    dropdown.clear()

                    col_options = [col for col in self.numeric_columns if col not in all_selected_columns]
                    new_items = [self.column_placeholder] + col_options
                    dropdown.addItems(new_items)

                    if len(col_options) == 0:
                        dropdown.setEnabled(False)
                        dropdown.setStyleSheet("QComboBox { background-color: #f0f0f0; color: #808080; }")
                    else:
                        dropdown.setEnabled(True)
                        dropdown.setStyleSheet("QComboBox { background-color: white; }")

        for dropdown in self.dropdowns_dict.values():
            dropdown.blockSignals(False)

    def check_date_format_warning(self):
        date_col = self.date_dropdown.currentText()

        if date_col == self.column_placeholder:
            self.format_label.hide()
            self.date_format_row.hide()
            self.date_format_dropdown.setCurrentText('Automatic')
            return False

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            try:
                pd.to_datetime(self.df[date_col])
                falls_back_to_dateutil = any("Could not infer format" in str(warning.message) for warning in w)
            except Exception:
                falls_back_to_dateutil = True

        if falls_back_to_dateutil:
            self.format_label.show()
            self.date_format_row.show()

            for label, format_string in self.date_format_map.items():
                sample_date = self.df[date_col].dropna().iloc[0]
                try:
                    separator = next(char for char in sample_date if char in '/-.')
                    adjusted_format = format_string.replace('-', separator)
                    pd.to_datetime(self.df[date_col], format=adjusted_format, errors='raise')
                    self.date_format_dropdown.setCurrentText(label)
                    break
                except Exception:
                    continue
        else:
            self.format_label.hide()
            self.date_format_row.hide()
            self.date_format_dropdown.setCurrentText('Automatic')

        return falls_back_to_dateutil

    def confirm_mapping(self):
        column_map = {'d': self.date_dropdown.currentText()}

        field_key_map = {'Dot': 'c', 'X': 'i', 'Floor': 'm'}
        for field, key in field_key_map.items():
            if field in self.dropdowns_dict and self.dropdowns_dict[field].currentText() != self.column_placeholder:
                column_map[key] = self.dropdowns_dict[field].currentText()

        misc_fields = [d for d in self.dropdowns_dict if d.startswith('Misc')]
        for idx, field in enumerate(misc_fields):
            if self.dropdowns_dict[field].currentText() != self.column_placeholder:
                column_map[f'o{idx}'] = self.dropdowns_dict[field].currentText()

        if self.date_format_dropdown.currentText() == 'Automatic':
            date_format = None
        else:
            date_format = self.date_format_map[self.date_format_dropdown.currentText()]
            date_col = column_map['d']
            sample_date = self.df[date_col].dropna().iloc[0]
            separator = next(char for char in sample_date if char in '/-.')
            date_format = date_format.replace('-', separator)

        self.data_manager.chart_data['column_map'] = column_map
        self.data_manager.chart_data['date_format'] = date_format

        self.accept()


class UserPrompt(QDialog):
    def __init__(self, title="Message", message="", choice=False, parent=None):
        super().__init__(parent)
        self._setup_window(title)
        self._create_layout()
        self._add_message_label(message)
        self._add_button_box(choice)
        self._apply_styles()

    def _setup_window(self, title):
        self.setWindowTitle(title)

    def _create_layout(self):
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)

    def _add_message_label(self, message):
        self.message_label = QLabel(message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.layout.addWidget(self.message_label)

    def _add_button_box(self, choice):
        buttons = (QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel if choice else QDialogButtonBox.StandardButton.Ok)
        self.button_box = QDialogButtonBox(buttons, self)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def _apply_styles(self):
        self.message_label.setStyleSheet("font-size: 16px; padding: 10px; font-style: normal;")
        self.button_box.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 8px 16px;
            }
        """)
        self.setStyleSheet("QDialog { padding: 20px; }")

    def display(self):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        return self.exec() == QDialog.DialogCode.Accepted


