
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QHBoxLayout, QPushButton, \
    QGroupBox, QRadioButton, QVBoxLayout, QLabel, QDateEdit, QFileDialog, QCheckBox, QComboBox, QMessageBox, QStackedWidget, QDialog, QSpacerItem, QSizePolicy, QStyle, QSpinBox, QColorDialog
from PyQt5.QtCore import Qt, QDate, QDir
from PyQt5.QtGui import QPainter, QColor, QPen, QFontMetrics

from FigureManager import FigureManager
from DataManager import DataManager
from support_classes import SaveImageDialog
import styles
import Modes as chart_mode


class TopPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()

        left_layout = QHBoxLayout()
        self.left_label = QLabel('iChart – Tester Version 0.2.0')
        self.left_label.setStyleSheet("color: #5a93cc; font-weight: bold;")
        self.left_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        left_layout.addWidget(self.left_label)
        left_layout.setContentsMargins(10, 0, 5, 0)
        layout.addLayout(left_layout)

        center_layout = QHBoxLayout()
        self.center_label = QLabel('Unnamed')
        self.center_label.setStyleSheet("color: #5a93cc; font-weight: bold;")
        self.center_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        center_layout.addStretch()
        center_layout.addWidget(self.center_label)
        center_layout.addStretch()
        layout.addLayout(center_layout)

        right_layout = QHBoxLayout()
        self.right_label = QLabel('Test version')
        self.right_label.setStyleSheet("color: #5a93cc; font-weight: bold;")
        self.right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right_layout.addWidget(self.right_label)
        right_layout.setContentsMargins(5, 0, 10, 0)  # Add margins around the right label
        layout.addLayout(right_layout)

        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw bottom border
        rect = self.rect()
        painter.setPen(QPen(QColor('#5a93cc'), 2))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())

    def update_left_label(self, text):
        self.left_label.setText(text)

    def update_center_label(self, text):
        self.center_label.setText(text)

    def update_right_label(self, text):
        self.right_label.setText(text)


class ChartApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Initialize and add the Matplotlib widget to the right panel
        self.data_manager = DataManager()
        self.figure_manager = FigureManager(self)

        # Setup interaction handling
        self.current_connection = None
        self.previous_mode = None
        self.loaded_chart_path = None
        self.manual_mode_widget = None

        # Initialize the main window properties
        self.setWindowTitle('iChart')

        # Create and set the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a vertical layout as the main layout wrapper
        self.wrapper_layout = QVBoxLayout(self.central_widget)

        # Create and add the custom top panel
        self.top_panel = TopPanel()
        self.wrapper_layout.addWidget(self.top_panel)

        # Add spacer item below the top panel
        spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.wrapper_layout.addItem(spacer)

        self.main_layout = QHBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)

        # Initialize EventHandlers
        self.event_handlers = EventHandlers(self, self.figure_manager, self.data_manager, self.top_panel)

        # Initialize the tabs for the left panel
        self.tabs = QTabWidget()

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

        # Set dynamic width for the QTabWidget
        self.set_dynamic_tab_width()

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
        self.current_connection = None
        self.xy_coord = None

        # Test
        self.top_panel.update_right_label(self.data_manager.user_preferences['chart_type'])

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
        self.set_manual_mode_widget()  # Initial manual mode widget
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
        btn_import_delete.setToolTip('Replot data from xls, xlsx, ods, or csv')
        btn_export = QPushButton("Export")
        btn_export.setToolTip('Export data as csv')
        layout_data.addWidget(btn_import_delete)

        layout_data.addWidget(btn_export)
        group_box_data.setLayout(layout_data)
        files_layout.addWidget(group_box_data)

        # Chart GroupBox
        group_box_chart = QGroupBox("Chart")
        layout_chart = QVBoxLayout()
        btn_new = QPushButton('New')
        btn_load = QPushButton('Load')
        btn_load.setToolTip('Load data and chart configs from json')
        btn_save = QPushButton('Save')
        btn_save.setToolTip('Save data and chart configs as json')
        btn_image = QPushButton('Get image')
        btn_image.setToolTip('Save chart as png file.')
        layout_chart.addWidget(btn_new)
        layout_chart.addWidget(btn_load)
        layout_chart.addWidget(btn_save)
        layout_chart.addWidget((btn_image))
        group_box_chart.setLayout(layout_chart)
        files_layout.addWidget(group_box_chart)

        # Button connections
        btn_import_delete.clicked.connect(self.event_handlers.import_data)
        btn_export.clicked.connect(self.event_handlers.export_data)
        # btn_new.clicked.connect(self.figure_manager.back_to_default)
        btn_new.clicked.connect(self.files_show_dialog)
        btn_image.clicked.connect(self.event_handlers.save_image)
        btn_save.clicked.connect(self.event_handlers.save_chart)
        btn_load.clicked.connect(self.event_handlers.load_chart)

        files_layout.addStretch()  # Prevents the buttons from vertically filling the whole panel

    def files_show_dialog(self):
        # Create a QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle("New chart")
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
        settings_zero_count_handling.addItem('Place below floor', True)
        settings_zero_count_handling.addItem('Do not show', False)

        # Set default selection based on bool_type
        if self.data_manager.user_preferences['place_below_floor']:
            settings_zero_count_handling.setCurrentIndex(0)  # Select 'Place below floor'
        else:
            settings_zero_count_handling.setCurrentIndex(1)  # Select 'Do not show'

        preferences_group_layout.addWidget(settings_zero_count_handling_label)
        preferences_group_layout.addWidget(settings_zero_count_handling)

        settings_zero_count_handling.currentIndexChanged.connect(
            lambda index: self.event_handlers.update_zero_count_handling(settings_zero_count_handling.itemData(index))
        )

        settings_layout.addWidget(preferences_group)

        # Set chart aggregation
        settings_data_agg_label = QLabel('Data aggregation')
        self.settings_data_agg = QComboBox()
        self.settings_data_agg.addItem('Sum', 'sum')
        self.settings_data_agg.addItem('Mean', 'mean')
        self.settings_data_agg.addItem('Median', 'median')

        # Load preference
        current_value = self.data_manager.user_preferences['chart_data_agg']
        index = self.settings_data_agg.findData(current_value)
        if index != -1:
            self.settings_data_agg.setCurrentIndex(index)

        preferences_group_layout.addWidget(settings_data_agg_label)
        preferences_group_layout.addWidget(self.settings_data_agg)
        self.settings_data_agg.currentIndexChanged.connect(self.event_handlers.on_agg_current_index_changed)


        # Add button below the start date dropdown
        path_label = QLabel('Default folder')
        preferences_group_layout.addWidget(path_label)
        self.settings_folder_btn = QPushButton(self.data_manager.user_preferences['home_folder'])
        self.settings_folder_btn.setStyleSheet("text-align: right;")
        self.settings_folder_btn.setToolTip(self.data_manager.user_preferences['home_folder'])
        self.settings_folder_btn.clicked.connect(self.event_handlers.set_data_folder)
        preferences_group_layout.addWidget(self.settings_folder_btn)

        # Create a group for Other settings
        other_settings_group = QGroupBox("Other")
        other_settings_layout = QVBoxLayout()
        other_settings_group.setLayout(other_settings_layout)
        settings_test_angle_check = QCheckBox('Test angle')
        other_settings_layout.addWidget(settings_test_angle_check)
        settings_test_angle_check.stateChanged.connect(self.event_handlers.test_angle)

        # Create group for Chart types
        chart_type_settings_group = QGroupBox('Chart')
        chart_type_settings_layout = QVBoxLayout()
        chart_type_settings_group.setLayout(chart_type_settings_layout)
        self.chart_type_settings_dropdown = QComboBox()
        self.chart_type_settings_dropdown.addItem('DailyMinute', 'DailyMinute')  # Adding item with data
        self.chart_type_settings_dropdown.addItem('Daily', 'Daily')
        self.chart_type_settings_dropdown.addItem('WeeklyMinute', 'WeeklyMinute')
        self.chart_type_settings_dropdown.addItem('Weekly', 'Weekly')
        self.chart_type_settings_dropdown.addItem('MonthlyMinute', 'MonthlyMinute')
        self.chart_type_settings_dropdown.addItem('Monthly', 'Monthly')
        chart_type_settings_layout.addWidget(self.chart_type_settings_dropdown)

        # Load chart preference
        chart_type = self.data_manager.user_preferences['chart_type']
        index = self.chart_type_settings_dropdown.findData(chart_type)
        if index != -1:
            self.chart_type_settings_dropdown.setCurrentIndex(index)
        self.chart_type_settings_dropdown.currentIndexChanged.connect(self.event_handlers.change_chart_type)
        settings_layout.addWidget(chart_type_settings_group)

        # Set start date
        start_date_label = QLabel('Set start date')
        chart_type_settings_layout.addWidget(start_date_label)
        self.start_date_input = QDateEdit()
        self.start_date_input.setDate(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat("dd-MM-yyyy")  # Custom format
        self.start_date_input.dateChanged.connect(self.event_handlers.change_start_date)
        chart_type_settings_layout.addWidget(self.start_date_input)
        settings_layout.addWidget(other_settings_group)

        # SpinBox for chart size
        chart_size_label = QLabel("Width (6 - 12)")
        self.chart_size_spinbox = QSpinBox()
        self.chart_size_spinbox.setRange(6, 12)  # Set the range as required
        self.chart_size_spinbox.setValue(self.data_manager.user_preferences.get('Width', 0))
        self.chart_size_spinbox.setValue(self.data_manager.user_preferences['width'])
        self.chart_size_spinbox.valueChanged.connect(self.event_handlers.change_width)
        chart_type_settings_layout.addWidget(chart_size_label)
        chart_type_settings_layout.addWidget(self.chart_size_spinbox)

        # Label for the font color button
        chart_font_color_label = QLabel("Colors")
        chart_type_settings_layout.addWidget(chart_font_color_label)
        self.chart_font_color_button = QPushButton("Font")
        chart_type_settings_layout.addWidget(self.chart_font_color_button)
        self.chart_font_color_button.clicked.connect(lambda: self.event_handlers.choose_color(color_category='chart_font_color'))

        # Label for the font color button
        self.chart_grid_color_button = QPushButton("Grid")
        chart_type_settings_layout.addWidget(self.chart_grid_color_button)
        self.chart_grid_color_button.clicked.connect(lambda: self.event_handlers.choose_color(color_category='chart_grid_color'))

        # Push everything to the top
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
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.phase_click)
        elif self.radio_trend.isChecked():
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.trend_click)
        elif self.radio_aim.isChecked():
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.aim_click)

    def trend_adjust_dates(self):
        date, order = self.figure_manager.trend_adjust_dates()
        if order == 'first':
            self.trend_mode_widget.trend_start_date_input.setDate(QDate(date.year, date.month, date.day))
        elif order == 'second':
            self.trend_mode_widget.trend_end_date_input.setDate(QDate(date.year, date.month, date.day))

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

    def closeEvent(self, event):
        # Stuff to do before closing application
        # Save current preferences
        self.data_manager.save_user_preferences()

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
                self.event_handlers.save_chart(self.loaded_chart_path)
                event.accept()  # Proceed with the window close
            elif reply == QMessageBox.No:
                event.accept()  # Proceed with the window close without saving
            else:
                event.ignore()  # Ignore the close event
        else:
            event.accept()  # Proceed with the window close if no chart is loaded

    def set_manual_mode_widget(self):
        """Change the manual mode widget to a new instance of the specified class."""
        if self.manual_mode_widget is not None:
            # Remove the current widget from the stacked widget
            index = self.stacked_widget.indexOf(self.manual_mode_widget)
            if index != -1:
                self.stacked_widget.removeWidget(self.manual_mode_widget)
        else:
            index = 1  # Assuming the manual mode widget is the second widget in the stack

        # Create a new instance of the specified class
        chart_type = self.data_manager.user_preferences['chart_type']
        if chart_type == 'DailyMinute':
            self.manual_mode_widget = chart_mode.ManualModeWidgetDailyMinute(self.figure_manager)
        elif chart_type == 'Daily':
            self.manual_mode_widget = chart_mode.ManualModeWidgetDaily(self.figure_manager)
        elif chart_type == 'WeeklyMinute':
            self.manual_mode_widget = chart_mode.ManualModeWidgetWeeklyMinute(self.figure_manager)
        elif chart_type == 'Weekly':
            self.manual_mode_widget = chart_mode.ManualModeWidgetWeekly(self.figure_manager)
        elif chart_type == 'Monthly':
            self.manual_mode_widget = chart_mode.ManualModeWidgetMonthly(self.figure_manager)
        elif chart_type == 'MonthlyMinute':
            self.manual_mode_widget = chart_mode.ManualModeWidgetMonthlyMinute(self.figure_manager)
        else:
            print('Unable to find chart type')
            self.manual_mode_widget = chart_mode.ManualModeWidgetDailyMinute(self.figure_manager)

        # Add the new widget to the stacked widget
        self.stacked_widget.insertWidget(index, self.manual_mode_widget)

        # Reconnect the radio button to the new widget
        self.radio_manual.toggled.connect(lambda checked: self.change_mode(index) if checked else None)

    def set_dynamic_tab_width(self):
        font_metrics = QFontMetrics(self.tabs.font())
        total_width = 0

        # Calculate the width for each tab
        for i in range(self.tabs.count()):
            tab_text = self.tabs.tabText(i)
            tab_width = font_metrics.width(tab_text) + self.tabs.style().pixelMetric(QStyle.PM_TabBarTabHSpace)
            total_width += tab_width

        # Add padding for the overall tab widget
        total_width += self.tabs.style().pixelMetric(QStyle.PM_TabBarTabHSpace)
        total_width -= 23

        self.tabs.setFixedWidth(total_width)

class EventHandlers:
    def __init__(self, chart_app, figure_manager, data_manager, top_panel):
        self.chart_app = chart_app
        self.figure_manager = figure_manager
        self.data_manager = data_manager
        self.top_panel = top_panel  # Accept the TopPanel instance

    def change_mode(self, index):
        pass

    def import_data(self, delete_data):
        # Open file dialog with support for CSV and Excel files
        file_path, _ = QFileDialog.getOpenFileName(self.chart_app, 'Select file', self.data_manager.user_preferences['home_folder'], 'CSV files (*.csv);;Excel files (*.xls *.xlsx);;ODS files (*.ods);;All files (*.*)')
        if file_path:
            self.figure_manager.fig_import_data(file_path)
            self.chart_app.set_interaction_mode()  # Make sure current mode is enabled for key handling

        # Display name of file imported
        file_name = os.path.basename(file_path)
        self.top_panel.update_center_label(file_name)

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self.chart_app, 'Save file', self.data_manager.user_preferences['home_folder'],
                                                   'CSV files (*.csv);;Excel files (*.xls *.xlsx);;ODS files (*.ods);;All files (*.*)')
        if file_path:
            self.data_manager.create_export_file(file_path)

    def files_show_dialog(self):
        pass

    def save_image(self):
        dialog = SaveImageDialog(self.chart_app)
        if dialog.exec_() == QDialog.Accepted:
            format_selected, resolution_selected = dialog.get_selected_options()
            options = f"{format_selected.upper()} files (*.{format_selected});;All files (*.*)"
            file_path, _ = QFileDialog.getSaveFileName(self.chart_app, 'Save file', self.data_manager.user_preferences['home_folder'], options)
            if file_path:
                self.figure_manager.fig_save_image(file_path, format=format_selected, dpi=resolution_selected)

    def save_chart(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(self.chart_app, 'Save file',
                                                       self.data_manager.user_preferences['home_folder'],
                                                       'JSON files (*.json);;All files (*.*)')
        if file_path:
            self.chart_app.loaded_chart_path = file_path
            self.data_manager.save_chart(file_path, self.figure_manager.Chart.start_date)

        # Display name of chart saved
        file_name = os.path.basename(file_path)
        self.top_panel.update_center_label(file_name)

    def load_chart(self):
        file_path, _ = QFileDialog.getOpenFileName(self.chart_app, 'Open file',
                                                   self.data_manager.user_preferences['home_folder'],
                                                   'JSON files (*.json);;All files (*.*)')
        if file_path:
            self.chart_app.loaded_chart_path = file_path
            self.figure_manager.fig_load_chart(file_path)

        # Display name of chart imported
        file_name = os.path.basename(file_path)
        self.top_panel.update_center_label(file_name)

    def update_zero_count_handling(self, bool_type):
        self.data_manager.user_preferences['place_below_floor'] = bool_type
        self.figure_manager.new_chart(self.data_manager.chart_data['start_date'])

    def set_data_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self.chart_app, "Select Folder", QDir.homePath())
        if folder_path:
            self.chart_app.settings_folder_btn.setText(folder_path)
            self.chart_app.settings_folder_btn.setToolTip(folder_path)
            self.data_manager.user_preferences['home_folder'] = folder_path

    def on_agg_current_index_changed(self, index):
        self.data_manager.user_preferences.update({'chart_data_agg': self.chart_app.settings_data_agg.itemData(index)})
        self.figure_manager.change_chart_type(self.data_manager.chart_data['type'])

    def settings_test_angle(self, state):
        pass

    def change_chart_type(self, index):
        self.figure_manager.change_chart_type(self.chart_app.chart_type_settings_dropdown.itemData(index)),
        self.chart_app.set_manual_mode_widget()
        # Update top panel with chart type
        self.top_panel.update_right_label(self.data_manager.user_preferences['chart_type'])

        # Make sure current mode is enabled for key handling
        self.chart_app.set_interaction_mode()

        # Update timing and floor checkboxes
        self.chart_app.view_mode_widget.update_timing_checkboxes()

    def change_start_date(self, new_date):
        self.figure_manager.settings_change_start_date(new_date)
        self.chart_app.set_interaction_mode()

    def change_width(self, new_width):
        self.data_manager.user_preferences['width'] = new_width
        self.figure_manager.settings_change_chart_width()
        self.chart_app.set_interaction_mode()

    def phase_click(self, event):
        # Update phase line form
        coordinates = self.figure_manager.phase_line_handle_click(event, self.chart_app.phase_mode_widget.phase_change_input.text())
        if coordinates:  # In case the user clicked outside the graph
            x, y = coordinates
            self.chart_app.phase_mode_widget.phase_y_input.setText(str(y))
            date = self.figure_manager.x_to_date[x]
            date_qt = QDate(date.year, date.month, date.day)
            self.chart_app.phase_mode_widget.phase_date_input.setDate(date_qt)

    def aim_click(self, event):
        coordinates = self.figure_manager.aim_click_info(event, self.chart_app.aim_mode_widget.aim_target_input.text())
        if coordinates:
            d1, d2, y = coordinates
            self.chart_app.aim_mode_widget.aim_y_input.setText(str(y))
            self.chart_app.aim_mode_widget.aim_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
            self.chart_app.aim_mode_widget.aim_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

    def trend_click(self, event):
        self.figure_manager.trend_on_click(event)
        self.chart_app.trend_adjust_dates()

    def test_angle(self, show):
        self.figure_manager.settings_test_angle(show)

    def choose_color(self, color_category):
        # Convert the stored color code to a QColor object
        initial_color = QColor(self.data_manager.user_preferences[color_category])
        QColorDialog.setCustomColor(0, QColor('#5ac9e2'))  # Behavior & Research Company hex
        QColorDialog.setCustomColor(1, QColor('#71B8FF'))
        QColorDialog.setCustomColor(2, QColor('#5a93cc'))
        color = QColorDialog.getColor(initial_color)

        if color.isValid():
            self.data_manager.user_preferences[color_category] = color.name()
            self.figure_manager.update_chart()
            self.chart_app.set_interaction_mode()


app = QApplication(sys.argv)
app.setStyleSheet(styles.general_stylesheet)
window = ChartApp()
window.show()
sys.exit(app.exec_())


