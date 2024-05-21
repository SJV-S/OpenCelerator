
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QGroupBox, QRadioButton, QVBoxLayout, QLineEdit, QLabel, QDateEdit, QListWidget, QFileDialog, QCheckBox, QButtonGroup, QDialog, QComboBox, QMessageBox, QGridLayout, QStackedWidget
from PyQt5.QtGui import QDoubleValidator, QFont
from PyQt5.QtCore import Qt, QDate

from FigureManager import FigureManager
from DataManager import DataManager
import Modes as chart_mode


class ChartApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize and add the Matplotlib widget to the right panel
        self.data_manager = DataManager()
        self.figure_manager = FigureManager(self)

        # Initialize the main window properties
        self.setWindowTitle('iChart')

        # Create and set the central widget and layout
        self.central_widget = QWidget()
        # self.central_widget.setObjectName("centralWidget")  # Assign object name
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Initialize the tabs for the left panel
        self.tabs = QTabWidget()
        self.tabs.setFixedWidth(176)
        self.main_layout.addWidget(self.tabs)
        self.tab_home = QWidget()
        self.files_tab = QWidget()
        self.tab_settings = QWidget()

        # Set up home tab
        self.home_layout = QVBoxLayout()  # Main layout for the home tab
        self.main_layout.addWidget(self.figure_manager)

        # Setup tabs
        self.setup_home_tab()
        self.setup_file_tab()
        self.setup_settings_tab()

        # Add tabs to the tab widget
        self.tabs.addTab(self.tab_home, 'Home')
        self.tabs.addTab(self.files_tab, 'Files')
        self.tabs.addTab(self.tab_settings, 'Settings')

        # Setup interaction handling
        self.current_connection = None
        self.previous_mode = None
        self.loaded_chart_path = None

        # Setup Radio Buttons
        # self.radio_view.setChecked(True)
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
        self.home_folder = os.path.expanduser("~")
        self.current_connection = None
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

    def change_mode(self, index):
        """Change the currently visible widget in the stack."""
        self.previous_mode = self.stacked_widget.currentIndex()
        self.stacked_widget.setCurrentIndex(index)
        self.set_interaction_mode()

        # To make keybindings work
        self.currentMode = self.mode_dict[index]

        # Cleanup edit objects from previous mode
        if self.previous_mode == 2:
            self.figure_manager.phase_cleanup_temp_line()
        elif self.previous_mode == 3:
            self.figure_manager.aim_cleanup()
        elif self.previous_mode == 4:
            self.figure_manager.trend_cleanup()

    def setup_home_tab(self):
        self.home_layout = QVBoxLayout(self.tab_home)  # Ensure this is the layout for tab_home

        # Setup group box for mode selection
        mode_selection_layout = QVBoxLayout()
        group_box_mode = QGroupBox("Mode")
        group_box_mode.setLayout(mode_selection_layout)

        # Radio buttons for mode selection
        self.radio_view = QRadioButton("View")
        self.radio_manual = QRadioButton("Entry")
        self.radio_phase = QRadioButton("Phase")
        self.radio_aim = QRadioButton("Aim")
        self.radio_trend = QRadioButton('Trend')
        self.radio_view.setChecked(True)  # Default to view mode

        # Add radio buttons to the group box layout
        mode_selection_layout.addWidget(self.radio_view)
        mode_selection_layout.addWidget(self.radio_manual)
        mode_selection_layout.addWidget(self.radio_phase)
        mode_selection_layout.addWidget(self.radio_aim)
        mode_selection_layout.addWidget(self.radio_trend)

        self.mode_dict = {0: 'view',
                          1: 'manual',
                          2: 'phase',
                          3: 'aim',
                          4: 'trend'}

        # Add group box to the home tab layout
        self.home_layout.addWidget(group_box_mode)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()
        self.home_layout.addWidget(self.stacked_widget)

        # Create and add widgets for each mode
        self.view_mode_widget = chart_mode.ViewModeWidget(self.figure_manager)
        self.manual_mode_widget = chart_mode.ManualModeWidget(self.figure_manager)
        self.phase_mode_widget = chart_mode.PhaseModeWidget(self.figure_manager)
        self.aim_mode_widget = chart_mode.AimModeWidget(self.figure_manager)
        self.trend_mode_widget = chart_mode.TrendModeWidget(self.figure_manager)
        self.stacked_widget.addWidget(self.view_mode_widget)
        self.stacked_widget.addWidget(self.manual_mode_widget)
        self.stacked_widget.addWidget(self.phase_mode_widget)
        self.stacked_widget.addWidget(self.aim_mode_widget)
        self.stacked_widget.addWidget(self.trend_mode_widget)

        # Ensure any other mode widgets are managed in terms of visibility or dynamically added/removed
        self.radio_view.toggled.connect(lambda checked: self.change_mode(0) if checked else None)
        self.radio_manual.toggled.connect(lambda checked: self.change_mode(1) if checked else None)
        self.radio_phase.toggled.connect(lambda checked: self.change_mode(2) if checked else None)
        self.radio_aim.toggled.connect(lambda checked: self.change_mode(3) if checked else None)
        self.radio_trend.toggled.connect(lambda checked: self.change_mode(4) if checked else None)

        # Stretch at the bottom to push everything up
        self.home_layout.addStretch(1)

        # Apply the layout to the home tab
        self.tab_home.setLayout(self.home_layout)

    def setup_file_tab(self):
        files_layout = QVBoxLayout()  # Create a QVBoxLayout instance
        self.files_tab.setLayout(files_layout)  # Set the layout to files_tab

        # Data GroupBox
        group_box_data = QGroupBox("Data")
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
        layout_chart = QVBoxLayout()
        btn_new = QPushButton('New')
        btn_load = QPushButton('Load')
        btn_save = QPushButton('Save')
        btn_save.setToolTip('Automatically saves upon closing.')
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

        if response == QMessageBox.Yes:
            self.loaded_chart_path = None  # Prevents from accidentally saving default chart
            self.figure_manager.back_to_default()

    def setup_settings_tab(self):
        # Create settings layout
        settings_layout = QVBoxLayout()
        self.tab_settings.setLayout(settings_layout)

        # Create a group for preferences
        preferences_group = QGroupBox("Preferences")
        preferences_group_layout = QVBoxLayout()
        preferences_group.setLayout(preferences_group_layout)

        # Zero counts below timing floor or don't display
        settings_zero_count_handling_label = QLabel('Zero counts')
        settings_zero_count_handling = QComboBox()
        settings_zero_count_handling.setToolTip('Set before importing data')
        settings_zero_count_handling.addItem('Place below floor')
        settings_zero_count_handling.addItem('Do not show')
        preferences_group_layout.addWidget(settings_zero_count_handling_label)
        preferences_group_layout.addWidget(settings_zero_count_handling)
        settings_zero_count_handling.currentIndexChanged.connect(
            lambda index: setattr(self.data_manager, 'place_zero_counts_below_floor',
                                  settings_zero_count_handling.itemText(index) == 'Place below floor')
        )
        settings_layout.addWidget(preferences_group)

        # # Set image quality
        settings_image_quality_label = QLabel('Image quality')
        settings_image_quality = QComboBox()
        settings_image_quality.addItem('High (300 dpi)', 300)  # Adding item with data
        settings_image_quality.addItem('Medium (200 dpi)', 200)
        settings_image_quality.addItem('Low (100 dpi)', 100)
        settings_image_quality.setCurrentIndex(1)
        preferences_group_layout.addWidget(settings_image_quality_label)
        preferences_group_layout.addWidget(settings_image_quality)
        settings_image_quality.currentIndexChanged.connect(
            lambda index: setattr(self.figure_manager, 'dpi', settings_image_quality.itemData(index)))

        # # Set start date
        start_date_label = QLabel('Set start date')
        preferences_group_layout.addWidget(start_date_label)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.start_date_input.dateChanged.connect(
            lambda new_date: (self.figure_manager.settings_change_start_date(new_date), self.set_interaction_mode()))
        preferences_group_layout.addWidget(self.start_date_input)

        # Create a group for Other settings
        other_settings_group = QGroupBox("Other")
        other_settings_layout = QVBoxLayout()
        other_settings_group.setLayout(other_settings_layout)

        # Test angle
        settings_test_angle_check = QCheckBox('Test angle')
        other_settings_layout.addWidget(settings_test_angle_check)
        settings_test_angle_check.stateChanged.connect(self.figure_manager.settings_test_angle)

        settings_layout.addWidget(other_settings_group)

        #
        # # Push everything to the top
        settings_layout.addStretch()

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
        coordinates = self.figure_manager.aim_click_info(event, self.aim_mode_widget.aim_target_input.text())
        if coordinates:
            d1, d2, y = coordinates
            self.aim_mode_widget.aim_y_input.setText(str(y))
            self.aim_mode_widget.aim_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
            self.aim_mode_widget.aim_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

    def trend_adjust_dates(self):
        if self.figure_manager.trend_current_temp_marker == 'first':
            x1 = self.figure_manager.trend_temp_first_marker.get_xdata()[0]
            d1 = self.figure_manager.x_to_date[x1]
            self.trend_mode_widget.trend_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
        elif self.figure_manager.trend_current_temp_marker == 'second':
            x2 = self.figure_manager.trend_temp_second_marker.get_xdata()[0]
            d2 = self.figure_manager.x_to_date[x2]
            self.trend_mode_widget.trend_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

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
        coordinates = self.figure_manager.phase_line_handle_click(event, self.phase_mode_widget.phase_change_input.text())
        if coordinates:  # In case the user clicked outside the graph
            x, y = coordinates
            self.phase_mode_widget.phase_y_input.setText(str(y))
            date = self.figure_manager.x_to_date[x]
            date_qt = QDate(date.year, date.month, date.day)
            self.phase_mode_widget.phase_date_input.setDate(date_qt)

    def sync_view_settings(self):
        # Set checkboxes (will only run here if there's a change, so unreliable)
        settings = self.data_manager.chart_data['view_check']
        self.view_mode_widget.minor_grid_check.setChecked(settings['minor_grid'])
        self.view_mode_widget.major_grid_check.setChecked(settings['major_grid'])
        self.view_mode_widget.dots_check.setChecked(settings['dots'])
        self.view_mode_widget.xs_check.setChecked(settings['xs'])
        self.view_mode_widget.dot_trends_check.setChecked(settings['dot_trends'])
        self.view_mode_widget.x_trends_check.setChecked(settings['x_trends'])
        self.view_mode_widget.timing_floor_check.setChecked(settings['timing_floor'])
        self.view_mode_widget.timing_grid_check.setChecked(settings['timing_grid'])
        self.view_mode_widget.phase_lines_check.setChecked(settings['phase_lines'])
        self.view_mode_widget.aims_check.setChecked(settings['aims'])

        dot_bool = False if settings['dot_color'] == 'black' else True
        x_bool = False if settings['x_color'] == 'black' else True
        self.view_mode_widget.dot_color_check.setChecked(dot_bool)
        self.view_mode_widget.x_color_check.setChecked(x_bool)

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
            self.loaded_chart_path = file_path
            self.figure_manager.fig_save_chart(file_path)

    def load_chart(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Save file', self.home_folder, 'Pickle files (*.pkl);;All files (*.*)')
        if file_path:
            self.loaded_chart_path = file_path
            self.figure_manager.fig_load_chart(file_path)

    from PyQt5.QtWidgets import QMessageBox

    def closeEvent(self, event):
        # Handle the window closing event to check if the chart needs to be saved. Overrides built-in function
        if self.loaded_chart_path:
            # Extract the file name from the path
            file_name = os.path.splitext(os.path.basename(self.loaded_chart_path))[0]

            # Create a message box to confirm if the user wants to save the chart
            reply = QMessageBox.question(self, 'Save Chart',
                                         f"Save {file_name} before closing?",
                                         QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                         QMessageBox.Cancel)

            if reply == QMessageBox.Yes:
                # Save the chart to the loaded path before closing
                self.figure_manager.fig_save_chart(self.loaded_chart_path)
                event.accept()  # Proceed with the window close
            elif reply == QMessageBox.No:
                event.accept()  # Proceed with the window close without saving
            else:
                event.ignore()  # Ignore the close event
        else:
            event.accept()  # Proceed with the window close if no chart is loaded


stylesheet = '''
/* Global styles for all widgets adapta blue: #00bcd4 */
QWidget {
}
/* QMainWindow styles */
QMainWindow {
    background-color: white;
}
/* QPushButton styles */
QPushButton {
    margin-top: 5px;
    border: 1px solid #5a93cc;
    padding: 5px;
    background-color: white;
    border-radius: 5px;
}
QPushButton:hover {
    background-color: #e7efff;
}
/* QRadioButton styles */
QRadioButton {
    margin: 5px;
}
/* QLabel styles */
QLabel {
    margin: 0px;
}
/* QLineEdit styles */
QLineEdit {
    border: 1px solid gray;
    padding: 4px;
    margin 0px;
}
/* QCheckBox styles */
QCheckBox {
    margin: 5px;
}

/* QGroupBox styles */
QGroupBox {
    border: 1px solid silver;
    border-radius: 5px;
    margin-top: 20px; /* Space above the group box */
    font-weight: bold;
    color: #5a93cc;
}
/* QGroupBox Title styles */
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center; /* Center the title */
    padding: 0 3px;
}
/* QTabWidget styles */
QTabWidget::pane {
    border: 1px solid #5a93cc;
    margin-top: 0px;
    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
}
QTabWidget::tab-bar {
}
/* Styling for individual tabs */
QTabBar::tab {
    background: white;
    padding: 5 11 5 11px;
    border: 0px solid #5a93cc;
    border-bottom-color: transparent;  /* Makes the bottom border of the tab invisible */
}
/* Styling for the first tab */
QTabBar::tab:first {
    border-top-left-radius: 10px;  /* Rounds the top left corner of the first tab */
    border-top: 1px solid #5a93cc;
    border-left: 1px solid #5a93cc;
    border-right: 1px solid #5a93cc;
}
/* Styling for the last tab */
QTabBar::tab:second {
    border-top: 1px solid #5a93cc;
}
/* Styling for the last tab */
QTabBar::tab:last {
    border-top: 1px solid #5a93cc;
    border-left: 1px solid #5a93cc;
    border-right: 1px solid #5a93cc;
    border-top-right-radius: 10px;  /* Rounds the top right corner of the last tab */
}
/* Styling for selected and hovered tabs */
QTabBar::tab:selected, QTabBar::tab:hover {
    background: #e7efff;
}
/* QDateEdit styles */
QDateEdit {
    border: 1px solid gray;
    padding: 3px;
}
/* QListWidget styles */
QListWidget {
    border: 1px solid gray;
    padding: 5px;
}
/* QDialog styles */
QDialog {
    background-color: #f0f0f0;
}
/* QComboBox styles */
QComboBox {
    border: 1px solid gray;
    padding: 3px;
}
/* QFileDialog styles */
QFileDialog {
    background-color: #f0f0f0;
}
/* QMessageBox styles */
QMessageBox {
    background-color: #f0f0f0;
}
'''

app = QApplication(sys.argv)
app.setStyleSheet(stylesheet)
window = ChartApp()
window.show()
sys.exit(app.exec_())


