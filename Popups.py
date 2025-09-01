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

        bitcoin_btn = QPushButton('Bitcoin')
        bitcoin_icon = QIcon(':/images/bitcoin_logo.png')
        bitcoin_btn.setIcon(bitcoin_icon)
        bitcoin_btn.clicked.connect(self.bitcoin_btn_clicked)

        btn_layout.addWidget(paypal_btn)
        btn_layout.addWidget(bitcoin_btn)
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
        self.event_bus.emit('save_complete_chart')

        self.accept()


class SpreadsheetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Editor")
        self.setMinimumSize(800, 600)

        # Initialize managers
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Get chart type
        self.chart_type = self.data_manager.chart_data['type']
        self.is_minute_chart = 'Minute' in self.chart_type

        # Data
        self.original_df = None  # snapshot of original data (unchanged until Apply)
        self.table_df = None  # live working copy that reflects table edits
        self._suppress_item_changed = False  # guard during programmatic population

        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.table)

        # Button bar
        button_layout = QHBoxLayout()

        delete_row_btn = QPushButton("Delete Selected")
        delete_row_btn.clicked.connect(self.delete_selected_rows)

        export_csv_btn = QPushButton("Export CSV")
        export_csv_btn.clicked.connect(self.export_to_csv)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_changes)
        apply_btn.setStyleSheet("background-color: #96deeb;")

        button_layout.addWidget(delete_row_btn)
        button_layout.addWidget(export_csv_btn)
        button_layout.addStretch()
        button_layout.addWidget(apply_btn)
        main_layout.addLayout(button_layout)

        # Live write-through
        self.table.itemChanged.connect(self._on_item_changed)

    def refresh_data(self):
        self.original_df = self.data_manager.df_raw.copy()
        self.table_df = self.data_manager.df_raw.copy(deep=True)
        self.populate_table()

    def populate_table(self):
        self._suppress_item_changed = True
        try:
            self.table.clear()

            # If empty, set up an empty table with headers from column_map
            if self.table_df is None or self.table_df.empty:
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

            # Prepare dataframe
            df = self.table_df.copy()
            if 'd' in df.columns:
                df['d'] = pd.to_datetime(df['d'], errors='coerce')
                df = df.sort_values('d')

            # Get column map and setup columns
            column_map = self.data_manager.chart_data['column_map']
            sys_cols = (['d'] + (['m'] if self.is_minute_chart and 'm' in df.columns else []))
            data_cols = sorted([col for col in df.columns if col not in ['d', 'm']],
                               key=lambda x: ('z' + x if not x.startswith('o') else x))
            all_cols = [c for c in sys_cols + data_cols if c in df.columns]

            # Create headers
            headers = []
            for col in all_cols:
                if col == 'd':
                    headers.append('Date')
                elif col == 'm':
                    headers.append('Minutes')
                else:
                    headers.append(next((user_col for sys_col, user_col in column_map.items() if sys_col == col), col))

            # Set table dimensions and headers
            self.table.setColumnCount(len(headers))
            self.table.setRowCount(len(df))
            self.table.setHorizontalHeaderLabels(headers)

            # Populate data
            for row_idx, (_, row_data) in enumerate(df.iterrows()):
                for col_idx, col_name in enumerate(all_cols):
                    cell_value = row_data.get(col_name, '')

                    if col_name == 'd':
                        date_str = ""
                        if pd.notna(cell_value):
                            date_str = pd.to_datetime(cell_value).strftime('%Y-%m-%d')
                        item = QTableWidgetItem(date_str)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    else:
                        if pd.isna(cell_value):
                            item = QTableWidgetItem("")
                        elif isinstance(cell_value, (float, int)):
                            formatted_value = self.data_manager.format_y_value(cell_value)
                            item = QTableWidgetItem(str(formatted_value))
                        else:
                            item = QTableWidgetItem(str(cell_value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Store the system column key for round-trip mapping
                    item.setData(Qt.ItemDataRole.UserRole, col_name)
                    self.table.setItem(row_idx, col_idx, item)

            # Set column resize modes
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)

            # Set numeric delegates for editing
            for col_idx in range(1, len(headers)):
                self.table.setItemDelegateForColumn(col_idx, self.create_numeric_delegate())
        finally:
            self._suppress_item_changed = False

    def _on_item_changed(self, item: QTableWidgetItem):
        """Live write-through: when a cell changes, write it to self.table_df."""
        if self._suppress_item_changed or self.table_df is None:
            return

        sys_col = item.data(Qt.ItemDataRole.UserRole)
        if not sys_col or sys_col == 'd':  # Date is non-editable
            return

        r = item.row()
        text = (item.text() or "").strip()

        # Parse into appropriate Python/NA value
        if text == "":
            value = pd.NA
        elif sys_col == 'm':
            try:
                value = float(text)
            except ValueError:
                value = pd.NA
        else:
            try:
                value = int(text)
            except ValueError:
                try:
                    value = float(text)
                except ValueError:
                    value = text

        # Assign; if dtype blocks, upcast to object
        try:
            self.table_df.at[r, sys_col] = value
        except Exception:
            self.table_df[sys_col] = self.table_df[sys_col].astype('object')
            self.table_df.at[r, sys_col] = value

    def show_context_menu(self, position):
        """Show context menu for table"""
        context_menu = QMenu(self)

        delete_action = QAction("Delete Row", self)
        delete_action.triggered.connect(self.delete_selected_rows)
        delete_action.setEnabled(len(self.table.selectedItems()) > 0)

        context_menu.addAction(delete_action)
        context_menu.exec(self.table.mapToGlobal(position))

    def delete_selected_rows(self):
        """Delete selected rows from both the UI and the working copy."""
        selected_rows = sorted({item.row() for item in self.table.selectedItems()}, reverse=True)
        if not selected_rows:
            return

        # Remove from working DataFrame by position
        keep_idx = [i for i in range(len(self.table_df)) if i not in selected_rows]
        self.table_df = self.table_df.iloc[keep_idx].reset_index(drop=True)

        # Remove from UI
        self._suppress_item_changed = True
        try:
            for row in selected_rows:
                self.table.removeRow(row)
        finally:
            self._suppress_item_changed = False

    def export_to_csv(self):
        if self.original_df is None or self.original_df.empty:
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

        # Export all data
        export_df = self.original_df.copy()
        if 'd' in export_df.columns:
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
        if self.table_df is None:
            self.reject()
            return None

        result = self.table_df.copy(deep=True)
        self.data_manager.df_raw = result

        # Refresh all plot columns
        for user_col in self.data_manager.plot_columns.keys():
            self.data_manager.plot_columns[user_col].refresh_view()

        # Refresh chart and save
        self.event_bus.emit('update_legend')
        self.event_bus.emit('refresh_chart')

        # Will change the chart data hash, thus triggering autosave or save-ask
        last_modified = int(time.time())
        self.event_bus.emit("update_chart_data", ['data_modified', last_modified])

        self.accept()

        return result

    def create_numeric_delegate(self):

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

        self.username_prefix = "User: "
        self.selected_chart_id = None
        self.selected_file_path = None

        # Get available locations
        self.location_names = self._get_available_locations()
        self.current_location = self._get_initial_location()

        # UI state
        self.location_grids = {}
        self.location_buttons = []
        self.plus_button = None
        self.location_layout = None  # Store reference to the button layout

        # Setup UI and load data
        self.setWindowTitle("Chart Browser")
        self.setMinimumSize(800, 600)
        self.setup_ui()

        # Load charts for all locations
        self.load_charts()

    def _get_available_locations(self):
        """Get list of available database locations"""
        db_locations = self.data_manager.user_preferences.get('db_location', {})
        # Keys are directory names (or 'local'/'cloud'), values are full paths
        return list(db_locations.keys())

    def _get_initial_location(self):
        """Determine initial location to display"""
        current_pref = self.event_bus.emit("get_user_preference", ['last_open_tab', 'local'])
        if current_pref not in self.location_names:
            return 'local'
        return current_pref

    def setup_ui(self):
        """Set up the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        self._create_top_bar(main_layout)
        self._create_content_area(main_layout)
        self._create_bottom_bar(main_layout)

        self.set_active_location(self.current_location)

    def _create_top_bar(self, main_layout):
        """Create the top bar with username and search"""
        top_layout = QHBoxLayout()
        top_layout.setSpacing(40)

        # Username section - anchored to left
        self._create_username_section(top_layout)

        # Search section
        self._create_search_section(top_layout)

        main_layout.addLayout(top_layout)

    def _create_username_section(self, parent_layout):
        """Create username display and editing controls"""
        username_layout = QHBoxLayout()
        username_layout.setSpacing(6)

        current_username = self.event_bus.emit("get_user_preference", ['user_name', ''])

        self.username_field = QLineEdit(f"{self.username_prefix}{current_username}")
        self.username_field.setReadOnly(True)
        self.username_field.setToolTip("Double click to edit")

        self._apply_username_styles()
        self._setup_username_events()

        # Calculate width based on username length plus two extra spaces AFTER applying styles
        font_metrics = self.username_field.fontMetrics()
        text_width = font_metrics.horizontalAdvance(f"{self.username_prefix}{current_username}  ")  # Two extra spaces
        # Account for the padding in the stylesheet (4px + 8px = 12px on each side = 24px total)
        total_width = text_width + 24
        self.username_field.setFixedWidth(total_width)

        username_layout.addWidget(self.username_field)
        parent_layout.addLayout(username_layout)

    def _apply_username_styles(self):
        """Apply styles to username field"""
        self.username_field.setStyleSheet("""
            QLineEdit[readOnly="true"] {
                padding: 4px 8px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                color: #333;
            }
            QLineEdit[readOnly="false"] {
                padding: 4px 8px;
                background-color: white;
                border: 2px solid #4080c0;
                border-radius: 4px;
                color: #000;
            }
        """)

    def _setup_username_events(self):
        """Setup username field event handlers"""

        def handle_double_click(event):
            self._start_username_edit(event)

        self.username_field.mouseDoubleClickEvent = handle_double_click
        self.username_field.editingFinished.connect(self._finish_username_edit)
        self.username_field.returnPressed.connect(self._finish_username_edit)

    def _create_search_section(self, parent_layout):
        """Create search input section"""
        search_layout = QHBoxLayout()
        search_layout.setSpacing(6)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name or credit lines (use ampersand for AND and comma for OR)")
        self.search_input.textChanged.connect(self.filter_charts)

        search_layout.addWidget(self.search_input)
        parent_layout.addLayout(search_layout)

    def _create_content_area(self, main_layout):
        """Create the main content area with stacked widgets"""
        self.stacked_widget = QStackedWidget()

        for location in self.location_names:
            if self._validate_location_path(location):
                grid = self._create_charts_grid()
                self.location_grids[location] = grid

                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(grid)
            else:
                container = self._create_add_folder_widget(location)

            self.stacked_widget.addWidget(container)

        main_layout.addWidget(self.stacked_widget)

    def _create_charts_grid(self):
        """Create a list widget for displaying chart thumbnails"""
        grid = QListWidget()
        grid.setViewMode(QListWidget.ViewMode.IconMode)
        grid.setIconSize(QSize(120, 100))
        grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        grid.setMovement(QListWidget.Movement.Static)
        grid.setGridSize(QSize(160, 160))
        grid.setSpacing(6)
        grid.setWordWrap(True)
        grid.setTextElideMode(Qt.TextElideMode.ElideMiddle)

        self._apply_grid_styles(grid)
        self._setup_grid_events(grid)

        return grid

    def _create_add_folder_widget(self, location):
        """Create widget for adding folder path when location path is invalid"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        add_folder_btn = QPushButton("Add Folder")
        add_folder_btn.setMinimumSize(200, 80)
        add_folder_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                background-color: #e0e0e0;
                border: 2px dashed #999;
                border-radius: 8px;
                color: #666;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
                border-color: #777;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        add_folder_btn.clicked.connect(lambda: self._select_folder_for_location(location))

        layout.addWidget(add_folder_btn)
        return container

    def _apply_grid_styles(self, grid):
        """Apply styles to chart grid"""
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

    def _setup_grid_events(self, grid):
        """Setup event handlers for chart grid"""
        grid.itemDoubleClicked.connect(self.chart_double_clicked)
        grid.itemSelectionChanged.connect(self.on_selection_changed)
        grid.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        grid.customContextMenuRequested.connect(self.show_chart_context_menu)

    def _create_bottom_bar(self, main_layout):
        """Create the bottom bar with location buttons and action buttons"""
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        self._create_location_buttons(bottom_layout)
        bottom_layout.addStretch(1)
        self._create_action_buttons(bottom_layout)

        main_layout.addLayout(bottom_layout)

    def _create_location_buttons(self, bottom_layout):
        """Create location selector buttons"""
        self.location_layout = QHBoxLayout()  # Store reference
        self.location_layout.setSpacing(0)

        for location in self.location_names:
            if location != 'cloud':  # Hidden for now
                button = self._create_location_button(location)
                self.location_layout.addWidget(button)
                self.location_buttons.append(button)

        # Add plus button for new locations - smaller and round
        # Count non-default locations (excluding 'local' and potentially 'cloud')
        non_default_locations = [loc for loc in self.location_names if loc not in ['local', 'cloud']]

        if len(non_default_locations) < 3:
            self.plus_button = QPushButton()
            self.plus_button.setCheckable(False)
            self.plus_button.setToolTip("Add new location")
            self.plus_button.setIcon(QIcon(':/images/plus-solid.svg'))
            self.plus_button.clicked.connect(self._add_new_location)
            self.plus_button.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ccc !important;
                    border-radius: 14px !important;
                    margin-left: 10px !important;
                    padding: 0px !important;
                    min-width: 28px !important;
                    min-height: 28px !important;
                    max-width: 28px !important; 
                    max-height: 28px !important;
                    background-color: #f8f8f8 !important;
                }
                QPushButton:hover {
                    background-color: #e0e0e0 !important;
                }
                QPushButton:pressed {
                    background-color: #d8d8d8 !important;
                }
            """)
            self.location_layout.addWidget(self.plus_button)

        bottom_layout.addLayout(self.location_layout)
        spacer = QSpacerItem(20, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        bottom_layout.addSpacerItem(spacer)

    def _create_location_button(self, location):
        """Create a single location button"""
        button = QPushButton(location.capitalize())
        button.setCheckable(True)
        button.setProperty("location", location)
        button.clicked.connect(self.on_location_button_clicked)

        # Add context menu and tooltip for non-local locations
        if location != 'local' and location != 'cloud':
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(
                lambda pos, loc=location: self._show_location_context_menu(pos, loc, button)
            )
            button.setToolTip("Right click for options.")

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
            }
            QPushButton:hover:!checked {
                background-color: #e8e8e8;
            }
        """)

        return button

    def _create_action_buttons(self, bottom_layout):
        """Create action buttons"""
        self.browse_button = QPushButton("Import")
        self.browse_button.clicked.connect(self.browse_for_json)
        bottom_layout.addWidget(self.browse_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        bottom_layout.addWidget(self.cancel_button)

        self.open_button = QPushButton("Open")
        self.open_button.clicked.connect(self.open_selected_chart)
        self.open_button.setEnabled(False)  # Initially disabled
        self.open_button.setStyleSheet("""
            QPushButton:disabled {
                color: #888888;
            }
        """)
        bottom_layout.addWidget(self.open_button)

    def _validate_location_path(self, location):
        """Check if location has a valid path"""
        if location == 'local':
            return True
        if location == 'cloud':
            return True  # Cloud is handled separately

        db_locations = self.data_manager.user_preferences.get('db_location', {})
        path = db_locations.get(location, '')

        if not path or path.lower() == 'none':
            return False

        return Path(path).exists()

    def _show_location_context_menu(self, position, location, button):
        """Show context menu for location buttons"""
        menu = QMenu(self)

        change_path_action = QAction("Change folder", self)
        change_path_action.triggered.connect(lambda: self._select_folder_for_location(location))
        menu.addAction(change_path_action)

        if location not in ['local', 'cloud']:  # Don't allow removal of default locations
            menu.addSeparator()
            remove_action = QAction("Remove", self)
            remove_action.triggered.connect(lambda: self._remove_location(location))
            menu.addAction(remove_action)

        menu.exec(button.mapToGlobal(position))

    def _select_folder_for_location(self, location):
        """Select folder for a specific location"""
        current_path = ""
        if location != 'local':
            db_locations = self.data_manager.user_preferences.get('db_location', {})
            current_path = db_locations.get(location, "")

        if not current_path or not Path(current_path).exists():
            current_path = self.event_bus.emit("get_user_preference", ['home_folder', str(Path.home())])

        folder = QFileDialog.getExistingDirectory(
            self, f"Select Folder for {location.capitalize()}", current_path
        )

        if folder:
            self._update_location_path(location, folder)

    def _update_location_path(self, location, path):
        """Update the path for a location"""
        db_locations = self.data_manager.user_preferences.get('db_location', {})

        # If changing path for existing location, we need to update the key
        if location != 'local' and location != 'cloud':
            # Remove old entry
            if location in db_locations:
                del db_locations[location]

            # Add new entry with directory name as key
            dir_name = Path(path).name

            # Handle duplicate directory names
            if dir_name in db_locations and dir_name not in ['local', 'cloud']:
                counter = 1
                original_name = dir_name
                while f"{original_name}_{counter}" in db_locations:
                    counter += 1
                dir_name = f"{original_name}_{counter}"

            db_locations[dir_name] = path

            # Update UI to reflect new name
            for i, button in enumerate(self.location_buttons):
                if button.property("location") == location:
                    button.setText(dir_name.capitalize())
                    button.setProperty("location", dir_name)
                    # Update context menu connection
                    try:
                        button.customContextMenuRequested.disconnect()
                    except:
                        pass
                    button.customContextMenuRequested.connect(
                        lambda pos, loc=dir_name: self._show_location_context_menu(pos, loc, button)
                    )
                    break

            # Update location_names
            index = self.location_names.index(location)
            self.location_names[index] = dir_name

            # Update current location if needed
            if self.current_location == location:
                self.current_location = dir_name
        else:
            # For local/cloud, just update the path
            db_locations[location] = path

        self.event_bus.emit("update_user_preference", ['db_location', db_locations])
        self.data_manager.save_user_preferences()

        # Refresh the view
        self._refresh_location_view(dir_name if location not in ['local', 'cloud'] else location)

    def _add_new_location(self):
        """Add a new location by selecting folder"""
        # Check if we already have 3 non-default locations
        non_default_locations = [loc for loc in self.location_names if loc not in ['local', 'cloud']]
        if len(non_default_locations) >= 3:
            QMessageBox.information(self, "Limit Reached", "Maximum of 3 additional locations allowed.")
            return

        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder",
            self.event_bus.emit("get_user_preference", ['home_folder', str(Path.home())])
        )

        if folder:
            db_locations = self.data_manager.user_preferences.get('db_location', {})
            dir_name = Path(folder).name

            # Handle duplicate directory names
            if dir_name in db_locations:
                counter = 1
                original_name = dir_name
                while f"{original_name}_{counter}" in db_locations:
                    counter += 1
                dir_name = f"{original_name}_{counter}"

            db_locations[dir_name] = folder
            self.event_bus.emit("update_user_preference", ['db_location', db_locations])
            self.data_manager.save_user_preferences()

            # Add to location_names
            self.location_names.append(dir_name)

            # Create button
            button = self._create_location_button(dir_name)

            # Insert before plus button
            if self.plus_button:
                plus_index = self.location_layout.indexOf(self.plus_button)
                self.location_layout.insertWidget(plus_index, button)
            else:
                self.location_layout.addWidget(button)

            self.location_buttons.append(button)

            # Hide plus button if we've reached the limit
            if len(non_default_locations) + 1 >= 3 and self.plus_button:
                self.plus_button.hide()

            # Create stacked widget
            grid = self._create_charts_grid()
            self.location_grids[dir_name] = grid

            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(grid)

            self.stacked_widget.addWidget(container)

            # Load charts for the new location
            self._load_charts_for_location(dir_name)

            # Switch to the new location
            self.set_active_location(dir_name)

    def _remove_location(self, location):
        """Remove a location after confirmation"""
        data = {
            'title': "Remove Location",
            'message': f"Remove location '{location}'?\nAll data in this location will be deleted.",
            'options': ['Yes', 'No']
        }
        result = self.event_bus.emit('trigger_user_prompt', data)

        if result == 0:  # "Yes"
            db_locations = self.data_manager.user_preferences.get('db_location', {})
            if location in db_locations:
                # Delete files before removing from preferences
                location_path = db_locations[location]
                if location_path and Path(location_path).exists():
                    try:
                        # Delete all JSON files in the location
                        for json_file in Path(location_path).glob("*.json"):
                            json_file.unlink()
                    except Exception as e:
                        print(f"Error deleting files in {location_path}: {e}")

                del db_locations[location]

                self.event_bus.emit("update_user_preference", ['db_location', db_locations])
                self.data_manager.save_user_preferences()

                # Remove from location_names
                if location in self.location_names:
                    index = self.location_names.index(location)
                    self.location_names.remove(location)

                    # Remove button
                    for i, button in enumerate(self.location_buttons):
                        if button.property("location") == location:
                            button.hide()
                            button.setParent(None)
                            button.deleteLater()
                            self.location_buttons.pop(i)
                            break

                    # Remove stacked widget
                    if index < self.stacked_widget.count():
                        widget = self.stacked_widget.widget(index)
                        self.stacked_widget.removeWidget(widget)
                        widget.deleteLater()

                    # Remove from grids
                    if location in self.location_grids:
                        del self.location_grids[location]

                # Show plus button if we're now under the limit
                non_default_locations = [loc for loc in self.location_names if loc not in ['local', 'cloud']]
                if len(non_default_locations) < 3 and self.plus_button:
                    self.plus_button.show()

                # Switch to local if current location was removed
                if self.current_location == location:
                    self.set_active_location('local')

    def _refresh_location_view(self, location):
        """Refresh view for a specific location"""
        if location in self.location_names:
            index = self.location_names.index(location)

            # Create new widget based on path validity
            if self._validate_location_path(location):
                grid = self._create_charts_grid()
                self.location_grids[location] = grid

                container = QWidget()
                layout = QVBoxLayout(container)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(grid)

                # Load charts for this location
                self._load_charts_for_location(location)
            else:
                container = self._create_add_folder_widget(location)
                if location in self.location_grids:
                    del self.location_grids[location]

            # Replace the widget in the stack
            old_widget = self.stacked_widget.widget(index)
            self.stacked_widget.removeWidget(old_widget)
            old_widget.deleteLater()
            self.stacked_widget.insertWidget(index, container)

            # Update current view if this is the active location
            if self.current_location == location:
                self.stacked_widget.setCurrentIndex(index)

    def _start_username_edit(self, event):
        """Start editing the username field on double-click"""
        # Extract just the username part for editing
        current_text = self.username_field.text()
        if current_text.startswith(self.username_prefix):
            username_only = current_text[len(self.username_prefix):]
            self.username_field.setText(username_only)

        self.username_field.setReadOnly(False)
        self.username_field.setProperty("readOnly", False)
        self.username_field.style().polish(self.username_field)
        self.username_field.selectAll()
        self.username_field.setFocus()

    def _finish_username_edit(self):
        """Finish editing the username field and apply changes"""
        full_text = self.username_field.text().strip()
        # Extract username part after prefix
        if full_text.startswith(self.username_prefix):
            new_username = full_text[len(self.username_prefix):]
        else:
            new_username = full_text

        current_username = self.event_bus.emit("get_user_preference", ['user_name', ''])

        # Set back to read-only and update style
        self.username_field.setReadOnly(True)
        self.username_field.setProperty("readOnly", True)
        self.username_field.style().polish(self.username_field)

        # Validate and update username
        if new_username and new_username != current_username and len(new_username) <= 50:
            success = self.event_bus.emit('update_username_ownership', {
                'old_username': current_username,
                'new_username': new_username
            })

            if success:
                # Update field width based on new username with prefix
                font_metrics = self.username_field.fontMetrics()
                text_width = font_metrics.horizontalAdvance(f"{self.username_prefix}{new_username}  ")
                min_width = max(text_width + 24, 60)
                self.username_field.setFixedWidth(min_width)

                self.load_charts()  # Refresh charts to reflect ownership changes
            else:
                self.username_field.setText(f"{self.username_prefix}{current_username}")  # Reset on failure
        else:
            self.username_field.setText(f"{self.username_prefix}{current_username}")

    def set_active_location(self, location):
        """Set the active location and update UI"""
        if location not in self.location_names:
            location = self.location_names[0] if self.location_names else 'local'

        self.current_location = location
        index = self.location_names.index(location)
        self.stacked_widget.setCurrentIndex(index)

        # Update button states
        for button in self.location_buttons:
            btn_loc = button.property("location")
            button.setChecked(btn_loc == location)

        # Save preference
        self.event_bus.emit("update_user_preference", ['last_open_tab', location])
        self.on_selection_changed()

    def on_location_button_clicked(self):
        """Handle location button clicks"""
        button = self.sender()
        location = button.property("location")
        self.set_active_location(location)

    # Chart Loading and Display
    def load_charts(self):
        """Load charts for all locations"""
        # Clear all grids first
        for grid in self.location_grids.values():
            grid.clear()

        # Load charts for each location that has a valid path
        for location in self.location_names:
            if self._validate_location_path(location):
                self._load_charts_for_location(location)

    def _load_charts_for_location(self, location):
        """Load charts for a specific location"""
        if not self._validate_location_path(location):
            return

        try:
            grid = self.location_grids.get(location)
            if not grid:
                return

            chart_ids = self.event_bus.emit('get_chart_ids_for_location', location)

            for chart_id in chart_ids:
                try:
                    self._create_chart_item(grid, chart_id, location)
                except Exception as e:
                    print(f"Error creating chart item for {chart_id}: {e}")

        except Exception as e:
            print(f"Error loading charts for location {location}: {e}")

    def _create_chart_item(self, grid, chart_id, location):
        """Create a chart item for the grid"""
        # Get chart metadata
        chart_data = self.event_bus.emit('get_chart_metadata', chart_id)
        if not chart_data:
            return

        metadata = chart_data['metadata']
        thumbnail_data = chart_data['thumbnail']

        # Create list item
        item = QListWidgetItem()

        # Set item text and data
        self._configure_chart_item_text(item, chart_id, metadata)
        self._configure_chart_item_icon(item, chart_id, location, thumbnail_data)

        # Set tooltip based on ownership
        permissions = self.event_bus.emit('get_chart_permissions', chart_id)
        is_owner = permissions.get('is_owner', False)

        if is_owner:
            item.setToolTip("Double left click to open.\nRight click for options.")
        elif location != 'local':
            # Get owner information from database for non-owned charts
            owner_result = self.data_manager.sqlite_manager._execute_with_retry(
                f"SELECT owner FROM {self.data_manager.sqlite_manager.TABLE_CHART_METADATA} WHERE chart_id = ?",
                (chart_id,),
                fetch='one'
            )

            if owner_result and owner_result[0]:
                owner_name = owner_result[0]
                item.setToolTip(f"{owner_name}'s chart")

        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        grid.addItem(item)

    def _configure_chart_item_text(self, item, chart_id, metadata):
        """Configure chart item text and user data"""
        # Extract chart name (remove timestamp if present)
        last_underscore = chart_id.rfind('_')
        chart_name = chart_id[:last_underscore] if last_underscore != -1 else chart_id
        chart_type = metadata.get('type', 'Unknown')

        item.setText(f"{chart_name}\n{chart_type}")
        item.setData(Qt.ItemDataRole.UserRole, chart_id)

        # Store credit lines for search functionality
        credit_lines = metadata.get('credit', [])
        if credit_lines and isinstance(credit_lines, (list, tuple)):
            credit_text = " ".join(str(line) for line in credit_lines)
            item.setData(Qt.ItemDataRole.UserRole + 1, credit_text)

    def _configure_chart_item_icon(self, item, chart_id, location, thumbnail_data):
        """Configure chart item icon with permission indicators"""
        if not thumbnail_data:
            item.setIcon(QIcon.fromTheme("image-missing"))
            return

        try:
            original_pixmap = QPixmap()
            if not original_pixmap.loadFromData(thumbnail_data) or original_pixmap.isNull():
                item.setIcon(QIcon.fromTheme("image-missing"))
                return

            # Add permission indicator for shared locations
            if location != 'local':
                final_pixmap = self._add_permission_indicator(original_pixmap, chart_id)
            else:
                final_pixmap = self._add_frame_to_pixmap(original_pixmap)

            item.setIcon(QIcon(final_pixmap))

        except Exception as e:
            print(f"Error processing thumbnail for chart {chart_id}: {e}")
            item.setIcon(QIcon.fromTheme("image-missing"))

    def _add_frame_to_pixmap(self, pixmap):
        """Add a black frame around a pixmap"""
        if pixmap.isNull():
            return pixmap

        frame_width = 2
        width = pixmap.width() + (frame_width * 2)
        height = pixmap.height() + (frame_width * 2)

        framed_pixmap = QPixmap(width, height)
        framed_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(framed_pixmap)
        painter.drawPixmap(frame_width, frame_width, pixmap)
        painter.setPen(QPen(QColor(0, 0, 0), frame_width))
        painter.drawRect(frame_width // 2, frame_width // 2, width - frame_width, height - frame_width)
        painter.end()

        return framed_pixmap

    def _add_permission_indicator(self, pixmap, chart_id):
        """Add permission indicator to pixmap"""
        if pixmap.isNull():
            return pixmap

        frame_width = 2
        width = pixmap.width() + (frame_width * 2)
        height = pixmap.height() + (frame_width * 2)

        framed_pixmap = QPixmap(width, height)
        framed_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(framed_pixmap)

        # Draw the original pixmap
        painter.drawPixmap(frame_width, frame_width, pixmap)

        # Draw frame
        painter.setPen(QPen(QColor(0, 0, 0), frame_width))
        painter.drawRect(frame_width // 2, frame_width // 2, width - frame_width, height - frame_width)

        # Get permissions and draw indicator
        permissions = self.event_bus.emit('get_chart_permissions', chart_id)
        is_owner = permissions.get('is_owner', False)
        has_write_access = permissions.get('has_write_access', False)

        # Draw permission indicator
        self._draw_permission_icon(painter, width, height, is_owner, has_write_access)

        painter.end()
        return framed_pixmap

    def _draw_permission_icon(self, painter, width, height, is_owner, has_write_access):
        """Draw permission icon on the pixmap"""
        icon_size = int(width * 0.2)
        icon_x = width - icon_size - 4
        icon_y = 4

        # Choose icon and background color based on permissions
        if is_owner:
            icon_path = ':/images/crown-solid.svg'
            background_color = QColor(255, 230, 150, 180)
        elif has_write_access:
            icon_path = ':/images/pen-to-square-regular.svg'
            background_color = QColor(150, 220, 150, 180)
        else:
            icon_path = ':/images/eye-regular.svg'
            background_color = QColor(150, 180, 255, 180)

        # Draw background circle
        painter.setBrush(background_color)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(icon_x, icon_y, icon_size, icon_size)

        # Draw icon
        icon_pixmap = QPixmap(icon_path)
        if not icon_pixmap.isNull():
            icon_inner_size = int(icon_size * 0.7)
            icon_offset = (icon_size - icon_inner_size) // 2

            scaled_icon = icon_pixmap.scaled(
                icon_inner_size,
                icon_inner_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            icon_draw_x = icon_x + icon_offset + (icon_inner_size - scaled_icon.width()) // 2
            icon_draw_y = icon_y + icon_offset + (icon_inner_size - scaled_icon.height()) // 2
            painter.drawPixmap(icon_draw_x, icon_draw_y, scaled_icon)

    # Chart Operations
    def show_chart_context_menu(self, position):
        """Show context menu when right-clicking on a chart"""
        if self.current_location not in self.location_grids:
            return

        grid = self.location_grids[self.current_location]
        item = grid.itemAt(position)

        if not item:
            return

        chart_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)

        # Get chart sync status and permissions
        is_synced = self.event_bus.emit('is_chart_synced', chart_id)
        permissions = self.event_bus.emit('get_chart_permissions', chart_id)
        is_owner = permissions.get('is_owner', False)

        # Add delete option for owned charts
        if is_owner:
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_chart(chart_id))
            menu.addAction(delete_action)

        if not is_synced:
            self._add_share_menu_items(menu, chart_id)
        else:
            self._add_sync_management_items(menu, chart_id, is_owner)

        if menu.actions():
            menu.exec(grid.mapToGlobal(position))

    def _add_share_menu_items(self, menu, chart_id):
        """Add share options to context menu"""
        # Get permissions to check if user owns the chart
        permissions = self.event_bus.emit('get_chart_permissions', chart_id)
        is_owner = permissions.get('is_owner', False)

        if is_owner:
            # Add export option for owned charts even if not synced
            export_action = QAction("Export", self)
            export_action.triggered.connect(lambda: self.export_chart(chart_id))
            menu.addAction(export_action)
            menu.addSeparator()

        db_locations = self.data_manager.user_preferences.get('db_location', {})
        sync_locations = [loc for loc in db_locations.keys() if loc != 'local']

        if sync_locations:
            for location in sync_locations:
                share_action = QAction(f"Share to {location.capitalize()}", self)
                share_action.triggered.connect(
                    lambda checked, loc=location: self._share_chart_to_location(chart_id, loc)
                )
                menu.addAction(share_action)

    def export_chart(self, chart_id):
        """Export a chart to JSON file"""
        try:
            # Extract display name for the default filename
            underscore = chart_id.rfind('_')
            display_chart_name = chart_id[:underscore] if underscore != -1 else chart_id

            # Get export folder preference
            export_folder = self.event_bus.emit("get_user_preference", ['export_folder', ''])
            if not export_folder:
                export_folder = self.event_bus.emit("get_user_preference", ['home_folder', str(Path.home())])

            # Open file dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export chart",
                str(Path(export_folder) / f"{display_chart_name}.json"),
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_path:
                return

            # Ensure .json extension
            if not file_path.endswith('.json'):
                file_path += '.json'

            # Save export directory preference
            export_dir = str(Path(file_path).parent)
            self.event_bus.emit("update_user_preference", ['export_folder', export_dir])

            # Export the chart through the event bus
            success = self.event_bus.emit('export_json_from_database', {
                'chart_id': chart_id,
                'file_path': file_path
            })

            if success:
                QMessageBox.information(self, "Export Successful", f"Chart exported to {file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Failed to export chart. Please try again.")

        except Exception as e:
            print(f"Error exporting chart {chart_id}: {e}")
            QMessageBox.warning(self, "Export Error", f"An error occurred while exporting: {str(e)}")

    def _add_sync_management_items(self, menu, chart_id, is_owner):
        """Add sync management options to context menu"""
        if is_owner:
            # Add export option
            export_action = QAction("Export Chart", self)
            export_action.triggered.connect(lambda: self.export_chart(chart_id))
            menu.addAction(export_action)

            # Add separator before other options
            menu.addSeparator()

            # Add unsync option
            unsync_action = QAction("Stop sharing", self)
            unsync_action.triggered.connect(lambda: self._unsync_chart(chart_id))
            menu.addAction(unsync_action)

            # Add toggle accepting changes option
            self._add_accepting_changes_toggle(menu, chart_id)

    def _add_accepting_changes_toggle(self, menu, chart_id):
        """Add accepting changes toggle to context menu"""
        try:
            permissions = self.event_bus.emit('get_chart_permissions', chart_id)
            is_owner = permissions.get('is_owner', False)
            accepting_changes = permissions.get('accepting_changes', False)

            if is_owner:
                if accepting_changes:
                    action_text = "Disable remote edits"
                else:
                    action_text = "Allow remote edits"

                toggle_action = QAction(action_text, self)
                toggle_action.triggered.connect(lambda: self._toggle_accepting_changes(chart_id))
                menu.addAction(toggle_action)

        except Exception as e:
            print(f"Error adding accepting_changes toggle for chart {chart_id}: {e}")

    def _share_chart_to_location(self, chart_id, location):
        """Share a chart to the specified location"""
        success = self.event_bus.emit('share_chart_to_location', {
            'chart_id': chart_id,
            'location': location
        })

        if success:
            self.load_charts()

    def _unsync_chart(self, chart_id):
        """Remove chart from sync"""
        # Extract display name for confirmation
        underscore = chart_id.rfind('_')
        display_chart_name = chart_id[:underscore] if underscore != -1 else chart_id

        data = {
            'title': "Remove from Sync",
            'message': f"Remove '{display_chart_name}' from sync? This will stop sharing it to remote locations.",
            'options': ['Yes', 'No']
        }
        result = self.event_bus.emit('trigger_user_prompt', data)

        if result == 0:  # "Yes"
            new_chart_id = self.event_bus.emit('unsync_chart', chart_id)
            if new_chart_id:
                self.load_charts()
            else:
                print(f"Failed to unsync chart {chart_id}")

    def _toggle_accepting_changes(self, chart_id):
        """Toggle accepting_changes for a chart"""
        success = self.event_bus.emit('toggle_accepting_changes', chart_id)
        if success:
            # Refresh current location to update icons - but clear first to prevent duplication
            grid = self.location_grids[self.current_location]
            grid.clear()
            self._load_charts_for_location(self.current_location)

    def delete_chart(self, chart_id):
        """Delete the specified chart"""

        underscore_idx = chart_id.rfind('_')
        chart_name = chart_id[:underscore_idx]
        data = {
            'title': "Delete Chart",
            'message': f"Delete {chart_name}?",
            'options': ['Yes', 'No']
        }
        result = self.event_bus.emit('trigger_user_prompt', data)

        if result == 0:
            success = self.event_bus.emit('delete_chart', chart_id)
            if success:
                self.load_charts()

    # Search and Filter
    def filter_charts(self):
        """Filter charts with & for AND and , for OR"""
        search_text = self.search_input.text().strip()

        if self.current_location in self.location_grids:
            grid = self.location_grids[self.current_location]

            for i in range(grid.count()):
                item = grid.item(i)
                if item:
                    item_text = item.text().lower()
                    credit_text = (item.data(Qt.ItemDataRole.UserRole + 1) or "").lower()
                    combined_text = f"{item_text} {credit_text}"

                    if not search_text:
                        item.setHidden(False)
                    elif ',' in search_text:
                        # Split by comma - any term can match (OR)
                        or_terms = [term.strip() for term in search_text.lower().split(',') if term.strip()]
                        should_hide = not any(term in combined_text for term in or_terms)
                        item.setHidden(should_hide)
                    elif '&' in search_text:
                        # Split by ampersand - all terms must match (AND)
                        and_terms = [term.strip() for term in search_text.lower().split('&') if term.strip()]
                        should_hide = not all(term in combined_text for term in and_terms)
                        item.setHidden(should_hide)
                    else:
                        # No operators, treat as single search term
                        should_hide = search_text.lower() not in combined_text
                        item.setHidden(should_hide)

    def on_selection_changed(self):
        """Handle selection changes"""
        # Enable/disable Open button based on selection
        has_selection = False
        if self.current_location in self.location_grids:
            grid = self.location_grids[self.current_location]
            has_selection = len(grid.selectedItems()) > 0

        self.open_button.setEnabled(has_selection)

    def open_selected_chart(self):
        """Open the currently selected chart"""
        if self.current_location not in self.location_grids:
            return

        grid = self.location_grids[self.current_location]
        selected_items = grid.selectedItems()

        if selected_items:
            item = selected_items[0]
            self.chart_double_clicked(item)

    # File Operations
    def chart_double_clicked(self, item):
        """Handle double-click on a chart item"""
        self.selected_chart_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def browse_for_json(self):
        """Open file dialog to browse for JSON file"""
        home_folder = self.event_bus.emit("get_user_preference", ['home_folder', str(Path.home())])

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select chart file',
            home_folder,
            'JSON files (*.json);;All files (*.*)'
        )

        if file_path:
            chart_id = Path(file_path).stem

            # Import to database without opening
            success = self.event_bus.emit('json_import_to_database', {
                'json_file_path': file_path,
                'chart_id': chart_id
            })

            if success:
                # Refresh charts to show the newly imported chart as thumbnail
                self.load_charts()
                # Don't set selected_chart_id or call accept() - just show as thumbnail
            else:
                QMessageBox.warning(self, "Import Failed", "Failed to import the selected chart file.")

    def get_selected_chart_path(self):
        """Return the full path or ID of the selected chart"""
        if self.selected_file_path:
            return self.selected_file_path
        elif self.selected_chart_id:
            return self.selected_chart_id
        return None

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event) if event else None

