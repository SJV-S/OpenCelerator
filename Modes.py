from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QGroupBox, QRadioButton, QLineEdit, QLabel, QDateEdit, QListWidget, QFileDialog, QCheckBox,
                               QButtonGroup, QDialog, QComboBox, QMessageBox, QGridLayout, QStackedWidget, QSpinBox,
                               QSpacerItem, QSizePolicy, QDoubleSpinBox, QColorDialog, QListWidgetItem, QFrame)
from PySide6.QtGui import QDoubleValidator, QFont, QIcon
from PySide6.QtCore import Qt, QDate

from Popups import InputDialog, ConfigurePhaseLinesDialog, ConfigureAimLinesDialog, ConfigureTrendLinesDialog, NoteDialog
from DataManager import DataManager
from EventBus import EventBus


class ModeWidget(QWidget):
    def __init__(self, figure_manager):
        super().__init__()
        self.figure_manager = figure_manager
        self.data_manager = DataManager()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.init_ui()

        # Initialize event bus instance for all mode widgets
        self.event_bus = EventBus()

    def init_ui(self):
        pass


class DataModeWidget(ModeWidget):
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

        spacer_item = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        main_layout.addItem(spacer_item)

        self.column_selector = QComboBox()
        self.column_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.column_selector.currentTextChanged.connect(self.update_style_widgets)
        self.column_selector.activated.connect(self.highlight_style_user_col)
        main_layout.addWidget(self.column_selector)

        # Create all widgets
        content_layout = QVBoxLayout()

        # First color buttons
        for style_key in ['face_colors', 'edge_colors', 'line_colors']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            content_layout.addWidget(widget)

        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        content_layout.addItem(spacer)

        # Then dropdowns with labels
        for style_key in ['markers', 'line_styles']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            content_layout.addWidget(QLabel(label))
            content_layout.addWidget(widget)
            widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Finally spinboxes with labels
        for style_key in ['marker_sizes', 'line_width']:
            widget_name, label = self.ui_element_map[style_key]
            widget = self.create_widget(style_key)
            self.widgets[widget_name] = widget
            content_layout.addWidget(QLabel(label))
            content_layout.addWidget(widget)

        spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        content_layout.addItem(spacer)
        content_layout.addStretch()

        main_layout.addLayout(content_layout)
        self.layout.addLayout(main_layout)

    def highlight_style_user_col(self):
        user_col = self.column_selector.currentText()
        if user_col:
            plot_columns = self.data_manager.plot_columns
            col_instance = plot_columns[user_col]
            col_instance.highlight()

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

        column_map = self.data_manager.chart_data['column_map']
        if column_map:
            data_columns = [v for k, v in column_map.items() if k != 'd']
            if data_columns:
                self.column_selector.addItems(data_columns)
                index = self.column_selector.findText(current_text)
                if index >= 0:
                    self.column_selector.setCurrentIndex(index)
                else:
                    self.column_selector.setCurrentIndex(0)

        self.update_style_widgets()

    def update_style_widgets(self):
        user_col = self.column_selector.currentText()
        if not user_col:
            return

        column_instance = self.data_manager.plot_columns[user_col]
        default_style = column_instance.column_default_style
        self.populate_fields(default_style)

    def populate_fields_with_defaults(self):
        user_col = self.column_selector.currentText()
        if user_col:
            column_instance = self.data_manager.plot_columns[user_col]
            default_style = column_instance.column_default_style
            self.populate_fields(default_style)

    def block_signals(self, block):
        for widget in self.widgets.values():
            widget.blockSignals(block)

    def populate_fields(self, default_values):
        key_mapping = {
            'markersize': 'marker_sizes',
            'marker': 'markers',
            'marker_face_color': 'face_colors',
            'marker_edge_color': 'edge_colors',
            'line_color': 'line_colors',
            'linewidth': 'line_width',
            'linestyle': 'line_styles'
        }

        converted_values = {
            new_key: default_values[old_key]
            for old_key, new_key in key_mapping.items()
        }

        self.block_signals(True)

        self.widgets['marker_size_spinbox'].setValue(converted_values['marker_sizes'])
        self.widgets['line_width_spinbox'].setValue(converted_values['line_width'])

        marker_key = next(k for k, v in self.marker_style_map.items() if v == converted_values['markers'])
        line_key = next(k for k, v in self.line_style_map.items() if v == converted_values['line_styles'])

        self.widgets['marker_style_combobox'].setCurrentText(marker_key)
        self.widgets['line_style_combobox'].setCurrentText(line_key)

        for color_key in ['face_colors', 'edge_colors', 'line_colors']:
            self.set_button_border_style(
                self.widgets[self.ui_element_map[color_key][0]],
                converted_values[color_key]
            )

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
        if user_col:
            data = {'user_col': user_col, 'style_cat': style_category, 'style_val': style_value}
            self.event_bus.emit('update_point_styles', data)
            self.event_bus.emit('update_legend')


class ViewModeWidget(ModeWidget):
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

        self.column_label = QLabel('Column')
        self.column_dropdown = QComboBox()
        group_label = QLabel("Group")
        self.group_dropdown = QComboBox()
        aggregate_label = QLabel("Aggregate")
        self.aggregate_dropdown = QComboBox()

        self.group_dropdown.addItems(['Day', 'Week', 'Month', 'Year'])
        self.aggregate_dropdown.addItems(['raw', 'sum', 'mean', 'median', 'min', 'max'])
        self.aggregate_dropdown.setCurrentText('median')
        self.toggle_group_column()

        column_wrapper = QVBoxLayout()
        column_wrapper.addWidget(self.column_label)
        column_wrapper.addWidget(self.column_dropdown)

        dropdown_layout.addLayout(column_wrapper, 0, 0, 1, 2)
        dropdown_layout.addWidget(group_label, 1, 0)
        dropdown_layout.addWidget(self.group_dropdown, 1, 1)
        dropdown_layout.addWidget(aggregate_label, 2, 0)
        dropdown_layout.addWidget(self.aggregate_dropdown, 2, 1)

        dropdown_widget = QWidget()
        dropdown_widget.setLayout(dropdown_layout)
        main_layout.addWidget(dropdown_widget)

        # Add spacing between dropdown and checkbox sections
        main_layout.addItem(spacer1)

        # Checkbox sections with their own grid
        checkbox_layout = QGridLayout()
        checkbox_layout.setSpacing(10)

        # Section headings
        font = QFont()
        grid_heading = QLabel("Grid")
        self.column_heading = QLabel("Column")
        other_heading = QLabel("Other")
        for heading in [grid_heading, self.column_heading, other_heading]:
            heading.setFont(font)

        # Column section
        checkbox_layout.addWidget(self.column_heading, 0, 0)
        self.data_check = QCheckBox('Data')
        self.trend_check = QCheckBox('Trend')
        self.bounce_check = QCheckBox('Bounce')
        self.celtext_check = QCheckBox('CelText')

        checkbox_layout.addWidget(self.data_check, 1, 0)
        checkbox_layout.addWidget(self.trend_check, 2, 0)
        checkbox_layout.addWidget(self.bounce_check, 3, 0)
        checkbox_layout.addWidget(self.celtext_check, 4, 0)

        # Grid section
        checkbox_layout.addWidget(grid_heading, 0, 1)
        self.major_vertical_check = QCheckBox('Dates')
        self.major_horizontal_check = QCheckBox('Counts')
        self.minor_grid_check = QCheckBox('Minor')
        self.time_grid_check = QCheckBox('Timing')

        checkbox_layout.addWidget(self.major_vertical_check, 1, 1)
        checkbox_layout.addWidget(self.major_horizontal_check, 2, 1)
        checkbox_layout.addWidget(self.minor_grid_check, 3, 1)
        checkbox_layout.addWidget(self.time_grid_check, 4, 1)

        # Other section
        checkbox_layout.addWidget(other_heading, 5, 0, 1, 2)
        self.phase_check = QCheckBox('Phase')
        self.aim_check = QCheckBox('Aim')
        self.celfan_check = QCheckBox('Fan')
        self.credit_check = QCheckBox('Credit')
        self.legend_check = QCheckBox('Legend')

        checkbox_layout.addWidget(self.phase_check, 6, 0)
        checkbox_layout.addWidget(self.aim_check, 6, 1)
        checkbox_layout.addWidget(self.celfan_check, 7, 0)
        checkbox_layout.addWidget(self.credit_check, 7, 1)
        checkbox_layout.addWidget(self.legend_check, 8, 0)

        checkbox_widget = QWidget()
        checkbox_widget.setLayout(checkbox_layout)
        main_layout.addWidget(checkbox_widget)

        # Add spacing between checkbox section and credit button
        main_layout.addItem(spacer2)

        # Credit button
        self.credit_lines_btn = QPushButton("Credit lines")
        self.credit_lines_btn.clicked.connect(self.credit_lines_popup)
        main_layout.addWidget(self.credit_lines_btn)

        self.layout.addLayout(main_layout)

        for checkbox in [self.major_vertical_check, self.major_horizontal_check,
                        self.minor_grid_check, self.data_check, self.trend_check,
                        self.bounce_check, self.celtext_check, self.phase_check,
                        self.aim_check, self.celfan_check, self.credit_check, self.legend_check]:
            checkbox.setChecked(True)
        self.time_grid_check.setChecked(False)

        # Connect signals
        self.column_dropdown.activated.connect(self.handle_column_dropdown_changed)
        self.group_dropdown.activated.connect(self.group_column_update)
        self.aggregate_dropdown.activated.connect(self.agg_column_update)

        self.data_check.stateChanged.connect(lambda state: self.set_data_visibility('data', state))
        self.trend_check.stateChanged.connect(lambda state: self.set_data_visibility('trend_line', state))
        self.bounce_check.stateChanged.connect(lambda state: self.set_data_visibility('bounce', state))
        self.celtext_check.stateChanged.connect(lambda state: self.set_data_visibility('cel_label', state))

        self.major_vertical_check.stateChanged.connect(lambda state: self.event_bus.emit('view_major_date_gridlines', state))
        self.major_horizontal_check.stateChanged.connect(lambda state: self.event_bus.emit('view_major_count_gridlines', state))
        self.minor_grid_check.stateChanged.connect(lambda state: self.event_bus.emit('view_minor_gridlines', state))
        self.time_grid_check.stateChanged.connect(lambda state: self.event_bus.emit('view_floor_grid', state))

        self.phase_check.stateChanged.connect(lambda state: self.event_bus.emit('view_phase_lines_toggle', state))
        self.aim_check.stateChanged.connect(lambda state: self.event_bus.emit('view_aims_toggle', state))
        self.celfan_check.stateChanged.connect(lambda state: self.event_bus.emit('view_cel_fan_toggle', state))
        self.legend_check.stateChanged.connect(lambda state: self.event_bus.emit('view_legend_toggle', state))
        self.credit_check.stateChanged.connect(lambda state: self.handle_credit_toggle(state))

        # Event bus subscriptions
        self.event_bus.subscribe('refresh_view_dropdown', self.refresh_view_dropdown)
        self.event_bus.subscribe('view_column_dropdown_update_label', self.view_column_dropdown_update_label)
        self.event_bus.subscribe('sync_grid_checkboxes', self.sync_grid_checkboxes)
        self.event_bus.subscribe('sync_data_checkboxes', self.sync_data_checkboxes)
        self.event_bus.subscribe('sync_misc_checkboxes', self.sync_misc_checkboxes)

        self.update_timing_checkboxes()

    def handle_credit_toggle(self, state):
        self.event_bus.emit('view_credit_lines_toggle', state)
        self.credit_lines_btn.setVisible(bool(state))

    def handle_column_dropdown_changed(self, index):
        self.view_column_dropdown_update_label(index)
        self.sync_data_checkboxes()

        user_col = self.column_dropdown.currentText()
        if not user_col:
            return
        column_instance = self.data_manager.plot_columns[user_col]
        column_instance.highlight()

    def set_data_visibility(self, element_type, show):
        user_col = self.column_dropdown.currentText()
        if not user_col:
            return

        column_instance = self.data_manager.plot_columns[user_col]
        column_instance.set_visibility(element_type, show)
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

        self.credit_lines_btn.setVisible(view_settings['credit'])

    def sync_grid_checkboxes(self):
        view_settings = self.data_manager.chart_data['view']['chart']
        checkboxes = [self.major_vertical_check, self.major_horizontal_check,
                      self.minor_grid_check, self.time_grid_check]

        for checkbox in checkboxes:
            checkbox.blockSignals(True)

        self.major_vertical_check.setChecked(view_settings['major_grid_dates'])
        self.major_horizontal_check.setChecked(view_settings['major_grid_counts'])
        self.minor_grid_check.setChecked(view_settings['minor_grid'])
        self.time_grid_check.setChecked(view_settings['floor_grid'])

        for checkbox in checkboxes:
            checkbox.blockSignals(False)

    def sync_data_checkboxes(self):
        user_col = self.column_dropdown.currentText()
        if not user_col:
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
        self.group_dropdown.setCurrentText(view_settings['calendar_group'])
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
        if not user_col or user_col not in self.data_manager.plot_columns.keys():
            return

        column_instance = self.data_manager.plot_columns[user_col]
        column_instance.view_settings[setting_key] = setting_value
        sys_col = column_instance.sys_col

        # Save view settings in chart data
        key = f'{sys_col}|{user_col}'
        view_dict = self.data_manager.chart_data['view']
        view_dict[key] = column_instance.view_settings

        column_instance.refresh_view()
        self.event_bus.emit('refresh_chart')

    def group_column_update(self):
        calendar_group = self.group_dropdown.currentText()
        self._update_column_settings('calendar_group', calendar_group)

    def agg_column_update(self):
        agg_type = self.aggregate_dropdown.currentText()
        self._update_column_settings('agg_type', agg_type)
        self.toggle_group_column()

    def view_column_dropdown_update_label(self, index=0):
        new_column_heading = self.column_dropdown.itemText(index)
        if new_column_heading:
            char_lim = 12
            if len(new_column_heading) > char_lim:
                new_column_heading = new_column_heading[:char_lim] + '...'
            self.column_heading.setText(new_column_heading)

    def refresh_view_dropdown(self):
        self.column_dropdown.clear()
        column_map = self.data_manager.chart_data['column_map']
        if column_map:
            self.column_dropdown.addItems([v for k, v in column_map.items() if k != 'd'])

    def credit_lines_popup(self):
        if self.dialog.exec() == QDialog.DialogCode.Accepted:
            r1, r2 = self.dialog.get_inputs()
            self.dialog.credit_row1 = r1
            self.dialog.credit_row2 = r2
            self.figure_manager.data_manager.chart_data['credit'] = (r1, r2)
            self.event_bus.emit('view_update_credit_lines')
        self.event_bus.emit('refresh_chart')

    def update_timing_checkboxes(self):
        condition = 'Minute' in self.data_manager.chart_data['type']
        self.time_grid_check.setEnabled(condition)


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
        undo_aim_line_btn.clicked.connect(self.figure_manager.aim_undo)
        configure_aim_btn.clicked.connect(self.configure_aim_lines)

        # Create a horizontal layout for the radio buttons
        radio_buttons_layout = QGridLayout()

        # Aim type radio buttons
        aim_type_label = QLabel('Line type')
        self.aim_type_group = QButtonGroup(self)
        self.aim_type_flat = QRadioButton('Flat')
        self.aim_type_slope = QRadioButton('Slope')

        # Set the aim type based on user preferences
        aim_text_type = self.data_manager.user_preferences.get('aim_line_type', 'Flat')
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
        aim_text_position = self.data_manager.user_preferences.get('aim_text_position', 'Middle')
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
        self.data_manager.user_preferences['aim_text_position'] = text_pos

    def update_aim_type(self, aim_type):
        self.data_manager.user_preferences["aim_line_type"] = aim_type

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
        self.envelope_methods = ['None', '5-95 percentile', 'Interquartile range', 'Standard deviation', '90% confidence interval']
        self.celeration_units = ['Daily', 'Weekly (standard)', 'Monthly (Weekly x4)', 'Yearly (Weekly x52)']

        # Trend type selector
        trend_col_label = QLabel('Column')
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

    def get_current_trend_column(self):
        return self.trend_type_combo.currentText()

    def set_celeration_unit(self, data):
        cel_unit = data['cel_unit']
        self.celeration_unit_combo.setCurrentText(cel_unit)
        self.data_manager.user_preferences['celeration_unit'] = cel_unit

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

    def _init_trend_controls(self):
        # Create and configure combos
        self.trend_method_combo = QComboBox()
        self.trend_method_combo.addItems(self.trend_methods)
        self.trend_method_combo.setCurrentText(self.data_manager.user_preferences['fit_method'])
        self.trend_method_combo.currentIndexChanged.connect(
            lambda index: self.data_manager.user_preferences.update(
                {'fit_method': self.trend_method_combo.currentText()})
        )

        self.envelope_method_combo = QComboBox()
        self.envelope_method_combo.addItems(self.envelope_methods)
        self.envelope_method_combo.setCurrentText(self.data_manager.user_preferences.get('bounce_envelope', 'None'))
        self.envelope_method_combo.currentIndexChanged.connect(
            lambda index: self.data_manager.user_preferences.update(
                {'bounce_envelope': self.envelope_method_combo.currentText()})
        )

        self.celeration_unit_combo = QComboBox()
        self.celeration_unit_combo.addItems(self.celeration_units)
        self.celeration_unit_combo.setCurrentText(
            self.data_manager.user_preferences.get('celeration_unit', 'Weekly (standard)'))
        self.celeration_unit_combo.currentIndexChanged.connect(
            lambda index: self.data_manager.user_preferences.update(
                {'celeration_unit': self.celeration_unit_combo.currentText()})
        )

        # Configure spinbox
        self.forward_projection_spinbox = QSpinBox()
        self.forward_projection_spinbox.setRange(0, 100)
        self.forward_projection_spinbox.setValue(self.data_manager.user_preferences.get('forward_projection', 0))
        self.forward_projection_spinbox.valueChanged.connect(
            lambda value: self.data_manager.user_preferences.update({'forward_projection': value})
        )

        # Create labels
        labels = {
            'trend_method': "Fit method",
            'forward_projection': "Forecast",
            'envelope_method': "Bounce envelope",
            'celeration_unit': "Celeration unit"
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
        self.trend_fit_btn = QPushButton('Fit')
        trend_undo_btn = QPushButton()
        trend_configure_btn = QPushButton()

        self.trend_add_btn.setIcon(QIcon(':/images/plus-solid-disabled.svg'))
        self.trend_add_btn.setEnabled(False)
        trend_undo_btn.setIcon(QIcon(':/images/minus-solid.svg'))
        trend_configure_btn.setIcon(QIcon(':/images/gear-solid.svg'))

        trend_button_layout.addWidget(self.trend_add_btn)
        trend_button_layout.addWidget(trend_undo_btn)
        trend_button_layout.addWidget(self.trend_fit_btn)
        trend_button_layout.addWidget(trend_configure_btn)

        # Connect buttons
        self.trend_fit_btn.clicked.connect(self.fit_trend)
        self.trend_add_btn.clicked.connect(self.add_trend)
        trend_undo_btn.clicked.connect(self.undo_trend)
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

    def add_trend(self):
        self.event_bus.emit('trend_finalize')
        self.set_plus_btn_status()

    def undo_trend(self):
        user_col = self.get_current_trend_column()
        if user_col:
            col_instance = self.figure_manager.data_manager.plot_columns[user_col]
            col_instance.remove_trend()
            self.event_bus.emit('refresh_chart')
            self.set_plus_btn_status()

    def fit_trend(self):
        trend_data = None
        self.event_bus.emit('plot_cel_trend_temp', trend_data)
        self.setFocus()
        self.set_plus_btn_status()
        self.event_bus.emit('refresh_chart')

    def set_plus_btn_status(self):
        if self.figure_manager.trend_manager.trend_temp_fit_on:
            self.trend_add_btn.setEnabled(True)
            self.trend_add_btn.setIcon(QIcon(':/images/plus-solid.svg'))
        else:
            self.trend_add_btn.setEnabled(False)
            self.trend_add_btn.setIcon(QIcon(':/images/plus-solid-disabled.svg'))

    def configure_trends(self):
        user_col = self.trend_type_combo.currentText()
        column_map = self.data_manager.chart_data['column_map']
        if column_map and user_col in column_map.values():
            trend_style = self.data_manager.plot_columns[user_col].get_default_trend_style()
            dialog = ConfigureTrendLinesDialog(user_col, trend_style, self.figure_manager, self)
            dialog.exec()


class NoteModeWidget(ModeWidget):
    def __init__(self, figure_manager):
        super().__init__(figure_manager)

        # Update notes
        self.event_bus.subscribe('refresh_note_listbox', self.refresh_note_listbox, has_data=False)

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()

        # Header section
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 5, 10, 5)

        # Header labels
        date_label = QLabel("Date")
        text_label = QLabel("Text")
        date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(date_label, stretch=1)
        header_layout.addWidget(text_label, stretch=1)

        # List widget
        self.note_list = QListWidget()
        self.note_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.note_list.itemClicked.connect(self.clicked_on_note)
        self.note_list.itemDoubleClicked.connect(self.double_clicked_on_note)
        self.note_list.setStyleSheet("""
            QListWidget {
                font-size: 14px;
            }
            QListWidget::item {
                padding: 5px;
                text-align: center;
                margin: 3px 0px;
            }
            
            QListWidget::item:hover {
            background-color: #96deeb;
            }
                
            QListWidget::item:selected {
                background-color: #05c3de;
                color: white;
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
        main_layout.addWidget(header_widget)  # Header
        main_layout.addWidget(self.note_list)  # List widget
        main_layout.addLayout(button_layout)  # Buttons

        # Set layout for the widget
        self.layout.addLayout(main_layout)

        # Connect button actions
        remove_note_btn.clicked.connect(self.remove_note)

    def refresh_note_listbox(self):
        self.note_list.clear()
        all_notes = self.data_manager.chart_data['notes']
        for note in all_notes:
            text, date_str, y_val = note.split('|')
            text_to_show = f'{text[:8]}...' if len(text) > 8 else text
            note_details_to_show = f'{date_str}\t{text_to_show}'
            item = QListWidgetItem(note_details_to_show)
            self.note_list.addItem(item)

    def remove_note(self):
        current_item = self.note_list.currentItem()  # Get the selected listbox item
        notes = self.data_manager.chart_data['notes']

        if current_item:
            # Get index
            idx = self.note_list.row(current_item)

            # Remove from listbox
            row = self.note_list.row(current_item)
            self.note_list.takeItem(row)

            # Remove from chart data
            if idx < len(notes):
                del notes[idx]

            self.event_bus.emit('refresh_note_locations')
            self.event_bus.emit('clear_previous_individual_note_object', data={'refresh': True})

    def clicked_on_note(self, item):
        if item:
            # Get the index of the clicked item
            index = self.note_list.row(item)
            # Get the full note data using the same index
            full_note = self.data_manager.chart_data['notes'][index]
            text, date_str, y_val = full_note.split('|')

            # # Emit event with the full note data
            self.event_bus.emit('show_individual_note_locations', data={'date_str': date_str, 'note_y': y_val})

    def double_clicked_on_note(self, item):
        if item:
            # Get the index of the clicked item
            index = self.note_list.row(item)
            # Get the full note data
            full_note = self.data_manager.chart_data['notes'][index]
            text, date_str, y_val = full_note.split('|')

            # Create and show the note dialog
            dialog = NoteDialog(date_str, float(y_val), self)
            dialog.text_edit.setPlainText(text)  # Set the existing note text

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get the new text from the dialog
                new_text = dialog.text_edit.toPlainText().replace('|', '')
                if new_text != text:  # Only update if the text changed
                    # Remove old note
                    del self.data_manager.chart_data['notes'][index]
                    # The new note will have been added by the dialog's save_note method
                    self.refresh_note_listbox()


