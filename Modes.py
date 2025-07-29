from app_imports import *
from DataManager import DataManager
from EventStateManager import EventBus
from Popups import InputDialog, ConfigurePhaseLinesDialog, ConfigureAimLinesDialog
from Popups import ConfigureTrendLinesDialog, NoteDialog, ModifyColumns, SpreadsheetDialog


class ModeWidget(QWidget):
    def __init__(self, figure_manager):
        super().__init__()
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # List to keep track of buttons that need double-click protection
        self.double_click_buttons = []

        # Initialize event bus instance for all mode widgets
        self.event_bus = EventBus()

        self.init_ui()

    def init_ui(self):
        pass

    def register_double_click_button(self, button, callback):
        """Register a button that should only respond to double-clicks.

        Args:
            button (QPushButton): The button to register
            callback (function): The function to call when button is double-clicked
        """
        button.setToolTip("Double-click")
        button.installEventFilter(self)
        self.double_click_buttons.append((button, callback))

        # Avoids type errors with receivers() method
        button.blockSignals(True)

    def eventFilter(self, obj, event):
        # Filter events for double-click buttons

        # Check if obj is a valid QObject and event is a valid QEvent
        if not isinstance(obj, QObject) or not isinstance(event, QEvent):
            return False

        # Check if double-click button
        for button, callback in self.double_click_buttons:
            # Make sure obj is the button object, not a QWidgetItem
            if obj == button and event.type() == QEvent.Type.MouseButtonDblClick:
                # Call the associated callback when double-clicked
                callback()
                return True  # Event was handled

        # Pass event to parent class if not handled
        return super().eventFilter(obj, event)


class StyleModeWidget(ModeWidget):
    def __init__(self, figure_manager):
        self.marker_style_map = {
            "Circle": "o", "Square": "s", "Triangle Up": "^", "Triangle Down": "v",
            "Star": "*", "Plus": "+", "X": "x", "Underscore": "_", "NoMarker": ''
        }
        self.line_style_map = {"Solid": "-", "Dashed": "--", "Dotted": ":", 'NoLine': ''}

        self.ui_element_map = {
            'marker_sizes': ('marker_size_spinbox', 'Marker Size'),
            'markers': ('marker_style_combobox', 'Marker Style'),
            'face_colors': ('marker_face_color_button', 'Marker Face Color'),
            'edge_colors': ('marker_edge_color_button', 'Marker Edge Color'),
            'line_colors': ('line_color_button', 'Line Color'),
            'line_width': ('line_width_spinbox', 'Line Width'),
            'line_styles': ('line_style_combobox', 'Line Style')
        }

        self.widgets = {}

        super().__init__(figure_manager)

        self.event_bus.subscribe('refresh_style_columns', self.refresh_style_columns)
        self.event_bus.subscribe('highlight_style_user_col', self.highlight_style_user_col)

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Add Column label directly to the layout
        column_label = QLabel(self.data_manager.ui_column_label)
        main_layout.addWidget(column_label)

        # Create the column selector dropdown
        self.column_selector = QComboBox()
        self.column_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Add "All" option
        self.column_selector.addItem("All")

        self.column_selector.currentTextChanged.connect(self.update_style_widgets)
        self.column_selector.activated.connect(self.highlight_style_user_col)
        main_layout.addWidget(self.column_selector)

        spacer_item = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        main_layout.addItem(spacer_item)

        # Create all style control widgets
        content_layout = QVBoxLayout()
        self._setup_style_controls(content_layout)

        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        content_layout.addItem(spacer)
        content_layout.addStretch()

        main_layout.addLayout(content_layout)
        self.layout.addLayout(main_layout)

    def _setup_style_controls(self, parent_layout):
        """Set up all style control widgets in the proper order"""
        # First color buttons
        for style_key in ['face_colors', 'edge_colors', 'line_colors']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            parent_layout.addWidget(widget)

        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        parent_layout.addItem(spacer)

        # Then dropdowns with labels
        for style_key in ['markers', 'line_styles']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            parent_layout.addWidget(QLabel(label))
            parent_layout.addWidget(widget)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Finally spinboxes with labels
        for style_key in ['marker_sizes', 'line_width']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            parent_layout.addWidget(QLabel(label))
            parent_layout.addWidget(widget)

    def highlight_style_user_col(self):
        user_col = self.column_selector.currentText()
        if user_col == "All":
            # When "All" is selected, don't highlight any specific column
            return
        elif user_col and user_col in self.data_manager.plot_columns:
            # For a specific column, highlight it
            col_instance = self.data_manager.plot_columns[user_col]
            col_instance.highlight()

    def _get_mode_styles_from_all_columns(self):
        """Get the most common style values across all columns"""
        if not self.data_manager.plot_columns:
            return None

        # Collect all values used across all columns/points
        all_values = {
            'marker_sizes': [],
            'marker': [],
            'face_color': [],
            'edge_color': [],
            'line_color': [],
            'line_width': [],
            'line_style': []
        }

        # Go through all plot columns and collect their actual values
        for column in self.data_manager.plot_columns.values():
            df = column.get_df()
            if not df.empty:
                all_values['marker_sizes'].extend(df['marker_sizes'].tolist())
                all_values['marker'].extend(df['markers'].tolist())
                all_values['face_color'].extend(df['face_colors'].tolist())
                all_values['edge_color'].extend(df['edge_colors'].tolist())
                all_values['line_color'].extend(df['line_colors'].tolist())
                all_values['line_width'].extend(df['line_width'].tolist())
                all_values['line_style'].extend(df['line_styles'].tolist())

        # Calculate mode (most common value) for each style property
        style = {}

        # For each property, find the most common value
        for key, values in all_values.items():
            if values:
                # Get the most frequent value
                value_counts = {}
                for value in values:
                    value_counts[value] = value_counts.get(value, 0) + 1

                # Find the value with the highest count
                mode_value = max(value_counts.items(), key=lambda x: x[1])[0]

                # Map the key back to the default style key format
                if key == 'face_color':
                    style['marker_face_color'] = mode_value
                elif key == 'edge_color':
                    style['marker_edge_color'] = mode_value
                elif key == 'line_style':
                    style['linestyle'] = mode_value
                elif key == 'line_width':
                    style['linewidth'] = mode_value
                elif key == 'marker_sizes':
                    style['markersize'] = mode_value
                else:
                    style[key] = mode_value

        return style

    def create_widget(self, style_key):
        if style_key == 'marker_sizes':
            widget = QDoubleSpinBox()
            widget.setRange(2, 200)
            widget.setSingleStep(2)
            widget.valueChanged.connect(
                lambda value: self.update_data_point_styles(style_key, value)
            )
        elif style_key == 'markers':
            widget = QComboBox()
            widget.addItems(self.marker_style_map.keys())
            widget.activated.connect(
                lambda: self.update_data_point_styles(style_key, self.marker_style_map[widget.currentText()])
            )
        elif style_key.endswith('colors'):
            widget = QPushButton(self.ui_element_map[style_key][1])
            widget.clicked.connect(
                lambda checked, key=style_key: self.choose_color(key)
            )
        elif style_key == 'line_width':
            widget = QDoubleSpinBox()
            widget.setRange(0.1, 10.0)
            widget.setSingleStep(0.1)
            widget.valueChanged.connect(
                lambda value: self.update_data_point_styles(style_key, value)
            )
        elif style_key == 'line_styles':
            widget = QComboBox()
            widget.addItems(self.line_style_map.keys())
            widget.activated.connect(
                lambda: self.update_data_point_styles(style_key, self.line_style_map[widget.currentText()])
            )
        return widget

    def refresh_style_columns(self, *args):
        current_text = self.column_selector.currentText()
        self.column_selector.clear()

        # Always add "All" as the first option
        self.column_selector.addItem("All")

        column_map = self.data_manager.chart_data['column_map']
        is_minute_chart = 'Minute' in self.data_manager.chart_data['type']

        if column_map:
            # Filter columns based on chart type
            data_columns = []
            for k, v in column_map.items():
                # Always exclude 'd' keys
                if k == 'd':
                    continue
                # Exclude 'm' keys only for non-minute charts
                if k == 'm' and not is_minute_chart:
                    continue
                data_columns.append(v)

            if data_columns:
                # Populate dropdown and try to restore previous selection
                self.column_selector.addItems(data_columns)

                # Try to restore previous selection, default to "All" if not found
                index = self.column_selector.findText(current_text)
                if index >= 0:
                    self.column_selector.setCurrentIndex(index)
                else:
                    self.column_selector.setCurrentIndex(0)  # Default to "All"

        self.update_style_widgets()

    def update_style_widgets(self):
        user_col = self.column_selector.currentText()

        if user_col == "All":
            # For "All", use the mode (most common value) across all columns
            mode_style = self._get_mode_styles_from_all_columns()
            if mode_style:
                self.populate_fields(mode_style)
        elif user_col in self.data_manager.plot_columns:
            # For a specific column, use its applied styles
            column_instance = self.data_manager.plot_columns[user_col]
            df = column_instance.get_df()

            if not df.empty:
                # Get the most common values from the dataframe for this column
                style = {}
                style['markersize'] = df['marker_sizes'].mode()[0]
                style['marker'] = df['markers'].mode()[0]
                style['marker_face_color'] = df['face_colors'].mode()[0]
                style['marker_edge_color'] = df['edge_colors'].mode()[0]
                style['line_color'] = df['line_colors'].mode()[0]
                style['linewidth'] = df['line_width'].mode()[0]
                style['linestyle'] = df['line_styles'].mode()[0]

                self.populate_fields(style)
            else:
                # Fallback to default if no data
                self.populate_fields(column_instance.column_default_style)

    def populate_fields_with_defaults(self):
        self.update_style_widgets()

    def block_signals(self, block):
        for widget in self.widgets.values():
            widget.blockSignals(block)

    def populate_fields(self, style_values):
        """Set the UI widgets to display the current style values"""
        # Block signals to prevent triggering updates while setting values
        self.block_signals(True)

        # Set numeric spinbox values if present
        if 'markersize' in style_values:
            self.widgets['marker_size_spinbox'].setValue(style_values['markersize'])
        if 'linewidth' in style_values:
            self.widgets['line_width_spinbox'].setValue(style_values['linewidth'])

        # Set marker style dropdown
        if 'marker' in style_values:
            marker_value = style_values['marker']
            for key, value in self.marker_style_map.items():
                if value == marker_value:
                    self.widgets['marker_style_combobox'].setCurrentText(key)
                    break

        # Set line style dropdown
        if 'linestyle' in style_values:
            line_style = style_values['linestyle']
            for key, value in self.line_style_map.items():
                if value == line_style:
                    self.widgets['line_style_combobox'].setCurrentText(key)
                    break

        # Set color button borders
        if 'marker_face_color' in style_values:
            self.set_button_border_style(
                self.widgets['marker_face_color_button'],
                style_values['marker_face_color']
            )
        if 'marker_edge_color' in style_values:
            self.set_button_border_style(
                self.widgets['marker_edge_color_button'],
                style_values['marker_edge_color']
            )
        if 'line_color' in style_values:
            self.set_button_border_style(
                self.widgets['line_color_button'],
                style_values['line_color']
            )

        # Re-enable signals
        self.block_signals(False)

    def set_button_border_style(self, button, color):
        button.setStyleSheet(f"border: 3px solid {color};")

    def choose_color(self, style_key):
        button = self.widgets[self.ui_element_map[style_key][0]]
        color = QColorDialog.getColor()
        if color.isValid():
            self.set_button_border_style(button, color.name())
            self.update_data_point_styles(style_key, color.name())

    def update_data_point_styles(self, style_category, style_value):
        user_col = self.column_selector.currentText()

        if user_col == "All":
            # Apply to all columns if "All" is selected
            for col_name in self.data_manager.plot_columns.keys():
                data = {'user_col': col_name, 'style_cat': style_category, 'style_val': style_value}
                self.event_bus.emit('update_point_styles', data)
        elif user_col:
            # Apply to selected column
            data = {'user_col': user_col, 'style_cat': style_category, 'style_val': style_value}
            self.event_bus.emit('update_point_styles', data)

        self.event_bus.emit('update_legend')


class ViewModeWidget(ModeWidget):
    default_agg = 'raw'

    def init_ui(self):
        self.dialog = InputDialog()
        self.event_bus = EventBus()

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Spacers
        spacer_height = 10
        spacer_width = 10
        spacer1 = QSpacerItem(spacer_width, spacer_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        spacer2 = QSpacerItem(spacer_width, spacer_height, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        # Dropdowns section with its own grid
        dropdown_layout = QGridLayout()
        dropdown_layout.setSpacing(10)

        self._setup_dropdown_section(dropdown_layout)

        dropdown_widget = QWidget()
        dropdown_widget.setLayout(dropdown_layout)
        main_layout.addWidget(dropdown_widget)

        # Add spacing between dropdown and checkbox sections
        main_layout.addItem(spacer1)

        # Checkbox sections with their own grid
        checkbox_layout = QGridLayout()
        checkbox_layout.setSpacing(10)

        self._setup_checkbox_section(checkbox_layout)

        checkbox_widget = QWidget()
        checkbox_widget.setLayout(checkbox_layout)
        main_layout.addWidget(checkbox_widget)

        # Add spacing between checkbox section and credit button
        main_layout.addItem(spacer2)

        self.layout.addLayout(main_layout)

        # Connect event bus subscriptions
        self._setup_event_subscriptions()

        # Initialize state for checkboxes
        self.sync_grid_checkboxes()
        self.sync_data_checkboxes()

    def _setup_dropdown_section(self, parent_layout):
        """Setup the dropdown section with column, group, and aggregate controls"""
        self.column_label = QLabel(self.data_manager.ui_column_label)
        self.column_dropdown = QComboBox()

        # Add "All" as the first option
        self.column_dropdown.addItem("All")

        group_label = QLabel("Group")
        self.group_dropdown = QComboBox()
        aggregate_label = QLabel("Aggregate")
        self.aggregate_dropdown = QComboBox()

        self.group_dropdown.addItems(['Day', 'Week', 'Month', 'Year'])
        self.update_aggregate_dropdown()  # Update aggregation options
        self.aggregate_dropdown.setCurrentText(self.default_agg)
        self.toggle_group_column()

        column_wrapper = QVBoxLayout()
        column_wrapper.addWidget(self.column_label)
        column_wrapper.addWidget(self.column_dropdown)

        parent_layout.addLayout(column_wrapper, 0, 0, 1, 2)
        parent_layout.addWidget(group_label, 1, 0)
        parent_layout.addWidget(self.group_dropdown, 1, 1)
        parent_layout.addWidget(aggregate_label, 2, 0)
        parent_layout.addWidget(self.aggregate_dropdown, 2, 1)

        # Connect signals for dropdowns
        self.column_dropdown.activated.connect(self.handle_column_dropdown_changed)
        self.group_dropdown.activated.connect(self.group_column_update)
        self.aggregate_dropdown.activated.connect(self.agg_column_update)

    def _setup_checkbox_section(self, parent_layout):
        """Setup the checkbox sections for visualization controls"""
        # Configure font for section headings
        font = QFont()

        # Create section headings
        grid_heading = QLabel("Grid")
        self.column_heading = QLabel(self.data_manager.ui_column_label)
        other_heading = QLabel("Other")
        for heading in [grid_heading, self.column_heading, other_heading]:
            heading.setFont(font)

        # Column section
        parent_layout.addWidget(self.column_heading, 0, 0)
        self.data_check = QCheckBox('Data')
        self.trend_check = QCheckBox('Change')
        self.bounce_check = QCheckBox('Bounce')
        self.celtext_check = QCheckBox('Label')

        parent_layout.addWidget(self.data_check, 1, 0)
        parent_layout.addWidget(self.trend_check, 2, 0)
        parent_layout.addWidget(self.bounce_check, 3, 0)
        parent_layout.addWidget(self.celtext_check, 4, 0)

        # Grid section
        parent_layout.addWidget(grid_heading, 0, 1)
        self.major_vertical_check = QCheckBox('Dates')
        self.major_horizontal_check = QCheckBox('Counts')
        self.minor_grid_check = QCheckBox('Minor')
        self.all_grid_check = QCheckBox('All')

        parent_layout.addWidget(self.all_grid_check, 1, 1)
        parent_layout.addWidget(self.major_vertical_check, 2, 1)
        parent_layout.addWidget(self.major_horizontal_check, 3, 1)
        parent_layout.addWidget(self.minor_grid_check, 4, 1)

        # Other section
        parent_layout.addWidget(other_heading, 5, 0, 1, 2)
        self.phase_check = QCheckBox('Phase')
        self.aim_check = QCheckBox('Aim')
        self.celfan_check = QCheckBox('Fan')
        self.credit_check = QCheckBox('Credit')
        self.legend_check = QCheckBox('Legend')

        parent_layout.addWidget(self.phase_check, 6, 0)
        parent_layout.addWidget(self.aim_check, 6, 1)
        parent_layout.addWidget(self.celfan_check, 7, 0)
        parent_layout.addWidget(self.credit_check, 7, 1)
        parent_layout.addWidget(self.legend_check, 8, 0)

        # Initially set all checkboxes to checked except all_grid_check
        for checkbox in [self.major_vertical_check, self.major_horizontal_check,
                         self.minor_grid_check, self.data_check, self.trend_check,
                         self.bounce_check, self.celtext_check, self.phase_check,
                         self.aim_check, self.celfan_check, self.credit_check, self.legend_check]:
            checkbox.setChecked(True)

        self.all_grid_check.setChecked(True)

        # Connect checkbox signals
        self._connect_checkbox_signals()

    def _connect_checkbox_signals(self):
        """Connect checkbox signals to their respective handlers"""
        # Data visibility checkboxes
        self.data_check.stateChanged.connect(lambda state: self.set_data_visibility('data', state))
        self.trend_check.stateChanged.connect(lambda state: self.set_data_visibility('trend_line', state))
        self.bounce_check.stateChanged.connect(lambda state: self.set_data_visibility('bounce', state))
        self.celtext_check.stateChanged.connect(lambda state: self.set_data_visibility('cel_label', state))

        # Grid checkboxes
        self.major_vertical_check.stateChanged.connect(
            lambda state: self.handle_individual_grid_toggle('view_major_date_gridlines', state))
        self.major_horizontal_check.stateChanged.connect(
            lambda state: self.handle_individual_grid_toggle('view_major_count_gridlines', state))
        self.minor_grid_check.stateChanged.connect(
            lambda state: self.handle_individual_grid_toggle('view_minor_gridlines', state))
        self.all_grid_check.stateChanged.connect(self.handle_all_grid_toggle)

        # Other checkboxes
        self.phase_check.stateChanged.connect(lambda state: self.event_bus.emit('view_phase_lines_toggle', state))
        self.aim_check.stateChanged.connect(lambda state: self.event_bus.emit('view_aims_toggle', state))
        self.celfan_check.stateChanged.connect(lambda state: self.event_bus.emit('view_cel_fan_toggle', state))
        self.legend_check.stateChanged.connect(lambda state: self.event_bus.emit('view_legend_toggle', state))
        self.credit_check.stateChanged.connect(lambda state: self.handle_credit_toggle(state))

    def _setup_event_subscriptions(self):
        """Set up all event bus subscriptions"""
        self.event_bus.subscribe('refresh_view_dropdown', self.refresh_view_dropdown)
        self.event_bus.subscribe('view_column_dropdown_update_label', self.view_column_dropdown_update_label)
        self.event_bus.subscribe('sync_grid_checkboxes', self.sync_grid_checkboxes)
        self.event_bus.subscribe('sync_data_checkboxes', self.sync_data_checkboxes)
        self.event_bus.subscribe('sync_misc_checkboxes', self.sync_misc_checkboxes)
        self.event_bus.subscribe('view_update_aggregate_dropdown', self.update_aggregate_dropdown)
        self.event_bus.subscribe('view_credit_lines_popup', self.credit_lines_popup)

    def _get_mode_settings_from_all_columns(self):
        """Get the most common settings from all columns"""
        if not self.data_manager.plot_columns:
            # Default settings if no columns exist
            return {
                'calendar_group': self.data_manager.chart_data['type'][0],
                'agg_type': 'median',
                'data': True,
                'trend_line': True,
                'bounce': True,
                'cel_label': True
            }

        # Collect settings from all columns
        settings_values = {
            'calendar_group': [],
            'agg_type': [],
            'data': [],
            'trend_line': [],
            'bounce': [],
            'cel_label': []
        }

        for column in self.data_manager.plot_columns.values():
            for key in settings_values:
                if key in column.view_settings:
                    settings_values[key].append(column.view_settings[key])

        # Determine most common value for each setting
        mode_settings = {}
        for key, values in settings_values.items():
            if not values:
                # Default if no values found
                if key == 'calendar_group':
                    mode_settings[key] = self.data_manager.chart_data['type'][0]
                elif key == 'agg_type':
                    mode_settings[key] = 'median'
                else:
                    mode_settings[key] = True
            else:
                # Find the most common value (mode)
                value_counts = {}
                for value in values:
                    if value in value_counts:
                        value_counts[value] += 1
                    else:
                        value_counts[value] = 1

                mode_settings[key] = max(value_counts.items(), key=lambda x: x[1])[0]

        return mode_settings

    def handle_individual_grid_toggle(self, event_name, state):
        # Emit the event for the specific checkbox
        self.event_bus.emit(event_name, state)
        # Check and update the 'All' checkbox state
        self.check_grid_state()

    def check_grid_state(self):
        check_states = [
            self.major_vertical_check.isChecked(),
            self.major_horizontal_check.isChecked(),
            self.minor_grid_check.isChecked()
        ]

        self.all_grid_check.blockSignals(True)
        if all(check_states):
            self.all_grid_check.setChecked(True)
        elif not any(check_states):
            self.all_grid_check.setChecked(False)
        self.all_grid_check.blockSignals(False)

    def update_aggregate_dropdown(self):
        self.aggregate_dropdown.clear()

        # Check if minute chart
        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        is_minute_chart = 'Minute' in chart_type
        if is_minute_chart:
            options = ['raw', 'mean', 'median', 'min', 'max']
        else:
            options = ['raw', 'sum', 'mean', 'median', 'min', 'max']

        self.aggregate_dropdown.addItems(options)

        # Get aggregation based on current selection
        user_col = self.column_dropdown.currentText()
        if user_col == "All":
            # For "All" selection, use the most common agg_type across all columns
            mode_settings = self._get_mode_settings_from_all_columns()
            agg_type = mode_settings.get('agg_type', self.default_agg)
            self.aggregate_dropdown.setCurrentText(agg_type)
        elif user_col and user_col in self.data_manager.plot_columns.keys():
            column_instance = self.data_manager.plot_columns[user_col]
            agg_type = column_instance.view_settings['agg_type']
            self.aggregate_dropdown.setCurrentText(agg_type)
        else:
            self.aggregate_dropdown.setCurrentText(self.default_agg)  # Default fallback

    def handle_credit_toggle(self, state):
        self.event_bus.emit('view_credit_lines_toggle', state)

    def handle_column_dropdown_changed(self, index):
        self.view_column_dropdown_update_label(index)
        self.sync_data_checkboxes()

        user_col = self.column_dropdown.currentText()
        if user_col != "All" and user_col in self.data_manager.plot_columns.keys():
            self.data_manager.plot_columns[user_col].highlight()

    def set_data_visibility(self, element_type, show):
        user_col = self.column_dropdown.currentText()

        # If "All" is selected, apply to all columns
        if user_col == "All":
            for col_name, column_instance in self.data_manager.plot_columns.items():
                column_instance.set_visibility(element_type, show)
                self.event_bus.emit('sync_column_view_settings', col_name)
        elif user_col in self.data_manager.plot_columns.keys():
            # Apply to just the selected column
            column_instance = self.data_manager.plot_columns[user_col]
            column_instance.set_visibility(element_type, show)
            self.sync_current_column_view_settings()

        self.event_bus.emit('refresh_chart')

    def sync_misc_checkboxes(self):
        view_settings = self.data_manager.chart_data['view']['chart']
        checkboxes = [
            (self.phase_check, 'phase'),
            (self.aim_check, 'aims'),
            (self.celfan_check, 'cel_fan'),
            (self.credit_check, 'credit'),
            (self.legend_check, 'legend')
        ]

        for checkbox, key in checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(view_settings[key])
            checkbox.blockSignals(False)

    def sync_grid_checkboxes(self):
        view_settings = self.data_manager.chart_data['view']['chart']
        checkboxes = [self.major_vertical_check, self.major_horizontal_check,
                      self.minor_grid_check, self.all_grid_check]

        for checkbox in checkboxes:
            checkbox.blockSignals(True)

        self.major_vertical_check.setChecked(view_settings['major_grid_dates'])
        self.major_horizontal_check.setChecked(view_settings['major_grid_counts'])
        self.minor_grid_check.setChecked(view_settings['minor_grid'])

        # Set the All checkbox based on whether all grid checkboxes are checked
        all_checked = (view_settings['major_grid_dates'] and
                       view_settings['major_grid_counts'] and
                       view_settings['minor_grid'])
        self.all_grid_check.setChecked(all_checked)

        for checkbox in checkboxes:
            checkbox.blockSignals(False)

    def handle_all_grid_toggle(self, state):
        # Block signals to prevent recursive calls
        self.major_vertical_check.blockSignals(True)
        self.major_horizontal_check.blockSignals(True)
        self.minor_grid_check.blockSignals(True)

        # Set all grid checkboxes to the same state
        self.major_vertical_check.setChecked(state)
        self.major_horizontal_check.setChecked(state)
        self.minor_grid_check.setChecked(state)

        # Unblock signals
        self.major_vertical_check.blockSignals(False)
        self.major_horizontal_check.blockSignals(False)
        self.minor_grid_check.blockSignals(False)

        # Emit events exactly like the individual checkboxes do
        self.event_bus.emit('view_major_date_gridlines', state)
        self.event_bus.emit('view_major_count_gridlines', state)
        self.event_bus.emit('view_minor_gridlines', state)

    def map_calendar_code_to_text(self, code):
        # Maps internal calendar code to dropdown text
        mapping = {
            'D': 'Day',
            'W': 'Week',
            'M': 'Month',
            'Y': 'Year'
        }
        return mapping.get(code, code)

    def map_calendar_text_to_code(self, text):
        # Maps dropdown text to internal calendar code
        mapping = {
            'Day': 'D',
            'Week': 'W',
            'Month': 'M',
            'Year': 'Y'
        }
        return mapping.get(text, text)

    def sync_data_checkboxes(self):
        user_col = self.column_dropdown.currentText()

        if user_col == "All":
            # For "All" selection, use the most common settings across all columns
            view_settings = self._get_mode_settings_from_all_columns()
        elif not user_col:
            # Use default view settings if no column is selected
            default_view_settings = {
                'calendar_group': self.data_manager.chart_data['type'][0],
                'agg_type': 'median',
                'data': True,
                'trend_line': True,
                'bounce': True,
                'cel_label': True
            }
            view_settings = default_view_settings
        else:
            # Use the specific column's settings
            column_instance = self.data_manager.plot_columns[user_col]
            view_settings = column_instance.view_settings

        # Sync checkboxes
        for checkbox, settings_key in [
            (self.data_check, 'data'),
            (self.trend_check, 'trend_line'),
            (self.bounce_check, 'bounce'),
            (self.celtext_check, 'cel_label')
        ]:
            checkbox.blockSignals(True)
            checkbox.setChecked(view_settings[settings_key])
            checkbox.blockSignals(False)

        # Sync dropdowns
        self.group_dropdown.blockSignals(True)
        self.aggregate_dropdown.blockSignals(True)

        # Map the internal calendar code to dropdown text
        calendar_text = self.map_calendar_code_to_text(view_settings['calendar_group'])
        self.group_dropdown.setCurrentText(calendar_text)

        self.aggregate_dropdown.setCurrentText(view_settings['agg_type'])
        self.group_dropdown.blockSignals(False)
        self.aggregate_dropdown.blockSignals(False)

        # Update group dropdown state
        self.toggle_group_column()

    def toggle_group_column(self):
        text = self.aggregate_dropdown.currentText()
        if text == 'raw':
            self.group_dropdown.setEnabled(False)
            self.group_dropdown.setStyleSheet('QComboBox:disabled { color: gray; }')
        else:
            self.group_dropdown.setEnabled(True)
            self.group_dropdown.setStyleSheet('')

    def _update_column_settings(self, setting_key, setting_value):
        user_col = self.column_dropdown.currentText()

        # If "All" is selected, apply to all columns
        if user_col == "All":
            for col_name, column_instance in self.data_manager.plot_columns.items():
                column_instance.view_settings[setting_key] = setting_value
                column_instance.refresh_view()
                self.event_bus.emit('sync_column_view_settings', col_name)
        elif user_col in self.data_manager.plot_columns.keys():
            # Apply to just the selected column
            column_instance = self.data_manager.plot_columns[user_col]
            column_instance.view_settings[setting_key] = setting_value
            column_instance.refresh_view()
            self.sync_current_column_view_settings()

        self.event_bus.emit('refresh_chart')

    def sync_current_column_view_settings(self):
        user_col = self.column_dropdown.currentText()
        if user_col and user_col != "All":
            self.event_bus.emit('sync_column_view_settings', user_col)

    def group_column_update(self):
        calendar_group_text = self.group_dropdown.currentText()
        calendar_group_code = self.map_calendar_text_to_code(calendar_group_text)
        self._update_column_settings('calendar_group', calendar_group_code)
        self.sync_current_column_view_settings()

    def agg_column_update(self):
        agg_type = self.aggregate_dropdown.currentText()
        self._update_column_settings('agg_type', agg_type)
        self.toggle_group_column()
        self.sync_current_column_view_settings()

    def view_column_dropdown_update_label(self, index=0):
        new_column_heading = self.column_dropdown.itemText(index)
        if new_column_heading:
            char_lim = 12
            if len(new_column_heading) > char_lim:
                new_column_heading = new_column_heading[:char_lim] + '...'
            self.column_heading.setText(new_column_heading)

    def refresh_view_dropdown(self):
        # Store current selection
        current_selection = self.column_dropdown.currentText()

        # Clear the dropdown
        self.column_dropdown.clear()

        # Always add "All" as the first option
        self.column_dropdown.addItem("All")

        # Get columns from column map
        column_map = self.data_manager.chart_data['column_map']
        is_minute_chart = 'Minute' in self.data_manager.chart_data['type']

        if column_map:
            filtered_columns = []
            for k, v in column_map.items():
                # Always exclude 'd' keys
                if k == 'd':
                    continue
                # Exclude 'm' keys only for non-minute charts
                if k == 'm' and not is_minute_chart:
                    continue
                filtered_columns.append(v)

            self.column_dropdown.addItems(filtered_columns)

        # Try to restore previous selection or default to "All"
        index = self.column_dropdown.findText(current_selection)
        if index >= 0:
            self.column_dropdown.setCurrentIndex(index)
        else:
            self.column_dropdown.setCurrentIndex(0)  # Default to "All"

        # Make sure we update the view settings based on the current selection
        self.handle_column_dropdown_changed(self.column_dropdown.currentIndex())

    def credit_lines_popup(self):
        if self.dialog.exec() == QDialog.DialogCode.Accepted:
            r1, r2 = self.dialog.get_inputs()
            self.dialog.credit_row1 = r1
            self.dialog.credit_row2 = r2
            self.figure_manager.data_manager.chart_data['credit'] = (r1, r2)
            self.event_bus.emit('view_update_credit_lines')
        self.event_bus.emit('refresh_chart')


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
        add_phase_line_btn.clicked.connect(
            lambda: self.event_bus.emit('phase_line_from_form', data={
                'text': self.phase_change_input.text(),
                'date': self.phase_date_input.text()
            })
        )

        self.register_double_click_button(undo_phase_line_btn, self.figure_manager.phase_undo_line)
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
        phase_text_type = self.event_bus.emit("get_user_preference", ['phase_text_type', 'Flag'])
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
        phase_text_position = self.event_bus.emit("get_user_preference", ['phase_text_position', 'Top'])
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
        for button in [self.phase_type_flag, self.phase_type_banner, self.position_top, self.position_center, self.position_bottom]:
            button.setEnabled(state)

    def update_preferences(self):
        phase_text_type = 'Flag' if self.phase_type_flag.isChecked() else 'Banner'
        self.event_bus.emit("update_user_preference", ['phase_text_type', phase_text_type])

    def update_position_preference(self, position):
        # Store the string value in user preferences
        self.event_bus.emit("update_user_preference", ['phase_text_position', position])


class AimModeWidget(ModeWidget):
    def init_ui(self):
        # Create the main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 0, 10, 10)

        # Create a QGridLayout for the input fields
        input_grid_layout = QGridLayout()
        input_grid_layout.setHorizontalSpacing(10)
        input_grid_layout.setVerticalSpacing(0)

        # Note input for aim
        self.aim_text_label = QLabel('Text')
        self.aim_text_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_text_input = QLineEdit('')

        # Baseline input for targeting (renamed from Start-Y)
        self.aim_baseline_label = QLabel('Baseline')
        self.aim_baseline_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_baseline_input = QLineEdit('')
        self.aim_baseline_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))

        # Y-value input for targeting
        self.aim_target_label = QLabel('Target')
        self.aim_target_label.setStyleSheet("margin-top: 10px; margin-bottom: 5px;")
        self.aim_target_input = QLineEdit('')
        self.aim_target_input.setValidator(QDoubleValidator(0.0, 9999.99, 4))

        # Start date input
        aim_label_start_date = QLabel('Start date')
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

        # Add widgets to the grid layout
        input_grid_layout.addWidget(self.aim_text_label, 0, 0, 1, 2)
        input_grid_layout.addWidget(self.aim_text_input, 1, 0, 1, 2)
        input_grid_layout.addWidget(self.aim_baseline_label, 2, 0)
        input_grid_layout.addWidget(self.aim_baseline_input, 3, 0)
        input_grid_layout.addWidget(self.aim_target_label, 4, 0)
        input_grid_layout.addWidget(self.aim_target_input, 5, 0)
        input_grid_layout.addWidget(aim_label_start_date, 2, 1)
        input_grid_layout.addWidget(self.aim_start_date_input, 3, 1)
        input_grid_layout.addWidget(aim_label_end_date, 4, 1)
        input_grid_layout.addWidget(self.aim_end_date_input, 5, 1)

        # Add input grid layout to the main layout
        main_layout.addLayout(input_grid_layout)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        # Add, Undo, and Configure buttons for setting aims
        add_aim_line_btn = QPushButton()
        add_aim_line_btn.setStyleSheet("margin-left: 0px; margin-top: 15px; margin-bottom: 15px")
        undo_aim_line_btn = QPushButton()
        undo_aim_line_btn.setStyleSheet("margin-top: 15px; margin-bottom: 15px")
        configure_aim_btn = QPushButton()
        configure_aim_btn.setStyleSheet("margin-right: 0px; margin-top: 15px; margin-bottom: 15px")

        # Add icons
        add_aim_line_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        undo_aim_line_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        configure_aim_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        # Add buttons to the button layout
        button_layout.addWidget(add_aim_line_btn)
        button_layout.addWidget(undo_aim_line_btn)
        button_layout.addWidget(configure_aim_btn)

        # Add the button layout to the main layout
        main_layout.addLayout(button_layout)

        # Create a container widget to hold the main layout
        container_widget = QWidget()
        container_widget.setLayout(main_layout)

        # Add the container widget to the existing layout
        self.layout.addWidget(container_widget)

        # Connect buttons to figure manager methods
        add_aim_line_btn.clicked.connect(lambda: self.figure_manager.aim_from_form(
            self.aim_text_input.text(),
            self.aim_baseline_input.text(),
            self.aim_target_input.text(),
            self.aim_start_date_input.text(),
            self.aim_end_date_input.text()
        ))
        self.register_double_click_button(undo_aim_line_btn, self.figure_manager.aim_undo)
        configure_aim_btn.clicked.connect(self.configure_aim_lines)

        # Create a horizontal layout for the radio buttons
        radio_buttons_layout = QGridLayout()

        # Aim type radio buttons
        aim_type_label = QLabel('Line type')
        self.aim_type_group = QButtonGroup(self)
        self.aim_type_flat = QRadioButton('Flat')
        self.aim_type_slope = QRadioButton('Slope')

        # Set the aim type based on user preferences
        aim_text_type = self.event_bus.emit("get_user_preference", ['aim_line_type', 'Flat'])
        self.aim_type_flat.setChecked(aim_text_type == 'Flat')
        self.aim_type_slope.setChecked(aim_text_type == 'Slope')

        self.aim_type_group.addButton(self.aim_type_flat)
        self.aim_type_group.addButton(self.aim_type_slope)

        # Connect radio button changes to a method to enable/disable Baseline
        self.aim_type_flat.toggled.connect(self.update_start_y_state)

        # Update aim line type
        self.aim_type_flat.toggled.connect(lambda checked: self.update_aim_type("Flat") if checked else None)
        self.aim_type_slope.toggled.connect(lambda checked: self.update_aim_type("Slope") if checked else None)

        # Position radio buttons
        position_label = QLabel('Text position')
        self.position_group = QButtonGroup(self)
        self.position_left = QRadioButton('Left')
        self.position_middle = QRadioButton('Middle')
        self.position_right = QRadioButton('Right')

        # Set the position based on user preferences
        aim_text_position = self.event_bus.emit("get_user_preference", ['aim_text_position', 'Middle'])
        self.position_left.setChecked(aim_text_position == 'Left')
        self.position_middle.setChecked(aim_text_position == 'Middle')
        self.position_right.setChecked(aim_text_position == 'Right')

        self.position_left.toggled.connect(lambda checked: self.update_aim_text_pos("Left") if checked else None)
        self.position_middle.toggled.connect(lambda checked: self.update_aim_text_pos("Middle") if checked else None)
        self.position_right.toggled.connect(lambda checked: self.update_aim_text_pos("Right") if checked else None)

        self.position_group.addButton(self.position_left)
        self.position_group.addButton(self.position_middle)
        self.position_group.addButton(self.position_right)

        # Add labels and radio buttons to the grid layout
        radio_buttons_layout.addWidget(aim_type_label, 0, 0)
        radio_buttons_layout.addWidget(self.aim_type_flat, 1, 0)
        radio_buttons_layout.addWidget(self.aim_type_slope, 2, 0)
        radio_buttons_layout.addWidget(position_label, 0, 1)
        radio_buttons_layout.addWidget(self.position_left, 1, 1)
        radio_buttons_layout.addWidget(self.position_middle, 2, 1)
        radio_buttons_layout.addWidget(self.position_right, 3, 1)

        # Add the grid layout with the radio buttons to the main layout
        main_layout.addLayout(radio_buttons_layout)

        # Initial call to set the Baseline state
        self.update_start_y_state()

    def update_aim_text_pos(self, text_pos):
        self.event_bus.emit("update_user_preference", ['aim_text_position', text_pos])

    def update_aim_type(self, aim_type):
        self.event_bus.emit("update_user_preference", ["aim_line_type", aim_type])

    def update_start_y_state(self):
        """Enable or disable the Baseline input and its label based on the selected line type."""
        is_flat = self.aim_type_flat.isChecked()
        self.aim_baseline_input.setEnabled(not is_flat)
        if is_flat:
            # Disable the input and change its appearance to indicate it's disabled
            self.aim_baseline_label.setStyleSheet("color: grey;")
            self.aim_baseline_input.setStyleSheet("background-color: #f0f0f0; color: grey;")
            self.aim_baseline_input.setText('')
            self.aim_text_input.setText('')
        else:
            # Enable the input and revert its appearance
            self.aim_baseline_label.setStyleSheet("color: black")
            self.aim_baseline_input.setStyleSheet("background-color: white;")
            self.aim_target_input.setStyleSheet("")

    def configure_aim_lines(self):
        dialog = ConfigureAimLinesDialog(self.figure_manager, self)
        dialog.exec()


class TrendModeWidget(ModeWidget):
    def init_ui(self):
        self.event_bus = EventBus()

        # Define combo box items
        self.trend_methods = ['Least-squares', 'Quarter-intersect', 'Split-middle-line', 'Mean', 'Median']
        self.envelope_methods = ['None', '5-95 percentile', 'Interquartile range', 'Standard deviation',
                                 '90% confidence interval']
        self.celeration_units = ['Daily', 'Weekly', 'Monthly (Weekly x4)', 'Six-monthly (Weekly x26)',
                                 'Yearly (Weekly x52)', 'Five-yearly (Yearly x5)']

        # Trend type selector
        trend_col_label = QLabel(self.data_manager.ui_column_label)
        trend_type_layout = QHBoxLayout()
        self.trend_type_combo = QComboBox()
        trend_type_layout.addWidget(self.trend_type_combo)
        self.layout.addWidget(trend_col_label)
        self.layout.addLayout(trend_type_layout)

        # Date inputs and buttons
        self.layout.addLayout(self._create_date_inputs())
        self.layout.addLayout(self._create_trend_buttons())

        # Trend controls
        self.layout.addSpacing(15)
        for widget in self._init_trend_controls():
            self.layout.addWidget(widget)
        self.layout.addStretch()

        # Disable add button by default
        self.update_trend_button_state()

        # Signal connections
        self.trend_type_combo.currentIndexChanged.connect(lambda: self.event_bus.emit('trend_cleanup'))
        self.trend_type_combo.currentTextChanged.connect(self.highlight_selected_data_series)
        self.trend_start_date_input.dateChanged.connect(self.figure_manager.trend_date1_changed)
        self.trend_end_date_input.dateChanged.connect(self.figure_manager.trend_date2_changed)

        # Event bus subscriptions
        self.event_bus.subscribe('refresh_trend_column_list', self.refresh_trend_column_list, has_data=False)
        self.event_bus.subscribe('set_celeration_unit', self.set_celeration_unit, has_data=True)
        self.event_bus.subscribe('get_current_trend_column', self.get_current_trend_column)
        self.event_bus.subscribe('highlight_selected_data_series', self.highlight_selected_data_series)
        self.event_bus.subscribe('update_trend_button_state', self.update_trend_button_state)

    def update_trend_button_state(self):
        # Update add button state based on marker status in TrendManager (FigureManager.py)
        first_marker, second_marker = self.event_bus.emit('get_trend_temp_marker_status')
        self.trend_add_btn.setEnabled(first_marker is not None and second_marker is not None)

    def get_current_trend_column(self):
        return self.trend_type_combo.currentText()

    def set_celeration_unit(self, data):
        cel_unit = data['cel_unit']
        self.celeration_unit_combo.setCurrentText(cel_unit)
        self.event_bus.emit("update_user_preference", ['celeration_unit', cel_unit])

    def highlight_selected_data_series(self, user_col=None):
        plot_columns = self.data_manager.plot_columns
        if user_col is None:
            user_col = self.get_current_trend_column()
            if user_col in plot_columns.keys():
                plot_columns[user_col].highlight()
        else:
            if user_col in plot_columns.keys():
                plot_columns[user_col].highlight()

    def refresh_trend_column_list(self):
        self.trend_type_combo.blockSignals(True)

        self.trend_type_combo.clear()
        column_map = self.data_manager.chart_data['column_map']
        if column_map:
            for sys_col, user_col in column_map.items():
                if sys_col not in ['d', 'm']:
                    self.trend_type_combo.addItem(user_col)

        self.trend_type_combo.blockSignals(False)

        # Also make sure add button is disabled
        self.update_trend_button_state()

    def _init_trend_controls(self):
        # Create and configure combos
        self.trend_method_combo = QComboBox()
        self.trend_method_combo.addItems(self.trend_methods)
        self.trend_method_combo.setCurrentText(
            self.event_bus.emit("get_user_preference", ['fit_method', 'Least-squares']))
        self.trend_method_combo.currentIndexChanged.connect(lambda index: self.event_bus.emit("update_user_preference",
                                                                                              ['fit_method',
                                                                                               self.trend_method_combo.currentText()]))

        self.envelope_method_combo = QComboBox()
        self.envelope_method_combo.addItems(self.envelope_methods)
        self.envelope_method_combo.setCurrentText(
            self.event_bus.emit("get_user_preference", ['bounce_envelope', 'None']))
        self.envelope_method_combo.currentIndexChanged.connect(
            lambda index: self.event_bus.emit("update_user_preference",
                                              ['bounce_envelope', self.envelope_method_combo.currentText()]))

        self.celeration_unit_combo = QComboBox()
        self.celeration_unit_combo.addItems(self.celeration_units)
        celeration_unit_text = self.event_bus.emit("get_user_preference", ['celeration_unit', 'Weekly'])
        self.celeration_unit_combo.setCurrentText(celeration_unit_text)
        self.celeration_unit_combo.currentIndexChanged.connect(
            lambda index: self.event_bus.emit("update_user_preference",
                                              ['celeration_unit', self.celeration_unit_combo.currentText()]))

        # Configure spinbox
        self.forward_projection_spinbox = QSpinBox()
        self.forward_projection_spinbox.setRange(0, 100)
        self.forward_projection_spinbox.setValue(self.event_bus.emit("get_user_preference", ['forward_projection', 0]))
        self.forward_projection_spinbox.valueChanged.connect(
            lambda value: self.event_bus.emit("update_user_preference", ['forward_projection', value]))

        # Create labels
        labels = {
            'trend_method': "Fit method",
            'forward_projection': "Forecast",
            'envelope_method': "Bounce envelope",
            'celeration_unit': f"{self.data_manager.ui_cel_label} unit"
        }

        return [
            QLabel(labels['trend_method']), self.trend_method_combo,
            QLabel(labels['forward_projection']), self.forward_projection_spinbox,
            QLabel(labels['envelope_method']), self.envelope_method_combo,
            QLabel(labels['celeration_unit']), self.celeration_unit_combo
        ]

    def _create_trend_buttons(self):
        trend_button_layout = QHBoxLayout()
        self.trend_add_btn = QPushButton()
        trend_undo_btn = QPushButton()
        trend_configure_btn = QPushButton()

        self.trend_add_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        self.trend_add_btn.setEnabled(True)
        trend_undo_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        trend_configure_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        trend_button_layout.addWidget(self.trend_add_btn)
        trend_button_layout.addWidget(trend_undo_btn)
        trend_button_layout.addWidget(trend_configure_btn)

        # Connect buttons - Plus button now directly fits and adds the trend
        self.trend_add_btn.clicked.connect(self.fit_and_add_trend)
        self.register_double_click_button(trend_undo_btn, self.undo_trend)
        trend_configure_btn.clicked.connect(self.configure_trends)

        return trend_button_layout

    def _create_date_inputs(self):
        # Date inputs for the start and end of the trend, arranged vertically
        date_input_layout = QVBoxLayout()

        date1_layout = QVBoxLayout()
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

        return date_input_layout

    def fit_and_add_trend(self):
        # First fit the trend
        trend_data = None
        self.event_bus.emit('plot_cel_trend', trend_data)

        # Immediately finalize/add the trend if a valid fit was created
        if self.figure_manager.trend_manager.trend_temp_fit_on:
            self.event_bus.emit('trend_finalize')

        self.setFocus()
        self.event_bus.emit('refresh_chart')

        self.update_trend_button_state()

    def undo_trend(self):
        user_col = self.get_current_trend_column()
        if user_col:
            col_instance = self.figure_manager.data_manager.plot_columns[user_col]
            col_instance.remove_trend()
            self.event_bus.emit('refresh_chart')

    def configure_trends(self):
        user_col = self.trend_type_combo.currentText()
        column_map = self.data_manager.chart_data['column_map']
        if column_map and user_col in column_map.values():
            trend_style = self.data_manager.plot_columns[user_col].get_default_trend_style()
            dialog = ConfigureTrendLinesDialog(user_col, trend_style, self.figure_manager, self)
            dialog.exec()


class NoteModeWidget(ModeWidget):
    # Text truncation parameter for easy testing
    TEXT_TRUNCATE_LENGTH = 8

    def __init__(self, figure_manager):
        super().__init__(figure_manager)

        # Update notes
        self.event_bus.subscribe('refresh_note_listbox', self.refresh_note_listbox, has_data=False)

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Custom list widget with improved styling
        self.note_list = QListWidget()
        self.note_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.note_list.itemClicked.connect(self.clicked_on_note)
        self.note_list.itemDoubleClicked.connect(self.double_clicked_on_note)
        self.note_list.setAlternatingRowColors(True)

        # Enhanced styling for better appearance
        self.note_list.setStyleSheet("""
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

        # Button layout
        button_layout = QHBoxLayout()
        remove_note_btn = QPushButton()
        remove_note_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        remove_note_btn.setStyleSheet("""
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
               background-color: #e0e0e0 !important;
           }
        """)
        button_layout.addWidget(remove_note_btn)

        # Combine all layouts
        main_layout.addWidget(self.note_list)  # List widget
        main_layout.addLayout(button_layout)  # Buttons

        # Set layout for the widget
        self.layout.addLayout(main_layout)

        # Connect button actions
        self.register_double_click_button(remove_note_btn, self.remove_note)

    def refresh_note_listbox(self):
        self.note_list.clear()
        chart_type = self.data_manager.chart_data['type']
        chart_period = chart_type[0] if chart_type else 'D'

        # Create header row first
        if chart_period == 'D':
            date_header_text = "Day"
        elif chart_period == 'W':
            date_header_text = "Week"
        elif chart_period == 'M':
            date_header_text = "Month"
        elif chart_period == 'Y':
            date_header_text = "Year"
        else:
            date_header_text = "Date"

        # Format header row with same spacing as data rows
        header_date = f"{date_header_text:^10}"  # Center-aligned, 10 chars wide
        header_text = f"{'Text':<12}"  # LEFT-aligned like data rows, 12 chars wide
        header_row = f"{header_date} {header_text}"

        # Create header item with special styling
        header_item = QListWidgetItem(header_row)
        header_font = header_item.font()
        header_font.setFamily("Courier New")
        header_font.setBold(True)
        header_item.setFont(header_font)
        header_item.setBackground(QColor("#f5f5f5"))
        header_item.setFlags(header_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)  # Make non-selectable
        self.note_list.addItem(header_item)

        # Add data rows
        all_notes = self.data_manager.chart_data['notes']
        for note in all_notes:
            text, date_str, y_val = note.split('|')

            # Truncate text if it's longer than the specified length
            if len(text) > self.TEXT_TRUNCATE_LENGTH:
                text_to_show = f'{text[:self.TEXT_TRUNCATE_LENGTH]}...'
            else:
                text_to_show = text

            # Format date based on chart type
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')

                if chart_period in ['D', 'W']:  # Daily or Weekly - show full date with 2-digit year
                    formatted_date = date_obj.strftime('%d-%m-%y')
                elif chart_period == 'M':  # Monthly - show only month number
                    formatted_date = date_obj.strftime('%m-%Y')
                elif chart_period == 'Y':  # Yearly - show only year number
                    formatted_date = date_obj.strftime('%Y')
                else:  # Default fallback to full date with 2-digit year
                    formatted_date = date_obj.strftime('%d-%m-%y')

            except:
                formatted_date = date_str  # Fallback to original format

            # Create properly formatted columns with centering for monthly/yearly
            if chart_period in ['M', 'Y']:  # Center align for monthly and yearly
                date_column = f"{formatted_date:^10}"  # Center-aligned, 10 chars wide
            else:  # Left align for daily and weekly
                date_column = f"{formatted_date:<10}"  # Left-aligned, 10 chars wide

            text_column = f"{text_to_show:<12}"  # Left-aligned, 12 chars wide

            # Combine columns with proper spacing
            note_details_to_show = f"{date_column} {text_column}"

            item = QListWidgetItem(note_details_to_show)

            # Set a monospace font for consistent spacing
            font = item.font()
            font.setFamily("Courier New")
            item.setFont(font)

            self.note_list.addItem(item)

    def remove_note(self):
        current_item = self.note_list.currentItem()  # Get the selected listbox item
        notes = self.data_manager.chart_data['notes']

        if current_item:
            # Get index
            idx = self.note_list.row(current_item)

            # Skip if header row is selected (index 0)
            if idx == 0:  # Header row
                return

            # Adjust index for data notes (subtract 1 for header)
            data_idx = idx - 1

            # Remove from listbox
            self.note_list.takeItem(idx)

            # Remove from chart data using adjusted index
            if data_idx < len(notes):
                del notes[data_idx]

            self.event_bus.emit('refresh_note_locations')
            self.event_bus.emit('clear_previous_individual_note_object', data={'refresh': True})

    def clicked_on_note(self, item):
        if item:
            # Skip if header row is clicked (index 0)
            index = self.note_list.row(item)
            if index == 0:  # Header row
                return

            # Adjust index for data notes (subtract 1 for header)
            data_index = index - 1

            # Get the full note data using the adjusted index
            full_note = self.data_manager.chart_data['notes'][data_index]
            text, date_str, y_val = full_note.split('|')

            # Emit event with the full note data
            self.event_bus.emit('show_individual_note_locations', data={'date_str': date_str, 'note_y': y_val})

    def double_clicked_on_note(self, item):
        if item:
            # Skip if header row is clicked (index 0)
            index = self.note_list.row(item)
            if index == 0:  # Header row
                return

            # Adjust index for data notes (subtract 1 for header)
            data_index = index - 1

            # Get the full note data
            full_note = self.data_manager.chart_data['notes'][data_index]
            text, date_str, y_val = full_note.split('|')

            # Create and show the note dialog
            dialog = NoteDialog(date_str, float(y_val), self)
            dialog.text_edit.setPlainText(text)  # Set the existing note text

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the new text from the dialog
                new_text = dialog.text_edit.toPlainText().replace('|', '')
                if new_text != text:  # Only update if the text changed
                    # Remove old note
                    del self.data_manager.chart_data['notes'][data_index]
                    # The new note will have been added by the dialog's save_note method
                    self.refresh_note_listbox()


class PlotModeWidget(ModeWidget):
    def __init__(self, figure_manager):
        self.data_manager = figure_manager.data_manager
        self.date_handler = ChartDateHandler(figure_manager.data_manager, figure_manager)
        super().__init__(figure_manager)

        # Vertical line for selected date
        self.selected_date_line = None

        # Event bus subscriptions
        self._setup_event_subscriptions()

        # Track column inputs
        self.column_input_list = {}

    def _setup_event_subscriptions(self):
        # Set up event bus subscriptions
        self.event_bus.subscribe('refresh_plot_mode_widget', self.refresh_plot_mode_widget, has_data=False)
        self.event_bus.subscribe('update_plot_mode', self.update_plot_mode, has_data=False)
        self.event_bus.subscribe('plot_date_clicked', self.plot_date_clicked, has_data=True)
        self.event_bus.subscribe('modify_columns', ModifyColumns(self).exec)

    def init_ui(self):
        # Conditionals for direct data entry
        self.is_minute_chart = 'Minute' in self.data_manager.chart_data['type']

        # Create UI components
        self._create_main_layout()

        # Initial state update
        self.update_plot_timing_inputs()
        self.update_spreadsheet_button_visibility()

        # Initial validation for minute chart mode
        self.validate_time_inputs()

    def _create_main_layout(self):
        # Create container for time inputs
        self.time_container = QWidget()

        # Main layout setup
        plot_layout = QVBoxLayout()

        # Add header components
        self._setup_header_components(plot_layout)

        # Add column input area
        self._setup_column_input_area(plot_layout)

        # Add time inputs
        self._setup_time_inputs()
        plot_layout.addWidget(self.time_container)

        # Add date selector
        self._setup_date_selector(plot_layout)

        # Add action buttons
        self._setup_action_buttons(plot_layout)

        # Add data info section
        self._setup_data_info_section(plot_layout)

        self.layout.addLayout(plot_layout)

    def _setup_header_components(self, parent_layout):
        # Add Column label at the top
        column_label = QLabel(self.data_manager.ui_column_label)
        parent_layout.addWidget(column_label)

        # Column name input box (visible only when adding new column via dialog)
        self.column_name_input = QLineEdit()
        self.column_name_input.setPlaceholderText("Enter column name")
        self.column_name_input.setVisible(False)
        parent_layout.addWidget(self.column_name_input)

        # Add marker style dropdown (visible only when adding new column via dialog)
        self.marker_combo = QComboBox()
        self.marker_combo.setVisible(False)
        self.marker_combo.addItem("⬤ Increase", "c")
        self.marker_combo.addItem("✕ Decrease", "i")
        self.marker_combo.addItem("▼ Other", "o1")
        parent_layout.addWidget(self.marker_combo)

    def _setup_column_input_area(self, parent_layout):
        # Create scrollable area for column inputs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.column_input_list_layout = QVBoxLayout(self.scroll_content)
        self.column_input_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.scroll_content)
        parent_layout.addWidget(self.scroll_area)

    def _setup_time_inputs(self):
        # Time inputs layout
        time_layout = QVBoxLayout(self.time_container)

        # Time inputs - using regular input fields with labels above
        time_inputs_layout = QHBoxLayout()

        # Hour input
        hour_layout = QVBoxLayout()
        hour_label = QLabel("Hour")
        self.hour_input = QLineEdit()
        self.hour_input.setPlaceholderText("0")
        self.hour_input.setValidator(QIntValidator(0, 23))
        hour_layout.addWidget(hour_label)
        hour_layout.addWidget(self.hour_input)

        # Minute input
        min_layout = QVBoxLayout()
        min_label = QLabel("Min")
        self.min_input = QLineEdit()
        self.min_input.setPlaceholderText("0")
        self.min_input.setValidator(QIntValidator(0, 59))
        min_layout.addWidget(min_label)
        min_layout.addWidget(self.min_input)

        # Second input
        sec_layout = QVBoxLayout()
        sec_label = QLabel("Sec")
        self.sec_input = QLineEdit()
        self.sec_input.setPlaceholderText("0")
        self.sec_input.setValidator(QIntValidator(0, 59))
        sec_layout.addWidget(sec_label)
        sec_layout.addWidget(self.sec_input)

        # Add the individual time layouts to a horizontal layout
        time_inputs_layout.addLayout(hour_layout)
        time_inputs_layout.addLayout(min_layout)
        time_inputs_layout.addLayout(sec_layout)

        time_layout.addLayout(time_inputs_layout)

        # Connect time inputs to validation
        self.hour_input.textChanged.connect(self.validate_time_inputs)
        self.min_input.textChanged.connect(self.validate_time_inputs)
        self.sec_input.textChanged.connect(self.validate_time_inputs)

    def _setup_date_selector(self, parent_layout):
        # Date selector row
        date_layout = QVBoxLayout()
        date_buttons_layout = QHBoxLayout()

        self.prev_date_btn = QPushButton()
        self.prev_date_btn.setIcon(QIcon(':/images/arrow-left-solid.svg'))
        self.prev_date_btn.clicked.connect(lambda: self.adjust_date(increment=False))

        self.date_btn = QPushButton()
        self.date_btn.clicked.connect(self.show_calendar)

        # Update date button initially
        self.update_date_button()

        self.next_date_btn = QPushButton()
        self.next_date_btn.setIcon(QIcon(':/images/arrow-right-solid.svg'))
        self.next_date_btn.clicked.connect(lambda: self.adjust_date(increment=True))

        date_buttons_layout.addWidget(self.prev_date_btn)
        date_buttons_layout.addWidget(self.date_btn)
        date_buttons_layout.addWidget(self.next_date_btn)

        date_layout.addLayout(date_buttons_layout)
        parent_layout.addLayout(date_layout)

    def _setup_action_buttons(self, parent_layout):
        # Action buttons
        button_layout = QHBoxLayout()

        # Add data button (plus icon)
        self.add_data_btn = QPushButton()
        self.add_data_btn.clicked.connect(self.add_data)
        self.add_data_btn.setIcon(QIcon(':/images/plus-solid.svg'))

        # Create remove data button (minus icon) with double-click requirement
        self.remove_data_btn = QPushButton()
        self.remove_data_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        self.register_double_click_button(self.remove_data_btn, self.remove_data)

        # Create configure columns button (cog icon)
        configure_columns_btn = QPushButton()
        configure_columns_btn.setToolTip('Modify columns')
        configure_columns_btn.setIcon(QIcon(':/images/gear-solid.svg'))
        configure_columns_btn.clicked.connect(self.show_modify_columns_dialog)

        button_layout.addWidget(self.add_data_btn)
        button_layout.addWidget(self.remove_data_btn)
        button_layout.addWidget(configure_columns_btn)
        parent_layout.addLayout(button_layout)

    def _setup_data_info_section(self, parent_layout):
        # Data points label
        data_label_layout = QVBoxLayout()
        self.data_label = QLabel('')
        data_label_layout.addWidget(self.data_label)

        # Add file path label
        self.file_path_label = QLabel('')
        self.file_path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the label
        data_label_layout.addWidget(self.file_path_label)

        # Add stretch to push everything to the bottom
        data_label_layout.addStretch()

        # Add spreadsheet button
        self.open_spreadsheet_btn = QPushButton("Spreadsheet")
        self.open_spreadsheet_btn.clicked.connect(self.open_spreadsheet)
        data_label_layout.addWidget(self.open_spreadsheet_btn)

        # Remove parent_layout.addStretch() since we want the data_label_layout to anchor at the bottom
        parent_layout.addLayout(data_label_layout)

    def show_modify_columns_dialog(self):
        self.event_bus.emit('modify_columns')

    def create_column_input_row(self, column_name):
        # Create a row for a column with input field
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # Create count input field with column name as placeholder
        count_input = QLineEdit()
        count_input.setPlaceholderText(column_name)
        count_input.setValidator(QIntValidator())

        # Add widget to row
        row_layout.addWidget(count_input)

        # Store reference to input field
        self.column_input_list[column_name] = count_input

        return row_widget

    def remove_data(self):
        self.event_bus.emit('remove_latest_entry')

    def update_plot_mode(self):
        # Update date handler calendar type
        self.date_handler.update_calendar_type()

        # Set current_date to normalized today's date (period-end)
        today = QDate.currentDate()
        normalized_date = self.date_handler.normalize_date_for_calendar_type(today)

        # Ensure date is valid or get middle date
        valid_date, _ = self.date_handler.ensure_valid_date(normalized_date)
        self.date_handler.current_date = valid_date

        # Update UI
        self.update_date_button()
        self.update_selected_date_line()

    def plot_date_clicked(self, date):
        qdate = QDate(date.year, date.month, date.day)

        # Normalize the date according to calendar type
        qdate = self.date_handler.normalize_date_for_calendar_type(qdate)

        # Update date in plot mode widget
        self.date_handler.current_date = qdate
        self.update_date_button()
        self.update_selected_date_line()  # Will refresh the chart

    def validate_time_inputs(self):
        # Validates time inputs and enables/disables add button accordingly
        if self.is_minute_chart:
            # Enable add button only if at least one time field has data
            has_time_data = bool(self.hour_input.text() or
                                 self.min_input.text() or
                                 self.sec_input.text())
            self.add_data_btn.setEnabled(has_time_data)

            # Update icon based on enabled state
            if has_time_data:
                self.add_data_btn.setIcon(QIcon(':/images/plus-solid.svg'))
            else:
                self.add_data_btn.setIcon(QIcon(':/images/plus-solid-disabled.svg'))
        else:
            # Always enable for non-minute charts
            self.add_data_btn.setEnabled(True)
            self.add_data_btn.setIcon(QIcon(':/images/plus-solid.svg'))

    def update_plot_timing_inputs(self):
        self.is_minute_chart = 'Minute' in self.data_manager.chart_data['type']
        self.time_container.setVisible(self.is_minute_chart)

        # Update button state after changing chart type
        self.validate_time_inputs()

    def refresh_column_list(self):
        # Clear existing widgets
        self._clear_column_inputs()

        # Reset tracking dictionary
        self.column_input_list.clear()

        # Get column data
        data_columns = self._get_data_columns()
        num_columns = len(data_columns)

        # Determine column display strategy and apply it
        if self._should_use_direct_layout(num_columns):
            self._apply_direct_layout_strategy(data_columns)
        else:
            self._apply_scroll_area_strategy(data_columns)

        # Update marker combo options
        self._update_marker_combo_options()

    def _clear_column_inputs(self):
        # Clear from scroll area
        for i in reversed(range(self.column_input_list_layout.count())):
            widget = self.column_input_list_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Find plot_layout
        plot_layout = self._find_plot_layout()

        if plot_layout:
            # Find indices
            marker_index = self._find_widget_index(plot_layout, self.marker_combo)
            scroll_index = self._find_widget_index(plot_layout, self.scroll_area)

            if marker_index != -1 and scroll_index != -1:
                # Remove widgets between marker_combo and scroll_area
                for i in reversed(range(marker_index + 1, scroll_index)):
                    widget = plot_layout.itemAt(i).widget()
                    if widget:
                        widget.deleteLater()

    def _find_plot_layout(self):
        # Find the plot_layout containing marker_combo
        for i in range(self.layout.count()):
            item = self.layout.itemAt(i)
            if item and item.layout():
                for j in range(item.layout().count()):
                    widget_item = item.layout().itemAt(j)
                    if widget_item and widget_item.widget() == self.marker_combo:
                        return item.layout()
        return None

    def _find_widget_index(self, layout, widget):
        # Find the index of a widget in a layout
        for i in range(layout.count()):
            if layout.itemAt(i).widget() == widget:
                return i
        return -1

    def _get_data_columns(self):
        # Get column names from data manager
        column_map = self.data_manager.chart_data['column_map']
        data_columns = []
        if column_map:
            data_columns = [v for k, v in column_map.items() if k not in ['d', 'm']]
        return data_columns

    def _should_use_direct_layout(self, num_columns):
        # Determine if we should use direct layout or scroll area
        return num_columns <= 4

    def _apply_direct_layout_strategy(self, data_columns):
        # Apply direct layout strategy for small column counts
        plot_layout = self._find_plot_layout()
        marker_index = self._find_widget_index(plot_layout, self.marker_combo)

        if plot_layout and marker_index != -1:
            self.scroll_area.setVisible(False)
            insert_point = marker_index + 1

            for column in data_columns:
                row = self.create_column_input_row(column)
                plot_layout.insertWidget(insert_point, row)
                insert_point += 1

    def _apply_scroll_area_strategy(self, data_columns):
        # Apply scroll area strategy for larger column counts
        self.scroll_area.setVisible(True)

        # Add widgets to scroll content
        for column in data_columns:
            row = self.create_column_input_row(column)
            self.column_input_list_layout.addWidget(row)

        # Configure scroll area
        ROW_HEIGHT = 40  # Height in pixels per row
        self.scroll_area.setFixedHeight(4 * ROW_HEIGHT)  # Show exactly 4 rows
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll_content.setMinimumHeight(len(data_columns) * ROW_HEIGHT)

    def _update_marker_combo_options(self):
        # Update marker combo options
        column_map = self.data_manager.chart_data['column_map']
        self.marker_combo.clear()

        if column_map:
            if 'c' not in column_map.keys():
                self.marker_combo.addItem("⬤ Increase", "c")
            if 'i' not in column_map.keys():
                self.marker_combo.addItem("✕ Decrease", "i")
            self.marker_combo.addItem("▼ Other", "o1")

    def refresh_plot_mode_widget(self):
        self.update_plot_timing_inputs()
        self.refresh_column_list()

        # Update calendar type in the date handler
        self.date_handler.update_calendar_type()

        # Update date display
        self.update_date_button()

        # Update vertical line
        # self.update_selected_date_line()

        # # Update spreadsheet button visibility
        self.update_spreadsheet_button_visibility()

    def update_selected_date_line(self):
        # Get valid date and corresponding timestamp
        valid_date, timestamp = self.date_handler.ensure_valid_date(self.date_handler.current_date)

        # Update current_date if it changed
        if valid_date != self.date_handler.current_date:
            self.date_handler.current_date = valid_date
            self.update_date_button()

        # Draw line if we have a valid timestamp
        if timestamp is not None:
            x_pos = self.figure_manager.Chart.date_to_pos.get(timestamp)
            if x_pos is not None:
                self.figure_manager.plot_draw_manager.draw_date_line(x_pos)

    def show_calendar(self):
        # Show calendar widget for date selection
        calendar = QCalendarWidget()
        calendar.setSelectedDate(self.date_handler.current_date)

        # Create a dialog to hold the calendar
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Date")
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.addWidget(calendar)

        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        dialog_layout.addWidget(button_box)

        if dialog.exec_() == QDialog.DialogCode.Accepted:
            # Update current_date in date handler
            self.date_handler.current_date = calendar.selectedDate()
            self.update_date_button()

            # Update vertical line
            self.update_selected_date_line()

    def update_date_button(self):
        # Get formatted date text and today status from date handler
        date_str, is_today = self.date_handler.get_formatted_date_text()
        self.date_btn.setText(date_str)

        # Highlight if date is today
        if is_today:
            self.date_btn.setStyleSheet("QPushButton { color: white; background-color: #5e81ac; }")
        else:
            self.date_btn.setStyleSheet("")

    def adjust_date(self, increment=True):
        # Use date handler to adjust date
        self.date_handler.adjust_date(increment)

        # Update UI elements
        self.update_date_button()
        self.update_selected_date_line()

    def add_data(self):
        # Collect data from input fields
        user_cols, count_strs, sys_cols = self._collect_column_data()

        # If no values were entered, return
        if not user_cols:
            return

        # Prepare data for event emission
        data = {
            'user_col': user_cols,
            'sys_col': sys_cols,
            'count_str': count_strs,
            'date_str': self.date_handler.current_date.toString('yyyy-MM-dd'),
            'hour_str': self.hour_input.text(),
            'minute_str': self.min_input.text(),
            'second_str': self.sec_input.text()
        }

        # Clear all count input fields
        for input_field in self.column_input_list.values():
            input_field.clear()

        self.event_bus.emit('direct_data_entry', data)
        self.refresh_column_list()
        self.update_spreadsheet_button_visibility()

    def _collect_column_data(self):
        # Extract data from all input fields with values
        user_cols = []
        count_strs = []
        sys_cols = []

        # Get all column inputs that have entries
        for col_name, input_field in self.column_input_list.items():
            count_value = input_field.text()
            user_cols.append(col_name)
            count_strs.append(count_value)

            # Look up the appropriate sys_col for this column
            column_map = self.data_manager.chart_data['column_map']
            sys_col = None
            for sc, uc in column_map.items():
                if uc == col_name and sc not in ['d', 'm']:
                    sys_col = sc
                    break

            # Append the sys_col (or default to "o1" if not found)
            sys_cols.append(sys_col or "o1")

        return user_cols, count_strs, sys_cols

    def open_spreadsheet(self):
        """
        Opens a spreadsheet-like dialog for viewing and editing chart data.
        Provides a better user experience than exporting to an external file.
        """
        if self.data_manager.df_raw is None or self.data_manager.df_raw.empty:
            QMessageBox.warning(self, "No Data", "There is no data to display.")
            return

        # Create and show the dialog
        dialog = SpreadsheetDialog(self)

        # Connect to the dataChanged signal
        dialog.dataChanged.connect(self.on_spreadsheet_data_changed)

        # Show the dialog
        dialog.exec()

    def on_spreadsheet_data_changed(self):
        """Handle data changes from the spreadsheet dialog"""
        # Refresh the plot mode UI
        self.event_bus.emit('refresh_plot_mode_widget')

        # Refresh the chart
        self.event_bus.emit('refresh_chart')

        # Update date display in plot mode
        self.update_date_button()

    def update_spreadsheet_button_visibility(self):
        # Temporarily disabled until I've fixed stuff here
        self.open_spreadsheet_btn.setVisible(False)

        # df = self.data_manager.df_raw
        # has_data = df is not None and not df.empty
        # self.open_spreadsheet_btn.setVisible(has_data)


class ChartDateHandler:
    def __init__(self, data_manager, figure_manager):
        self.data_manager = data_manager
        self.figure_manager = figure_manager

        # Store the calendar type
        self.calendar_type = self.data_manager.chart_data['type'][0]

        # Initialize with current date but normalize it to period-end
        today = QDate.currentDate()
        self.current_date = self.normalize_date_for_calendar_type(today)

    def normalize_date_for_calendar_type(self, date):
        """
        Normalizes a date according to the current calendar type (D, W, M, Y),
        aligning with the period-end date format in the date_to_pos mapping.
        Returns the normalized QDate.
        """
        if self.calendar_type == 'W':
            # Keep the Sunday normalization for weekly data
            days_to_sunday = date.dayOfWeek() % 7
            return date.addDays(-days_to_sunday)
        elif self.calendar_type == 'M':
            # Normalize to the last day of the month
            year = date.year()
            month = date.month()
            # Calculate last day of current month
            last_day = QDate(year, month, 1).addMonths(1).addDays(-1).day()
            return QDate(year, month, last_day)
        elif self.calendar_type == 'Y':
            # Normalize to December 31st of the current year
            return QDate(date.year(), 12, 31)
        else:  # 'D' or default
            return date

    def ensure_valid_date(self, date):
        """
        Ensures the provided date exists in date_to_pos.
        If not, returns the middle date from date_to_pos.
        Returns: (QDate, pandas.Timestamp or None) - tuple of valid QDate and its corresponding timestamp
        """
        # Convert QDate to pandas timestamp for lookup
        pd_stamp = pd.Timestamp(date.toString('yyyy-MM-dd'))
        closest_date = self.figure_manager.data_manager.find_closest_date(pd_stamp,
                                                                          self.figure_manager.Chart.date_to_pos)

        # If date is valid, return it
        if closest_date is not None:
            return date, closest_date

        # Otherwise, try to find middle date
        if not self.figure_manager.Chart.date_to_pos:
            return date, None  # No data available, return original date

        # Find middle date
        sorted_dates = sorted(self.figure_manager.Chart.date_to_pos.keys())
        middle_timestamp = sorted_dates[len(sorted_dates) // 2]
        middle_qdate = QDate(middle_timestamp.year, middle_timestamp.month, middle_timestamp.day)

        return middle_qdate, middle_timestamp

    def adjust_date(self, increment=True):
        """
        Adjusts the current date forward or backward according to calendar type
        increment: True to move forward, False to move backward
        Returns: The adjusted QDate
        """
        # Determine the direction (increment or decrement)
        direction = 1 if increment else -1

        if self.calendar_type == 'D':
            # Daily adjustment remains unchanged
            self.current_date = self.current_date.addDays(direction)
        elif self.calendar_type == 'W':
            # Weekly adjustment - move to next/previous Sunday
            days_to_sunday = self.current_date.dayOfWeek() % 7
            sunday = self.current_date.addDays(-days_to_sunday)
            self.current_date = sunday.addDays(7 * direction)
        elif self.calendar_type == 'M':
            # Monthly adjustment - move to the last day of next/previous month
            year = self.current_date.year()
            month = self.current_date.month()

            # First ensure we're at the end of the current month
            current_month_end = QDate(year, month, 1).addMonths(1).addDays(-1)

            # Then move to next/previous month end
            next_month_end = current_month_end.addMonths(direction)
            self.current_date = next_month_end
        elif self.calendar_type == 'Y':
            # Yearly adjustment - move to December 31st of next/previous year
            year = self.current_date.year()
            # Ensure we're at year end first
            current_year_end = QDate(year, 12, 31)
            # Move to next/previous year end
            next_year_end = current_year_end.addYears(direction)
            self.current_date = next_year_end
        else:
            # Default case
            self.current_date = self.current_date.addDays(direction)

        return self.current_date

    def get_formatted_date_text(self):
        """
        Returns the formatted date text according to the calendar type
        Also indicates if the current date is today
        Returns: (str, bool) - formatted date string and boolean indicating if date is today
        """
        today = QDate.currentDate()
        normalized_today = self.normalize_date_for_calendar_type(today)

        # Check if date is today based on calendar type
        if self.calendar_type == 'D':
            is_today = self.current_date == today
        elif self.calendar_type == 'W':
            days_to_sunday = self.current_date.dayOfWeek() % 7
            week_start = self.current_date.addDays(-days_to_sunday)
            week_end = week_start.addDays(6)
            is_today = today >= week_start and today <= week_end
        elif self.calendar_type == 'M':
            is_today = (self.current_date.year() == today.year() and
                        self.current_date.month() == today.month())
        elif self.calendar_type == 'Y':
            is_today = self.current_date.year() == today.year()
        else:
            is_today = self.current_date == today

        # Format date string based on calendar type
        if self.calendar_type == 'D':
            date_str = self.current_date.toString("dd-MM-yyyy")
        elif self.calendar_type == 'W':
            # Find the Sunday of this week
            days_to_sunday = self.current_date.dayOfWeek() % 7
            sunday = self.current_date.addDays(-days_to_sunday)
            week_num = self.current_date.weekNumber()[0]
            date_str = f"W{week_num} {sunday.toString('dd-MM-yyyy')}"
        elif self.calendar_type == 'M':
            date_str = self.current_date.toString("MMM yyyy")
        elif self.calendar_type == 'Y':
            date_str = self.current_date.toString("yyyy")
        else:
            date_str = self.current_date.toString("dd-MM-yyyy")  # Default

        return date_str, is_today

    def update_calendar_type(self):
        """Updates the calendar type from data_manager"""
        self.calendar_type = self.data_manager.chart_data['type'][0]