from PySide6 import QtCore  # Must be at the top of the script

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QHBoxLayout, QPushButton, QGroupBox,
                               QVBoxLayout, QLabel, QFileDialog, QCheckBox, QComboBox, QMessageBox,
                               QStackedWidget, QDialog, QSpacerItem, QSizePolicy, QSpinBox, QColorDialog, QListWidget,
                               QListWidgetItem)
from PySide6.QtCore import Qt, QDate, QDir
from PySide6.QtGui import QPainter, QColor, QIcon, QPixmap

import sys
import os
from FigureManager import FigureManager
from DataManager import DataManager
from Popups import SaveImageDialog, StartDateDialog, SupportDevDialog
import styles
import Modes as chart_mode
import warnings

# For generating error reports
import error_logging
logger = error_logging.logger

# Only uncomment for Windows splash screen
# import tempfile
# if "NUITKA_ONEFILE_PARENT" in os.environ:
#     splash_filename = os.path.join(
#         tempfile.gettempdir(),
#         "onefile_%d_splash_feedback.tmp" % int(os.environ["NUITKA_ONEFILE_PARENT"]),
#     )
#     if os.path.exists(splash_filename):
#         os.unlink(splash_filename)
# print("Splash Screen has been removed")


# I had to use Y and M instead of YE and ME because the executable won't currently run with YE and ME
warnings.filterwarnings(action='ignore', category=FutureWarning, message=".*'Y' is deprecated.*")
warnings.filterwarnings(action='ignore', category=FutureWarning, message=".*'M' is deprecated.*")


class ChartApp(QMainWindow):
    def __init__(self):
        super().__init__()
        # Define a custom data role
        self.FullFilePathRole = Qt.ItemDataRole.UserRole

        # Initialize and add the Matplotlib widget to the right panel
        self.data_manager = DataManager()
        self.figure_manager = FigureManager(self)

        # Setup interaction handling
        self.current_connection = None
        self.previous_mode = None
        self.loaded_chart_path = None
        self.manual_mode_widget = None
        # Initialize the main window properties
        self.window_title_str = 'iChart v0.6.0'
        self.setWindowTitle(self.window_title_str)
        self.setWindowIcon(QIcon(':/images/ichart_logo_no_text.svg'))
        
        # Create and set the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a vertical layout as the main layout wrapper
        self.wrapper_layout = QVBoxLayout(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)

        # Initialize EventHandlers
        self.event_handlers = EventHandlers(self, self.figure_manager, self.data_manager)

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
        self.tabs.addTab(self.tab_settings, 'Config')

        # Set view interaction mode
        self.mode = 0  # View mode by default
        selected = '#05c3de'
        self.button_view.setStyleSheet(self.get_mode_button_style(selected))
        self.set_interaction_mode()

        # Define the key press handling methods for different modes
        self.keyHandlers = {
            'view': self.handleViewKeyPress,
            # 'manual': self.handleManualKeyPress,
            'phase': self.handlePhaseKeyPress
        }
        self.currentMode = 'view'  # Start in Manual mode by default

        # Enable key event handling
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()  # Set focus to the main window

        # Control variables
        self.current_connection = None
        self.xy_coord = None
        self.save_preferences_upon_close = True

    def support_dev_btn_clicked(self):
        dialog = SupportDevDialog()
        dialog.exec()

    # def handleManualKeyPress(self, event):
    #     if event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
    #         self.manual.handle_key_press(event)
    #         self.manual_update_xy_pos_label()
    #     elif event.key() == Qt.Key_Return:
    #         self.manual.finalize_point()

    def handlePhaseKeyPress(self, event):
        # Implement specific key handling for Phase mode if needed
        pass

    def handleViewKeyPress(self, event):
        # Minimal or no key handling for View mode if needed
        pass

    def get_mode_button_style(self, background_color='#e7efff'):
        button_style = f"""
            QPushButton {{
                background-color: {background_color};
                border: 0px solid lightblue;
                border-radius: 0px;
                margin: 0px;
                padding: 5px;
                font-style: normal;
            }}
            QPushButton:hover {{
                background-color: #96deeb;
            }}
        """
        return button_style

    def change_mode(self, index):
        # Change the currently visible widget in the stack.
        self.previous_mode = self.stacked_widget.currentIndex()
        self.stacked_widget.setCurrentIndex(index)
        self.mode = index
        self.set_interaction_mode()

        # To make keybindings work
        self.currentMode = self.mode_dict[index]

        # Mode styling
        selected = '#6ad1e3'
        non_selected = '#e7efff'
        self.button_view.setStyleSheet(self.get_mode_button_style(selected if index == 0 else non_selected))
        self.button_manual.setStyleSheet(self.get_mode_button_style(selected if index == 1 else non_selected))
        self.button_phase.setStyleSheet(self.get_mode_button_style(selected if index == 2 else non_selected))
        self.button_aim.setStyleSheet(self.get_mode_button_style(selected if index == 3 else non_selected))
        self.button_trend.setStyleSheet(self.get_mode_button_style(selected if index == 4 else non_selected))

        # Cleanup edit objects from previous mode
        if self.previous_mode == 2:
            self.figure_manager.phase_cleanup_temp_line()
        elif self.previous_mode == 3:
            self.figure_manager.aim_cleanup()
        elif self.previous_mode == 4:
            self.figure_manager.trend_cleanup()
        elif self.previous_mode == 1:
            self.figure_manager.data_styling_cleanup()

    def setup_home_tab(self):
        self.tab_home.setContentsMargins(0, 0, 0, 0)  # Add this line to remove margins from the tab
        self.home_layout = QVBoxLayout(self.tab_home)  # Ensure this is the layout for tab_home
        self.home_layout.setContentsMargins(0, 0, 0, 0)  # Add this line to remove margins from the home layout

        # Setup layout for mode selection
        mode_selection_layout = QVBoxLayout()
        mode_selection_layout.setSpacing(0)
        mode_selection_layout.setContentsMargins(0, 0, 0, 0)

        # Helper function to create a button with an icon above the text

        def create_icon_text_button(icon_path, text, color='black'):
            button = QPushButton()
            layout = QHBoxLayout()

            icon_pixmap = QPixmap(icon_path)  # Create QPixmap from icon path
            colored_pixmap = QPixmap(icon_pixmap.size())  # Create a new pixmap with the same size
            colored_pixmap.fill(Qt.GlobalColor.transparent)  # Fill it with transparency

            painter = QPainter(colored_pixmap)  # Start QPainter to draw on the new pixmap
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawPixmap(0, 0, icon_pixmap)  # Draw the original icon
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.setBrush(QColor(color))  # Set brush color
            painter.setPen(QColor(color))  # Set pen color
            painter.drawRect(colored_pixmap.rect())  # Draw a rectangle with the color
            painter.end()  # End QPainter

            icon_label = QLabel()
            icon_label.setPixmap(colored_pixmap.scaled(16, 16, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                                       QtCore.Qt.TransformationMode.SmoothTransformation))  # Use the colored QPixmap
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            text_label = QLabel(text)
            text_label.setStyleSheet(f"font-style: normal; color: {color};")
            text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(text_label)
            layout.addWidget(icon_label)
            layout.setContentsMargins(0, 0, 0, 0)

            container = QWidget()
            container.setLayout(layout)

            button_layout = QVBoxLayout(button)
            button_layout.addWidget(container)
            button_layout.setContentsMargins(0, 0, 0, 0)
            button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button.setLayout(button_layout)

            button.setFixedHeight(50)  # Adjust height as needed
            return button

        # Create buttons with icons and text
        self.button_view = create_icon_text_button(':/images/eye-regular.svg', 'View ')
        self.button_manual = create_icon_text_button(':/images/pen-to-square-regular.svg', 'Data ')
        self.button_phase = create_icon_text_button(':/images/flag-regular.svg', 'Phase ')
        self.button_aim = create_icon_text_button(':/images/crosshairs-solid.svg', 'Aim ')
        self.button_trend = create_icon_text_button(':/images/celeration.svg', 'Celeration ')

        self.button_view.setStyleSheet(self.get_mode_button_style())
        self.button_manual.setStyleSheet(self.get_mode_button_style())
        self.button_phase.setStyleSheet(self.get_mode_button_style())
        self.button_aim.setStyleSheet(self.get_mode_button_style())
        self.button_trend.setStyleSheet(self.get_mode_button_style())

        # Add push buttons to the mode selection layout with vertical alignment
        mode_selection_layout.addWidget(self.button_view)
        mode_selection_layout.addWidget(self.button_manual)
        mode_selection_layout.addWidget(self.button_phase)
        mode_selection_layout.addWidget(self.button_aim)
        mode_selection_layout.addWidget(self.button_trend)

        self.mode_dict = {
            0: 'view',
            1: 'manual',
            2: 'phase',
            3: 'aim',
            4: 'trend',
        }

        # Add mode selection layout directly to the home layout
        self.home_layout.addLayout(mode_selection_layout)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)  # Ensure no margins around the stacked widget
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

        # Connect push buttons to set interaction mode
        self.button_view.clicked.connect(lambda: self.change_mode(0))
        self.button_manual.clicked.connect(lambda: self.change_mode(1))
        self.button_phase.clicked.connect(lambda: self.change_mode(2))
        self.button_aim.clicked.connect(lambda: self.change_mode(3))
        self.button_trend.clicked.connect(lambda: self.change_mode(4))

        # Stretch at the bottom to push everything up
        self.home_layout.addStretch(1)

        # Apply the layout to the home tab
        self.tab_home.setLayout(self.home_layout)

    def setup_file_tab(self):
        files_layout = QVBoxLayout()  # Create a QVBoxLayout instance
        self.files_tab.setLayout(files_layout)  # Set the layout to files_tab

        # Data GroupBox
        group_box_data = QGroupBox("Raw Data")
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
        btn_image = QPushButton('Export')
        btn_image.setToolTip('Export chart as png, jpeg or pdf')
        layout_chart.addWidget(btn_new)
        layout_chart.addWidget(btn_load)
        layout_chart.addWidget(btn_save)
        layout_chart.addWidget(btn_image)
        group_box_chart.setLayout(layout_chart)
        files_layout.addWidget(group_box_chart)

        spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        files_layout.addItem(spacer)

        # Recent Data Imports ListBox
        lbl_recent_data_imports = QLabel("Recent Imports")
        lbl_recent_data_imports.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_recent_data_imports.setStyleSheet("font-weight: bold; font-style: normal;")
        self.lst_recent_data_imports = QListWidget()
        self.lst_recent_data_imports.setFixedHeight(150)
        files_layout.addWidget(lbl_recent_data_imports)
        files_layout.addWidget(self.lst_recent_data_imports)

        spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        files_layout.addItem(spacer)

        # Recent Charts ListBox
        lbl_recent_charts = QLabel("Recent Charts")
        lbl_recent_charts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_recent_charts.setStyleSheet("font-weight: bold; font-style: normal;")
        self.lst_recent_charts = QListWidget()
        self.lst_recent_charts.setFixedHeight(150)
        files_layout.addWidget(lbl_recent_charts)
        files_layout.addWidget(self.lst_recent_charts)

        # Populate recents for listboxes
        self.refresh_recent_data_imports_list()
        self.refresh_recent_charts_list()

        # Button connections
        btn_import_delete.clicked.connect(lambda: self.event_handlers.import_data(None))
        btn_export.clicked.connect(self.event_handlers.export_data)
        btn_new.clicked.connect(self.files_show_dialog)
        btn_image.clicked.connect(self.event_handlers.save_image)
        btn_save.clicked.connect(self.event_handlers.save_chart)
        btn_load.clicked.connect(lambda: self.event_handlers.load_chart(None))

        # Double-click connections for list items
        self.lst_recent_data_imports.itemDoubleClicked.connect(self.handle_import_double_click)
        self.lst_recent_charts.itemDoubleClicked.connect(self.handle_chart_double_click)

        files_layout.addStretch()  # Prevents the buttons from vertically filling the whole panel

    def refresh_recent_data_imports_list(self):
        self.lst_recent_data_imports.clear()
        recent_imports = self.data_manager.user_preferences.get('recent_imports', [])
        for file_path in recent_imports:
            if os.path.isfile(file_path):
                name = os.path.splitext(os.path.basename(file_path))[0]
                item = QListWidgetItem(name)
                item.setData(self.FullFilePathRole, file_path)
                self.lst_recent_data_imports.addItem(item)
            else:
                self.data_manager.user_preferences['recent_imports'].remove(file_path)

    def refresh_recent_charts_list(self):
        self.lst_recent_charts.clear()
        recent_charts = self.data_manager.user_preferences.get('recent_charts', [])
        for chart_path in recent_charts:
            if os.path.isfile(chart_path):
                name = os.path.splitext(os.path.basename(chart_path))[0]
                item = QListWidgetItem(name)
                item.setData(self.FullFilePathRole, chart_path)
                self.lst_recent_charts.addItem(item)
            else:
                self.data_manager.user_preferences['recent_charts'].remove(chart_path)

    def handle_import_double_click(self, item):
        file_path = item.data(self.FullFilePathRole)
        if os.path.isfile(file_path):
            self.event_handlers.import_data(file_path)
        else:
            self.data_manager.user_preferences['recent_imports'].remove(file_path)
        self.refresh_recent_data_imports_list()

    def handle_chart_double_click(self, item):
        chart_path = item.data(self.FullFilePathRole)
        if os.path.isfile(chart_path):
            self.event_handlers.load_chart(chart_path)
        else:
            self.data_manager.user_preferences['recent_charts'].remove(chart_path)
        self.refresh_recent_charts_list()

    def files_show_dialog(self):
        # Create a QMessageBox
        msg_box = QMessageBox()
        msg_box.setWindowTitle("New chart")
        msg_box.setText("Remove current chart?")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        # Execute the message box and get the response
        response = msg_box.exec()

        if response == QMessageBox.StandardButton.Yes:
            self.loaded_chart_path = None  # Prevents from accidentally saving default chart
            self.figure_manager.back_to_default()

            # Remove display name of imported/loaded chart
            self.setWindowTitle(self.window_title_str)

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

        # Reset preferences to default
        self.reset_preferences_btn = QPushButton('Reset')
        self.reset_preferences_btn.clicked.connect(self.reset_preferences_msg)
        preferences_group_layout.addWidget(self.reset_preferences_btn)

        # Create group for Chart types
        chart_type_settings_group = QGroupBox('Chart')
        chart_type_settings_layout = QVBoxLayout()
        chart_type_settings_group.setLayout(chart_type_settings_layout)

        chart_type_label = QLabel("Type")
        chart_type_settings_layout.addWidget(chart_type_label)
        self.chart_type_settings_dropdown = QComboBox()
        self.chart_type_settings_dropdown.addItem('DailyMinute', 'DailyMinute')  # Adding item with data
        self.chart_type_settings_dropdown.addItem('Daily', 'Daily')
        self.chart_type_settings_dropdown.addItem('WeeklyMinute', 'WeeklyMinute')
        self.chart_type_settings_dropdown.addItem('Weekly', 'Weekly')
        self.chart_type_settings_dropdown.addItem('MonthlyMinute', 'MonthlyMinute')
        self.chart_type_settings_dropdown.addItem('Monthly', 'Monthly')
        self.chart_type_settings_dropdown.addItem('YearlyMinute', 'YearlyMinute')
        self.chart_type_settings_dropdown.addItem('Yearly', 'Yearly')
        chart_type_settings_layout.addWidget(self.chart_type_settings_dropdown)

        # Load chart preference
        chart_type = self.data_manager.user_preferences['chart_type']
        index = self.chart_type_settings_dropdown.findData(chart_type)
        if index != -1:
            self.chart_type_settings_dropdown.setCurrentIndex(index)
        self.chart_type_settings_dropdown.currentIndexChanged.connect(self.event_handlers.change_chart_type)
        settings_layout.addWidget(chart_type_settings_group)

        # SpinBox for chart size
        chart_size_label = QLabel("Width (6 - 12)")
        self.chart_size_spinbox = QSpinBox()
        self.chart_size_spinbox.setRange(6, 12)  # Set the range as required
        self.chart_size_spinbox.setValue(self.data_manager.user_preferences.get('Width', 0))
        self.chart_size_spinbox.setValue(self.data_manager.user_preferences['width'])
        self.chart_size_spinbox.valueChanged.connect(self.event_handlers.change_width)
        chart_type_settings_layout.addWidget(chart_size_label)
        chart_type_settings_layout.addWidget(self.chart_size_spinbox)

        # Change start date
        self.change_start_date_btn = QPushButton('Start Date', self)
        self.change_start_date_btn.clicked.connect(self.event_handlers.show_date_dialog)
        chart_type_settings_layout.addWidget(self.change_start_date_btn)

        # Label for the font color button
        self.chart_font_color_button = QPushButton("Font Color")
        chart_type_settings_layout.addWidget(self.chart_font_color_button)
        self.chart_font_color_button.clicked.connect(lambda: self.event_handlers.choose_color(color_category='chart_font_color'))

        # Label for the font color button
        self.chart_grid_color_button = QPushButton("Grid Color")
        chart_type_settings_layout.addWidget(self.chart_grid_color_button)
        self.chart_grid_color_button.clicked.connect(lambda: self.event_handlers.choose_color(color_category='chart_grid_color'))

        # Create a group for Other settings
        other_settings_group = QGroupBox("Misc")
        other_settings_layout = QVBoxLayout()
        other_settings_group.setLayout(other_settings_layout)
        settings_test_angle_check = QCheckBox('Test angle')
        other_settings_layout.addWidget(settings_test_angle_check)
        settings_test_angle_check.stateChanged.connect(self.event_handlers.test_angle)
        settings_layout.addWidget(other_settings_group)

        self.right_dev_btn = QPushButton('Support developer')
        self.right_dev_btn.setStyleSheet("font-weight: bold; background-color: #96deeb; font-size: 10pt;")
        other_settings_layout.addWidget((self.right_dev_btn))
        self.right_dev_btn.clicked.connect(self.support_dev_btn_clicked)

        # Push everything to the top
        settings_layout.addStretch()

    def reset_preferences_msg(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('Reset preferences')
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText("Everything will go back to default. A manual reboot of iChart is required. Are you sure?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.save_preferences_upon_close = False
            self.data_manager.delete_user_preferences()
            QApplication.instance().quit()

    def keyPressEvent(self, event):
        # Check if the manual mode is active
        # if self.currentMode == 'manual':
        #     # Optionally, log all key presses for debugging
        #     # print("Key pressed in manual mode:", event.key(), "Modifiers:", int(event.modifiers()))
        #
        #     # Handle specific keys like Ctrl+Z for undo
        #     if event.modifiers() & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Z:
        #         self.figure_manager.undo_point()
        #         event.accept()  # Mark the event as handled
        #     else:
        #         # Consume all other key events to prevent any other key handling
        #         event.accept()  # This prevents the event from propagating further
        #     return  # Exit the function to stop any further key event processing

        # Handle other keys as usual in other modes
        super().keyPressEvent(event)

        if self.currentMode == 'trend':
        # Check if space was pressed
            if event.key() == Qt.Key.Key_Left:
                self.figure_manager.trend_move_temp_marker('left')
                self.trend_adjust_dates()
                self.figure_manager.trend_move_temp_est_with_arrows('left')
            elif event.key() == Qt.Key.Key_Right:
                self.figure_manager.trend_move_temp_marker('right')
                self.trend_adjust_dates()
                self.figure_manager.trend_move_temp_est_with_arrows('right')
            elif event.key() == Qt.Key.Key_Up:
                self.figure_manager.trend_move_temp_est_with_arrows('up')
            elif event.key() == Qt.Key.Key_Down:
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
        if self.mode == 0:  # View mode
            pass  # No interaction
        elif self.mode == 1:  # Manual mode
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.point_click)
        elif self.mode == 2:  # Phase mode
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.phase_click)
        elif self.mode == 3:  # Aim mode
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.aim_click)
        elif self.mode == 4:  # Trend mode
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', self.event_handlers.trend_click)

    def trend_adjust_dates(self):
        result = self.figure_manager.trend_adjust_dates()
        if result:
            date, order = result
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
        self.view_mode_widget.dot_bounce_check.setChecked(settings['dot_bounce'])
        self.view_mode_widget.x_bounce_check.setChecked(settings['x_bounce'])
        self.view_mode_widget.dot_est_check.setChecked(settings['dot_est'])
        self.view_mode_widget.x_est_check.setChecked(settings['x_est'])

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
        self.figure_manager.view_dot_bounce(settings['dot_bounce'], refresh=refresh)
        self.figure_manager.view_x_bounce(settings['x_bounce'], refresh=refresh)
        self.figure_manager.view_dot_est(settings['dot_est'], refresh=refresh)
        self.figure_manager.view_x_est(settings['x_est'], refresh=refresh)

        self.figure_manager.refresh()  # Only refresh canvas once!

    def closeEvent(self, event):
        # Stuff to do before closing application

        # Save current preferences
        if self.save_preferences_upon_close:
            self.data_manager.save_user_preferences()

        # Handle the window closing event to check if the chart needs to be saved. Overrides built-in function
        if self.loaded_chart_path:
            # Extract the file name from the path
            file_name = os.path.splitext(os.path.basename(self.loaded_chart_path))[0]

            # Create a message box to confirm if the user wants to save the chart
            reply = QMessageBox.question(self, 'Save Chart',
                                         f"Save {file_name} before closing?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                                         QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Yes:
                # Save the chart to the loaded path before closing
                self.event_handlers.save_chart(self.loaded_chart_path)
                event.accept()  # Proceed with the window close
            elif reply == QMessageBox.StandardButton.No:
                event.accept()  # Proceed with the window close without saving
            else:
                event.ignore()  # Ignore the close event
        else:
            event.accept()  # Proceed with the window close if no chart is loaded

    def set_manual_mode_widget(self):
        # Ensure currentMode is initialized before using it
        if not hasattr(self, 'currentMode'):
            self.currentMode = 'view'

        # Always rebuild the widget
        if self.manual_mode_widget is not None:
            # Remove the current widget from the stacked widget
            self.stacked_widget.removeWidget(self.manual_mode_widget)

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
        elif chart_type == 'YearlyMinute':
            self.manual_mode_widget = chart_mode.ManualModeWidgetYearlyMinute(self.figure_manager)
        elif chart_type == 'Yearly':
            self.manual_mode_widget = chart_mode.ManualModeWidgetYearly(self.figure_manager)
        else:
            print('Unable to find chart type')
            self.manual_mode_widget = chart_mode.ManualModeWidgetDailyMinute(self.figure_manager)

        # Add the new widget to the stacked widget
        index = 1  # Assuming manual mode widget is the second widget in the stack
        self.stacked_widget.insertWidget(index, self.manual_mode_widget)

        # # Safely disconnect the button if it is connected
        # try:
        #     self.button_manual.clicked.disconnect()
        # except TypeError:
        #     pass  # No connection to disconnect

        # Reconnect the button to the new widget
        self.button_manual.clicked.connect(lambda: self.change_mode(index))

        # Force an update if manual mode is already selected
        if self.currentMode == 'manual':
            self.change_mode(index)


class EventHandlers:
    def __init__(self, chart_app, figure_manager, data_manager):
        self.chart_app = chart_app
        self.figure_manager = figure_manager
        self.data_manager = data_manager

    def show_date_dialog(self):
        dialog = StartDateDialog(self.chart_app)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_start_date = dialog.get_date()
            self.figure_manager.settings_change_start_date(new_start_date)
            self.chart_app.set_interaction_mode()

    def save_recent(self, file_path, recent_type):
        if file_path in self.data_manager.user_preferences[recent_type]:
            self.data_manager.user_preferences[recent_type].remove(file_path)
        self.data_manager.user_preferences[recent_type].insert(0, file_path)
        self.data_manager.user_preferences[recent_type] = self.data_manager.user_preferences[recent_type][:7]

    def import_data(self, file_path):
        if file_path is None:
            # Open file dialog with support for CSV and Excel files
            file_path, _ = QFileDialog.getOpenFileName(self.chart_app, 'Select file',
                                                       self.data_manager.user_preferences['home_folder'],
                                                       'CSV, Excel, ODS files (*.csv *.xls *.xlsx *.ods)')

        if file_path:
            try:
                self.figure_manager.fig_import_data(file_path, self.chart_app.loaded_chart_path)

                # Save to recents and refresh list
                self.save_recent(file_path, 'recent_imports')
                self.chart_app.refresh_recent_data_imports_list()

            except:
                msg_box = QMessageBox()
                msg_box.setWindowTitle('Failed to import data')
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setText('Likely reason: The data sheet is incorrectly formatted.')
                msg_box.setInformativeText("Solution: Check out formatting instructions on <a href='https://github.com/SJV-S/iChart/blob/main/README.md#import-formatting'>https://github.com/SJV-S/iChart/blob/main/README.md#import-formatting</a>.")
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.setStyleSheet("QLabel{ font-style: normal; }")
                msg_box.exec()

        self.chart_app.set_interaction_mode()  # Make sure current mode is enabled for key handling

        # Display name of file imported
        file_name = os.path.basename(file_path)
        self.chart_app.setWindowTitle(f'{self.chart_app.window_title_str} – {file_name}')

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self.chart_app, 'Save file', self.data_manager.user_preferences['home_folder'],
                                                   'CSV files (*.csv);;Excel files (*.xls *.xlsx);;ODS files (*.ods);;All files (*.*)')
        if file_path:
            self.data_manager.create_export_file(file_path)

    def save_image(self):
        dialog = SaveImageDialog(self.chart_app)
        if dialog.exec() == QDialog.DialogCode.Accepted:
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
        self.chart_app.setWindowTitle(f'{self.chart_app.window_title_str} – {file_name}')

    def load_chart(self, file_path):
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(self.chart_app, 'Open file',
                                                       self.data_manager.user_preferences['home_folder'],
                                                       'JSON files (*.json);;All files (*.*)')
        if file_path:
            self.chart_app.loaded_chart_path = file_path
            self.figure_manager.fig_load_chart(file_path)

            # Save to recents and refresh list
            self.save_recent(file_path, 'recent_charts')
            self.chart_app.refresh_recent_charts_list()

            # Update the chart type dropdown to reflect the loaded chart type
            chart_type = self.data_manager.chart_data['type']
            index = self.chart_app.chart_type_settings_dropdown.findData(chart_type)
            if index != -1:
                # Update chart dropdown without double creation of the canvas
                self.chart_app.chart_type_settings_dropdown.blockSignals(True)
                self.chart_app.chart_type_settings_dropdown.setCurrentIndex(index)  # Normally, this would also create a new canvas because the chart type was changed
                self.chart_app.chart_type_settings_dropdown.blockSignals(False)

            self.chart_app.set_interaction_mode()  # Make sure current mode is enabled for key handling

        # Display name of chart imported
        file_name = os.path.basename(file_path)
        self.chart_app.setWindowTitle(f'{self.chart_app.window_title_str} – {file_name}')

    def update_zero_count_handling(self, bool_type):
        self.data_manager.user_preferences['place_below_floor'] = bool_type
        self.figure_manager.new_chart(self.data_manager.chart_data['start_date'])
        self.chart_app.set_interaction_mode()  # Make sure current mode is enabled for key handling

    def set_data_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self.chart_app, "Select Folder", QDir.homePath())
        if folder_path:
            self.chart_app.settings_folder_btn.setText(folder_path)
            self.chart_app.settings_folder_btn.setToolTip(folder_path)
            self.data_manager.user_preferences['home_folder'] = folder_path

    def on_agg_current_index_changed(self, index):
        self.data_manager.user_preferences.update({'chart_data_agg': self.chart_app.settings_data_agg.itemData(index)})
        self.figure_manager.change_chart_type(self.data_manager.user_preferences['chart_type'])
        self.chart_app.set_interaction_mode()  # Making sure current mode is enabled for key handling

    def change_chart_type(self, index):
        self.figure_manager.change_chart_type(self.chart_app.chart_type_settings_dropdown.itemData(index)),
        self.chart_app.set_manual_mode_widget()

        # Make sure current mode is enabled for key handling
        self.chart_app.set_interaction_mode()

        # Update timing and floor checkboxes
        self.chart_app.view_mode_widget.update_timing_checkboxes()

    def change_width(self, new_width):
        self.data_manager.user_preferences['width'] = new_width
        self.figure_manager.settings_change_chart_width()
        self.chart_app.set_interaction_mode()

    def phase_click(self, event):
        # Update phase line form
        coordinates = self.figure_manager.phase_line_handle_click(event, self.chart_app.phase_mode_widget.phase_change_input.text())
        if coordinates:  # In case the user clicked outside the graph
            x, y = coordinates
            if x in self.figure_manager.x_to_date.keys():
                # self.chart_app.phase_mode_widget.phase_y_input.setText(str(y))
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

    def point_click(self, event):
        self.figure_manager.point_on_click(event)

    def test_angle(self, show):
        self.figure_manager.settings_test_angle(show)

    def choose_color(self, color_category):
        # Convert the stored color code to a QColor object
        initial_color = QColor(self.data_manager.user_preferences[color_category])
        QColorDialog.setCustomColor(0, QColor('#5ac9e2'))  # Behavior & Research Company hex extracted
        QColorDialog.setCustomColor(1, QColor('#6ad1e3'))  # Behavior & Research Company hex from website (1)
        QColorDialog.setCustomColor(2, QColor('#05c3de'))  # Behavior & Research Company hex from website (2)
        QColorDialog.setCustomColor(3, QColor('#71B8FF'))  # My original choice of font color
        QColorDialog.setCustomColor(4, QColor('#5a93cc'))  # My original choice of grid color
        color = QColorDialog.getColor(initial_color)

        if color.isValid():
            self.data_manager.user_preferences[color_category] = color.name()
            self.figure_manager.update_chart()
            self.chart_app.set_interaction_mode()


app = QApplication(sys.argv)
app.setStyleSheet(styles.general_stylesheet)
window = ChartApp()
window.show()
sys.exit(app.exec())

