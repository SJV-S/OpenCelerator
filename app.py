from app_imports import *
from FigureManager import FigureManager
from DataManager import DataManager
from database import DatabaseMonitor
from EventStateManager import EventBus, StateRegistry
from Popups import SaveImageDialog, StartDateDialog, SupportDevDialog, NoteDialog, DataColumnMappingDialog, UserPrompt
from Modes import ViewModeWidget, StyleModeWidget, PhaseModeWidget, AimModeWidget, TrendModeWidget, NoteModeWidget, PlotModeWidget
import styles

# For generating error reports
import error_logging
logger = error_logging.logger

# I had to use Y and M instead of YE and ME because the executable won't currently run with YE and ME
warnings.filterwarnings(action='ignore', category=FutureWarning, message=".*'Y' is deprecated.*")
warnings.filterwarnings(action='ignore', category=FutureWarning, message=".*'M' is deprecated.*")


class ChartApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Define a custom data role
        self.FullFilePathRole = Qt.ItemDataRole.UserRole

        # Initialize main classes
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.state_registry = StateRegistry(self.data_manager)
        self.data_manager.default_chart_assessment()
        self.figure_manager = FigureManager(self)

        # Initialize the mode manager
        self.mode_manager = ModeManager(self, self.figure_manager, self.event_bus)

        # Event subscriptions with data
        self.event_bus.subscribe('save_decision', self.save_decision, has_data=True)

        # Event chains
        self.event_bus.add_event_trigger('new_chart', 'cleanup_after_chart_update')

        # Initialize the main window properties
        version = self.event_bus.emit("get_user_preference", ['version', ''])
        self.window_title_str = f'OpenCelerator v{version}' if version else 'OpenCelerator'
        self.setWindowTitle(self.window_title_str)
        self.setWindowIcon(QIcon(':/images/opencelerator_logo_no_text.svg'))

        # Create and set the central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a vertical layout as the main layout wrapper
        self.wrapper_layout = QVBoxLayout(self.central_widget)
        self.main_layout = QHBoxLayout()
        self.wrapper_layout.addLayout(self.main_layout)

        # Initialize EventHandlers
        self.event_handlers = EventHandlers(self, self.figure_manager, self.data_manager)

        # Create the FilesTab instance
        self.files_tab = FilesTab(self, self.event_handlers, self.data_manager)

        # Initialize the tabs for the left panel
        self.tabs = QTabWidget()

        self.main_layout.addWidget(self.tabs)
        self.tab_home = QWidget()
        self.tab_settings = QWidget()

        # Crosshair control variables
        self.shift_key_down = False
        self.alt_key_down = False
        QApplication.instance().installEventFilter(self)

        # Set up home tab
        self.home_layout = QVBoxLayout()  # Main layout for the home tab
        self.main_layout.addWidget(self.figure_manager)

        # Setup tabs
        self.setup_home_tab()
        self.setup_settings_tab()

        # Add tabs to the tab widget
        self.tabs.addTab(self.tab_home, 'Home')
        self.tabs.addTab(self.files_tab, 'Files')  # Use the FilesTab instance
        self.tabs.addTab(self.tab_settings, 'Config')
        self.tabs.setCurrentIndex(1)  # Default to Files tab on boot

        # Set up mode shortcuts
        self.mode_manager.setup_shortcuts(self)

        # Tab key bindings
        self.shortcut_home = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_H), self)
        self.shortcut_home.activated.connect(lambda: self.tabs.setCurrentIndex(0))
        self.shortcut_files = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_F), self)
        self.shortcut_files.activated.connect(lambda: self.tabs.setCurrentIndex(1))
        self.shortcut_config = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_O), self)
        self.shortcut_config.activated.connect(lambda: self.tabs.setCurrentIndex(2))

        # File keybindings
        self.shortcut_import = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_D), self)
        self.shortcut_import.activated.connect(lambda: self.event_handlers.import_data())
        self.shortcut_load = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_L), self)
        self.shortcut_load.activated.connect(lambda: self.event_handlers.load_chart(None))
        self.shortcut_export = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_E), self)
        self.shortcut_export.activated.connect(self.event_handlers.save_image)
        self.shortcut_new = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_N), self)
        self.shortcut_new.activated.connect(self.files_tab.new_chart_dialog)
        self.shortcut_save = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_S), self)
        self.shortcut_save.activated.connect(lambda: self.event_handlers.save_chart())

        # Control variables
        self.xy_coord = None
        self.save_preferences_upon_close = True

        # Check version change status
        self.report_on_version_change()

        # Setup remote db sync
        self.event_bus.emit('sync_remotes')  # Initial sync on boot
        self.db_monitor = DatabaseMonitor(self.data_manager)
        QTimer.singleShot(1000, self.db_monitor.start_monitoring)  # Start monitoring remote db for changes

    def report_on_version_change(self):
        if hasattr(sys, 'version_change_status') and sys.version_change_status:
            current_version = self.event_bus.emit("get_user_preference", ['version', 'unknown'])

            if sys.version_change_status == "update":
                data = {
                    'title': "Version Update",
                    'message': f"Upgraded to version {current_version}",
                    'options': ['OK']
                }
                self.event_bus.emit('trigger_user_prompt', data)
            elif sys.version_change_status == "downgrade":
                data = {
                    'title': "Version Downgrade",
                    'message': f"Downgraded to version {current_version}",
                    'options': ['OK']
                }
                self.event_bus.emit('trigger_user_prompt', data)

    def eventFilter(self, obj, event):
        # Check if obj is a valid QObject and event is a valid QEvent
        if not isinstance(obj, QObject) or not isinstance(event, QEvent):
            # If not proper types, just return false (don't handle)
            return False

        try:
            # Check if the event is a key press event
            if event.type() == QEvent.Type.KeyPress:
                if (event.key() == Qt.Key.Key_Shift and not self.shift_key_down) or \
                        (event.key() == Qt.Key.Key_Alt and not self.alt_key_down):

                    # Set key state
                    if event.key() == Qt.Key.Key_Shift:
                        self.shift_key_down = True
                        self.figure_manager.hover_manager.show_lines = True
                    else:  # Alt key
                        self.alt_key_down = True
                        self.figure_manager.hover_manager.show_lines = False

                    # Save the background for blitting using hover manager
                    self.figure_manager.hover_manager.save_crosshair_background()

                    # Connect mouse motion event to update hover coordinates
                    self.figure_manager.canvas.mpl_connect('motion_notify_event', self.update_hover_coordinates)

            # Check if the event is a key release event
            elif event.type() == QEvent.Type.KeyRelease:
                if (event.key() == Qt.Key.Key_Shift and self.shift_key_down) or \
                        (event.key() == Qt.Key.Key_Alt and self.alt_key_down):

                    # Reset appropriate key state
                    if event.key() == Qt.Key.Key_Shift:
                        self.shift_key_down = False
                    else:  # Alt key
                        self.alt_key_down = False

                    # Clear the crosshairs using hover manager
                    self.figure_manager.hover_manager.clear_crosshair_blit()
        except Exception:
            # If any error occurs during event handling, reset key states
            self.shift_key_down = False
            self.alt_key_down = False
            return False

        return super().eventFilter(obj, event)

    def update_hover_coordinates(self, event):
        ax = event.inaxes
        if (self.shift_key_down and QApplication.keyboardModifiers() == Qt.KeyboardModifier.ShiftModifier) or \
                (self.alt_key_down and QApplication.keyboardModifiers() == Qt.KeyboardModifier.AltModifier):
            if ax and event.xdata is not None and event.ydata is not None:
                x, y = event.xdata, event.ydata
                x = self.figure_manager.data_manager.find_closest_x(int(x), self.figure_manager.Chart.date_to_pos)
                y = self.data_manager.format_y_value(y)
                self.figure_manager.hover_manager.crosshair_blit(x, y)

    def support_dev_btn_clicked(self):
        dialog = SupportDevDialog()
        dialog.exec()

    def setup_home_tab(self):
        self.tab_home.setContentsMargins(0, 0, 0, 0)
        self.home_layout = QVBoxLayout(self.tab_home)
        self.home_layout.setContentsMargins(0, 0, 0, 0)

        # Setup layout for mode selection
        mode_selection_layout = QVBoxLayout()
        mode_selection_layout.setSpacing(0)
        mode_selection_layout.setContentsMargins(0, 0, 0, 0)

        # Helper function to create a button with an icon above the text
        def create_icon_text_button(icon_path, text, color='black', icon_width=16, icon_height=16, button_height=50):
            button = QPushButton()
            layout = QHBoxLayout()

            icon_pixmap = QPixmap(icon_path)
            colored_pixmap = QPixmap(icon_pixmap.size())
            colored_pixmap.fill(Qt.GlobalColor.transparent)

            painter = QPainter(colored_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
            painter.drawPixmap(0, 0, icon_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.setBrush(QColor(color))
            painter.setPen(QColor(color))
            painter.drawRect(colored_pixmap.rect())
            painter.end()

            icon_label = QLabel()
            icon_label.setPixmap(colored_pixmap.scaled(icon_width, icon_height, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation))
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

            button.setFixedHeight(button_height)
            return button

        # Create buttons with icons and text
        self.button_view = create_icon_text_button(':/images/eye-regular.svg', 'View ')
        self.button_phase = create_icon_text_button(':/images/flag-regular.svg', 'Phase ')
        self.button_aim = create_icon_text_button(':/images/crosshairs-solid.svg', 'Aim ')
        self.button_trend = create_icon_text_button(':/images/celeration.svg', f'{self.data_manager.ui_cel_label} ')
        self.button_note = create_icon_text_button(':/images/note-sticky-regular.svg', 'Notes ')
        self.button_manual = create_icon_text_button(':/images/style-svgrepo-com.svg', 'Style ')
        self.button_plot = create_icon_text_button(':/images/pen-to-square-regular.svg', 'Plot ')

        # Add push buttons to the mode selection layout with vertical alignment
        mode_selection_layout.addWidget(self.button_view)
        mode_selection_layout.addWidget(self.button_plot)
        mode_selection_layout.addWidget(self.button_phase)
        mode_selection_layout.addWidget(self.button_aim)
        mode_selection_layout.addWidget(self.button_trend)
        mode_selection_layout.addWidget(self.button_note)
        mode_selection_layout.addWidget(self.button_manual)

        # Add mode selection layout directly to the home layout
        self.home_layout.addLayout(mode_selection_layout)

        # Create the stacked widget
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)  # Ensure no margins around the stacked widget
        self.home_layout.addWidget(self.stacked_widget)

        self.mode_manager.setup_mode_ui(self.stacked_widget)

        # Connect push buttons to set interaction mode
        self.button_view.clicked.connect(lambda: self.event_bus.emit("view_mode_selected"))
        self.button_manual.clicked.connect(lambda: self.event_bus.emit("style_mode_selected"))
        self.button_phase.clicked.connect(lambda: self.event_bus.emit('phase_mode_selected'))
        self.button_aim.clicked.connect(lambda: self.event_bus.emit('aim_mode_selected'))
        self.button_trend.clicked.connect(lambda: self.event_bus.emit('celeration_mode_selected'))
        self.button_note.clicked.connect(lambda: self.event_bus.emit('note_mode_selected'))
        self.button_plot.clicked.connect(lambda: self.event_bus.emit("plot_mode_selected"))

        # Stretch at the bottom to push everything up
        self.home_layout.addStretch(1)

        # Apply the layout to the home tab
        self.tab_home.setLayout(self.home_layout)

    def setup_settings_tab(self):
        # Create settings layout
        settings_layout = QVBoxLayout()
        self.tab_settings.setLayout(settings_layout)

        # Create group for Chart types (moved to top)
        chart_type_settings_group = QGroupBox('Chart')
        chart_type_settings_layout = QVBoxLayout()
        chart_type_settings_group.setLayout(chart_type_settings_layout)

        chart_type_label = QLabel("Type")
        chart_type_settings_layout.addWidget(chart_type_label)
        chart_type_options = [
            ('Daily', 'Daily'),
            ('Weekly', 'Weekly'),
            ('Monthly', 'Monthly'),
            ('Yearly', 'Yearly'),
            ('DailyMinute', 'DailyMinute'),
            ('WeeklyMinute', 'WeeklyMinute'),
            ('MonthlyMinute', 'MonthlyMinute'),
            ('YearlyMinute', 'YearlyMinute')
        ]
        self.chart_type_settings_dropdown = QComboBox()
        for display, value in chart_type_options:
            self.chart_type_settings_dropdown.addItem(display, value)
        chart_type_settings_layout.addWidget(self.chart_type_settings_dropdown)

        # Load chart preference
        chart_type = self.data_manager.chart_data['type']
        index = self.chart_type_settings_dropdown.findData(chart_type)
        if index != -1:
            self.chart_type_settings_dropdown.setCurrentIndex(index)
        self.chart_type_settings_dropdown.currentIndexChanged.connect(self.event_handlers.change_chart_type)

        # Zero counts below timing floor or don't display
        settings_zero_count_handling_label = QLabel('Zero counts')
        self.settings_zero_count_handling = QComboBox()
        self.settings_zero_count_handling.addItem('Place below floor', True)
        self.settings_zero_count_handling.addItem('Do not show', False)
        # Set default selection based on bool_type
        if self.data_manager.chart_data['place_below_floor']:
            # Select 'Place below floor'
            self.settings_zero_count_handling.setCurrentIndex(0)
        else:
            # Select 'Do not show'
            self.settings_zero_count_handling.setCurrentIndex(1)

        chart_type_settings_layout.addWidget(settings_zero_count_handling_label)
        chart_type_settings_layout.addWidget(self.settings_zero_count_handling)
        self.settings_zero_count_handling.currentIndexChanged.connect(
            lambda index: self.event_handlers.update_zero_count_handling(
                self.settings_zero_count_handling.itemData(index)))

        # SpinBox for chart size
        chart_size_label = QLabel("Width (6 - 15)")
        self.chart_size_spinbox = QSpinBox()
        self.chart_size_spinbox.setRange(6, 15)  # Set the range as required
        self.chart_size_spinbox.setValue(self.data_manager.user_preferences.get('Width', 0))
        self.chart_size_spinbox.setValue(self.event_bus.emit("get_user_preference", ['width', 10]))
        self.chart_size_spinbox.valueChanged.connect(self.event_handlers.change_width)
        chart_type_settings_layout.addWidget(chart_size_label)
        chart_type_settings_layout.addWidget(self.chart_size_spinbox)

        # Change start date
        self.change_start_date_btn = QPushButton('Start Date', self)
        self.change_start_date_btn.clicked.connect(self.event_handlers.show_date_dialog)
        chart_type_settings_layout.addWidget(self.change_start_date_btn)

        # Label for the font color button
        self.chart_font_color_button = QPushButton('Font Color')
        chart_type_settings_layout.addWidget(self.chart_font_color_button)
        self.chart_font_color_button.clicked.connect(
            lambda: self.event_handlers.choose_color(color_category='chart_font_color'))

        # Label for the font color button
        self.chart_grid_color_button = QPushButton('Grid Color')
        chart_type_settings_layout.addWidget(self.chart_grid_color_button)
        self.chart_grid_color_button.clicked.connect(
            lambda: self.event_handlers.choose_color(color_category='chart_grid_color'))

        settings_layout.addWidget(chart_type_settings_group)

        # Add spacing between Chart and Preferences
        settings_layout.addSpacing(20)

        # Create a group for preferences
        preferences_group = QGroupBox("Preferences")
        preferences_group_layout = QVBoxLayout()
        preferences_group.setLayout(preferences_group_layout)

        # Reset preferences to default
        self.reset_preferences_btn = QPushButton('Reset')
        self.reset_preferences_btn.clicked.connect(self.reset_preferences_msg)
        preferences_group_layout.addWidget(self.reset_preferences_btn)

        # Autosave
        settings_autosave_label = QLabel('Autosave')
        self.settings_autosave_options = QComboBox()
        self.settings_autosave_options.addItem("On")
        self.settings_autosave_options.addItem("Off")
        autosave = self.event_bus.emit("get_user_preference", ['autosave', False])
        self.settings_autosave_options.setCurrentText("On" if autosave else "Off")
        self.settings_autosave_options.currentIndexChanged.connect(
            lambda index: self.event_bus.emit("update_user_preference",
                                              ['autosave', self.settings_autosave_options.currentText() == "On"]))
        preferences_group_layout.addWidget(settings_autosave_label)
        preferences_group_layout.addWidget(self.settings_autosave_options)

        update_checker_settings = QComboBox()
        update_checker_label = QLabel('Updates')
        update_checker_settings.addItems(['Auto', 'Off'])
        update_policy = self.event_bus.emit("get_user_preference", ['update', 'Off'])
        update_checker_settings.setCurrentText(update_policy)
        update_checker_settings.activated.connect(lambda idx: self.event_bus.emit("update_user_preference", ['update',
                                                                                                             update_checker_settings.currentText()]))
        preferences_group_layout.addWidget(update_checker_label)
        preferences_group_layout.addWidget(update_checker_settings)

        settings_layout.addWidget(preferences_group)

        # Add spacing between Preferences and Misc
        settings_layout.addSpacing(20)

        # Create a group for Other settings
        other_settings_group = QGroupBox('Misc')
        other_settings_layout = QVBoxLayout()
        other_settings_group.setLayout(other_settings_layout)

        settings_test_angle_check = QCheckBox('Test angle')
        other_settings_layout.addWidget(settings_test_angle_check)
        settings_test_angle_check.stateChanged.connect(self.event_handlers.test_angle)

        self.right_dev_btn = QPushButton('Support developer')
        self.right_dev_btn.setStyleSheet('font-weight: bold; background-color: #96deeb')
        other_settings_layout.addWidget((self.right_dev_btn))
        self.right_dev_btn.clicked.connect(self.support_dev_btn_clicked)

        settings_layout.addWidget(other_settings_group)

        # Push everything to the top
        settings_layout.addStretch()

    def reset_preferences_msg(self):
        msg_box = QMessageBox()
        msg_box.setWindowTitle('Reset preferences')
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(
            "Everything will go back to default. A manual reboot of OpenCelerator is required. Are you sure?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

        reply = msg_box.exec()

        if reply == QMessageBox.StandardButton.Yes:
            self.save_preferences_upon_close = False
            self.data_manager.delete_user_preferences()
            QApplication.instance().quit()

    def save_decision(self, event=None):
        # Collect all bools and variables needed for decision making
        chart_file_path = self.data_manager.chart_data['chart_file_path']
        autosave = self.event_bus.emit("get_user_preference", ['autosave', False])
        data_exists = self.data_manager.df_raw is not None and not self.data_manager.df_raw.empty
        has_chart_path = bool(chart_file_path)
        save_needed = self.event_bus.emit('has_chart_changed', chart_file_path) if has_chart_path else False
        has_event = event is not None

        # Extract display name once (remove timestamp after last underscore)
        if has_chart_path and isinstance(chart_file_path, str):
            last_underscore = chart_file_path.rfind('_')
            display_name = chart_file_path[:last_underscore] if last_underscore != -1 else chart_file_path
        else:
            display_name = chart_file_path

        # Decision logic
        if has_chart_path and not autosave and save_needed:
            # Prompt user to save
            options = ['Yes', 'No', 'Cancel'] if has_event else ['Yes', 'No']
            data = {
                'title': 'Save Chart',
                'message': f"Save {display_name}?",
                'options': options
            }
            result = self.event_bus.emit('trigger_user_prompt', data)

            if result == 0:  # Yes selected
                self.event_handlers.save_chart(chart_file_path)
            elif result == 2 and has_event:  # Cancel selected (only possible with event)
                event.ignore()

        elif autosave and has_chart_path and save_needed:
            # Autosave without prompting
            self.event_handlers.save_chart(chart_file_path)
            if has_event:
                event.accept()

        elif not has_chart_path and data_exists:
            # No chart file but data exists - prompt to save
            data = {
                'title': "No chart file",
                'message': 'Save this chart?',
                'options': ['Yes', 'No']
            }
            result = self.event_bus.emit('trigger_user_prompt', data)

            if result == 0:  # Yes selected
                self.event_handlers.save_chart(chart_file_path)
            if has_event:
                event.accept()

    def closeEvent(self, event):
        # Stuff to do before closing application
        self.event_bus.emit('save_decision', data=event)

        # Save current preferences
        if self.save_preferences_upon_close:
            self.data_manager.save_user_preferences()

        # Sync with remote databases after all save operations
        self.event_bus.emit('sync_remotes')

        # Reclaim space
        self.event_bus.emit('vacuum_database')

        # Accept the close event to close the window
        event.accept()


class ModeManager:
    def __init__(self, main_app, figure_manager, event_bus):
        self.main_app = main_app
        self.figure_manager = figure_manager
        self.event_bus = event_bus

        # Mode state
        self.current_mode_name = 'view'  # View mode by default
        self.previous_mode_name = None
        self.current_connection = None

        # Mode widgets (will be created during initialization)
        self.mode_widgets = {}

        # The ordered list of modes determines the stacked widget order
        self.mode_ordered_list = ['view', 'manual', 'phase', 'aim', 'trend', 'note', 'plot']

        # Mode buttons
        self.mode_buttons = {}

        # Stacked widget reference
        self.stacked_widget = None

        # Canvas connections
        self.legend_pick_cid = None
        self.credit_pick_cid = None
        self.fan_pick_cid = None
        self.fan_release_cid = None
        self.fan_motion_cid = None

        # Set up event subscriptions
        self.setup_event_subscriptions()
        self.setup_universal_connections()

        # Event bus subscriptions
        self.event_bus.subscribe('reload_current_mode', self.reload_current_mode)

    def reload_current_mode(self):
        self.change_mode(self.current_mode_name)

    def setup_event_subscriptions(self):
        # Event subscriptions for mode changes
        self.event_bus.subscribe("view_mode_selected", lambda: self.change_mode('view'), has_data=False)
        self.event_bus.subscribe("style_mode_selected", lambda: self.change_mode('manual'), has_data=False)
        self.event_bus.subscribe("phase_mode_selected", lambda: self.change_mode('phase'), has_data=False)
        self.event_bus.subscribe("aim_mode_selected", lambda: self.change_mode('aim'), has_data=False)
        self.event_bus.subscribe("celeration_mode_selected", lambda: self.change_mode('trend'), has_data=False)
        self.event_bus.subscribe("note_mode_selected", lambda: self.change_mode('note'), has_data=False)
        self.event_bus.subscribe("plot_mode_selected", lambda: self.change_mode('plot'), has_data=False)

        # Additional events for accessing mode widgets
        self.event_bus.subscribe("get_mode_widget", self.get_mode_widget, has_data=True)

    def create_mode_widgets(self):
        # Create all mode widgets as a dictionary only
        self.mode_widgets = {
            'view': ViewModeWidget(self.figure_manager),
            'manual': StyleModeWidget(self.figure_manager),
            'phase': PhaseModeWidget(self.figure_manager),
            'aim': AimModeWidget(self.figure_manager),
            'trend': TrendModeWidget(self.figure_manager),
            'note': NoteModeWidget(self.figure_manager),
            'plot': PlotModeWidget(self.figure_manager)
        }

        return self.mode_widgets

    def setup_mode_ui(self, stacked_widget):
        """Set up the UI components for all modes."""
        self.stacked_widget = stacked_widget

        # Store button references directly by their names
        # The main app will need to change its button dict to use names
        self.mode_buttons = {
            'view': self.main_app.button_view,
            'manual': self.main_app.button_manual,
            'phase': self.main_app.button_phase,
            'aim': self.main_app.button_aim,
            'trend': self.main_app.button_trend,
            'note': self.main_app.button_note,
            'plot': self.main_app.button_plot
        }

        # Create mode widgets if not already created
        if not self.mode_widgets:
            self.create_mode_widgets()

        # Add all mode widgets to the stacked widget in the same order as the predefined list
        for mode_name in self.mode_ordered_list:
            self.stacked_widget.addWidget(self.mode_widgets[mode_name])

        # Initialize styling
        self.update_mode_button_styles()

        # Sync settings for view mode
        self.event_bus.emit('sync_grid_checkboxes')
        self.event_bus.emit('sync_misc_checkboxes')
        self.event_bus.emit('apply_all_grid_settings')
        self.event_bus.emit('apply_all_misc_settings')

    def setup_shortcuts(self, parent):
        self.shortcut_view = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_V), parent)
        self.shortcut_manual = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_T), parent)
        self.shortcut_phase = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_P), parent)
        self.shortcut_aim = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_A), parent)
        self.shortcut_trend = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_C), parent)
        self.shortcut_note = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_M), parent)
        self.shortcut_plot = QShortcut(QKeyCombination(Qt.KeyboardModifier.ShiftModifier, Qt.Key.Key_G), parent)

        # Connect shortcuts to mode changes
        self.shortcut_view.activated.connect(
            lambda: [self.event_bus.emit('view_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_manual.activated.connect(
            lambda: [self.event_bus.emit('style_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_phase.activated.connect(
            lambda: [self.event_bus.emit('phase_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_aim.activated.connect(
            lambda: [self.event_bus.emit('aim_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_trend.activated.connect(
            lambda: [self.event_bus.emit('celeration_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_note.activated.connect(
            lambda: [self.event_bus.emit('note_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])
        self.shortcut_plot.activated.connect(
            lambda: [self.event_bus.emit('plot_mode_selected'),
                     self.main_app.tabs.setCurrentWidget(self.main_app.tab_home)])

    def change_mode(self, mode_name):
        if self.stacked_widget is None:
            return  # Not fully initialized yet

        if mode_name not in self.mode_ordered_list:
            return  # Invalid mode name

        # Store previous mode for cleanup
        mode_index = self.mode_ordered_list.index(mode_name)
        self.previous_mode_name = self.current_mode_name
        self.stacked_widget.setCurrentIndex(mode_index)
        self.current_mode_name = mode_name

        # Update interaction mode
        self.set_interaction_mode()

        # Update button styles
        self.update_mode_button_styles()

        # Run mode-specific initialization based on the selected mode
        self.run_mode_specific_actions(mode_name)

        # Cleanup edit objects from previous mode
        self.cleanup_previous_mode()

    def update_mode_button_styles(self):
        # Update the visual style of mode buttons based on current selection
        if not self.mode_buttons:
            return  # Not fully initialized yet

        selected = '#6ad1e3'
        non_selected = '#e7efff'

        # Set appropriate styles based on current mode
        for mode_name, button in self.mode_buttons.items():
            button.setStyleSheet(self.get_mode_button_style(
                selected if mode_name == self.current_mode_name else non_selected
            ))

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

    def set_interaction_mode(self):
        # Disconnect previous connection if it exists
        if self.current_connection:
            self.figure_manager.canvas.mpl_disconnect(self.current_connection)
            self.current_connection = None

        # Universal connections that apply to all modes
        self.setup_universal_connections()

        # Mode-specific connections - properly mapping each mode to its handler
        mode_handlers = {
            'manual': self.point_click,
            'phase': self.handle_phase_click,
            'aim': self.handle_aim_click,
            'trend': self.handle_trend_click,
            'note': self.note_click,
            'plot': self.plot_click,
            # 'view' mode intentionally missing as it has no handler
        }

        # Connect the appropriate handler if one exists for the current mode
        handler = mode_handlers.get(self.current_mode_name)
        if handler:
            self.current_connection = self.figure_manager.canvas.mpl_connect('button_press_event', handler)

    def setup_universal_connections(self):
        self.legend_pick_cid = self.figure_manager.canvas.mpl_connect(
            'pick_event', self.figure_manager.view_manager.legend_pick)

        self.credit_pick_cid = self.figure_manager.canvas.mpl_connect(
            'pick_event', self.figure_manager.view_manager.view_on_credit_line_pick)

        self.fan_pick_cid = self.figure_manager.canvas.mpl_connect(
            'pick_event', self.figure_manager.drag_fan_manager.on_pick)

        self.fan_release_cid = self.figure_manager.canvas.mpl_connect(
            'button_release_event', self.figure_manager.drag_fan_manager.on_release)

        self.fan_motion_cid = self.figure_manager.canvas.mpl_connect(
            'motion_notify_event', self.figure_manager.drag_fan_manager.on_motion)

        self.event_bus.emit('refresh_drag_connections')

    def run_mode_specific_actions(self, mode_name):
        if mode_name == 'note':
            self.event_bus.emit('refresh_note_listbox')
            self.event_bus.emit('refresh_note_locations')
        elif mode_name == 'trend':
            self.event_bus.emit('refresh_trend_column_list')
        elif mode_name == 'manual':  # Style mode
            self.event_bus.emit('refresh_style_columns')
        elif mode_name == 'view':
            self.event_bus.emit('refresh_view_dropdown')
            self.event_bus.emit('view_update_aggregate_dropdown')
        elif mode_name == 'plot':
            self.event_bus.emit('refresh_plot_mode_widget')
            self.event_bus.emit('update_plot_mode')

    def cleanup_previous_mode(self):
        if self.previous_mode_name is None:
            return

        if self.previous_mode_name == 'phase':
            self.figure_manager.phase_cleanup_temp_line()
        elif self.previous_mode_name == 'aim':
            self.figure_manager.aim_cleanup()
        elif self.previous_mode_name == 'trend':
            self.event_bus.emit('trend_cleanup')
        elif self.previous_mode_name == 'manual':  # Style mode
            self.event_bus.emit('style_cleanup')
        elif self.previous_mode_name == 'note':
            self.figure_manager.hover_manager.disable_note_crosshair()
            self.event_bus.emit('remove_note_locations')
            self.event_bus.emit('clear_previous_individual_note_object', data={'refresh': True})
        elif self.previous_mode_name == 'view':
            self.event_bus.emit('view_column_dropdown_update_label')
        elif self.previous_mode_name == 'plot' and self.current_mode_name != 'plot':
            self.event_bus.emit('plot_cleanup')

    def get_mode_widget(self, data):
        # Get a mode widget by name
        mode_identifier = data.get('mode', None)

        if mode_identifier is None:
            return None

        # If given a string mode name, return the corresponding widget
        if isinstance(mode_identifier, str) and mode_identifier in self.mode_widgets:
            return self.mode_widgets[mode_identifier]

        return None

    def get_current_mode_name(self):
        return self.current_mode_name

    def handle_phase_click(self, event):
        if self.figure_manager.pick_event:
            return

        text = self.mode_widgets['phase'].phase_change_input.text()
        coordinates = self.event_bus.emit('phase_line_handle_click', {'event': event, 'text': text})
        if coordinates:  # In case the user clicked outside the graph
            x, y = coordinates
            if x in self.figure_manager.x_to_date.keys():
                date = self.figure_manager.x_to_date[x]
                date_qt = QDate(date.year, date.month, date.day)
                self.mode_widgets['phase'].phase_date_input.setDate(date_qt)

    def handle_aim_click(self, event):
        text = self.mode_widgets['aim'].aim_text_input.text()
        info = self.event_bus.emit('aim_click_info', {'event': event, 'note': text})
        click_event = info[0] if info is not None else None

        if click_event:
            line_type = self.event_bus.emit("get_user_preference", ['aim_line_type', 'Slope'])

            if click_event == 'first' and line_type == 'Slope':
                _, baseline, d1 = info
                self.mode_widgets['aim'].aim_baseline_input.setText(str(baseline))
                self.mode_widgets['aim'].aim_target_input.setText('')
                self.mode_widgets['aim'].aim_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
            elif click_event == 'second' and line_type == 'Slope':
                _, d2, baseline, target = info
                self.mode_widgets['aim'].aim_target_input.setText(str(target))
                self.mode_widgets['aim'].aim_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))
                self.mode_widgets['aim'].aim_text_input.setText(self.figure_manager.aim_manager.slope)
            elif click_event == 'first' and line_type == 'Flat':
                _, target, d1 = info
                self.mode_widgets['aim'].aim_baseline_input.setText('')
                self.mode_widgets['aim'].aim_target_input.setText(str(target))
                self.mode_widgets['aim'].aim_start_date_input.setDate(QDate(d1.year, d1.month, d1.day))
            elif click_event == 'second' and line_type == 'Flat':
                _, d2, baseline, target = info
                self.mode_widgets['aim'].aim_end_date_input.setDate(QDate(d2.year, d2.month, d2.day))

    def handle_trend_click(self, event):
        self.event_bus.emit('trend_on_click', event)
        self.trend_adjust_dates()
        self.main_app.setFocus()

    def trend_adjust_dates(self):
        result = self.figure_manager.trend_adjust_dates()
        if result:
            date, order = result
            if order == 'first':
                self.mode_widgets['trend'].trend_start_date_input.setDate(QDate(date.year, date.month, date.day))
            elif order == 'second':
                self.mode_widgets['trend'].trend_end_date_input.setDate(QDate(date.year, date.month, date.day))

    def note_click(self, event):
        if self.figure_manager.pick_event:
            return

        x, y = event.xdata, event.ydata
        if x and y:  # Check if valid coordinates are passed
            y = self.figure_manager.data_manager.format_y_value(y)
            x = int(x)
            if x in self.figure_manager.x_to_date.keys():
                x_date = self.figure_manager.x_to_date[x].strftime(
                    self.figure_manager.data_manager.standard_date_string)
                dialog = NoteDialog(x_date, y, self.main_app)  # Pass the main window as parent
                dialog.exec()

    def point_click(self, event):
        self.event_bus.emit('style_point_on_click', event)

    def plot_click(self, event):
        if self.figure_manager.pick_event:
            return

        if event.inaxes and event.xdata is not None:
            x = self.figure_manager.data_manager.find_closest_x(int(event.xdata),
                                                                self.figure_manager.Chart.date_to_pos)
            if x in self.figure_manager.x_to_date:
                date = self.figure_manager.x_to_date[x]
                self.event_bus.emit('plot_date_clicked', date)


class FilesTab(QWidget):
    def __init__(self, chart_app, event_handlers, data_manager):
        super().__init__()
        self.chart_app = chart_app
        self.event_handlers = event_handlers
        self.data_manager = data_manager
        self.event_bus = EventBus()

        # Event bus subscriptions without data
        self.event_bus.subscribe('refresh_recent_charts_list', self.refresh_recent_charts_list)

        self.setup_ui()

    def setup_ui(self):
        files_layout = QVBoxLayout()  # Create a QVBoxLayout instance
        self.setLayout(files_layout)  # Set the layout to the FilesTab instance

        # Chart GroupBox
        group_box_chart = QGroupBox("Chart")
        layout_chart = QVBoxLayout()
        btn_new = QPushButton('New')
        btn_new.setToolTip('Get default chart')
        btn_import_delete = QPushButton('Import Data')
        btn_import_delete.setToolTip('Import spreadsheet data onto existing chart')
        btn_load = QPushButton('Open')
        btn_load.setToolTip('Open chart file')
        btn_save = QPushButton('Save')
        btn_save.setToolTip('Save chart file (data plus chart settings)')
        btn_image = QPushButton('Export Chart')
        btn_image.setToolTip('Get chart as png, jpeg, pdf, or svg')
        layout_chart.addWidget(btn_new)
        layout_chart.addWidget(btn_load)
        layout_chart.addWidget(btn_save)
        layout_chart.addWidget(btn_import_delete)
        layout_chart.addWidget(btn_image)
        group_box_chart.setLayout(layout_chart)
        files_layout.addWidget(group_box_chart)

        spacer = QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        files_layout.addItem(spacer)

        # Recent Charts ListBox - Remove the separate label since we'll add a header row
        self.lst_recent_charts = QListWidget()

        # Apply the same enhanced styling as NoteModeWidget
        self.lst_recent_charts.setStyleSheet("""
            QListWidget {
                font-size: 12px;
                font-family: monospace;
                border: 1px solid #ccc;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QListWidget::item {
                padding: 8px 5px;
                border-bottom: 1px solid #e0e0e0;
                min-height: 20px;
            }
            QListWidget::item:alternate {
                background-color: #f9f9f9;
            }
            QListWidget::item:hover {
                background-color: #e3f2fd;
            }
            QListWidget::item:selected {
                background-color: #2196f3;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #1976d2;
            }
            QListWidget QScrollBar:horizontal {
                height: 0px;
            }
        """)

        self.lst_recent_charts.setFixedHeight(500)
        files_layout.addWidget(self.lst_recent_charts)

        # Populate recents for listboxes
        self.event_bus.emit('refresh_recent_charts_list')

        # Button connections
        btn_import_delete.clicked.connect(lambda: self.event_handlers.import_data())
        btn_new.clicked.connect(self.new_chart_dialog)
        btn_image.clicked.connect(self.event_handlers.save_image)
        btn_save.clicked.connect(self.event_handlers.save_chart)
        btn_load.clicked.connect(lambda: self.event_handlers.load_chart(None))

        # Double-click connections for list items
        self.lst_recent_charts.itemDoubleClicked.connect(self.handle_chart_double_click)

        self.lst_recent_charts.installEventFilter(self)

        files_layout.addStretch()  # Prevents the buttons from vertically filling the whole panel

    def eventFilter(self, obj, event):
        # Check if obj is a valid QObject and event is a valid QEvent
        if not isinstance(obj, QObject) or not isinstance(event, QEvent):
            # If not proper types, just return false (don't handle)
            return False

        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_D:
                if obj == self.lst_recent_charts:
                    self.remove_selected_item(self.lst_recent_charts, 'recent_charts')
                    return True
        return super().eventFilter(obj, event)

    def remove_selected_item(self, list_widget, preference_key):
        selected_item = list_widget.currentItem()
        if selected_item:
            # Skip if header row is selected (index 0)
            index = list_widget.row(selected_item)
            if index == 0:  # Header row
                return

            file_path = selected_item.data(self.chart_app.FullFilePathRole)
            preference_value = self.event_bus.emit("get_user_preference", [preference_key, []])
            if file_path in preference_value:
                preference_value.remove(file_path)
                self.event_bus.emit("update_user_preference", [preference_key, preference_value])
            list_widget.takeItem(index)

    def refresh_recent_charts_list(self):
        self.lst_recent_charts.clear()
        header_text = "Recent charts"

        # Create header item with special styling
        header_item = QListWidgetItem(header_text)
        header_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        header_font = header_item.font()
        header_font.setFamily("Courier New")
        header_font.setBold(True)
        header_item.setFont(header_font)
        header_item.setBackground(QColor("#f5f5f5"))
        header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Make non-selectable
        self.lst_recent_charts.addItem(header_item)

        # Add data rows
        recent_charts = self.event_bus.emit("get_user_preference", ['recent_charts', []])
        db_chart_ids = self.data_manager.sqlite_manager.get_all_chart_ids()
        valid_chart_ids = []

        # Get chart display info for all recent charts that exist in database
        existing_chart_ids = [chart_id for chart_id in recent_charts if chart_id in db_chart_ids]
        chart_info = self.event_bus.emit('get_chart_display_info', existing_chart_ids)

        for chart_id in recent_charts:
            if chart_id in db_chart_ids and chart_id in chart_info:
                # Display just the name part (before timestamp)
                last_underscore = chart_id.rfind('_')
                display_name = chart_id[:last_underscore] if last_underscore != -1 else chart_id

                # Get ownership information from chart_info
                info = chart_info[chart_id]
                is_owner = info['is_owner']

                # Create item with icon if not owner
                if not is_owner:
                    # Create item with scaled share icon
                    original_icon = QIcon(':/images/share-nodes-solid.svg')
                    scaled_pixmap = original_icon.pixmap(16, 16)  # 16x16 pixels or whatever size you want
                    scaled_icon = QIcon(scaled_pixmap)
                    item = QListWidgetItem(scaled_icon, display_name)

                    # Set tooltip with owner name
                    owner_name = info['owner']
                    item.setToolTip(f"{owner_name}'s chart")
                else:
                    item = QListWidgetItem(display_name)

                # Set a monospace font for consistent spacing
                font = item.font()
                font.setFamily("Courier New")
                item.setFont(font)

                item.setData(self.chart_app.FullFilePathRole, chart_id)  # Store full ID
                self.lst_recent_charts.addItem(item)
                valid_chart_ids.append(chart_id)

        # Update the user preferences to remove any invalid entries
        if len(valid_chart_ids) != len(recent_charts):
            self.event_bus.emit("update_user_preference", ['recent_charts', valid_chart_ids])

    def handle_chart_double_click(self, item):
        if item:
            # Skip if header row is clicked (index 0)
            index = self.lst_recent_charts.row(item)
            if index == 0:  # Header row
                return

            # Adjust index for data charts (subtract 1 for header)
            chart_id = item.data(self.chart_app.FullFilePathRole)

            if chart_id:
                # Load the chart using the ID
                self.event_handlers.load_chart(chart_id)

                # Update recents list - ensure the selected chart is moved to the top
                recent_charts = self.event_bus.emit("get_user_preference", ['recent_charts', []])

                # Remove the chart ID if it exists in the list
                if chart_id in recent_charts:
                    recent_charts.remove(chart_id)
                # Also try removing as file path for backward compatibility
                elif isinstance(chart_id, str) and chart_id.endswith('.json') and chart_id in recent_charts:
                    recent_charts.remove(chart_id)

                # Add the chart ID to the top of the list
                recent_charts.insert(0, chart_id)

                # Update the preference and refresh the list
                self.event_bus.emit("update_user_preference", ['recent_charts', recent_charts])
                self.event_bus.emit('refresh_recent_charts_list')

    def new_chart_dialog(self):
        # Use the event bus to trigger a user prompt
        data = {
            'title': "New chart",
            'message': "Remove current chart?",
            'options': ['Yes', 'Cancel']
        }
        response = self.event_bus.emit('trigger_user_prompt', data)

        # Check if the first option (Yes) was selected
        if response == 0:  # Yes selected
            # Decide whether to save chart
            self.event_bus.emit('save_decision', data=None)

            # Save current chart if any and if autosave is enabled
            autosave = self.event_bus.emit("get_user_preference", ['autosave', False])
            if self.data_manager.chart_data['chart_file_path'] and autosave:
                self.event_handlers.save_chart(self.data_manager.chart_data['chart_file_path'])

            # Prevents from accidentally saving default chart
            self.data_manager.chart_data['chart_file_path'] = None
            self.chart_app.figure_manager.back_to_default()

            # Remove display name of imported/loaded chart
            self.chart_app.setWindowTitle(self.chart_app.window_title_str)

            # Select view mode by default
            self.event_bus.emit('view_mode_selected')


class EventHandlers:
    def __init__(self, chart_app, figure_manager, data_manager):
        self.chart_app = chart_app
        self.figure_manager = figure_manager
        self.data_manager = data_manager
        self.event_bus = self.chart_app.event_bus

        # Event subscriptions without data
        self.event_bus.subscribe('cleanup_after_chart_update', self.cleanup_after_chart_update)
        self.event_bus.subscribe('select_import_path', self.select_import_path)

        # Event subscriptions with data
        self.event_bus.subscribe('column_map_dialog', self.column_map_dialog, has_data=True)
        self.event_bus.subscribe('save_chart_as_recent', self.save_recent, has_data=True)
        self.event_bus.subscribe('trigger_user_prompt', self.trigger_user_prompt, has_data=True)

    def show_date_dialog(self):
        dialog = StartDateDialog(self.chart_app)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_start_date = dialog.get_date()
            self.event_bus.emit("update_chart_data", ['start_date', new_start_date])
            self.event_bus.emit('new_chart', new_start_date)

    def save_recent(self, data):
        file_path = data['file_path']
        recent_type = data['recent_type']
        max_recent = 25
        if file_path in self.data_manager.user_preferences[recent_type]:
            self.data_manager.user_preferences[recent_type].remove(file_path)
        self.data_manager.user_preferences[recent_type].insert(0, file_path)
        self.data_manager.user_preferences[recent_type] = self.data_manager.user_preferences[recent_type][
                                                          :max_recent]

    def column_map_dialog(self, file_path):
        dialog = DataColumnMappingDialog(self.chart_app, file_path)
        dialog.exec()

    def select_import_path(self, file_path=None):
        if file_path is None:
            # Get the last used import folder or fallback to home folder
            import_folder = self.event_bus.emit("get_user_preference", ['import_data_folder', ''])
            if not import_folder:
                import_folder = self.event_bus.emit("get_user_preference", ['home_folder', ''])

            # Open file dialog with support for CSV and Excel files
            file_path, _ = QFileDialog.getOpenFileName(self.chart_app, 'Select data set',
                                                       import_folder,
                                                       'CSV, Excel, ODS files (*.csv *.xls *.xlsx *.ods)')
        if file_path:
            # Save the directory as the import_data_folder preference
            import_dir = str(Path(file_path).parent)
            self.event_bus.emit("update_user_preference", ['import_data_folder', import_dir])

            return file_path

    def import_data(self, file_path=None):
        file_path = self.select_import_path(file_path)
        if not file_path:
            return

        # Create raw df for chart_data
        self.data_manager.chart_data['column_map'] = {}  # If re-importing
        self.event_bus.emit('column_mapped_raw_data_import', file_path)

        # Will be None if user canceled import
        if self.data_manager.chart_data['column_map'] is not None:
            # Make sure the user doesn't end up with a blank chart
            start_date = self.data_manager.prevent_blank_chart()

            # Get new chart
            self.event_bus.emit('new_chart', start_date)

    def save_image(self):
        dialog = SaveImageDialog(self.chart_app)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            format_selected, resolution_selected = dialog.get_selected_options()

            # Get the last used export folder or fallback to home folder
            export_folder = self.event_bus.emit("get_user_preference", ['chart_export_folder', ''])
            if not export_folder:
                export_folder = self.event_bus.emit("get_user_preference", ['home_folder', ''])

            options = f"{format_selected.upper()} files (*.{format_selected});;All files (*.*)"
            file_path, _ = QFileDialog.getSaveFileName(self.chart_app, 'Save file',
                                                       export_folder, options)
            if file_path:
                # Save the directory as the chart_export_folder preference
                export_dir = str(Path(file_path).parent)
                self.event_bus.emit("update_user_preference", ['chart_export_folder', export_dir])

                self.event_bus.emit('view_mode_selected')  # Will wipe any temporary markers before saving
                self.figure_manager.fig_save_image(file_path, format=format_selected, dpi=resolution_selected)

    def save_chart(self, chart_id=None):
        # If no explicit chart_id is provided, prompt the user for a name
        if not chart_id:

            # Prompt the user for a chart name
            chart_name, ok = QInputDialog.getText(
                self.chart_app,
                "Save Chart",
                "Enter a name for this chart:"
            )

            # User canceled or provided empty name
            if not ok or not chart_name.strip():
                return

            # Generate chart_id with timestamp to prevent conflicts
            timestamp = int(time.time())
            chart_id = f"{chart_name.strip()}_{timestamp}"

        # Save directly to database
        self.data_manager.chart_data['chart_file_path'] = chart_id
        self.event_bus.emit('save_complete_chart')

        # Update UI - display just the name part for readability
        display_name = chart_id.split('_')[0] if '_' in chart_id else chart_id
        self.chart_app.setWindowTitle(f'{self.chart_app.window_title_str} – {display_name}')

        # Update recents
        self.event_bus.emit('save_chart_as_recent', data={'file_path': chart_id, 'recent_type': 'recent_charts'})
        self.event_bus.emit('refresh_recent_charts_list')

    def load_chart(self, file_path):
        # Decide whether to save data
        if file_path is None:
            # Use the new chart browser dialog instead of QFileDialog
            from Popups import ChartBrowserDialog
            browser_dialog = ChartBrowserDialog(self.chart_app)

            # Make it non-modal but still behave like modal
            browser_dialog.setModal(False)
            browser_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
            browser_dialog.show()

            # Connect to finished signal instead of using exec()
            browser_dialog.finished.connect(lambda result: self._handle_browser_result(browser_dialog, result))
            return

        # If we have a file_path, proceed with loading directly
        if file_path:
            self.event_bus.emit('save_decision', data=None)
            self.event_bus.emit('load_chart', file_path)

    def _handle_browser_result(self, dialog, result):
        if result == QDialog.DialogCode.Accepted:
            file_path = dialog.get_selected_chart_path()
            dialog.deleteLater()  # Clean up the dialog

            if file_path:
                # Don't call load_chart() again - just emit the events directly
                self.event_bus.emit('save_decision', data=None)
                self.event_bus.emit('load_chart', file_path)
        else:
            dialog.deleteLater()

    def update_zero_count_handling(self, bool_type):
        # Update chart data with the new zero count handling setting
        self.event_bus.emit("update_chart_data", ['place_below_floor', bool_type])

        # Refresh each column's view instead of recreating the entire chart
        for column in self.data_manager.plot_columns.values():
            column.refresh_view()

        # Refresh the chart to show the changes
        self.event_bus.emit('refresh_chart')

        # Make sure current mode is enabled for key handling
        self.chart_app.mode_manager.set_interaction_mode()

    def update_cel_fan(self, status):
        self.figure_manager.drag_fan_manager.update_visibility()
        self.event_bus.emit('refresh_chart')

    def set_data_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self.chart_app, "Select Folder", QDir.homePath())
        if folder_path:
            short_path = Path(*Path(folder_path).parts[-1:])
            self.chart_app.settings_folder_btn.setText(str(short_path))
            self.chart_app.settings_folder_btn.setToolTip(folder_path)
            self.event_bus.emit("update_user_preference", ['home_folder', folder_path])

    def change_chart_type(self, index):
        new_type = self.chart_app.chart_type_settings_dropdown.itemData(index)
        self.event_bus.emit("update_chart_data", ['type', new_type])
        start_date = self.data_manager.prevent_blank_chart()
        self.event_bus.emit('new_chart', start_date)
        self.event_bus.emit('view_mode_selected')

    def cleanup_after_chart_update(self):
        # Make sure current mode is enabled for key handling
        self.chart_app.mode_manager.set_interaction_mode()

        # Update the chart type dropdown to reflect the loaded chart type
        chart_type = self.data_manager.chart_data['type']
        index = self.chart_app.chart_type_settings_dropdown.findData(chart_type)
        if index != -1:
            current_index = self.chart_app.chart_type_settings_dropdown.currentIndex()
            if current_index != index:
                self.chart_app.chart_type_settings_dropdown.blockSignals(True)
                self.chart_app.chart_type_settings_dropdown.setCurrentIndex(index)
                self.chart_app.chart_type_settings_dropdown.blockSignals(False)

        # Display name of loaded chart file
        chart_id = self.data_manager.chart_data['chart_file_path']
        if chart_id:
            last_underscore = chart_id.rfind('_')
            display_name = chart_id[:last_underscore] if last_underscore != -1 else chart_id
            self.chart_app.setWindowTitle(f'{self.chart_app.window_title_str} – {display_name}')
        else:
            self.chart_app.setWindowTitle(self.chart_app.window_title_str)

        self.event_bus.emit('refresh_trend_column_list')
        self.event_bus.emit('refresh_style_columns')

        # Set trend fit after chart type
        chart_mapping = {
            'Daily': 'Weekly',
            'Weekly': 'Monthly (Weekly x4)',
            'Monthly': 'Six-monthly (Weekly x26)',
            'Yearly': 'Five-yearly (Yearly x5)',
            'DailyMinute': 'Weekly (standard)',
            'WeeklyMinute': 'Monthly (Weekly x4)',
            'MonthlyMinute': 'Six-monthly (Weekly x26)',
            'YearlyMinute': 'Five-yearly (Yearly x5)'
        }
        chart_type = self.data_manager.chart_data['type']
        cel_unit = chart_mapping[chart_type]
        self.event_bus.emit('set_celeration_unit', data={'cel_unit': cel_unit})

        self.event_bus.emit('refresh_view_dropdown')
        self.event_bus.emit('view_update_aggregate_dropdown')

    def change_width(self, new_width):
        self.event_bus.emit("update_user_preference", ['width', new_width])
        self.event_bus.emit('new_chart', self.data_manager.chart_data['start_date'])

    def test_angle(self, show):
        self.figure_manager.settings_test_angle(show)

    def choose_color(self, color_category):
        # Convert the stored color code to a QColor object
        initial_color = QColor(self.event_bus.emit("get_user_preference", [color_category, '#000000']))
        QColorDialog.setCustomColor(0, QColor('#5ac9e2'))  # Behavior & Research Company hex extracted
        QColorDialog.setCustomColor(1, QColor('#6ad1e3'))  # Behavior & Research Company hex from website (1)
        QColorDialog.setCustomColor(2, QColor('#05c3de'))  # Behavior & Research Company hex from website (2)
        QColorDialog.setCustomColor(3, QColor('#71B8FF'))  # My original choice of font color
        QColorDialog.setCustomColor(4, QColor('#5a93cc'))  # My original choice of grid color
        color = QColorDialog.getColor(initial_color)
        # Carl Binder's grid choice on fluency.org: #55AAFF (font was just black)

        if color.isValid():
            self.event_bus.emit("update_user_preference", [color_category, color.name()])
            self.event_bus.emit('new_chart', self.data_manager.chart_data['start_date'])
            self.chart_app.mode_manager.set_interaction_mode()

    def trigger_user_prompt(self, data):
        # Check if 'options' exists in data, otherwise default to binary choice behavior
        if 'options' in data and isinstance(data['options'], list):
            prompt = UserPrompt(
                title=data['title'],
                message=data['message'],
                options=data['options']
            )
            return prompt.display()  # Now returns selected index or -1 if canceled
        else:
            # Maintain backward compatibility with binary choice
            prompt = UserPrompt(
                title=data['title'],
                message=data['message'],
                options=['OK'] if not data.get('choice', False) else [data.get('ok_text', 'OK'), data.get('cancel_text', 'Cancel')]
            )
            result = prompt.display()
            # Convert result to original boolean behavior for backward compatibility
            return result >= 0 if not data.get('choice', False) else (result == 0)


if __name__ == "__main__":
    # Run from app.py
    app = QApplication()
    app.setStyleSheet(styles.general_stylesheet)
    window = ChartApp()
    window.show()
    app.exec()
    sys.exit()
else:
    # Run from launcher (OpenCelerator.py)
    app = getattr(sys, 'app', None)
    app.setStyleSheet(styles.general_stylesheet)
    window = ChartApp()
    window.show()
