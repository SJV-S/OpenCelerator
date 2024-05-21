from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QGroupBox, QRadioButton, QVBoxLayout, QLineEdit, QLabel, QDateEdit, QListWidget, QFileDialog, QCheckBox, QButtonGroup, QDialog, QComboBox, QMessageBox, QGridLayout, QStackedWidget
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtCore import Qt, QDate

from support_classes import InputDialog


class ModeWidget(QWidget):
    def __init__(self, figure_manager):
        super().__init__()
        self.figure_manager = figure_manager
        self.layout = QVBoxLayout(self)
        self.init_ui()

    def init_ui(self):
        pass


class ViewModeWidget(ModeWidget):
    def init_ui(self):
        self.dialog = InputDialog()

        # Creating grid layout to organize the checkboxes
        view_grid = QGridLayout()

        # Headings for Dot and X settings
        font = QFont()
        font.setBold(True)
        dot_heading = QLabel("Dot")
        dot_heading.setFont(font)
        x_heading = QLabel("X")
        x_heading.setFont(font)
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
        self.dots_check = QCheckBox('Point')
        self.xs_check = QCheckBox('Point')
        self.dot_trends_check = QCheckBox('Trend')
        self.x_trends_check = QCheckBox('Trend')
        self.dot_lines_check = QCheckBox('Line')
        self.x_lines_check = QCheckBox('Line')
        self.dot_color_check = QCheckBox('Green')
        self.x_color_check = QCheckBox('Red')
        self.minor_grid_check = QCheckBox('Minor')
        self.major_grid_check = QCheckBox('Major')
        self.timing_floor_check = QCheckBox('Floor')
        self.timing_grid_check = QCheckBox('Timing')
        self.phase_lines_check = QCheckBox('Phase')
        self.aims_check = QCheckBox('Aim')

        # Adding checkboxes to the grid
        view_grid.addWidget(self.dots_check, 1, 0)
        view_grid.addWidget(self.dot_trends_check, 4, 0)
        view_grid.addWidget(self.dot_lines_check, 2, 0)
        view_grid.addWidget(self.dot_color_check, 3, 0)
        view_grid.addWidget(self.xs_check, 1, 1)
        view_grid.addWidget(self.x_trends_check, 4, 1)
        view_grid.addWidget(self.x_lines_check, 2, 1)
        view_grid.addWidget(self.x_color_check, 3, 1)
        view_grid.addWidget(self.minor_grid_check, 8, 0)
        view_grid.addWidget(self.major_grid_check, 7, 0)
        view_grid.addWidget(self.timing_grid_check, 9, 0)
        view_grid.addWidget(self.aims_check, 7, 1)
        view_grid.addWidget(self.timing_floor_check, 8, 1)
        view_grid.addWidget(self.phase_lines_check, 9, 1)

        # Setting initial states of checkboxes
        for checkbox in [self.minor_grid_check, self.major_grid_check, self.dots_check, self.xs_check,
                         self.dot_trends_check, self.x_trends_check, self.phase_lines_check,
                         self.aims_check, self.timing_floor_check]:
            checkbox.setChecked(True)

        for checkbox in [self.timing_grid_check, self.dot_lines_check, self.x_lines_check,
                         self.dot_color_check, self.x_color_check]:
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
        self.dot_lines_check.stateChanged.connect(self.figure_manager.view_dot_lines)
        self.x_lines_check.stateChanged.connect(self.figure_manager.view_x_lines)
        self.dot_color_check.stateChanged.connect(self.figure_manager.view_color_dots)
        self.x_color_check.stateChanged.connect(self.figure_manager.view_color_xs)

        # Credit lines button
        credit_lines_btn = QPushButton("Credit lines")
        credit_lines_btn.clicked.connect(self.credit_lines_popup)
        self.layout.addLayout(view_grid)
        self.layout.addWidget(credit_lines_btn)

    def credit_lines_popup(self):
        if self.dialog.exec_() == QDialog.Accepted:  # Check if the dialog was accepted
            r1, r2, r3 = self.dialog.get_inputs()  # Retrieve the inputs
            self.dialog.credit_row1 = r1
            self.dialog.credit_row2 = r2
            self.dialog.credit_row3 = r3
            self.figure_manager.view_update_credit_lines(r1, r2, r3)


class ManualModeWidget(ModeWidget):
    def init_ui(self):
        # Group box for radio buttons to select dot type
        radio_layout = QHBoxLayout()
        radio_dot = QRadioButton("Dots")
        radio_x = QRadioButton("Xs")
        radio_dot.setChecked(True)  # Start with dot by default

        radio_layout.addWidget(radio_dot)
        radio_layout.addWidget(radio_x)
        self.layout.addLayout(radio_layout)

        # Connect radio buttons to change point type in figure manager
        radio_dot.toggled.connect(lambda checked: setattr(self.figure_manager, 'point_type', True) if checked else None)
        radio_x.toggled.connect(lambda checked: setattr(self.figure_manager, 'point_type', False) if checked else None)

        # Validators for input fields
        validator = QDoubleValidator(0.0, 9999.99, 2)

        # Setup for Count input
        label_manual_count = QLabel('Count')
        count_input = QLineEdit('')
        count_input.setValidator(validator)
        self.layout.addWidget(label_manual_count)
        self.layout.addWidget(count_input)

        # Setup for Date input
        date_input = QDateEdit()
        date_input.setDate(QDate.currentDate())
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("dd-MM-yyyy")
        self.layout.addWidget(QLabel('Date'))
        self.layout.addWidget(date_input)

        # Time input setup
        time_input_layout = QHBoxLayout()
        hour_input = self.create_time_input("Hour", validator)
        min_input = self.create_time_input("Min", validator)
        sec_input = self.create_time_input("Sec", validator)
        time_input_layout.addLayout(hour_input)
        time_input_layout.addLayout(min_input)
        time_input_layout.addLayout(sec_input)
        self.layout.addLayout(time_input_layout)

        # Buttons for adding and undoing manual entries
        manual_buttons_layout = QHBoxLayout()
        add_button = QPushButton('Add')
        undo_button = QPushButton('Undo')
        manual_buttons_layout.addWidget(add_button)
        manual_buttons_layout.addWidget(undo_button)
        self.layout.addLayout(manual_buttons_layout)

        # Connect buttons to figure manager methods
        add_button.clicked.connect(lambda: self.figure_manager.manual_plot_from_form(
            count_input.text(),
            hour_input.itemAt(1).widget().text(),
            min_input.itemAt(1).widget().text(),
            sec_input.itemAt(1).widget().text(),
            date_input.text()
        ))
        undo_button.clicked.connect(self.figure_manager.manual_undo_point)

        # Label for displaying coordinates
        label_xy_coordinates = QLabel('')
        self.layout.addWidget(label_xy_coordinates)

        # Eliminate any extra vertical stretches
        self.layout.addStretch()

    def create_time_input(self, label_text, validator):
        """Helper method to create time input layouts."""
        layout = QVBoxLayout()
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setValidator(validator)
        layout.addWidget(label, 0, Qt.AlignCenter)
        layout.addWidget(input_field)
        return layout


class PhaseModeWidget(ModeWidget):
    def init_ui(self):
        # Creating label and input for phase change description
        phase_change_label = QLabel('Change')
        self.phase_change_input = QLineEdit('')
        self.layout.addWidget(phase_change_label)
        self.layout.addWidget(self.phase_change_input)

        # Y-value input
        phase_label_y = QLabel('Y-value')
        self.phase_y_input = QLineEdit('500')  # Default value set to 500
        validator = QDoubleValidator(0.0, 9999.99, 4)
        self.phase_y_input.setValidator(validator)
        self.layout.addWidget(phase_label_y)
        self.layout.addWidget(self.phase_y_input)

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
        add_phase_line_btn = QPushButton('Add')
        undo_phase_line_btn = QPushButton('Undo')
        phase_line_button_layout.addWidget(add_phase_line_btn)
        phase_line_button_layout.addWidget(undo_phase_line_btn)
        self.layout.addLayout(phase_line_button_layout)

        # Connect buttons to figure manager methods
        add_phase_line_btn.clicked.connect(lambda: self.figure_manager.phase_line_from_form(
            self.phase_y_input.text(),
            self.phase_change_input.text(),
            self.phase_date_input.text()
        ))
        undo_phase_line_btn.clicked.connect(self.figure_manager.phase_undo_line)

        # Eliminate any extra vertical stretches
        self.layout.addStretch()


class AimModeWidget(ModeWidget):
    def init_ui(self):

        # Note input for aim
        aim_target_label = QLabel('Note')
        self.aim_target_input = QLineEdit('')
        self.layout.addWidget(aim_target_label)
        self.layout.addWidget(self.aim_target_input)

        # Y-value input for targeting
        aim_label_y = QLabel('Target')
        self.aim_y_input = QLineEdit('')
        self.aim_y_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))
        self.layout.addWidget(aim_label_y)
        self.layout.addWidget(self.aim_y_input)

        # Start date input
        aim_label_start_date = QLabel('Start')
        self.aim_start_date_input = QDateEdit()
        self.aim_start_date_input.setDate(QDate.currentDate())
        self.aim_start_date_input.setCalendarPopup(True)
        self.aim_start_date_input.setDisplayFormat("dd-MM-yyyy")
        self.layout.addWidget(aim_label_start_date)
        self.layout.addWidget(self.aim_start_date_input)

        # Deadline date input
        aim_label_end_date = QLabel('Deadline')
        self.aim_end_date_input = QDateEdit()
        self.aim_end_date_input.setDate(QDate.currentDate())
        self.aim_end_date_input.setCalendarPopup(True)
        self.aim_end_date_input.setDisplayFormat("dd-MM-yyyy")
        self.layout.addWidget(aim_label_end_date)
        self.layout.addWidget(self.aim_end_date_input)

        # Add and Undo buttons for setting aims
        aim_line_button_layout = QHBoxLayout()
        add_aim_line_btn = QPushButton('Add')
        undo_aim_line_btn = QPushButton('Undo')
        aim_line_button_layout.addWidget(add_aim_line_btn)
        aim_line_button_layout.addWidget(undo_aim_line_btn)
        self.layout.addLayout(aim_line_button_layout)

        # Connect buttons to figure manager methods
        add_aim_line_btn.clicked.connect(lambda: self.figure_manager.aim_from_form(
            self.aim_target_input.text(),
            self.aim_y_input.text(),
            self.aim_start_date_input.text(),
            self.aim_end_date_input.text()
        ))
        undo_aim_line_btn.clicked.connect(self.figure_manager.aim_undo)


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
        trend_add_btn = QPushButton('Add')
        self.trend_fit_btn = QPushButton('Fit')
        trend_undo_btn = QPushButton('Undo')

        trend_button_layout.addWidget(trend_add_btn)
        trend_button_layout.addWidget(self.trend_fit_btn)
        trend_button_layout.addWidget(trend_undo_btn)
        self.layout.addLayout(trend_button_layout)

        # Clean up when switching between point type
        self.trend_radio_dot.toggled.connect(self.figure_manager.trend_cleanup)
        trend_radio_x.toggled.connect(self.figure_manager.trend_cleanup)

        # Connect buttons to figure manager methods
        self.trend_fit_btn.clicked.connect(self.handle_fit_button)
        trend_add_btn.clicked.connect(lambda: self.figure_manager.trend_finalize(self.trend_radio_dot.isChecked()))
        trend_undo_btn.clicked.connect(lambda: self.figure_manager.trend_undo(self.trend_radio_dot.isChecked()))

        # Connect date changes to figure manager updates
        self.trend_start_date_input.dateChanged.connect(self.figure_manager.trend_date1_changed)
        self.trend_end_date_input.dateChanged.connect(self.figure_manager.trend_date2_changed)

        # Eliminate any extra vertical stretches
        self.layout.addStretch()

    def handle_fit_button(self):
        self.figure_manager.trend_fit(self.trend_radio_dot.isChecked())
        self.setFocus()  # Set focus back to the main window