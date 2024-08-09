from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QGroupBox, QRadioButton, QLineEdit, QLabel, QDateEdit, QListWidget, QFileDialog, QCheckBox,
                               QButtonGroup, QDialog, QComboBox, QMessageBox, QGridLayout, QStackedWidget, QSpinBox,
                               QSpacerItem, QSizePolicy, QDoubleSpinBox, QColorDialog)
from PySide6.QtGui import QDoubleValidator, QFont, QIcon
from PySide6.QtCore import Qt, QDate

from Popups import InputDialog, ConfigurePhaseLinesDialog, ConfigureAimLinesDialog, ConfigureTrendLinesDialog
from DataManager import DataManager


class ModeWidget(QWidget):
    def __init__(self, figure_manager):
        super().__init__()
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.init_ui()

    def init_ui(self):
        pass


class DataModeWidget(ModeWidget):
    def __init__(self, figure_manager):
        self.marker_style_map = {"Circle": "o", "Square": "s", "Triangle Up": "^", "Triangle Down": "v", "Star": "*",
                                 "Plus": "+", "X": "x", "Underscore": "_", "NoMarker": ''}
        self.line_style_map = {"Solid": "-", "Dashed": "--", "Dotted": ":", 'NoLine': ''}
        self.current_button = None
        super().__init__(figure_manager)
        self.populate_fields_with_defaults()

    def init_ui(self):
        main_layout = QVBoxLayout()

        date1 = self.figure_manager.x_to_date[0].strftime(self.data_manager.standard_date_string)
        date2 = self.figure_manager.x_to_date[max(self.figure_manager.Chart.date_to_pos.values())].strftime(
            self.data_manager.standard_date_string)

        self.date_range_label = QLabel(f'{date1} ~ {date2}')
        self.date_range_label.setStyleSheet("font-style: normal;")
        self.date_range_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        date_layout = QVBoxLayout()
        date_layout.addWidget(self.date_range_label)
        main_layout.addLayout(date_layout)

        # Add a spacer item to create a larger margin
        spacer_item = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        main_layout.addItem(spacer_item)

        # Create navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        nav_layout.setSpacing(0)  # Remove spacing

        self.dot_button = self.create_nav_button("Dot", 0)
        self.x_button = self.create_nav_button("X", 1)
        self.floor_button = self.create_nav_button("Floor", 2)
        self.misc_button = self.create_nav_button("Misc", 3)

        nav_layout.addWidget(self.dot_button)
        nav_layout.addWidget(self.x_button)
        nav_layout.addWidget(self.floor_button)
        nav_layout.addWidget(self.misc_button)
        main_layout.addLayout(nav_layout)

        # Style group
        style_layout = QVBoxLayout()

        # Stacked widget for style categories
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add style categories to stacked widget
        self.dot_category = self.add_style_category(self.stacked_widget, 'Dot', self.data_manager.user_preferences['corr_style'])
        self.x_category = self.add_style_category(self.stacked_widget, 'X', self.data_manager.user_preferences['err_style'])
        self.floor_category = self.add_style_category(self.stacked_widget, 'Floor', self.data_manager.user_preferences['floor_style'])
        self.misc_category = self.add_style_category(self.stacked_widget, 'Misc', self.data_manager.user_preferences['misc_style'])

        style_layout.addWidget(self.stacked_widget)
        main_layout.addLayout(style_layout)

        self.layout.addLayout(main_layout)  # Use existing layout

        self.switch_category(0, self.dot_button)  # Set default selected category

    def create_nav_button(self, text, index):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-top: 1px solid black;
                margin: 0;
                padding: 10px;
                background-color: #e7efff;
                border-radius: 0; /* No rounded corners */
            }}
            QPushButton:checked {{
                background-color: #6ad1e3; /* Background color when selected */
            }}
        """)
        button.setCheckable(True)
        button.clicked.connect(lambda: self.switch_category(index, button))
        return button

    def switch_category(self, index, button):
        self.stacked_widget.setCurrentIndex(index)
        if self.current_button:
            self.current_button.setChecked(False)  # Uncheck the previous button
        button.setChecked(True)  # Check the current button
        self.current_button = button

    def add_style_category(self, stacked_widget, category_name, default_values):
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)

        # Choose marker size
        marker_size_spinbox = QDoubleSpinBox()
        marker_size_spinbox.setRange(1, 100)
        marker_size_spinbox.setSingleStep(1)
        marker_size_spinbox.valueChanged.connect(
            lambda value, cat=category_name, field='markersize': self.update_data_point_styles(cat, field, value)
        )
        category_layout.addWidget(QLabel("Marker Size"))
        category_layout.addWidget(marker_size_spinbox)

        # Choose marker style
        marker_style_combobox = QComboBox()
        marker_style_combobox.addItems(self.marker_style_map.keys())
        marker_style_combobox.currentTextChanged.connect(
            lambda value, cat=category_name, field='marker': self.update_data_point_styles(cat, field,
                                                                                           self.marker_style_map[value])
        )
        category_layout.addWidget(QLabel("Marker Style"))
        category_layout.addWidget(marker_style_combobox)

        # Marker face color
        marker_face_color_button = QPushButton("Marker Face Color")
        marker_face_color_button.clicked.connect(lambda: self.choose_marker_face_color(category_name))
        category_layout.addWidget(marker_face_color_button)

        # Marker edge color
        marker_edge_color_button = QPushButton("Marker Edge Color")
        marker_edge_color_button.clicked.connect(lambda: self.choose_marker_edge_color(category_name))
        category_layout.addWidget(marker_edge_color_button)

        # Line color
        line_color_button = QPushButton("Line Color")
        line_color_button.clicked.connect(lambda: self.choose_line_color(category_name))
        category_layout.addWidget(line_color_button)

        # Line width
        line_width_spinbox = QDoubleSpinBox()
        line_width_spinbox.setRange(0.1, 10.0)
        line_width_spinbox.setSingleStep(0.1)
        line_width_spinbox.valueChanged.connect(
            lambda value, cat=category_name, field='linewidth': self.update_data_point_styles(cat, field, value)
        )
        category_layout.addWidget(QLabel("Line Width"))
        category_layout.addWidget(line_width_spinbox)

        # Line style
        line_style_combobox = QComboBox()
        line_style_combobox.addItems(self.line_style_map.keys())
        line_style_combobox.currentTextChanged.connect(
            lambda value, cat=category_name, field='linestyle': self.update_data_point_styles(cat, field, self.line_style_map[value]))
        category_layout.addWidget(QLabel("Line Style"))
        category_layout.addWidget(line_style_combobox)

        # Add "Set as default" button
        set_default_button = QPushButton("Set as default")
        set_default_button.clicked.connect(lambda: self.change_default(category_name))

        # Add vertical spacing before set-as-default button
        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        category_layout.addItem(spacer)

        category_layout.addWidget(set_default_button)

        category_layout.addStretch()
        stacked_widget.addWidget(category_widget)

        return {
            'marker_size_spinbox': marker_size_spinbox,
            'marker_style_combobox': marker_style_combobox,
            'marker_face_color_button': marker_face_color_button,
            'marker_edge_color_button': marker_edge_color_button,
            'line_color_button': line_color_button,
            'line_width_spinbox': line_width_spinbox,
            'line_style_combobox': line_style_combobox,
            'set_default_button': set_default_button
        }

    def populate_fields_with_defaults(self):
        self.populate_fields_for_category(self.dot_category, self.data_manager.user_preferences['corr_style'],
                                          self.marker_style_map, self.line_style_map)
        self.populate_fields_for_category(self.x_category, self.data_manager.user_preferences['err_style'],
                                          self.marker_style_map, self.line_style_map)
        self.populate_fields_for_category(self.floor_category, self.data_manager.user_preferences['floor_style'],
                                          self.marker_style_map, self.line_style_map)
        self.populate_fields_for_category(self.misc_category, self.data_manager.user_preferences['misc_style'],
                                          self.marker_style_map, self.line_style_map)

    def populate_fields_for_category(self, category, default_values, marker_style_map, line_style_map):
        self.block_signals(category, True)
        category['marker_size_spinbox'].setValue(default_values['markersize'])

        marker_style_key = next((key for key, value in marker_style_map.items() if value == default_values['marker']),
                                None)
        if marker_style_key is not None:
            index = category['marker_style_combobox'].findText(marker_style_key)
            category['marker_style_combobox'].setCurrentIndex(index)

        self.set_button_border_style(category['marker_face_color_button'], default_values['marker_face_color'])
        self.set_button_border_style(category['marker_edge_color_button'], default_values['marker_edge_color'])
        self.set_button_border_style(category['line_color_button'], default_values['line_color'])
        category['line_width_spinbox'].setValue(default_values['linewidth'])

        style_key = next((key for key, value in line_style_map.items() if value == default_values['linestyle']), None)
        if style_key is not None:
            index = category['line_style_combobox'].findText(style_key)
            category['line_style_combobox'].setCurrentIndex(index)
        self.block_signals(category, False)

    def block_signals(self, category, block):
        category['marker_size_spinbox'].blockSignals(block)
        category['marker_style_combobox'].blockSignals(block)
        category['marker_face_color_button'].blockSignals(block)
        category['marker_edge_color_button'].blockSignals(block)
        category['line_color_button'].blockSignals(block)
        category['line_width_spinbox'].blockSignals(block)
        category['line_style_combobox'].blockSignals(block)

    def choose_marker_face_color(self, category_name):
        button = self.get_category(category_name)['marker_face_color_button']
        self.select_color(button)
        color = self.get_color(button)
        self.update_data_point_styles(category_name, 'marker_face_color', color)

    def choose_marker_edge_color(self, category_name):
        button = self.get_category(category_name)['marker_edge_color_button']
        self.select_color(button)
        color = self.get_color(button)
        self.update_data_point_styles(category_name, 'marker_edge_color', color)

    def choose_line_color(self, category_name):
        button = self.get_category(category_name)['line_color_button']
        self.select_color(button)
        color = self.get_color(button)
        self.update_data_point_styles(category_name, 'line_color', color)

    def select_color(self, button):
        color = QColorDialog.getColor()
        if color.isValid():
            button.setStyleSheet(f"border: 3px solid {color.name()};")

    def set_button_border_style(self, button, color):
        button.setStyleSheet(f"border: 3px solid {color};")

    def get_color(self, button):
        style_sheet = button.styleSheet()
        if (color := style_sheet.split(' ')[-1].strip(';')):
            return color
        return '#000000'  # Default to black if no color is set

    def get_category(self, category_name):
        if category_name == 'Dot':
            return self.dot_category
        elif category_name == 'X':
            return self.x_category
        elif category_name == 'Floor':
            return self.floor_category
        elif category_name == 'Misc':
            return self.misc_category
        return None

    def update_data_point_styles(self, point_category, input_field, value):
        self.figure_manager.update_point_styles(point_category, input_field, value)

    def change_default(self, category_name):
        category = self.get_category(category_name)

        default_values = {
            'markersize': category['marker_size_spinbox'].value(),
            'marker': self.marker_style_map[category['marker_style_combobox'].currentText()],
            'marker_face_color': self.get_color(category['marker_face_color_button']),
            'marker_edge_color': self.get_color(category['marker_edge_color_button']),
            'line_color': self.get_color(category['line_color_button']),
            'linewidth': category['line_width_spinbox'].value(),
            'linestyle': self.line_style_map[category['line_style_combobox'].currentText()]
        }

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setWindowTitle("Set Default")
        msg_box.setText(f"Make current {category_name} settings default for all charts?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        result = msg_box.exec()

        if result == QMessageBox.StandardButton.Yes:
            if category_name == 'Dot':
                self.data_manager.user_preferences['corr_style'] = default_values
            elif category_name == 'X':
                self.data_manager.user_preferences['err_style'] = default_values
            elif category_name == 'Floor':
                self.data_manager.user_preferences['floor_style'] = default_values
            elif category_name == 'Misc':
                self.data_manager.user_preferences['misc_style'] = default_values


class ViewModeWidget(ModeWidget):
    def init_ui(self):
        self.dialog = InputDialog()

        # Creating grid layout to organize the checkboxes
        view_grid = QGridLayout()

        # Headings for Dot and X settings
        font = QFont()
        dot_heading = QLabel("Dot")
        dot_heading.setFont(font)
        dot_heading.setAlignment(Qt.AlignmentFlag.AlignBottom)  # Align label to the bottom of its grid cell
        x_heading = QLabel("X")
        x_heading.setFont(font)
        x_heading.setAlignment(Qt.AlignmentFlag.AlignBottom)
        grid_heading = QLabel("\nGrid")
        grid_heading.setFont(font)
        other_heading = QLabel("\nOther")
        other_heading.setFont(font)

        # Placing the headings
        view_grid.addWidget(dot_heading, 0, 0)
        view_grid.addWidget(x_heading, 0, 1)
        view_grid.addWidget(grid_heading, 6, 0)
        view_grid.addWidget(other_heading, 6, 1)

        # Checkboxes for various view options
        self.dots_check = QCheckBox('Data')
        self.xs_check = QCheckBox('Data')
        self.dot_trends_check = QCheckBox('Trend')
        self.x_trends_check = QCheckBox('Trend')
        self.dot_bounce_check = QCheckBox('Bounce')
        self.x_bounce_check = QCheckBox('Bounce')
        self.dot_est_check = QCheckBox('CelTxt')
        self.x_est_check = QCheckBox('CelTxt')
        self.minor_grid_check = QCheckBox('Minor')
        self.major_grid_check = QCheckBox('Major')
        self.timing_floor_check = QCheckBox('Floor')
        self.timing_grid_check = QCheckBox('Time')
        self.phase_lines_check = QCheckBox('Phase')
        self.aims_check = QCheckBox('Aim')
        self.fan_check = QCheckBox('CelFan')
        self.credit_check = QCheckBox('Credit')
        self.misc_point_check = QCheckBox('MiscD')

        # Adding checkboxes to the grid
        view_grid.addWidget(self.dots_check, 1, 0)
        view_grid.addWidget(self.dot_trends_check, 3, 0)
        view_grid.addWidget(self.dot_bounce_check, 4, 0)
        view_grid.addWidget(self.dot_est_check, 5, 0)  # Add new checkbox for Dot Est
        view_grid.addWidget(self.xs_check, 1, 1)
        view_grid.addWidget(self.x_trends_check, 3, 1)
        view_grid.addWidget(self.x_bounce_check, 4, 1)
        view_grid.addWidget(self.x_est_check, 5, 1)  # Add new checkbox for X Est
        view_grid.addWidget(self.minor_grid_check, 8, 0)
        view_grid.addWidget(self.major_grid_check, 7, 0)
        view_grid.addWidget(self.timing_grid_check, 9, 0)
        view_grid.addWidget(self.aims_check, 7, 1)
        view_grid.addWidget(self.timing_floor_check, 9, 1)
        view_grid.addWidget(self.phase_lines_check, 8, 1)
        view_grid.addWidget(self.fan_check, 10, 1)
        view_grid.addWidget(self.credit_check, 11, 1)
        view_grid.addWidget(self.misc_point_check, 12, 1)

        # Set spacing between rows
        view_grid.setSpacing(10)

        # Setting initial states of checkboxes
        for checkbox in [self.minor_grid_check, self.major_grid_check, self.dots_check, self.xs_check,
                         self.dot_trends_check, self.x_trends_check, self.phase_lines_check,
                         self.aims_check, self.timing_floor_check, self.dot_bounce_check, self.x_bounce_check,
                         self.dot_est_check, self.x_est_check, self.fan_check, self.credit_check, self.misc_point_check]:
            checkbox.setChecked(True)

        for checkbox in [self.timing_grid_check]:
            checkbox.setChecked(False)

        # Connect checkboxes to figure manager methods for handling changes
        self.dots_check.stateChanged.connect(self.figure_manager.view_dots)
        self.xs_check.stateChanged.connect(self.figure_manager.view_xs)
        self.minor_grid_check.stateChanged.connect(self.figure_manager.view_minor_gridlines)
        self.major_grid_check.stateChanged.connect(self.figure_manager.view_major_gridlines)
        self.timing_floor_check.stateChanged.connect(self.figure_manager.view_floor)
        self.phase_lines_check.stateChanged.connect(self.figure_manager.view_phase_lines)
        self.timing_grid_check.stateChanged.connect(self.figure_manager.view_floor_grid)
        self.aims_check.stateChanged.connect(self.figure_manager.view_aims)
        self.dot_trends_check.stateChanged.connect(self.figure_manager.view_dot_trend)
        self.x_trends_check.stateChanged.connect(self.figure_manager.view_x_trend)
        self.dot_bounce_check.stateChanged.connect(self.figure_manager.view_dot_bounce)
        self.x_bounce_check.stateChanged.connect(self.figure_manager.view_x_bounce)
        self.dot_est_check.stateChanged.connect(self.figure_manager.view_dot_est)
        self.x_est_check.stateChanged.connect(self.figure_manager.view_x_est)
        self.fan_check.stateChanged.connect(self.figure_manager.view_update_celeration_fan)
        self.credit_check.stateChanged.connect(self.toggle_credit_lines)
        self.misc_point_check.stateChanged.connect(self.figure_manager.view_misc_points)

        # Credit lines button
        credit_lines_btn = QPushButton("Credit lines")
        credit_lines_btn.clicked.connect(self.credit_lines_popup)
        self.layout.addLayout(view_grid)
        self.layout.addWidget(credit_lines_btn)

        # Call the method to check the condition and update checkbox states
        self.update_timing_checkboxes()

    def credit_lines_popup(self):
        if self.dialog.exec() == QDialog.DialogCode.Accepted:  # Check if the dialog was accepted
            r1, r2, r3 = self.dialog.get_inputs()  # Retrieve the inputs
            self.dialog.credit_row1 = r1
            self.dialog.credit_row2 = r2
            self.dialog.credit_row3 = r3
            self.figure_manager.view_update_credit_lines(r1, r2, r3)

    def update_timing_checkboxes(self):
        # Replace the following condition with your actual condition
        condition = 'Minute' in self.data_manager.user_preferences['chart_type']
        self.timing_floor_check.setEnabled(condition)
        self.timing_grid_check.setEnabled(condition)

    def toggle_credit_lines(self, status):
        self.data_manager.chart_data['view_check']['credit_spacing'] = bool(status)
        self.figure_manager.update_chart()


class PhaseModeWidget(ModeWidget):
    def init_ui(self):
        # Creating label and input for phase change description
        phase_change_label = QLabel('Text')
        self.phase_change_input = QLineEdit('')
        self.layout.addWidget(phase_change_label)
        self.layout.addWidget(self.phase_change_input)

        # Connect phase_change_input to enable/disable radio buttons
        self.phase_change_input.textChanged.connect(self.toggle_radio_buttons)

        # Date input setup
        phase_label_date = QLabel('Date')
        self.phase_date_input = QDateEdit()
        self.phase_date_input.setDate(QDate.currentDate())
        self.phase_date_input.setCalendarPopup(True)
        self.phase_date_input.setDisplayFormat("dd-MM-yyyy")
        self.layout.addWidget(phase_label_date)
        self.layout.addWidget(self.phase_date_input)

        # Buttons for adding and undoing phase lines
        phase_line_button_layout = QHBoxLayout()
        add_phase_line_btn = QPushButton()
        undo_phase_line_btn = QPushButton()
        config_btn = QPushButton()

        # Add icons
        add_phase_line_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        undo_phase_line_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        config_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        phase_line_button_layout.addWidget(add_phase_line_btn)
        phase_line_button_layout.addWidget(undo_phase_line_btn)
        phase_line_button_layout.addWidget(config_btn)
        self.layout.addLayout(phase_line_button_layout)

        # Connect buttons to figure manager methods
        add_phase_line_btn.clicked.connect(lambda: self.figure_manager.phase_line_from_form(
            self.phase_change_input.text(),
            self.phase_date_input.text()
        ))
        undo_phase_line_btn.clicked.connect(self.figure_manager.phase_undo_line)
        config_btn.clicked.connect(self.configure_phase_lines)

        # Add vertical spacing before the radio buttons
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.layout.addItem(spacer)

        # Create a horizontal layout for the radio buttons
        radio_buttons_layout = QGridLayout()

        # Phase type radio buttons
        phase_type_label = QLabel('Text type')
        self.phase_type_group = QButtonGroup(self)
        self.phase_type_flag = QRadioButton('Flag')
        self.phase_type_banner = QRadioButton('Banner')

        # Set the phase type based on user preferences
        phase_text_type = self.data_manager.user_preferences.get('phase_text_type', 'Flag')
        self.phase_type_flag.setChecked(phase_text_type == 'Flag')
        self.phase_type_banner.setChecked(phase_text_type == 'Banner')

        self.phase_type_group.addButton(self.phase_type_flag)
        self.phase_type_group.addButton(self.phase_type_banner)

        # Position radio buttons
        position_label = QLabel('Text position')
        self.position_group = QButtonGroup(self)
        self.position_top = QRadioButton('Top')
        self.position_center = QRadioButton('Center')
        self.position_bottom = QRadioButton('Bottom')

        # Set the position based on user preferences
        phase_text_position = self.data_manager.user_preferences.get('phase_text_position', 'Top')
        self.position_top.setChecked(phase_text_position == 'Top')
        self.position_center.setChecked(phase_text_position == 'Center')
        self.position_bottom.setChecked(phase_text_position == 'Bottom')

        self.position_group.addButton(self.position_top)
        self.position_group.addButton(self.position_center)
        self.position_group.addButton(self.position_bottom)

        # Add labels and radio buttons to the grid layout
        radio_buttons_layout.addWidget(phase_type_label, 0, 0)
        radio_buttons_layout.addWidget(self.phase_type_flag, 1, 0)
        radio_buttons_layout.addWidget(self.phase_type_banner, 2, 0)
        radio_buttons_layout.addWidget(position_label, 0, 1)
        radio_buttons_layout.addWidget(self.position_top, 1, 1)
        radio_buttons_layout.addWidget(self.position_center, 2, 1)
        radio_buttons_layout.addWidget(self.position_bottom, 3, 1)

        # Add the grid layout with the radio buttons to the main layout
        self.layout.addLayout(radio_buttons_layout)

        # Add vertical spacing after the radio buttons
        spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        self.layout.addItem(spacer)

        # Eliminate any extra vertical stretches
        self.layout.addStretch()

        # Connect the radio buttons to the method to enable/disable based on text input
        self.phase_type_flag.toggled.connect(self.update_preferences)
        self.phase_type_banner.toggled.connect(self.update_preferences)

        # Connect text position buttons
        self.position_top.clicked.connect(lambda: self.update_position_preference('Top'))
        self.position_center.clicked.connect(lambda: self.update_position_preference('Center'))
        self.position_bottom.clicked.connect(lambda: self.update_position_preference('Bottom'))

        # Initial state of radio buttons
        self.toggle_radio_buttons()

    def configure_phase_lines(self):
        dialog = ConfigurePhaseLinesDialog(self.figure_manager, self)
        dialog.exec()

    def toggle_radio_buttons(self):
        state = bool(self.phase_change_input.text())
        for button in [self.phase_type_flag, self.phase_type_banner, self.position_top, self.position_center,
                       self.position_bottom]:
            button.setEnabled(state)

    def update_preferences(self):
        phase_text_type = 'Flag' if self.phase_type_flag.isChecked() else 'Banner'
        self.data_manager.user_preferences['phase_text_type'] = phase_text_type

    def update_position_preference(self, position):
        if getattr(self, f'position_{position.lower()}').isChecked():
            self.data_manager.user_preferences['phase_text_position'] = position


class AimModeWidget(ModeWidget):
    def init_ui(self):
        # Create a QGridLayout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(0)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # Note input for aim
        aim_target_label = QLabel('Note')
        aim_target_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_target_input = QLineEdit('')

        # Y-value input for targeting
        aim_label_y = QLabel('Target')
        aim_label_y.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_y_input = QLineEdit('')
        self.aim_y_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))

        # Start date input
        aim_label_start_date = QLabel('Start')
        aim_label_start_date.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_start_date_input = QDateEdit()
        self.aim_start_date_input.setDate(QDate.currentDate())
        self.aim_start_date_input.setCalendarPopup(True)
        self.aim_start_date_input.setDisplayFormat("dd-MM-yyyy")

        # Deadline date input
        aim_label_end_date = QLabel('Deadline')
        aim_label_end_date.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_end_date_input = QDateEdit()
        self.aim_end_date_input.setDate(QDate.currentDate())
        self.aim_end_date_input.setCalendarPopup(True)
        self.aim_end_date_input.setDisplayFormat("dd-MM-yyyy")

        # Add, Undo, and Configure buttons for setting aims
        add_aim_line_btn = QPushButton()
        add_aim_line_btn.setStyleSheet("margin-right: 5px; margin-top: 15px")
        undo_aim_line_btn = QPushButton()
        undo_aim_line_btn.setStyleSheet("margin-left: 5px; margin-top: 15px")
        configure_aim_btn = QPushButton()
        configure_aim_btn.setStyleSheet("margin-left: 5px; margin-top: 15px")

        # Add icons
        add_aim_line_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        undo_aim_line_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        configure_aim_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        # Add widgets to the grid layout
        grid_layout.addWidget(aim_target_label, 0, 0)
        grid_layout.addWidget(self.aim_target_input, 1, 0)
        grid_layout.addWidget(aim_label_y, 2, 0)
        grid_layout.addWidget(self.aim_y_input, 3, 0)
        grid_layout.addWidget(aim_label_start_date, 4, 0)
        grid_layout.addWidget(self.aim_start_date_input, 5, 0)
        grid_layout.addWidget(aim_label_end_date, 6, 0)
        grid_layout.addWidget(self.aim_end_date_input, 7, 0)

        # Add buttons to a horizontal layout
        aim_line_button_layout = QHBoxLayout()
        aim_line_button_layout.addWidget(add_aim_line_btn)
        aim_line_button_layout.addWidget(undo_aim_line_btn)
        aim_line_button_layout.addWidget(configure_aim_btn)

        # Add the button layout to the grid layout
        grid_layout.addLayout(aim_line_button_layout, 8, 0, 1, 1)

        # Create a container widget to hold the grid layout
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.addLayout(grid_layout)
        container_layout.addStretch()  # Add a stretch to push everything to the top
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Add the container widget to the existing layout
        self.layout.addWidget(container_widget)

        # Connect buttons to figure manager methods
        add_aim_line_btn.clicked.connect(lambda: self.figure_manager.aim_from_form(
            self.aim_target_input.text(),
            self.aim_y_input.text(),
            self.aim_start_date_input.text(),
            self.aim_end_date_input.text()
        ))
        undo_aim_line_btn.clicked.connect(self.figure_manager.aim_undo)
        configure_aim_btn.clicked.connect(self.configure_aim_lines)

    def configure_aim_lines(self):
        dialog = ConfigureAimLinesDialog(self.figure_manager, self)
        dialog.exec()


class TrendModeWidget(ModeWidget):
    def init_ui(self):
        # Creating a radio button group for selecting trend type
        radio_group_layout = QHBoxLayout()
        self.trend_radio_dot = QRadioButton("Dots")
        trend_radio_x = QRadioButton("Xs")
        trend_radio_group = QButtonGroup(self)
        trend_radio_group.addButton(self.trend_radio_dot)
        trend_radio_group.addButton(trend_radio_x)
        self.trend_radio_dot.setChecked(True)

        radio_group_layout.addWidget(self.trend_radio_dot)
        radio_group_layout.addWidget(trend_radio_x)
        self.layout.addLayout(radio_group_layout)

        # Date inputs for the start and end of the trend, arranged vertically
        date_input_layout = QVBoxLayout()

        date1_layout = QVBoxLayout()
        # Add vertical margin before Date 1 label
        date1_layout.addSpacing(10)
        trend_label_start_date = QLabel('Date 1')
        self.trend_start_date_input = QDateEdit()
        self.trend_start_date_input.setDate(QDate.currentDate())
        self.trend_start_date_input.setCalendarPopup(True)
        self.trend_start_date_input.setDisplayFormat("dd-MM-yyyy")
        date1_layout.addWidget(trend_label_start_date)
        date1_layout.addWidget(self.trend_start_date_input)

        date2_layout = QVBoxLayout()
        trend_label_end_date = QLabel('Date 2')
        self.trend_end_date_input = QDateEdit()
        self.trend_end_date_input.setDate(QDate.currentDate())
        self.trend_end_date_input.setCalendarPopup(True)
        self.trend_end_date_input.setDisplayFormat("dd-MM-yyyy")
        date2_layout.addWidget(trend_label_end_date)
        date2_layout.addWidget(self.trend_end_date_input)

        # Add the date layouts to the main date input layout
        date_input_layout.addLayout(date1_layout)
        date_input_layout.addLayout(date2_layout)

        self.layout.addLayout(date_input_layout)

        # Buttons for managing trends
        trend_button_layout = QHBoxLayout()
        self.trend_add_btn = QPushButton()
        self.trend_fit_btn = QPushButton('Fit')
        trend_undo_btn = QPushButton()
        trend_configure_btn = QPushButton()

        # Add icons
        self.trend_add_btn.setIcon(QIcon(':/images/plus-solid-disabled.svg'))
        self.trend_add_btn.setEnabled(False)
        trend_undo_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        trend_configure_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        trend_button_layout.addWidget(self.trend_add_btn)
        trend_button_layout.addWidget(trend_undo_btn)
        trend_button_layout.addWidget(self.trend_fit_btn)
        trend_button_layout.addWidget(trend_configure_btn)

        self.layout.addLayout(trend_button_layout)

        # Add vertical margin before Fit method label
        self.layout.addSpacing(15)

        # Combo box for selecting the trend calculation method
        trend_method_label = QLabel("Fit method")
        self.trend_method_combo = QComboBox()
        self.trend_method_combo.addItem('Least-squares')
        self.trend_method_combo.addItem('Quarter-intersect')
        self.trend_method_combo.addItem('Split-middle-line')
        self.trend_method_combo.setCurrentText(self.data_manager.user_preferences['fit_method'])
        self.trend_method_combo.currentIndexChanged.connect(lambda index: self.data_manager.user_preferences.update({'fit_method': self.trend_method_combo.currentText()}))

        # SpinBox for Forward Projection
        forward_projection_label = QLabel("Forward projection")
        self.forward_projection_spinbox = QSpinBox()
        self.forward_projection_spinbox.setRange(0, 100)  # Set the range as required
        self.forward_projection_spinbox.setValue(self.data_manager.user_preferences.get('forward_projection', 0))
        self.forward_projection_spinbox.valueChanged.connect(lambda value: self.data_manager.user_preferences.update({'forward_projection': value}))

        # Combo box for envelope method
        envelope_method_label = QLabel("Bounce envelope")
        self.envelope_method_combo = QComboBox()
        self.envelope_method_combo.addItem('None')
        self.envelope_method_combo.addItem('5-95 percentile')
        self.envelope_method_combo.addItem('Interquartile range')
        self.envelope_method_combo.addItem('Standard deviation')
        self.envelope_method_combo.setCurrentText(self.data_manager.user_preferences.get('bounce_envelope', 'None'))
        self.envelope_method_combo.currentIndexChanged.connect(lambda index: self.data_manager.user_preferences.update({'bounce_envelope': self.envelope_method_combo.currentText()}))

        # Combo box for celeraiton unit
        celeration_unit_label = QLabel("Celeration unit")
        self.celeration_unit_combo = QComboBox()
        self.celeration_unit_combo.addItem('Daily')
        self.celeration_unit_combo.addItem('Weekly (standard)')
        self.celeration_unit_combo.addItem('Monthly (Weekly x4)')
        self.celeration_unit_combo.addItem('Yearly (Weekly x52)')
        self.celeration_unit_combo.setCurrentText(self.data_manager.user_preferences.get('celeration_unit', 'Weekly (standard)'))
        self.celeration_unit_combo.currentIndexChanged.connect(lambda index: self.data_manager.user_preferences.update({'celeration_unit': self.celeration_unit_combo.currentText()}))

        # Add components to the main layout
        self.layout.addWidget(trend_method_label)
        self.layout.addWidget(self.trend_method_combo)
        self.layout.addWidget(forward_projection_label)
        self.layout.addWidget(self.forward_projection_spinbox)
        self.layout.addWidget(envelope_method_label)
        self.layout.addWidget(self.envelope_method_combo)
        self.layout.addWidget(celeration_unit_label)
        self.layout.addWidget(self.celeration_unit_combo)

        # Eliminate any extra vertical stretches
        self.layout.addStretch()

        # Clean up when switching between point type
        self.trend_radio_dot.toggled.connect(self.figure_manager.trend_cleanup)
        trend_radio_x.toggled.connect(self.figure_manager.trend_cleanup)

        # Connect buttons to figure manager methods
        self.trend_fit_btn.clicked.connect(self.handle_fit_button)
        self.trend_add_btn.clicked.connect(self.add_trend)
        trend_undo_btn.clicked.connect(self.undo_trend)
        trend_configure_btn.clicked.connect(self.configure_trends)

        # Connect date changes to figure manager updates
        self.trend_start_date_input.dateChanged.connect(self.figure_manager.trend_date1_changed)
        self.trend_end_date_input.dateChanged.connect(self.figure_manager.trend_date2_changed)

    def add_trend(self):
        self.figure_manager.trend_finalize(self.trend_radio_dot.isChecked())
        self.set_plus_btn_status()

    def undo_trend(self):
        self.figure_manager.trend_undo(self.trend_radio_dot.isChecked())
        self.set_plus_btn_status()

    def handle_fit_button(self):
        self.figure_manager.trend_fit(self.trend_radio_dot.isChecked())
        self.setFocus()  # Set focus back to the main window
        self.set_plus_btn_status()

    def set_plus_btn_status(self):
        # If a magenta trend was placed, make the plus button available
        if self.figure_manager.trend_manager.trend_temp_fit_on:
            self.trend_add_btn.setEnabled(True)
            self.trend_add_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        else:
            self.trend_add_btn.setEnabled(False)
            self.trend_add_btn.setIcon(QIcon(':/images/plus-solid-disabled.svg'))

    def configure_trends(self):
        dialog = ConfigureTrendLinesDialog(self.trend_radio_dot.isChecked(), self.figure_manager, self)
        dialog.exec()
