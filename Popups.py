from app_imports import *
from EventStateManager import EventBus
from DataManager import DataManager


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

        start_date = self.data_manager.chart_data['start_date']
        if hasattr(start_date, 'to_pydatetime'):
            start_date = start_date.to_pydatetime()
        else:
            # Convert string to datetime using pandas
            try:
                start_date = pd.to_datetime(start_date).to_pydatetime()
            except:
                # Default to current date if parsing fails
                start_date = pd.Timestamp.now().to_pydatetime()

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

        # Get all trend items but filter them to only include ones for the current column
        all_items = self.data_manager.chart_data[trend_style]
        self.items = [item for item in all_items if item.get('user_col') == user_col]

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

        # Get the plot column instance for this user_col
        col_instance = self.data_manager.plot_columns[self.user_col]

        # Find the corresponding trend in trend_set by matching with the trend_data
        trend_set = col_instance.get_trend_set()
        if trend_set:
            # Try to find the matching trend in the trend_set
            found_index = None
            for i, (trend_elements, trend_data) in enumerate(trend_set):
                if trend_data is old_trend or (trend_data and trend_data.get('date1') == old_trend.get('date1') and
                                               trend_data.get('date2') == old_trend.get('date2')):
                    found_index = i
                    break

            if found_index is not None:
                trend_elements, _ = trend_set[found_index]

                # Update trend elements styling - main trend line
                if trend_elements.get('trend_line'):
                    trend_elements['trend_line'].set_color(new_trend['line_color'])
                    trend_elements['trend_line'].set_linewidth(new_trend['linewidth'])
                    trend_elements['trend_line'].set_linestyle(new_trend['linestyle'])

                # Update bounce lines - specifically fixing the issue with bounce lines
                if trend_elements.get('upper_line'):
                    trend_elements['upper_line'].set_color(new_trend['line_color'])
                    trend_elements['upper_line'].set_linestyle(new_trend['linestyle'])
                    trend_elements['upper_line'].set_linewidth(new_trend['linewidth'])

                if trend_elements.get('lower_line'):
                    trend_elements['lower_line'].set_color(new_trend['line_color'])
                    trend_elements['lower_line'].set_linestyle(new_trend['linestyle'])
                    trend_elements['lower_line'].set_linewidth(new_trend['linewidth'])

                # Update text label
                if trend_elements.get('cel_label'):
                    trend_elements['cel_label'].set_color(new_trend['font_color'])
                    trend_elements['cel_label'].set_fontsize(new_trend['font_size'])
                    trend_elements['cel_label'].set_text(new_trend['text'])

                # Update the trend_data in both places
                trend_set[found_index] = (trend_elements, new_trend)
                self.items[selected_item] = new_trend

                # Also update the original trend list in chart_data
                trend_type = self.trend_style
                all_trends = self.data_manager.chart_data[trend_type]

                # Find and update the matching trend in the original list
                for i, trend in enumerate(all_trends):
                    if (trend.get('user_col') == self.user_col and
                            trend.get('date1') == old_trend.get('date1') and
                            trend.get('date2') == old_trend.get('date2')):
                        all_trends[i] = new_trend
                        break

        # Force a refresh of the figure to show all changes including bounce lines
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

            # Get the trend data for the selected item
            selected_trend = self.items[selected_item]

            # Find the corresponding trend in trend_set by matching date1 and date2
            trend_set = col_instance.get_trend_set()
            if trend_set:
                # Try to find the matching trend in the trend_set
                found_index = None
                for i, (_, trend_data) in enumerate(trend_set):
                    if (trend_data and trend_data.get('date1') == selected_trend.get('date1') and
                            trend_data.get('date2') == selected_trend.get('date2')):
                        found_index = i
                        break

                if found_index is not None:
                    # Remove from the column instance's trend_set
                    col_instance.remove_trend(found_index)

            # Also remove from the items list and the list widget
            self.items.pop(selected_item)
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
    date_pattern = r'^(?=.*\d{2})(?:[^-/.\n]*[-/.]){2,}[^-/.\n]*$'
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
        minute_chart_msg = 'Expected to be raw counts, that will be divided by the timing floor automatically.'

        self.field_explanations = {
            '📅': f'Date {self.data_manager.ui_column_label.lower()} goes here. The format should be detected automatically (in most cases).',
            '⬤': f'Something to increase. {minute_chart_msg if self.is_minute_chart else ""}',
            '✕': f'Something to decrease. {minute_chart_msg if self.is_minute_chart else ""}',
            '⧖': 'Expected to be minutes. The inverse is charted automatically.',
            'date_format': "The date format could not be inferred. A qualified guess has been made.",
        }

        self._setup_ui()
        self._load_data()
        self._setup_column_filters()
        self._create_date_controls()
        self._create_field_dropdowns()

    def _setup_ui(self):
        self.setStyleSheet("""QWidget {font-size: 12pt; font-style: normal;}""")
        self.setWindowTitle(f"{self.data_manager.ui_column_label} Mapping")
        self.setMinimumSize(400, 500)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"What data {self.data_manager.ui_column_label.lower()} will you be using?")
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
        self.add_misc_button.setToolTip(f'Add {self.data_manager.ui_column_label}')
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
        # Only a smaller sample is needed, hence row_limit
        self.df = self.data_manager.get_df_from_data_file(self.file_path, row_limit=None)
        if self.df is None:
            print('Column mapping popup failed to read data')
            self.reject()
        else:
            self.df = self.df.dropna(axis=1, how='all')  # Filter out empty columns
            # self.df = self.df[self.df.columns[:100]]
            self.df = self.df.fillna(0)

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
        dropdown.setFixedWidth(250)
        dropdown.addItem(self.column_placeholder)
        dropdown.addItems(items)
        if on_change:
            dropdown.currentTextChanged.connect(on_change)

        tooltip_text = self.field_explanations.get(field_name.split()[0], f"Other data {self.data_manager.ui_column_label.lower()}.")
        info_label = self._create_info_label(tooltip_text)

        row_layout = QHBoxLayout()
        row_layout.addWidget(dropdown)
        row_layout.addWidget(info_label)

        self.form_layout.addRow(QLabel(field_name), row_layout)
        return dropdown

    def _create_date_controls(self):
        self.date_dropdown = self._create_dropdown_row('📅', self.date_columns, self.check_date_format_warning)

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
            dropdown = self._create_dropdown_row('⧖', self.numeric_columns,
                                                 lambda *args: self.on_dropdown_changed('Floor'))
            self.dropdowns_dict['Floor'] = dropdown

        icon_map = {'Dot': '⬤', 'X': '✕'}
        for field, icon in icon_map.items():
            dropdown = self._create_dropdown_row(icon, self.numeric_columns,
                                                 lambda *args, f=field: self.on_dropdown_changed(f))
            self.dropdowns_dict[field] = dropdown

    def add_misc_dropdown(self):
        misc_idx = len(self.misc_dropdowns)
        dropdown = self._create_dropdown_row('▼', self.numeric_columns,
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

    def _lazy_check(self, df, pattern, threshold=0.8, check_limit=10, date_check=False):
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
        # Only for minute charts, check if the Floor/minute field is selected
        if self.is_minute_chart and 'Floor' in self.dropdowns_dict:
            if self.dropdowns_dict['Floor'].currentText() == self.column_placeholder:
                # Highlight only the Floor field with a red background
                self.dropdowns_dict['Floor'].setStyleSheet("QComboBox { background-color: #FF9999; }")
                return  # Don't proceed with confirmation

        # If we get here, proceed with the regular confirmation
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

        # Necessary when selecting mapping for non-minute charts
        if 'm' not in column_map.keys():
            self.data_manager.chart_data['column_map']['m'] = 'minutes'

        self.accept()


class UserPrompt(QDialog):
    def __init__(self, title="Message", message="", options=None, parent=None):
        super().__init__(parent)
        self.selected_option = -1

        self._setup_window(title)
        self._create_layout()
        self._add_message_label(message)

        if options and isinstance(options, list) and len(options) > 0:
            self._add_option_buttons(options)
        else:
            self._add_button_box(True, "OK", "Cancel")

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
        self.message_label.setMinimumWidth(200)
        self.layout.addWidget(self.message_label)

    def _add_option_buttons(self, options):
        self.buttons_layout = QVBoxLayout()
        self.buttons = []

        for i, option_text in enumerate(options):
            button = QPushButton(option_text, self)
            button.clicked.connect(lambda checked, idx=i: self._on_option_selected(idx))
            button.setStyleSheet("font-size: 14px; padding: 8px 16px; text-align: center;")
            self.buttons.append(button)
            self.buttons_layout.addWidget(button)

        self.layout.addLayout(self.buttons_layout)

        # No need for an additional cancel button as the dialog can be closed with X
        # or ESC key, which will return -1

    def _on_option_selected(self, index):
        self.selected_option = index
        self.accept()

    def _add_button_box(self, choice, ok_text="OK", cancel_text="Cancel"):
        buttons = (
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel if choice else QDialogButtonBox.StandardButton.Ok)
        self.button_box = QDialogButtonBox(buttons, self)

        # Set custom button text
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(ok_text)
        if choice:
            self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(cancel_text)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def _apply_styles(self):
        self.message_label.setStyleSheet("font-size: 16px; padding: 10px; font-style: normal;")
        self.setStyleSheet("QDialog { padding: 20px; }")

    def display(self):
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint |
            Qt.WindowType.WindowCloseButtonHint  # Add close button to allow cancel
        )

        result = self.exec() == QDialog.DialogCode.Accepted
        if result and hasattr(self, 'selected_option'):
            return self.selected_option
        return -1 if not result else 0


class ModifyColumns(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.column_inputs = []

        # List to keep track of buttons that need double-click protection
        self.double_click_buttons = []

        # Common button styles
        self.button_styles = {
            'small': """
               QPushButton {
                   border: 1px solid #ccc !important;
                   border-radius: 12px !important;
                   margin: 0px !important;
                   padding: 0px !important;
                   min-width: 24px !important;
                   min-height: 24px !important;
                   max-width: 24px !important; 
                   max-height: 24px !important;
               }
               QPushButton:hover {
                   background-color: #f0f0f0;
               }
            """,
            'large': """
               QPushButton {
                   border: 1px solid #ccc !important;
                   border-radius: 16px !important;
                   margin: 10px 0 !important;
                   padding: 0px !important;
                   min-width: 32px !important;
                   min-height: 32px !important;
                   max-width: 32px !important; 
                   max-height: 32px !important;
               }
               QPushButton:hover {
                   background-color: #f0f0f0;
               }
            """
        }

        self._setup_ui()

    def showEvent(self, event):
        # Clear existing column inputs before repopulating
        self._clear_column_inputs()
        self._populate_columns()
        super().showEvent(event)

    def _clear_column_inputs(self):
        for column in self.column_inputs:
            widget = column['row_widget']
            self.columns_layout.removeWidget(widget)
            widget.hide()  # Hide widget immediately
            widget.setParent(None)  # Remove from widget hierarchy
            widget.deleteLater()

        # Clear the tracking list
        self.column_inputs = []
        self.double_click_buttons = []

        # Force processing events to handle pending deletions
        QApplication.processEvents()

    def _setup_ui(self):
        self.setWindowTitle(f"Modify {self.data_manager.ui_column_label}")
        self.setMinimumSize(350, 400)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel(f"Manage Data {self.data_manager.ui_column_label}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # Scrollable area for column inputs
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.columns_layout = QVBoxLayout(container)
        self.columns_layout.setSpacing(10)
        self.columns_layout.setContentsMargins(0, 10, 0, 10)
        self.columns_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Added this line

        # Add plus button inside scroll area
        self.add_column_button = QPushButton()
        self.add_column_button.setToolTip(f'Add {self.data_manager.ui_column_label.lower()}')
        self.add_column_button.setIcon(QIcon(':/images/plus-solid.svg'))
        self.add_column_button.setStyleSheet(self.button_styles['large'])
        self.add_column_button.clicked.connect(lambda: self.add_column_input())
        self.columns_layout.addWidget(self.add_column_button, alignment=Qt.AlignmentFlag.AlignHCenter)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_changes)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def register_double_click_button(self, button, callback):
        button.setToolTip("Double-click")
        button.installEventFilter(self)
        self.double_click_buttons.append((button, callback))

        # Avoids type errors with receivers() method
        button.blockSignals(True)

    def eventFilter(self, obj, event):
        # Filter events for registered double-click buttons
        # Check if obj is a valid QObject and event is a valid QEvent
        if not isinstance(obj, QObject) or not isinstance(event, QEvent):
            return False

        # Check double-click button
        for button, callback in self.double_click_buttons:
            # Make sure obj is the button object, not a QWidgetItem
            if obj == button and event.type() == QEvent.Type.MouseButtonDblClick:
                # Call the associated callback when double-clicked
                callback()
                return True  # Event was handled

        # Pass event to parent class if not handled
        return super().eventFilter(obj, event)

    def _populate_columns(self):
        column_map = self.data_manager.chart_data.get('column_map', {})
        is_minute_chart = 'Minute' in self.data_manager.chart_data.get('type', '')

        self.add_column_input(column_map['d'], 'd')

        if is_minute_chart:
            self.add_column_input(column_map['m'], 'm')

        for sys_col_type in ['c', 'i']:
            self.add_column_input(column_map.get(sys_col_type, ''), sys_col_type)

        # Add any remaining sys cols
        fixed_types = ['d', 'm', 'c', 'i']
        other_sys_col = [k for k in column_map.keys() if k not in fixed_types]
        for sys_col in other_sys_col:
            user_col = column_map[sys_col]
            self.add_column_input(user_col, sys_col)

    def increment_misc_sys_col(self):
        prefix = 'o'
        num = 1
        existing_o_cols = [col['sys_col'] for col in self.column_inputs if col['sys_col'].startswith('o')]
        while f"{prefix}{num}" in existing_o_cols:
            num += 1

        return f"{prefix}{num}"

    def add_column_input(self, column_name="", sys_col='o'):
        if sys_col == 'o':
            sys_col = self.increment_misc_sys_col()

        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        input_field = QLineEdit(column_name)
        input_field.setPlaceholderText("Enter column name")

        # Create badge indicating column type (d, c, i, m, o)
        column_type_label = QLabel()
        if sys_col == 'c':
            badge_text = "⬤"  # Dot for Increase
        elif sys_col == 'i':
            badge_text = "✕"  # X for Decrease
        elif sys_col == 'm':
            badge_text = "⧖"  # Underscore for timing
        elif sys_col == 'd':
            badge_text = "📅"  # Calendar for date
        else:
            badge_text = "▼"  # Triangle for Other

        column_type_label.setText(badge_text)
        column_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column_type_label.setStyleSheet("font-size: 16px; min-width: 20px; font-style: normal; font-weight: normal;")

        # Add widgets to row
        row_layout.addWidget(column_type_label)
        row_layout.addWidget(input_field, 1)  # Stretch factor 1

        # Only add remove button if sys_col is not 'm' or 'd' AND column_name is not empty
        remove_btn = None
        if sys_col not in ['m', 'd'] and column_name.strip():
            remove_btn = QPushButton()
            remove_btn.setIcon(QIcon(':/images/minus-solid.svg'))
            remove_btn.setStyleSheet(self.button_styles['small'])
            row_layout.addWidget(remove_btn)
        else:
            # Add invisible spacer with same dimensions as the button
            spacer = QWidget()
            spacer.setFixedSize(24, 24)  # Same size as small button
            spacer.setStyleSheet("background-color: transparent;")
            row_layout.addWidget(spacer)

        # Insert before the plus button
        self.columns_layout.insertWidget(self.columns_layout.count() - 1, row_widget)

        # Store reference to widgets
        self.column_inputs.append({
            'row_widget': row_widget,
            'input_field': input_field,
            'remove_btn': remove_btn,
            'sys_col': sys_col
        })

        # Connect remove button with double-click handling if it exists
        if remove_btn:
            # Use a closure that captures the widget reference, not the index
            self.register_double_click_button(
                remove_btn,
                lambda widget=row_widget: self.remove_column_input(widget))

    def remove_column_input(self, widget):
        # Remove widget from layout
        self.columns_layout.removeWidget(widget)

        # Clean up and delete the widget
        widget.deleteLater()

        # Remove from tracking list - find the column by widget reference
        for i, col in enumerate(self.column_inputs):
            if col['row_widget'] == widget:
                self.column_inputs.pop(i)
                break

    def confirm_changes(self):
        # Capture input data in a dictionary - each sys_col: user_col
        is_minute_chart = 'Minute' in self.data_manager.chart_data['type']
        old_column_map = self.data_manager.chart_data['column_map']
        plot_columns = self.data_manager.plot_columns
        new_column_map = {}

        # Only process columns that are still valid (not removed)
        for column in self.column_inputs:
            sys_col = column['sys_col']

            # Check if input_field is still valid before accessing
            try:
                user_col = column['input_field'].text().strip()

                # Only include non-empty columns
                if user_col:
                    # Prevent duplicates by incrementing
                    base_user_col = user_col
                    counter = 1
                    while user_col in new_column_map.values():
                        user_col = f"{base_user_col}_{counter}"
                        counter += 1
                    new_column_map[sys_col] = user_col
            except (RuntimeError, AttributeError):
                # Skip this column if the widget has been deleted
                continue

        # In case m was omitted
        if 'm' in old_column_map.keys() and 'm' not in new_column_map.keys():
            new_column_map['m'] = old_column_map['m']

        # Create a mapping of old column names to new column names
        column_name_mapping = {}
        for sys_col, new_user_col in new_column_map.items():
            if sys_col in old_column_map:
                old_user_col = old_column_map[sys_col]
                if old_user_col != new_user_col:
                    column_name_mapping[old_user_col] = new_user_col

        # Re-map plot column instances
        new_plot_columns = {}
        discarded_columns = []
        for old_key, column_obj in plot_columns.items():
            if column_obj.sys_col in new_column_map:
                new_key = new_column_map[column_obj.sys_col]
                column_obj.user_col = new_key
                new_plot_columns[new_key] = column_obj
            else:
                discarded_columns.append(column_obj)

        # Remove discarded columns from chart
        for column_obj in discarded_columns:
            column_obj.delete()

        # Create any new necessary columns instances
        for sys_col, user_col in new_column_map.items():

            # Skip date mapping columns
            if sys_col == 'd':
                continue
            # Skip floor column for non-minute charts
            if sys_col == 'm' and not is_minute_chart:
                continue

            if user_col not in new_plot_columns.keys():
                new_plot_columns[user_col] = self.event_bus.emit('get_data_point_column', {'sys_col': sys_col, 'user_col': user_col})

        # 1. Update view settings
        view_settings = self.data_manager.chart_data['view']
        new_view_settings = {}

        for key, value in view_settings.items():
            if '|' in key:
                sys_col, user_col = key.split('|')
                if user_col in column_name_mapping:
                    new_key = f"{sys_col}|{column_name_mapping[user_col]}"
                    new_view_settings[new_key] = value
                else:
                    new_view_settings[key] = value
            else:
                new_view_settings[key] = value

        self.data_manager.chart_data['view'] = new_view_settings

        # 2. Update data_point_styles
        data_point_styles = self.data_manager.chart_data.get('data_point_styles', {})
        new_data_point_styles = {}

        for key, value in data_point_styles.items():
            if isinstance(key, str) and key in column_name_mapping:
                new_data_point_styles[column_name_mapping[key]] = value
            else:
                new_data_point_styles[key] = value

        self.data_manager.chart_data['data_point_styles'] = new_data_point_styles

        # 3. Update trend references (trend_corr, trend_err, trend_misc)
        for trend_type in ['trend_corr', 'trend_err', 'trend_misc']:
            trends = self.data_manager.chart_data.get(trend_type, [])
            for trend in trends:
                if 'user_col' in trend and trend['user_col'] in column_name_mapping:
                    trend['user_col'] = column_name_mapping[trend['user_col']]

        # Apply updates
        self.data_manager.plot_columns = new_plot_columns
        self.data_manager.chart_data['column_map'] = new_column_map
        self.event_bus.emit("reload_current_mode")
        self.event_bus.emit('update_legend')
        self.data_manager.handle_data_saving()

        self.accept()


class SpreadsheetDialog(QDialog):
    """
    A dialog that provides a spreadsheet-like interface for viewing and editing chart data.
    Allows users to navigate through data by calendar unit, edit cells, and delete rows.
    """
    dataChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Editor")
        self.setMinimumSize(800, 600)

        # Initialize managers
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Get chart type and calendar unit
        self.chart_type = self.data_manager.chart_data['type']
        self.calendar_unit = self.chart_type[0]  # D, W, M, Y
        self.is_minute_chart = 'Minute' in self.chart_type

        # Current view date and data
        self.current_view_date = pd.Timestamp.now()
        self.df_view = None
        self.original_df = None
        self.start_date = None
        self.end_date = None

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.Shape.StyledPanel)
        sidebar_layout = QVBoxLayout(sidebar)

        # Calendar unit mapping
        calendar_unit_map = {'D': 'Day', 'W': 'Week', 'M': 'Month', 'Y': 'Year'}
        calendar_unit_text = calendar_unit_map.get(self.calendar_unit, 'Dates')

        dates_group = QGroupBox(calendar_unit_text)
        dates_group.setStyleSheet("QGroupBox { border: none; }")
        dates_layout = QVBoxLayout(dates_group)

        self.dates_list = QListWidget()
        self.dates_list.itemClicked.connect(self.on_date_list_item_clicked)
        dates_layout.addWidget(self.dates_list)
        sidebar_layout.addWidget(dates_group)

        # === MAIN CONTENT ===
        main_content = QFrame()
        main_content_layout = QVBoxLayout(main_content)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        main_content_layout.addWidget(self.table)

        # Button bar
        button_layout = QHBoxLayout()

        add_row_btn = QPushButton("Add Row")
        add_row_btn.clicked.connect(self.add_row)

        delete_row_btn = QPushButton("Delete Selected")
        delete_row_btn.clicked.connect(self.delete_selected_rows)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_to_csv)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_changes)
        apply_btn.setStyleSheet("background-color: #96deeb;")

        button_layout.addWidget(add_row_btn)
        button_layout.addWidget(delete_row_btn)
        button_layout.addWidget(export_csv_btn)
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        main_content_layout.addLayout(button_layout)

        # Add to splitter and layout
        splitter.addWidget(sidebar)
        splitter.addWidget(main_content)
        splitter.setSizes([200, 600])
        main_layout.addWidget(splitter)

    def refresh_data(self):
        """Refresh the dialog with current data"""
        self.original_df = self.data_manager.df_raw.copy()

        # Set initial view date
        if self.original_df is not None and not self.original_df.empty and 'd' in self.original_df.columns:
            self.current_view_date = pd.to_datetime(self.original_df['d']).min()
        else:
            self.current_view_date = pd.Timestamp.now()

        self.populate_dates_list()
        self.calculate_view_dates()
        self.update_view_data()
        self.populate_table()

    def calculate_view_dates(self):
        """Calculate start and end dates for the current view based on calendar unit"""
        current_date = self.current_view_date

        if self.calendar_unit == 'D':
            self.start_date = pd.Timestamp(current_date.year, current_date.month, current_date.day)
            self.end_date = self.start_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        elif self.calendar_unit == 'W':
            weekday = current_date.weekday()
            sunday_offset = weekday + 1 if weekday < 6 else 0
            self.start_date = current_date - pd.Timedelta(days=sunday_offset)
            self.start_date = pd.Timestamp(self.start_date.year, self.start_date.month, self.start_date.day)
            self.end_date = self.start_date + pd.Timedelta(days=7) - pd.Timedelta(seconds=1)
        elif self.calendar_unit == 'M':
            self.start_date = pd.Timestamp(current_date.year, current_date.month, 1)
            if current_date.month == 12:
                self.end_date = pd.Timestamp(current_date.year + 1, 1, 1) - pd.Timedelta(seconds=1)
            else:
                self.end_date = pd.Timestamp(current_date.year, current_date.month + 1, 1) - pd.Timedelta(seconds=1)
        elif self.calendar_unit == 'Y':
            self.start_date = pd.Timestamp(current_date.year, 1, 1)
            self.end_date = pd.Timestamp(current_date.year, 12, 31, 23, 59, 59)

    def update_view_data(self):
        """Update the data view based on the current date range"""
        if self.original_df is not None and not self.original_df.empty:
            df = self.original_df.copy()
            df['d'] = pd.to_datetime(df['d'])
            self.df_view = df[(df['d'] >= self.start_date) & (df['d'] <= self.end_date)].copy()
            self.df_view = self.df_view.sort_values('d')

    def populate_table(self):
        """Populate the table with data from the current view"""
        self.table.clear()

        if self.df_view is None or self.df_view.empty:
            # Set up empty table with headers
            column_map = self.data_manager.chart_data['column_map']
            headers = ['Date']
            if self.is_minute_chart:
                headers.append('Minutes')
            for col_key, col_name in column_map.items():
                if col_key not in ['d', 'm']:
                    headers.append(col_name)

            self.table.setColumnCount(len(headers))
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(0)
            return

        # Get column map and setup columns
        column_map = self.data_manager.chart_data['column_map']
        sys_cols = ['d'] + (['m'] if self.is_minute_chart else [])
        data_cols = sorted([col for col in self.df_view.columns if col not in ['d', 'm']],
                           key=lambda x: ('z' + x if not x.startswith('o') else x))
        all_cols = sys_cols + data_cols

        # Create headers
        headers = []
        for col in all_cols:
            if col == 'd':
                headers.append('Date')
            elif col == 'm':
                headers.append('Minutes')
            else:
                # Find user column name
                headers.append(next((user_col for sys_col, user_col in column_map.items() if sys_col == col), col))

        # Set table dimensions and headers
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(self.df_view))
        self.table.setHorizontalHeaderLabels(headers)

        # Populate data
        for row_idx, (_, row_data) in enumerate(self.df_view.iterrows()):
            for col_idx, col_name in enumerate(all_cols):
                cell_value = row_data.get(col_name, '')

                if col_name == 'd':
                    date_str = pd.to_datetime(cell_value).strftime('%Y-%m-%d')
                    item = QTableWidgetItem(date_str)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                else:
                    if pd.isna(cell_value):
                        item = QTableWidgetItem("")  # Show empty string for NaN
                    elif isinstance(cell_value, (float, int)):
                        formatted_value = self.data_manager.format_y_value(cell_value)
                        item = QTableWidgetItem(str(formatted_value))
                    else:
                        item = QTableWidgetItem(str(cell_value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                item.setData(Qt.ItemDataRole.UserRole, col_name)
                self.table.setItem(row_idx, col_idx, item)

        # Set column resize modes
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

        # Set numeric delegates for editing
        for col_idx in range(1, len(headers)):
            self.table.setItemDelegateForColumn(col_idx, self.create_numeric_delegate())

    def populate_dates_list(self):
        """Populate the dates list with all unique dates in the data"""
        self.dates_list.clear()

        if self.original_df is None or self.original_df.empty:
            return

        df = self.original_df.copy()
        df['d'] = pd.to_datetime(df['d'])
        grouped_dates = []

        # Group dates by calendar unit - handle each case separately due to pandas limitations
        if self.calendar_unit == 'D':
            unique_dates = df['d'].dt.floor('D').unique()
            for date in sorted(unique_dates):
                formatted_date = date.strftime('%Y-%m-%d')
                grouped_dates.append((date, formatted_date))
        elif self.calendar_unit == 'W':
            df['week_start'] = df['d'].dt.floor('D') - pd.to_timedelta(df['d'].dt.dayofweek, unit='D')
            unique_dates = df['week_start'].unique()
            for date in sorted(unique_dates):
                week_end = date + pd.Timedelta(days=6)
                formatted_date = f"{date.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}"
                grouped_dates.append((date, formatted_date))
        elif self.calendar_unit == 'M':
            # Create month start dates manually to avoid pandas floor('M') issue
            df['month_start'] = pd.to_datetime(df['d'].dt.to_period('M').dt.start_time)
            unique_dates = df['month_start'].unique()
            for date in sorted(unique_dates):
                formatted_date = date.strftime('%B %Y')
                grouped_dates.append((date, formatted_date))
        elif self.calendar_unit == 'Y':
            df['year_start'] = pd.to_datetime(df['d'].dt.year, format='%Y')
            unique_dates = df['year_start'].unique()
            for date in sorted(unique_dates):
                formatted_date = date.strftime('%Y')
                grouped_dates.append((date, formatted_date))

        # Add items to list and calculate optimal width
        max_text_width = 0
        font_metrics = QFontMetrics(self.dates_list.font())

        for date_value, date_text in grouped_dates:
            item = QListWidgetItem(date_text)
            item.setData(Qt.ItemDataRole.UserRole, date_value)
            self.dates_list.addItem(item)
            max_text_width = max(max_text_width, font_metrics.horizontalAdvance(date_text))

        # Set optimal list width
        optimal_width = max_text_width + 39  # 16 scrollbar + 8 padding + 15 extra
        self.dates_list.setFixedWidth(optimal_width)

        # Find and set sidebar width
        sidebar = self.dates_list.parent().parent()
        if sidebar:
            sidebar.setFixedWidth(optimal_width + 4)

        # Update splitter sizes
        splitter = self.findChild(QSplitter)
        if splitter:
            total_width = sum(splitter.sizes())
            splitter.setSizes([optimal_width + 4, total_width - optimal_width - 4])

        self.highlight_current_date_in_list()

    def highlight_current_date_in_list(self):
        """Highlight the current date/period in the dates list"""
        for i in range(self.dates_list.count()):
            item = self.dates_list.item(i)
            date_value = item.data(Qt.ItemDataRole.UserRole)

            # Check if current date falls within this period
            match_conditions = {
                'D': date_value.date() == self.current_view_date.date(),
                'W': date_value <= self.current_view_date <= date_value + pd.Timedelta(days=6),
                'M': (date_value.month == self.current_view_date.month and
                      date_value.year == self.current_view_date.year),
                'Y': date_value.year == self.current_view_date.year
            }

            if match_conditions.get(self.calendar_unit, False):
                self.dates_list.setCurrentItem(item)
                break

    def on_date_list_item_clicked(self, item):
        """Handle click on a date in the dates list"""
        date_value = item.data(Qt.ItemDataRole.UserRole)
        self.current_view_date = date_value
        self.calculate_view_dates()
        self.update_view_data()
        self.populate_table()

    def show_context_menu(self, position):
        """Show context menu for table"""
        context_menu = QMenu(self)

        add_action = QAction("Add Row", self)
        add_action.triggered.connect(self.add_row)

        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self.delete_selected_rows)
        delete_action.setEnabled(len(self.table.selectedItems()) > 0)

        context_menu.addAction(add_action)
        context_menu.addAction(delete_action)
        context_menu.exec(self.table.mapToGlobal(position))

    def add_row(self):
        """Add a new row to the table"""
        current_rows = self.table.rowCount()
        self.table.insertRow(current_rows)

        column_map = self.data_manager.chart_data['column_map']

        # Set date (non-editable)
        date_str = self.current_view_date.strftime('%Y-%m-%d')
        date_item = QTableWidgetItem(date_str)
        date_item.setData(Qt.ItemDataRole.UserRole, 'd')
        date_item.setFlags(date_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(current_rows, 0, date_item)

        # Set default values for other columns
        for col_idx in range(1, self.table.columnCount()):
            header_text = self.table.horizontalHeaderItem(col_idx).text()

            # Find system column key
            sys_col = next((key for key, value in column_map.items() if value == header_text), None)

            if sys_col:
                default_value = "1" if sys_col == 'm' else "0"
                item = QTableWidgetItem(default_value)
                item.setData(Qt.ItemDataRole.UserRole, sys_col)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(current_rows, col_idx, item)

    def delete_selected_rows(self):
        """Delete selected rows from the table"""
        selected_rows = {item.row() for item in self.table.selectedItems()}
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)

    def _collect_table_data(self):
        """Helper method to collect data from table and return processed DataFrame"""
        new_data_rows = []
        column_map = self.data_manager.chart_data['column_map']

        # Process each row in the table
        for row_idx in range(self.table.rowCount()):
            row_data = {}

            # Process each column in the row
            for col_idx in range(self.table.columnCount()):
                item = self.table.item(row_idx, col_idx)
                if not item:
                    continue

                sys_col = item.data(Qt.ItemDataRole.UserRole)
                if not sys_col:
                    continue

                cell_value = item.text().strip()

                if sys_col == 'd':
                    row_data['d'] = pd.to_datetime(cell_value)
                elif sys_col == 'm':
                    minutes_val = float(cell_value) if cell_value else 1.0
                    row_data['m'] = max(1.0, minutes_val)
                else:
                    if not cell_value:
                        row_data[sys_col] = np.nan
                    else:
                        # Use pd.to_numeric which handles invalid values gracefully
                        numeric_val = pd.to_numeric(cell_value, errors='coerce')
                        if pd.isna(numeric_val):
                            row_data[sys_col] = np.nan
                        else:
                            row_data[sys_col] = max(0, numeric_val)

            if 'd' in row_data:
                new_data_rows.append(row_data)

        if not new_data_rows:
            return pd.DataFrame()

        # Convert to DataFrame
        new_df = pd.DataFrame(new_data_rows)

        # Ensure all required columns exist
        all_sys_cols = set(column_map.keys())
        for sys_col in all_sys_cols:
            if sys_col not in new_df.columns:
                if sys_col == 'm':
                    new_df[sys_col] = 1.0
                elif sys_col != 'd':
                    new_df[sys_col] = np.nan

        # Sort by date
        return new_df.sort_values('d').reset_index(drop=True)

    def export_to_csv(self):
        """Export current data to CSV file"""
        # Get current table data
        export_df = self._collect_table_data()

        if export_df.empty:
            QMessageBox.warning(self, "Export Error", "No data to export.")
            return

        export_folder = self.event_bus.emit("get_user_preference", ['export_csv_folder', ''])
        if not export_folder:
            export_folder = self.event_bus.emit("get_user_preference", ['home_folder', ''])

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", export_folder, "CSV Files (*.csv);;All Files (*)"
        )

        if not file_path:
            return

        if not file_path.endswith('.csv'):
            file_path += '.csv'

        # Save export directory preference
        export_dir = str(Path(file_path).parent)
        self.event_bus.emit("update_user_preference", ['export_csv_folder', export_dir])

        # Prepare export dataframe
        export_df['d'] = pd.to_datetime(export_df['d']).dt.strftime('%Y-%m-%d')

        if not self.is_minute_chart and 'm' in export_df.columns:
            export_df = export_df.drop(columns=['m'])

        # Rename columns using column map
        column_map = self.data_manager.chart_data['column_map']
        rename_dict = {col: column_map[col] for col in export_df.columns if col in column_map}

        if rename_dict:
            export_df = export_df.rename(columns=rename_dict)

        export_df.to_csv(file_path, index=False)
        QMessageBox.information(self, "Export Successful", f"Data exported to {file_path}")

    def apply_changes(self):
        """Apply changes to the dataframe and close the dialog"""
        new_df = self._collect_table_data()
        if new_df.empty:
            return

        # Update data manager
        self.data_manager.df_raw = new_df
        column_map = self.data_manager.chart_data['column_map']

        # Update plot columns
        plot_column_keys_except_floor = [v for k, v in column_map.items() if k not in ['d', 'm']]

        for user_col in plot_column_keys_except_floor:
            if user_col not in self.data_manager.plot_columns:
                sys_col = next((k for k, v in column_map.items() if v == user_col), None)
                if sys_col:
                    self.data_manager.plot_columns[user_col] = self.event_bus.emit(
                        'get_data_point_column', {'sys_col': sys_col, 'user_col': user_col})

        # Refresh all plot columns
        for user_col in self.data_manager.plot_columns.keys():
            self.data_manager.plot_columns[user_col].refresh_view()

        # Handle minute column for minute charts
        if self.is_minute_chart:
            minute_col_name = column_map.get('m', 'minutes')
            if minute_col_name not in self.data_manager.plot_columns:
                self.data_manager.plot_columns[minute_col_name] = self.event_bus.emit(
                    'get_data_point_column', {'sys_col': 'm', 'user_col': minute_col_name})
            self.data_manager.plot_columns[minute_col_name].refresh_view()

        # Refresh chart and save
        self.event_bus.emit('update_legend')
        self.event_bus.emit('refresh_chart')
        self.data_manager.handle_data_saving()
        self.dataChanged.emit()
        self.accept()

    def create_numeric_delegate(self):
        """Create a numeric delegate for table cells"""

        class NumericDelegate(QItemDelegate):
            def createEditor(self, parent, option, index):
                editor = QLineEdit(parent)
                header_text = index.model().headerData(index.column(), Qt.Orientation.Horizontal)

                if header_text == "Minutes":
                    # Minutes column uses standard validator (no empty allowed)
                    validator = QDoubleValidator(0, 1440, 2, editor)
                    validator.setNotation(QDoubleValidator.Notation.StandardNotation)
                else:
                    # Other numeric columns allow empty strings
                    class IntValidator(QIntValidator):
                        def validate(self, input_str, pos):
                            if input_str == "":
                                return (QValidator.State.Acceptable, input_str, pos)
                            return super().validate(input_str, pos)

                    validator = IntValidator(0, 999999, editor)

                editor.setValidator(validator)
                return editor

        return NumericDelegate(self)


class ChartBrowserDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_manager = DataManager()
        self.event_bus = EventBus()
        self.selected_chart_id = None
        self.selected_file_path = None
        self.chart_metadata_cache = {}  # Cache for chart metadata
        self.current_location = self.data_manager.event_bus.emit("get_user_preference", ['last_open_tab', 'local'])

        self.setWindowTitle("Chart Browser")
        self.setMinimumSize(800, 600)

        self.setup_ui()
        self.load_charts()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Search bar with label
        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by name, type, or credit lines")
        self.search_input.textChanged.connect(self.filter_charts)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        main_layout.addLayout(search_layout)

        # Stacked widget for location views
        self.stacked_widget = QStackedWidget()

        # Create grids for each location
        self.grid_local = self.create_charts_grid()
        self.grid_cloud = self.create_charts_grid()
        self.grid_other = self.create_charts_grid()

        # Add message labels for cloud and other
        self.cloud_label = QLabel("Coming in a future version")
        self.cloud_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cloud_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")

        self.other_label = QLabel("Coming in a future version")
        self.other_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.other_label.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")

        # Create container widgets for each grid
        local_widget = QWidget()
        local_layout = QVBoxLayout(local_widget)
        local_layout.setContentsMargins(0, 0, 0, 0)
        local_layout.addWidget(self.grid_local)

        cloud_widget = QWidget()
        cloud_layout = QVBoxLayout(cloud_widget)
        cloud_layout.setContentsMargins(0, 0, 0, 0)
        cloud_layout.addWidget(self.grid_cloud)
        self.cloud_label.setParent(self.grid_cloud)

        other_widget = QWidget()
        other_layout = QVBoxLayout(other_widget)
        other_layout.setContentsMargins(0, 0, 0, 0)
        other_layout.addWidget(self.grid_other)
        self.other_label.setParent(self.grid_other)

        # Add widgets to stacked widget
        self.stacked_widget.addWidget(local_widget)
        self.stacked_widget.addWidget(cloud_widget)
        self.stacked_widget.addWidget(other_widget)

        # Add stacked widget to main layout
        main_layout.addWidget(self.stacked_widget)

        # Bottom bar layout with location buttons on left, control buttons on right
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        # Create location selector buttons with custom styling
        self.location_buttons = []

        # Location buttons - left side
        location_layout = QHBoxLayout()
        location_layout.setSpacing(0)  # Tighter spacing between buttons

        for loc in ['local', 'cloud', 'other']:
            button = QPushButton(loc.capitalize())
            button.setCheckable(True)
            button.setProperty("location", loc)
            button.clicked.connect(self.on_location_button_clicked)

            # Apply custom styling for tab-like buttons
            button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #c0c0c0;
                    border-radius: 0;
                    padding: 6px 12px;
                    background-color: #f0f0f0;
                    min-width: 80px;
                }
                QPushButton:checked {
                    background-color: #e0e0e0;
                    border-bottom: 3px solid #4080c0;
                    font-weight: bold;
                }
                QPushButton:hover:!checked {
                    background-color: #e8e8e8;
                }
            """)

            location_layout.addWidget(button)
            self.location_buttons.append(button)

        # Add location buttons to left side of bottom bar
        bottom_layout.addLayout(location_layout)

        # Add a small spacer instead of a vertical line
        spacer = QSpacerItem(20, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        bottom_layout.addSpacerItem(spacer)

        # Add a stretch to push the action buttons to the right
        bottom_layout.addStretch(1)

        # File operations
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_for_json)
        bottom_layout.addWidget(self.browse_button)

        # Add delete button
        self.delete_button = QPushButton("Delete")
        self.delete_button.setEnabled(False)
        self.delete_button.setStyleSheet("QPushButton { color: #a0a0a0; }")
        self.delete_button.clicked.connect(self.delete_selected_chart)
        bottom_layout.addWidget(self.delete_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_button)

        # Add the bottom bar to the main layout
        main_layout.addLayout(bottom_layout)

        # Now that all UI elements are created, set the active location
        self.set_active_location(self.current_location)

        # Set positions of message labels
        self.resizeEvent(None)

    def set_active_location(self, location):
        """Set the active location and update UI"""
        self.current_location = location
        index = ['local', 'cloud', 'other'].index(location)

        # Update stacked widget
        self.stacked_widget.setCurrentIndex(index)

        # Update button states
        for button in self.location_buttons:
            btn_loc = button.property("location")
            button.setChecked(btn_loc == location)

        # Save preference
        self.data_manager.event_bus.emit("update_user_preference", ['last_open_tab', location])

        # Update selection state
        self.on_selection_changed()

    def on_location_button_clicked(self):
        """Handle location button clicks"""
        button = self.sender()
        location = button.property("location")
        self.set_active_location(location)

    def resizeEvent(self, event):
        # Position message labels in center of their grids
        if hasattr(self, 'cloud_label'):
            self.cloud_label.setGeometry(0, 0, self.grid_cloud.width(), self.grid_cloud.height())

        if hasattr(self, 'other_label'):
            self.other_label.setGeometry(0, 0, self.grid_other.width(), self.grid_other.height())

        super().resizeEvent(event) if event else None

    def create_charts_grid(self):
        """Create a list widget for displaying chart thumbnails with consistent styling"""
        grid = QListWidget()
        grid.setViewMode(QListWidget.ViewMode.IconMode)
        grid.setIconSize(QSize(120, 100))
        grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid.setMovement(QListWidget.Movement.Static)
        grid.setGridSize(QSize(160, 160))
        grid.setSpacing(6)
        grid.setWordWrap(True)
        grid.setTextElideMode(Qt.TextElideMode.ElideMiddle)

        # Set stylesheet for grid items
        grid.setStyleSheet("""
            QListWidget::item {
                border: 1px solid transparent;
                padding: 2px;
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background: #d0e7f7;
                border: 1px solid #99c9ef;
            }
            QListWidget::item:hover {
                background: #e8f0f8;
                border: 1px solid #c0d0e0;
            }
            QListWidget {
                padding: 4px;
                background-color: #f3f3f3;
            }
        """)

        grid.itemDoubleClicked.connect(self.chart_double_clicked)
        grid.itemSelectionChanged.connect(self.on_selection_changed)
        return grid

    def delete_selected_chart(self):
        # Get the active grid based on current location
        active_grid = getattr(self, f"grid_{self.current_location}")

        # Get the currently selected chart
        selected_items = active_grid.selectedItems()
        if not selected_items:
            return

        # Get the chart_id from the selected item
        chart_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Use the user prompt system to confirm deletion
        data = {
            'title': "Delete Chart",
            'message': f"Delete {chart_id}?",
            'options': ['Yes', 'No']
        }
        result = self.event_bus.emit('trigger_user_prompt', data)

        # Delete if user confirmed (selected "Yes")
        if result == 0:  # "Yes" is index 0
            # Delete the chart using event bus
            self.event_bus.emit('delete_chart', chart_id)

            # Refresh the chart grid
            self.load_charts()

    def on_selection_changed(self):
        """Enable the Open and Delete buttons if a chart is selected"""
        # Get active grid based on current location
        active_grid = getattr(self, f"grid_{self.current_location}")

        # Only enable buttons for Local tab for now
        if self.current_location != 'local':
            self.delete_button.setEnabled(False)
            self.delete_button.setStyleSheet("QPushButton { color: #a0a0a0; }")
            return

        selected_items = active_grid.selectedItems()
        is_selected = len(selected_items) > 0

        # Enable/disable buttons
        self.delete_button.setEnabled(is_selected)

        # Visual indication for delete button
        if is_selected:
            self.delete_button.setStyleSheet("")
        else:
            self.delete_button.setStyleSheet("QPushButton { color: #a0a0a0; }")

    def add_frame_to_pixmap(self, pixmap):
        """Add a black frame around a pixmap"""
        if pixmap.isNull():
            return pixmap

        # Create a slightly larger pixmap to accommodate the frame
        frame_width = 2  # 2px border
        width = pixmap.width() + (frame_width * 2)
        height = pixmap.height() + (frame_width * 2)

        framed_pixmap = QPixmap(width, height)
        framed_pixmap.fill(Qt.GlobalColor.transparent)  # Start with transparent background

        # Create painter for drawing
        painter = QPainter(framed_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw the original pixmap in the center
        painter.drawPixmap(frame_width, frame_width, pixmap)

        # Draw the black frame
        painter.setPen(QPen(QColor(0, 0, 0), frame_width))
        painter.drawRect(frame_width // 2, frame_width // 2,
                         width - frame_width, height - frame_width)

        painter.end()
        return framed_pixmap

    def load_charts(self):
        # Clear all grids
        self.grid_local.clear()
        self.grid_cloud.clear()
        self.grid_other.clear()

        # Only load data for local tab for now
        active_grid = self.grid_local

        # Get chart IDs from SQLite database
        chart_ids = self.data_manager.sqlite_manager.get_all_chart_ids()

        # Clear metadata cache
        self.chart_metadata_cache.clear()

        for chart_id in chart_ids:
            # Get metadata and thumbnail for the chart
            metadata = self._get_chart_metadata(chart_id)
            thumbnail_data = self.data_manager.sqlite_manager.get_chart_thumbnail(chart_id)

            if metadata:
                # Store metadata in cache for search filtering
                self.chart_metadata_cache[chart_id] = metadata

                # Create list item for the grid
                item = QListWidgetItem()

                # Set chart name
                chart_name = Path(chart_id).stem

                # Get chart type
                chart_type = metadata.get('type', 'Unknown')

                # Set display text - keep it shorter to ensure tight layout
                item.setText(f"{chart_name}\n{chart_type}")

                # Store metadata for search filtering
                item.setData(Qt.ItemDataRole.UserRole, chart_id)

                # Add credit lines as additional search data
                credit_lines = metadata.get('credit', [])
                if credit_lines and isinstance(credit_lines, (list, tuple)):
                    credit_text = " ".join(str(line) for line in credit_lines)
                    item.setData(Qt.ItemDataRole.UserRole + 1, credit_text)

                # Set icon with black frame by creating a framed pixmap
                if thumbnail_data:
                    original_pixmap = QPixmap()
                    original_pixmap.loadFromData(thumbnail_data)

                    # Create a new pixmap with a border
                    framed_pixmap = self.add_frame_to_pixmap(original_pixmap)
                    item.setIcon(QIcon(framed_pixmap))
                else:
                    # Use a default icon if no thumbnail
                    item.setIcon(QIcon.fromTheme("image-missing"))

                # Set alignment
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Add to grid view
                active_grid.addItem(item)

    def _get_chart_metadata(self, chart_id):
        """Get metadata for a chart from the database"""
        try:
            # Query the database
            conn = self.data_manager.sqlite_manager.connection
            if not conn:
                self.data_manager.sqlite_manager.connect()
                conn = self.data_manager.sqlite_manager.connection

            if conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT metadata FROM {self.data_manager.sqlite_manager.TABLE_CHART_METADATA} WHERE chart_id = ?",
                    (chart_id,)
                )
                result = cursor.fetchone()

                if result and result[0]:
                    # Parse the JSON metadata
                    return json.loads(result[0])

            return None
        except Exception as e:
            print(f"Error retrieving chart metadata: {e}")
            return None

    def filter_charts(self):
        """Filter charts based on search input - includes credit lines"""
        search_text = self.search_input.text().lower()

        # Only filter the current active grid
        active_grid = getattr(self, f"grid_{self.current_location}")

        if self.current_location == 'local':  # Only filter local tab (has actual data)
            for i in range(active_grid.count()):
                item = active_grid.item(i)
                if item:
                    # Get item text (name and type)
                    item_text = item.text().lower()

                    # Get credit lines from cached metadata
                    chart_id = item.data(Qt.ItemDataRole.UserRole)
                    credit_text = item.data(Qt.ItemDataRole.UserRole + 1) or ""
                    credit_text = credit_text.lower()

                    # Show item if search text is in either name, type, or credit lines
                    # Only hide if: there is a search text AND it's not found in either place
                    should_hide = bool(search_text) and (search_text not in item_text) and (
                                search_text not in credit_text)
                    item.setHidden(should_hide)

    def chart_double_clicked(self, item):
        """Handle double-click on a chart item"""
        self.selected_chart_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def browse_for_json(self):
        """Open file dialog to browse for JSON file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select chart file',
            self.data_manager.user_preferences['home_folder'],
            'JSON files (*.json);;All files (*.*)'
        )

        if file_path:
            # Store both the chart_id (for database lookup) and the full file path
            self.selected_chart_id = Path(file_path).stem
            self.selected_file_path = file_path  # Store the full path
            self.accept()

    def get_selected_chart_path(self):
        """Return the full path or ID of the selected chart"""
        if self.selected_file_path:
            return self.selected_file_path
        elif self.selected_chart_id:
            return self.selected_chart_id
        return None

