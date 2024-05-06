
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QGroupBox, QRadioButton, QVBoxLayout, QLineEdit, QLabel, QDateEdit, QListWidget, QFileDialog, QCheckBox, QButtonGroup, QDialog, QComboBox, QMessageBox, QGridLayout
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtCore import Qt, QDate

from FigureManager import FigureManager
from DataManager import DataManager
from support_classes import InputDialog

'''
Fix: 
- Investigate why export are not saving as proper datetimes
- Find a way to better organize the code in figure manager
'''

class ChartApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize the main window properties
        self.setWindowTitle('iChart')

        self.data_manager = DataManager()

        # Default to home folder
        self.home_folder = os.path.expanduser("~")

        # Create and set the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Initialize the tabs for the left panel
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(178)
        self.main_layout.addWidget(self.tabs)
        self.tab_home = QWidget()
        self.files_tab = QWidget()
        self.tab_settings = QWidget()

        # Add tabs to the tab widget
        self.tabs.addTab(self.tab_home, 'Home')
        self.tabs.addTab(self.files_tab, 'Files')
        self.tabs.addTab(self.tab_settings, 'Settings')

        # Set up home tab
        self.home_layout = QVBoxLayout()  # Main layout for the home tab

        # Initialize and add the Matplotlib widget to the right panel
        self.figure_manager = FigureManager(self)
        self.main_layout.addWidget(self.figure_manager)

        # Setup interaction handling
        self.current_connection = None

        # Setup tabs
        self.setup_home_tab()
        self.setup_file_tab()
        self.setup_settings_tab()

        # Setup Radio Buttons
        self.radio_view.setChecked(True)
        self.set_interaction_mode()

        # Define the key press handling methods for different modes
        self.keyHandlers = {
            'view': self.handleViewKeyPress,
            'manual': self.handleManualKeyPress,
            'phase': self.handlePhaseKeyPress
        }
        self.currentMode = 'view'  # Start in Manual mode by default

        # Enable key event handling
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()  # Set focus to the main window

        # Control variables
        self.xy_coord = None

    def handleManualKeyPress(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            self.manual.handle_key_press(event)
            self.manual_update_xy_pos_label()
        elif event.key() == Qt.Key_Return:
            self.manual.finalize_point()

    def handlePhaseKeyPress(self, event):
        # Implement specific key handling for Phase mode if needed
        pass

    def handleViewKeyPress(self, event):
        # Minimal or no key handling for View mode if needed
        pass

    def setup_home_tab(self):

        # Mode GroupBox
        group_box_mode = QGroupBox("Mode")
        group_box_mode.setStyleSheet("QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; }")
        layout_mode = QVBoxLayout()
        self.radio_view = QRadioButton("View")
        self.radio_manual = QRadioButton("Entry")
        self.radio_phase = QRadioButton("Phase")
        self.radio_aim = QRadioButton("Aim")
        self.radio_trend = QRadioButton('Trend')
        layout_mode.addWidget(self.radio_view)
        layout_mode.addWidget(self.radio_manual)
        layout_mode.addWidget(self.radio_phase)
        layout_mode.addWidget(self.radio_aim)
        layout_mode.addWidget(self.radio_trend)
        group_box_mode.setLayout(layout_mode)
        self.home_layout.addWidget(group_box_mode)

        # Connect radio buttons to interaction mode setter
        self.radio_view.toggled.connect(lambda checked: self.setMode('view') if checked else None)
        self.radio_manual.toggled.connect(lambda checked: self.setMode('manual') if checked else None)
        self.radio_phase.toggled.connect(lambda checked: self.setMode('phase') if checked else None)
        self.radio_aim.toggled.connect(lambda checked: self.setMode('aim') if checked else None)
        self.radio_trend.toggled.connect(lambda checked: self.setMode('trend') if checked else None)

        # Set up modes
        self.setup_view_mode()
        self.dialog = InputDialog(self)  # Also for view mode
        self.setup_manual_mode()
        self.setup_phase_mode()
        self.setup_aim_mode()
        self.setup_trend_mode()

        # Set layout to home tab
        self.home_layout.addStretch()  # Prevents the buttons from vertically filling the whole panel
        self.tab_home.setLayout(self.home_layout)

    def setup_file_tab(self):
        files_layout = QVBoxLayout()  # Create a QVBoxLayout instance
        self.files_tab.setLayout(files_layout)  # Set the layout to files_tab

        # Data GroupBox
        group_box_data = QGroupBox("Data")
        group_box_data.setStyleSheet("QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; }")
        layout_data = QVBoxLayout()
        btn_import_delete = QPushButton('Import')
        btn_import_delete.setToolTip('Replot all data points.')
        btn_export = QPushButton("Export")
        btn_export.setToolTip('Export data as csv.')
        layout_data.addWidget(btn_import_delete)

        layout_data.addWidget(btn_export)
        group_box_data.setLayout(layout_data)
        files_layout.addWidget(group_box_data)

        # Chart GroupBox
        group_box_chart = QGroupBox("Chart")
        group_box_chart.setStyleSheet("QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top center; }")
        layout_chart = QVBoxLayout()
        btn_new = QPushButton('New')
        btn_load = QPushButton('Load')
        btn_save = QPushButton('Save')
        btn_image = QPushButton('Get image')
        btn_image.setToolTip('Save chart as png file.')
        layout_chart.addWidget(btn_new)
        layout_chart.addWidget(btn_load)
        layout_chart.addWidget(btn_save)
        layout_chart.addWidget((btn_image))
        group_box_chart.setLayout(layout_chart)
        files_layout.addWidget(group_box_chart)

        # Button connections
        btn_import_delete.clicked.connect(self.import_data)
        btn_export.clicked.connect(self.export_data)
        # btn_new.clicked.connect(self.figure_manager.back_to_default)
        btn_new.clicked.connect(self.files_show_dialog)
        btn_image.clicked.connect(self.save_image)
        btn_save.clicked.connect(self.save_chart)
        btn_load.clicked.connect(self.load_chart)

        files_layout.addStretch()  # Prevents the buttons from vertically filling the whole panel

    def files_show_dialog(self):
        # Create a QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Load new chart")
        msg_box.setText("Remove current chart?")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)

        # Execute the message box and get the response
        response = msg_box.exec_()

        # Check the response and perform actions based on it
        if response == QMessageBox.Yes:
            self.figure_manager.back_to_default()

    def setup_settings_tab(self):
        # Create settings layout
        settings_layout = QVBoxLayout()
        self.tab_settings.setLayout(settings_layout)

        # Test angle
        settings_test_angle_check = QCheckBox('Test angle')
        settings_layout.addWidget(settings_test_angle_check)
        settings_test_angle_check.stateChanged.connect(self.figure_manager.settings_test_angle)

        # Zero counts below timing floor or don't display
        settings_zero_count_handling_label = QLabel('Handle zero counts')
        settings_zero_count_handling = QComboBox()
        settings_zero_count_handling.setToolTip('Set before importing data')
        settings_zero_count_handling.addItem('Place below floor')
        settings_zero_count_handling.addItem('Do not show')
        settings_layout.addWidget(settings_zero_count_handling_label)
        settings_layout.addWidget(settings_zero_count_handling)
        settings_zero_count_handling.currentIndexChanged.connect(
            lambda index: setattr(self.data_manager, 'place_zero_counts_below_floor',
                                  settings_zero_count_handling.itemText(index) == 'Place below floor')
        )

        # Set image quality
        settings_image_quality_label = QLabel('Image quality when saving')
        settings_image_quality = QComboBox()
        settings_image_quality.addItem('High (300 dpi)', 300)  # Adding item with data
        settings_image_quality.addItem('Medium (200 dpi)', 200)
        settings_image_quality.addItem('Low (100 dpi)', 100)
        settings_image_quality.setCurrentIndex(1)
        settings_layout.addWidget(settings_image_quality_label)
        settings_layout.addWidget(settings_image_quality)
        settings_image_quality.currentIndexChanged.connect(
            lambda index: setattr(self.figure_manager, 'dpi', settings_image_quality.itemData(index)))

        # Set start date
        start_date_label = QLabel('Set start date')
        settings_layout.addWidget(start_date_label)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.start_date_input.dateChanged.connect(
            lambda new_date: (self.figure_manager.settings_change_start_date(new_date), self.set_interaction_mode()))
        settings_layout.addWidget(self.start_date_input)

        # Push everything to the top
        settings_layout.addStretch()

    def setMode(self, mode):
        self.currentMode = mode
        self.view_mode_interface(mode == 'view')
        self.manual_mode_interface(mode == 'manual')
        self.phase_mode_interface(mode == 'phase')
        self.aim_mode_interface(mode == 'aim')
        self.trend_mode_interface(mode == 'trend')
        self.set_interaction_mode()

    def keyPressEvent(self, event):
        # Check if the manual mode is active
        if self.currentMode == 'manual':
            # Optionally, log all key presses for debugging
            # print("Key pressed in manual mode:", event.key(), "Modifiers:", int(event.modifiers()))

            # Handle specific keys like Ctrl+Z for undo
            if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Z:
                self.figure_manager.undo_point()
                event.accept()  # Mark the event as handled
            else:
                # Consume all other key events to prevent any other key handling
                event.accept()  # This prevents the event from propagating further
            return  # Exit the function to stop any further key event processing

        # Handle other keys as usual in other modes
        super().keyPressEvent(event)

        if self.currentMode == 'trend':
        # Check if space was pressed
            if event.key() == Qt.Key_Left:
                self.figure_manager.trend_move_temp_marker('left')
                self.trend_adjust_dates()
                self.figure_manager.trend_move_temp_est_with_arrows('left')
            elif event.key() == Qt.Key_Right:
                self.figure_manager.trend_move_temp_marker('right')
                self.trend_adjust_dates()
                self.figure_manager.trend_move_temp_est_with_arrows('right')
            elif event.key() == Qt.Key_Up:
                self.figure_manager.trend_move_temp_est_with_arrows('up')
            elif event.key() == Qt.Key_Down:
                self.figure_manager.trend_move_temp_est_with_arrows('down')



        # if self.currentMode == 'phase':
        #     # Check if space was pressed
        #     if event.key() == Qt.Key_Space:
        #         event.accept()
        #         return
        #     if event.key() == Qt.Key_Left:
        #         self.phase.move_line_left()
        #     elif event.key() == Qt.Key_Right:
        #         self.phase.move_line_right()

        # Use existing key handling
        handler = self.keyHandlers.get(self.currentMode)
        if handler:
            handler(event)
            event.accept()  # Mark the event as handled
        else:
            super().keyPressEvent(event)  # Call the parent class's keyPressEvent if no handler is defined

    def set_interaction_mode(self):
        if self.current_connection:
            self.figure_manager.canvas.mpl_disconnect(self.current_connection)

        if self.radio_view.isChecked():
            pass  # No interaction
        elif self.radio_phase.isChecked():
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.phase_click)
        elif self.radio_trend.isChecked():
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.trend_click)
        elif self.radio_aim.isChecked():
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.aim_click)

    def aim_click(self, event):
        coordinates = self.figure_manager.aim_click_info(event, self.aim_target_input.text())
        if coordinates:
            d1, d2, y = coordinates
            self.aim_y_input.setText(str(y))
            self.aim_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
            self.aim_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

    def trend_adjust_dates(self):
        if self.figure_manager.trend_current_temp_marker == 'first':
            x1 = self.figure_manager.trend_temp_first_marker.get_xdata()[0]
            d1 = self.figure_manager.x_to_date[x1]
            self.trend_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
        elif self.figure_manager.trend_current_temp_marker == 'second':
            x2 = self.figure_manager.trend_temp_second_marker.get_xdata()[0]
            d2 = self.figure_manager.x_to_date[x2]
            self.trend_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

    def trend_click(self, event):
        # Set to run on second click
        self.figure_manager.trend_on_click(event)

        if self.figure_manager.trend_first_click_x and not self.figure_manager.trend_second_click_x:
            self.figure_manager.plot_trend_temp_first_marker(self.figure_manager.trend_first_click_x)
        elif self.figure_manager.trend_second_click_x:
            self.figure_manager.plot_trend_temp_second_marker(self.figure_manager.trend_second_click_x)

        self.trend_adjust_dates()

    def phase_click(self, event):
        # Update phase line form
        coordinates = self.figure_manager.phase_line_handle_click(event, self.phase_change_input.text())
        if coordinates:  # In case the user clicked outside the graph
            x, y = coordinates
            self.phase_y_input.setText(str(y))
            date = self.figure_manager.x_to_date[x]
            date_qt = QDate(date.year, date.month, date.day)
            self.phase_date_input.setDate(date_qt)

    def setup_manual_mode(self):
        self.group_box_manual_modes = QGroupBox()
        layout_manual_modes = QVBoxLayout()
        self.radio_dot = QRadioButton("Dots")
        self.radio_x = QRadioButton("Xs")
        layout_manual_modes.addWidget(self.radio_dot)
        layout_manual_modes.addWidget(self.radio_x)
        self.radio_dot.setChecked(True)  # Start with dot by default
        self.group_box_manual_modes.setLayout(layout_manual_modes)
        self.home_layout.addWidget(self.group_box_manual_modes)
        self.radio_dot.toggled.connect(lambda checked: setattr(self.figure_manager, 'point_type', True))
        self.radio_x.toggled.connect(lambda checked: setattr(self.figure_manager, 'point_type', False))

        validator = QDoubleValidator(0.0, 9999.99, 2)  # Setting range from 0.0 to 9999.99 with 2 decimal places

        self.count_input = QLineEdit('')
        self.count_input.setValidator(validator)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format

        # Count
        self.label_manual_count = QLabel('Count')
        self.home_layout.addWidget(self.label_manual_count)
        self.home_layout.addWidget(self.count_input)

        # Set up labels above inputs for Hour, Min, and Sec
        time_input_layout = QHBoxLayout()  # Main layout for time inputs

        # Setup for Hour input
        hour_layout = QVBoxLayout()
        self.label_hour = QLabel('Hour')
        self.hour_input = QLineEdit()
        self.hour_input.setValidator(validator)
        hour_layout.addWidget(self.label_hour, 0, Qt.AlignCenter)  # Align label to center
        hour_layout.addWidget(self.hour_input)
        time_input_layout.addLayout(hour_layout)

        # Setup for Minute input
        min_layout = QVBoxLayout()
        self.label_min = QLabel('Min')
        self.min_input = QLineEdit()
        self.min_input.setValidator(validator)
        min_layout.addWidget(self.label_min, 0, Qt.AlignCenter)  # Align label to center
        min_layout.addWidget(self.min_input)
        time_input_layout.addLayout(min_layout)

        # Setup for Second input
        sec_layout = QVBoxLayout()
        self.label_sec = QLabel('Sec')
        self.sec_input = QLineEdit()
        self.sec_input.setValidator(validator)
        sec_layout.addWidget(self.label_sec, 0, Qt.AlignCenter)  # Align label to center
        sec_layout.addWidget(self.sec_input)
        time_input_layout.addLayout(sec_layout)

        # Add the time inputs layout to the main layout
        self.home_layout.addLayout(time_input_layout)

        # Dates
        self.label_manual_date = QLabel('Date')
        self.home_layout.addWidget(self.label_manual_date)
        self.home_layout.addWidget(self.date_input)

        # Add and Undo buttons
        manual_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton('Add')
        self.undo_button = QPushButton('Undo')
        manual_buttons_layout.addWidget(self.add_button)
        manual_buttons_layout.addWidget(self.undo_button)
        self.home_layout.addLayout(manual_buttons_layout)

        self.add_button.clicked.connect(lambda: self.figure_manager.manual_plot_from_form(
            self.count_input.text(),
            self.hour_input.text(),
            self.min_input.text(),
            self.sec_input.text(),
            self.date_input.text()
        ))

        self.undo_button.clicked.connect(self.figure_manager.manual_undo_point)

        # Create and add the QLabel for displaying coordinates
        self.label_xy_coordinates = QLabel('')
        self.home_layout.addWidget(self.label_xy_coordinates)

        # Hide manual mode interface
        self.manual_mode_interface(False)

    def manual_mode_interface(self, show):
        self.group_box_manual_modes.setVisible(show)  # Initially hidden
        self.count_input.setVisible(show)
        self.date_input.setVisible(show)
        self.label_manual_date.setVisible(show)
        self.label_manual_count.setVisible(show)
        self.add_button.setVisible(show)
        self.undo_button.setVisible(show)
        self.hour_input.setVisible(show)
        self.label_hour.setVisible(show)
        self.min_input.setVisible(show)
        self.label_min.setVisible(show)
        self.sec_input.setVisible(show)
        self.label_sec.setVisible(show)
        self.label_xy_coordinates.setVisible(show)

        if not show:
            self.label_xy_coordinates.setText('')

    def setup_phase_mode(self):

        self.phase_change_label = QLabel('Change')
        self.phase_change_input = QLineEdit('')

        self.add_phase_line_btn = QPushButton('Add')
        self.undo_phase_line_btn = QPushButton('Undo')
        self.home_layout.addWidget(self.phase_change_label)
        self.home_layout.addWidget(self.phase_change_input)

        self.phase_label_y = QLabel('Y-value')
        self.phase_y_input = QLineEdit('500')
        self.phase_y_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))
        self.home_layout.addWidget(self.phase_label_y)
        self.home_layout.addWidget(self.phase_y_input)

        # Dates
        self.phase_label_date = QLabel('Date')
        self.home_layout.addWidget(self.phase_label_date)
        self.phase_date_input = QDateEdit()
        self.phase_date_input.setDate(QDate.currentDate())
        self.phase_date_input.setCalendarPopup(True)
        self.phase_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.home_layout.addWidget(self.phase_date_input)

        # Buttons
        phase_line_button_layout = QHBoxLayout()
        phase_line_button_layout.addWidget(self.add_phase_line_btn)
        phase_line_button_layout.addWidget(self.undo_phase_line_btn)
        self.home_layout.addLayout(phase_line_button_layout)

        self.add_phase_line_btn.clicked.connect(lambda: self.figure_manager.phase_line_from_form(
            self.phase_y_input.text(),
            self.phase_change_input.text(),
            self.phase_date_input.text()
        ))

        self.undo_phase_line_btn.clicked.connect(self.figure_manager.phase_undo_line)

        self.phase_mode_interface(False)

    def phase_mode_interface(self, show):
        self.phase_change_label.setVisible(show)
        self.phase_change_input.setVisible(show)
        self.add_phase_line_btn.setVisible(show)
        self.undo_phase_line_btn.setVisible(show)
        self.phase_label_date.setVisible(show)
        self.phase_date_input.setVisible(show)
        self.phase_label_y.setVisible(show)
        self.phase_y_input.setVisible(show)

        if not show:
            self.figure_manager.phase_cleanup_temp_line()

    def setup_view_mode(self):
        # Checkboxes
        self.minor_grid_check = QCheckBox('Minor')
        self.major_grid_check = QCheckBox('Major')
        self.dots_check = QCheckBox('Point')
        self.xs_check = QCheckBox('Point')
        self.dot_trends_check = QCheckBox('Trend')
        self.x_trends_check = QCheckBox('Trend')
        self.timing_floor_check = QCheckBox('Floor')
        self.timing_grid_check = QCheckBox('Timing')
        self.phase_lines_check = QCheckBox('Phase')
        self.aims_check = QCheckBox('Aim')
        self.dot_lines_check = QCheckBox('Line')
        self.x_lines_check = QCheckBox('Line')
        self.x_color_check = QCheckBox('Red')
        self.dot_color_check = QCheckBox('Green')

        view_grid = QGridLayout()

        # Point column headings
        self.dot_heading = QLabel("Dot")
        self.x_heading = QLabel("X")
        # Other headings
        self.grid_heading = QLabel("\nGrid")
        self.other_heading = QLabel("\nOther")
        # Set the font to be bold
        font = QFont()
        font.setBold(True)
        self.dot_heading.setFont(font)
        self.x_heading.setFont(font)
        self.grid_heading.setFont(font)
        self.other_heading.setFont(font)

        # Add headings to the grid
        view_grid.addWidget(self.dot_heading, 0, 0)
        view_grid.addWidget(self.x_heading, 0, 1)

        # Add Dot related checkboxes in column 0
        view_grid.addWidget(self.dots_check, 1, 0)
        view_grid.addWidget(self.dot_trends_check, 4, 0)
        view_grid.addWidget(self.dot_lines_check, 2, 0)
        view_grid.addWidget(self.dot_color_check, 3, 0)

        # Add X related checkboxes in column 1
        view_grid.addWidget(self.xs_check, 1, 1)
        view_grid.addWidget(self.x_trends_check, 4, 1)
        view_grid.addWidget(self.x_lines_check, 2, 1)
        view_grid.addWidget(self.x_color_check, 3, 1)

        # Gridlines
        view_grid.addWidget(self.grid_heading, 6, 0)
        view_grid.addWidget(self.major_grid_check, 7, 0)  # Major gridlines
        view_grid.addWidget(self.minor_grid_check, 8, 0)  # Minor gridlines
        view_grid.addWidget(self.timing_grid_check, 9, 0)  # Timing grid

        # Other
        view_grid.addWidget(self.other_heading, 6, 1)
        view_grid.addWidget(self.aims_check, 7, 1)  # Aims
        view_grid.addWidget(self.timing_floor_check, 8, 1)  # Timing floor
        view_grid.addWidget(self.phase_lines_check, 9, 1)  # Phase lines

        # Checkbox connections
        self.minor_grid_check.stateChanged.connect(self.figure_manager.view_minor_gridlines)
        self.major_grid_check.stateChanged.connect(self.figure_manager.view_major_gridlines)
        self.dots_check.stateChanged.connect(self.figure_manager.view_dots)
        self.xs_check.stateChanged.connect(self.figure_manager.view_xs)
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

        view_grid_widget = QWidget()
        view_grid_widget.setLayout(view_grid)
        self.home_layout.addWidget(view_grid_widget)

        # Set checked boxes
        for check_box in [self.minor_grid_check,
                          self.major_grid_check,
                          self.dots_check,
                          self.xs_check,
                          self.dot_trends_check,
                          self.x_trends_check,
                          self.phase_lines_check,
                          self.aims_check,
                          self.timing_floor_check,
                          ]:
            check_box.setChecked(True)

        # Set unchecked boxes
        for check_box in [self.timing_grid_check,
                          self.dot_lines_check,
                          self.x_lines_check,
                          self.dot_color_check,
                          self.x_color_check
                          ]:
            check_box.setChecked(False)

        # Credit lines button
        self.credit_lines_btn = QPushButton("Credit lines")
        self.home_layout.addWidget(self.credit_lines_btn)
        self.credit_lines_btn.clicked.connect(self.credit_lines_popup)

        self.view_mode_interface(False)

    def sync_view_settings(self):
        # Set checkboxes (will only run here if there's a change, so unreliable)
        settings = self.data_manager.chart_data['view_check']
        self.minor_grid_check.setChecked(settings['minor_grid'])
        self.major_grid_check.setChecked(settings['major_grid'])
        self.dots_check.setChecked(settings['dots'])
        self.xs_check.setChecked(settings['xs'])
        self.dot_trends_check.setChecked(settings['dot_trends'])
        self.x_trends_check.setChecked(settings['x_trends'])
        self.timing_floor_check.setChecked(settings['timing_floor'])
        self.timing_grid_check.setChecked(settings['timing_grid'])
        self.phase_lines_check.setChecked(settings['phase_lines'])
        self.aims_check.setChecked(settings['aims'])

        # Update view checks
        refresh = False
        self.figure_manager.view_minor_gridlines(settings['minor_grid'], refresh=refresh)
        self.figure_manager.view_major_gridlines(settings['major_grid'], refresh=refresh)
        self.figure_manager.view_dots(settings['dots'], refresh=refresh)
        self.figure_manager.view_xs(settings['xs'], refresh=refresh)
        self.figure_manager.view_dot_trend(settings['dot_trends'], refresh=refresh)
        self.figure_manager.view_x_trend(settings['x_trends'], refresh=refresh)
        self.figure_manager.view_floor(settings['timing_floor'], refresh=refresh)
        self.figure_manager.view_floor_grid(settings['timing_grid'], refresh=refresh)
        self.figure_manager.view_phase_lines(settings['phase_lines'], refresh=refresh)
        self.figure_manager.view_aims(settings['aims'], refresh=refresh)
        self.figure_manager.view_dot_lines(settings['dot_lines'], refresh=refresh)
        self.figure_manager.view_x_lines(settings['x_lines'], refresh=refresh)
        self.figure_manager.refresh()  # Only refresh canvas once!

    def credit_lines_popup(self):
        if self.dialog.exec_() == QDialog.Accepted:  # Check if the dialog was accepted
            r1, r2, r3 = self.dialog.get_inputs()  # Retrieve the inputs
            self.dialog.credit_row1 = r1
            self.dialog.credit_row2 = r2
            self.dialog.credit_row3 = r3
            self.figure_manager.view_update_credit_lines(r1, r2, r3)

    def view_mode_interface(self, show):
        self.minor_grid_check.setVisible(show)
        self.major_grid_check.setVisible(show)
        self.dots_check.setVisible(show)
        self.xs_check.setVisible(show)
        self.dot_trends_check.setVisible(show)
        self.x_trends_check.setVisible(show)
        self.timing_floor_check.setVisible(show)
        self.timing_grid_check.setVisible(show)
        self.phase_lines_check.setVisible(show)
        self.aims_check.setVisible(show)
        self.credit_lines_btn.setVisible(show)
        self.dot_lines_check.setVisible(show)
        self.x_lines_check.setVisible(show)
        self.dot_heading.setVisible(show)
        self.x_heading.setVisible(show)
        self.grid_heading.setVisible(show)
        self.other_heading.setVisible(show)
        self.x_color_check.setVisible(show)
        self.dot_color_check.setVisible(show)

    def setup_aim_mode(self):

        self.aim_target_label = QLabel('Note')
        self.aim_target_input = QLineEdit('')
        self.home_layout.addWidget(self.aim_target_label)
        self.home_layout.addWidget(self.aim_target_input)

        self.aim_label_y = QLabel('Target')
        self.aim_y_input = QLineEdit('')
        self.aim_y_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))
        self.home_layout.addWidget(self.aim_label_y)
        self.home_layout.addWidget(self.aim_y_input)

        # Start date
        self.aim_label_start_date = QLabel('Start')
        self.home_layout.addWidget(self.aim_label_start_date)
        self.aim_start_date_input = QDateEdit()
        self.aim_start_date_input.setDate(QDate.currentDate())
        self.aim_start_date_input.setCalendarPopup(True)
        self.aim_start_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.home_layout.addWidget(self.aim_start_date_input)

        # Deadlines date
        self.aim_label_end_date = QLabel('Deadline')
        self.home_layout.addWidget(self.aim_label_end_date)
        self.aim_end_date_input = QDateEdit()
        self.aim_end_date_input.setDate(QDate.currentDate())
        self.aim_end_date_input.setCalendarPopup(True)
        self.aim_end_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.home_layout.addWidget(self.aim_end_date_input)

        # Add and undo buttons
        self.add_aim_line_btn = QPushButton('Add')
        self.undo_aim_line_btn = QPushButton('Undo')
        aim_line_button_layout = QHBoxLayout()
        aim_line_button_layout.addWidget(self.add_aim_line_btn)
        aim_line_button_layout.addWidget(self.undo_aim_line_btn)
        self.home_layout.addLayout(aim_line_button_layout)

        self.add_aim_line_btn.clicked.connect(lambda: self.figure_manager.aim_from_form(
            self.aim_target_input.text(),
            self.aim_y_input.text(),
            self.aim_start_date_input.text(),
            self.aim_end_date_input.text()
        ))

        self.undo_aim_line_btn.clicked.connect(lambda: self.figure_manager.aim_undo())

        self.aim_mode_interface(False)

    def aim_mode_interface(self, show):
        self.aim_target_label.setVisible(show)
        self.aim_target_input.setVisible(show)
        self.add_aim_line_btn.setVisible(show)
        self.undo_aim_line_btn.setVisible(show)
        self.aim_label_y.setVisible(show)
        self.aim_y_input.setVisible(show)
        self.aim_label_start_date.setVisible(show)
        self.aim_start_date_input.setVisible(show)
        self.aim_label_end_date.setVisible(show)
        self.aim_end_date_input.setVisible(show)
        if not show:
            self.figure_manager.aim_cleanup()

    def setup_trend_mode(self):
        # Create trend radio group for corrects and errors
        self.trend_radio_dot = QRadioButton("Dots")
        self.trend_radio_x = QRadioButton("Xs")
        self.trend_radio_group = QButtonGroup()
        self.trend_radio_group.addButton(self.trend_radio_dot)
        self.trend_radio_group.addButton(self.trend_radio_x)
        self.trend_radio_dot.setChecked(True)
        self.home_layout.addWidget(self.trend_radio_dot)
        self.home_layout.addWidget(self.trend_radio_x)

        # Start date
        self.trend_label_start_date = QLabel('Date 1')
        self.home_layout.addWidget(self.trend_label_start_date)
        self.trend_start_date_input = QDateEdit()
        self.trend_start_date_input.setDate(QDate.currentDate())
        self.trend_start_date_input.setCalendarPopup(True)
        self.trend_start_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.home_layout.addWidget(self.trend_start_date_input)

        # End date
        self.trend_label_end_date = QLabel('Date 2')
        self.home_layout.addWidget(self.trend_label_end_date)
        self.trend_end_date_input = QDateEdit()
        self.trend_end_date_input.setDate(QDate.currentDate())
        self.trend_end_date_input.setCalendarPopup(True)
        self.trend_end_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.home_layout.addWidget(self.trend_end_date_input)

        # Add and undo buttons
        self.trend_add_btn = QPushButton('Add')
        self.trend_add_btn.setToolTip('Finalize trend (use Fit first)')
        self.trend_undo_btn = QPushButton('Undo')
        self.trend_fit_btn = QPushButton('Fit')
        trend_button_layout = QHBoxLayout()
        trend_button_layout.addWidget(self.trend_add_btn)
        trend_button_layout.addWidget(self.trend_fit_btn)
        trend_button_layout.addWidget(self.trend_undo_btn)
        self.home_layout.addLayout(trend_button_layout)

        self.trend_fit_btn.clicked.connect(
            lambda: (self.figure_manager.trend_fit(self.trend_radio_dot.isChecked()),
                     self.setFocus()))

        self.trend_add_btn.clicked.connect(lambda: self.figure_manager.trend_finalize(
            self.trend_radio_dot.isChecked(),
        ))

        self.trend_undo_btn.clicked.connect(lambda: self.figure_manager.trend_undo(
            self.trend_radio_dot.isChecked()
        ))

        # Relocate edit lines when updating dates
        self.trend_start_date_input.dateChanged.connect(self.figure_manager.trend_date1_changed)
        self.trend_end_date_input.dateChanged.connect(self.figure_manager.trend_date2_changed)

    def trend_mode_interface(self, show):
        self.trend_radio_dot.setVisible(show)
        self.trend_radio_x.setVisible(show)
        self.trend_label_start_date.setVisible(show)
        self.trend_start_date_input.setVisible(show)
        self.trend_label_end_date.setVisible(show)
        self.trend_end_date_input.setVisible(show)
        self.trend_add_btn.setVisible(show)
        self.trend_undo_btn.setVisible(show)
        self.trend_fit_btn.setVisible(show)
        if not show:
            self.figure_manager.trend_cleanup()

    def import_data(self, delete_data):
        # Open file dialog with support for CSV and Excel files
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select file', self.home_folder, 'CSV files (*.csv);;Excel files (*.xls *.xlsx);;ODS files (*.ods);;All files (*.*)')
        if file_path:
            self.figure_manager.fig_import_data(file_path)
            self.set_interaction_mode()  # Make sure current mode is enabled for key handling

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save file', self.home_folder, 'CSV files (*.csv);;Excel files (*.xls *.xlsx);;ODS files (*.ods);;All files (*.*)')
        if file_path:
            self.data_manager.create_export_file(file_path)

    def save_image(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save file', self.home_folder, 'PNG files (*.png);;All files (*.*)')
        if file_path:
            self.figure_manager.fig_save_image(file_path)

    def save_chart(self):
        file_path, _ = QFileDialog.getSaveFileName(self, 'Save file', self.home_folder, 'Pickle files (*.pkl);;All files (*.*)')
        if file_path:
            self.figure_manager.fig_save_chart(file_path)

    def load_chart(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Save file', self.home_folder, 'Pickle files (*.pkl);;All files (*.*)')
        if file_path:
            self.figure_manager.fig_load_chart(file_path)


app = QApplication(sys.argv)
window = ChartApp()
window.show()
sys.exit(app.exec_())


