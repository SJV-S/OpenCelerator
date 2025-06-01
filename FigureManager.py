from app_imports import *
from DataManager import DataManager, DataPointColumn  # Direct import to avoid circular dependency
from EventStateManager import EventBus  # Direct import to avoid circular dependency
import scc  # Direct import to avoid circular dependency


class FigureManager(QWidget):
    def __init__(self, parent=None):
        super(FigureManager, self).__init__(parent)
        self.main_app = parent  # Assuming parent is an instance of ChartApp
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Event subscriptions
        self.event_bus.subscribe('new_chart', self.new_chart, has_data=True)
        self.event_bus.subscribe('get_data_point_column', self.get_data_point_column, has_data=True)
        self.event_bus.subscribe('refresh_chart', self.refresh)
        self.event_bus.subscribe('get_thumbnail', self.get_thumbnail, has_data=True)

        # Managers
        self.phase_manager = PhaseManager(self)
        self.aim_manager = AimManager(self)
        self.trend_manager = TrendManager(self)
        self.view_manager = ViewManager(self)
        self.manual_manager = StyleManager(self)
        self.drag_fan_manager = DraggableFanManager(self)
        self.plot_draw_manager = PlotDrawManager(self)
        self.drag_manager = DragManager(self)

        self.chart_objects = {'phase_obj': [],
                              'aim_obj': [],
                              'legend_obj': []
                              }

        # Object styles
        self.default_phase_item = self.event_bus.emit("get_user_preference", ['phase_style', {}])
        self.default_aim_item = self.event_bus.emit("get_user_preference", ['aim_style', {}])
        self.default_trend_corr_item = self.event_bus.emit("get_user_preference", ['trend_corr_style', {}])
        self.default_trend_err_item = self.event_bus.emit("get_user_preference", ['trend_err_style', {}])
        self.default_trend_misc_item = self.event_bus.emit("get_user_preference", ['trend_misc_style', {}])

        # Ensure the figure and layout are correctly initialized
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()  # Properly initialize the layout
        self.setLayout(self.layout)  # Set the layout for this widget
        self.layout.addWidget(self.canvas)  # Add the canvas to the layout

        # For eval
        self.date_tuple_pattern = re.compile(r"\('(\d{4}-\d{2}-\d{2})', '(\d{4}-\d{2}-\d{2})'\)")
        self.style_tuple_pattern = re.compile(r"\('([A-Za-z_]{1,30})', '([A-Za-z_]{1,30})'\)")

        # Data point styling control variables
        self.x_style_array = None

        # Other control variables
        self.deceleration_as_division = True
        self.credit_lines_space = True
        self.test_angle = False
        self.fig_init = False  # True after figure has been initialized on boot
        self.pick_event = False # Will block mode mouse events if the user is trying to object-click

        self.new_chart(start_date=pd.to_datetime('today').normalize())

        # Other managers for which self.ax is expected to be defined
        self.note_manager = NoteManager(self)
        self.hover_manager = Hover(self)

    def init_state(self, start_date=None):
        # Close any previously created figure
        if hasattr(self, 'figure') and self.figure:
            plt.close(self.figure)

        # Select chart type
        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        chart_width = self.event_bus.emit("get_user_preference", ['width', 10])
        chart_font_color = self.event_bus.emit("get_user_preference", ['chart_font_color', '#000000'])
        chart_grid_color = self.event_bus.emit("get_user_preference", ['chart_grid_color', '#000000'])

        self.credit_lines_space = self.event_bus.emit("get_chart_data", [['view', 'chart', 'credit'], False])

        if chart_type == 'DailyMinute':
            self.Chart = scc.DailyMinute(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'Daily':
            self.Chart = scc.Daily(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'WeeklyMinute':
            self.Chart = scc.WeeklyMinute(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'Weekly':
            self.Chart = scc.Weekly(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'MonthlyMinute':
            self.Chart = scc.MonthlyMinute(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'Monthly':
            self.Chart = scc.Monthly(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'YearlyMinute':
            self.Chart = scc.YearlyMinute(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        elif chart_type == 'Yearly':
            self.Chart = scc.Yearly(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)
        else:
            self.Chart = scc.DailyMinute(floor_grid_on=True, start_date=start_date, width=chart_width, style_color=chart_font_color, custom_grid_color=chart_grid_color)

        self.figure, self.ax = self.Chart.get_figure()
        self.x_to_date = {v: k for k, v in self.Chart.date_to_pos.items()}
        self.credit_lines_object = None

        # Super important to make pickable events working
        self.ax.set_zorder(5)  # Lifts ax to the top so that pickable objects can be reached
        self.ax.patch.set_visible(False)  # Make background transparent

        # Add celeration fan
        self.drag_fan_manager.initialize_fan()

        # Run replot
        self.replot()
        self.fig_init = True

        # Control variables
        self.temp_point = None
        self.point_type = True  # Dots if True, else X

    def setup_layout(self):
        # Clear existing canvas
        self.layout.removeWidget(self.canvas)
        self.canvas.setParent(None)  # Disconnect from the layout
        self.canvas.close()  # Close the canvas
        self.canvas.deleteLater()  # Schedule for deletion
        self.canvas = None

        # Create a new canvas and add it to the layout
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        fig_width, fig_height = self.figure.get_size_inches()
        dpi = self.figure.get_dpi()
        self.canvas.setFixedSize(int(fig_width * dpi), int(fig_height * dpi))

        self.canvas.draw()  # Draw the initial state of the figure

    def get_data_point_column(self, data):
        sys_col = data['sys_col']
        user_col = data['user_col']
        view_settings = data.get('view_settings', None)

        data_point_column = DataPointColumn(ax=self.ax,
                                            date_to_x=self.Chart.date_to_pos,
                                            x_to_day_count=self.Chart.x_to_day_count,
                                            sys_col=sys_col,
                                            user_col=user_col,
                                            view_settings=view_settings)
        self.data_manager.plot_columns[user_col] = data_point_column
        return data_point_column

    def replot(self):
        self.data_manager.plot_columns = {}  # Clear dict
        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        is_minute_chart = 'Minute' in chart_type
        column_map = self.event_bus.emit("get_chart_data", ['column_map', {}])
        all_view_settings = self.event_bus.emit("get_chart_data", ['view', {}])
        for sys_col, user_col in column_map.items():

            # Skip date mapping columns
            if sys_col == 'd':
                continue
            # Skip floor column for non-minute charts
            if sys_col == 'm' and not is_minute_chart:
                continue

            view_key = f'{sys_col}|{user_col}'
            view_settings = all_view_settings[view_key] if view_key in all_view_settings.keys() else None
            data = {'sys_col': sys_col, 'user_col': user_col, 'view_settings': view_settings}
            data_point_column = self.get_data_point_column(data)
            data_point_column.replot_cel_trends()
            data_point_column.plot()
            data_point_column.sync_visibility()

        # Reset graph objects
        self.chart_objects = {'phase_obj': [], 'aim_obj': [], 'legend_obj': []}
        self.replot_chart_objects()

        # Add other objects
        self.event_bus.emit('create_legend')
        self.event_bus.emit('view_update_credit_lines')

        # View sync
        if self.fig_init:
            self.event_bus.emit('refresh_view_dropdown')
            self.event_bus.emit('sync_data_checkboxes')
            self.event_bus.emit('sync_grid_checkboxes')
            self.event_bus.emit('sync_misc_checkboxes')

        self.event_bus.emit('apply_all_grid_settings')
        self.event_bus.emit('apply_all_misc_settings')

        self.event_bus.emit('refresh_chart')

    def replot_chart_objects(self):
        all_phase_lines = self.event_bus.emit("get_chart_data", ['phase', []])
        for phase in all_phase_lines:
            self.phase_replot(phase)

        all_aim_lines = self.event_bus.emit("get_chart_data", ['aim', []])
        for aim in all_aim_lines:
            self.aim_replot(aim)

    def safe_eval_tuple(self, date_tuple_str):
        # Check if the string matches either of the expected patterns
        if self.date_tuple_pattern.fullmatch(date_tuple_str) or self.style_tuple_pattern.fullmatch(date_tuple_str):
            return eval(date_tuple_str)
        else:
            raise ValueError("Invalid tuple string format")

    def x_to_row_num(self, x_min, x_max, df):
        row_min = None
        row_max = None

        # Finding row_min
        while x_min >= 0:
            if x_min in df['x'].values:
                row_min = df[df['x'] == x_min].index[0]
                break
            x_min -= 1
        if row_min is None:
            row_min = df.index.min()

        # Finding row_max
        max_x = df['x'].max()
        while x_max <= max_x:
            if x_max in df['x'].values:
                row_max = df[df['x'] == x_max].index[-1]
                break
            x_max += 1
        if row_max is None:
            row_max = df.index.max()

        return row_min, row_max

    def phase_replot(self, phase):
        phase = self.data_manager.ensure_backwards_compatibility(phase, self.data_manager.default_phase_style)
        date = self.data_manager.find_closest_date(phase['date'], self.Chart.date_to_pos)
        if date:
            x_i = self.Chart.date_to_pos[date]

            relative_pos = phase['text_position']
            ymin = self.Chart.ymin
            ymax = self.Chart.ymax
            log_ymin = np.log10(ymin)
            log_ymax = np.log10(ymax)
            y_text_pos = 10 ** (log_ymin + relative_pos * (log_ymax - log_ymin))

            phase_line = self.ax.vlines(x_i,
                                        ymax=ymax,
                                        ymin=0,
                                        color=phase['line_color'],
                                        linestyle=phase['linestyle'],
                                        linewidth=phase['linewidth'])

            # Add phase line text
            if phase['text_mode'] == 'Flag':
                va = 'bottom'
                rotation = 0
            elif phase['text_mode'] == 'Banner':
                va = 'center'
                rotation = 90

            phase_text = self.ax.text(x_i + 1,
                                      y_text_pos,
                                      phase['text'],
                                      ha="left",
                                      va=va,
                                      rotation=rotation,
                                      fontsize=phase['font_size'],
                                      color=phase['font_color']
                                      )

            # Make the phase text draggable
            self.event_bus.emit('make_draggable', data={
                'objects': phase_text,
                'save_obj': phase,
                'save_event': 'save_phase_text_pos',
                'horizontal': False,  # Only allow vertical movement
                'vertical': True,
            })

            self.chart_objects['phase_obj'].append((phase_line, phase_text))
        else:
            # Necessary to make sure phase_obj list stays in synch with list of ALL phase lines added
            self.chart_objects['phase_obj'].append(None)

    def aim_replot(self, aim):
        aim = self.data_manager.ensure_backwards_compatibility(aim, self.data_manager.default_aim_style)
        date1 = self.data_manager.find_closest_date(aim['date1'], self.Chart.date_to_pos)
        date2 = self.data_manager.find_closest_date(aim['date2'], self.Chart.date_to_pos)
        if date1 != date2 and all(key in self.Chart.date_to_pos for key in [date1, date2]):
            xmin = self.Chart.date_to_pos[date1]
            xmax = self.Chart.date_to_pos[date2]
            target = float(aim['y'])

            line_type = aim['line_type']
            if line_type == 'Slope':
                baseline = float(aim['baseline'])
                pos_x, pos_y, ha, angle, _, text_offset_x, text_offset_y = self.data_manager.get_aim_slope_text(aim['text_pos'], xmin, xmax, baseline, target,  self.Chart.x_to_day_count)

                aim_line, = self.ax.plot([xmin, xmax], [baseline, target],
                                          color=aim['line_color'],
                                          linewidth=aim['linewidth'],
                                          linestyle=aim['linestyle'])

                aim_note = self.ax.annotate(aim['text'], xy=(pos_x, pos_y), xytext=(text_offset_x, text_offset_y), textcoords='offset fontsize', ha=ha, va='bottom', rotation=angle, rotation_mode='anchor', color=aim['font_color'], fontsize=aim['font_size'])

            else:
                text_x, ha = self.aim_manager.aim_get_text_pos(xmin, xmax, text_pos=aim['text_pos'])
                aim_line = self.ax.hlines(xmin=xmin,
                                          xmax=xmax,
                                          y=target,
                                          colors=aim['line_color'],
                                          linewidth=aim['linewidth'],
                                          linestyle=aim['linestyle'])

                aim_note = self.ax.text(text_x,
                                        target * 1.2,
                                        aim['text'],
                                        color=aim['font_color'],
                                        ha=ha,
                                        fontsize=aim['font_size'])

            self.chart_objects['aim_obj'].append((aim_line, aim_note))
        else:
            # Necessary to make sure aim_obj list stays in synch with list of ALL aims lines added
            self.chart_objects['aim_obj'].append(None)

    def selective_item_removal(self, item_type, selected, corr=None):
        if item_type == 'trend':
            item_type = 'trend_corr' if corr else 'trend_err'

        # Delete the data
        items = self.data_manager.chart_data[item_type]
        if items:
            del items[selected]

        # Remove from chart
        if 'trend' in item_type:
            if corr:
                trend_obj, bounce_obj, est_obj = 'trend_corr_obj', 'trend_corr_bounce_obj', 'trend_corr_est_obj'
            else:
                trend_obj, bounce_obj, est_obj = 'trend_err_obj', 'trend_err_bounce_obj', 'trend_err_est_obj'

            if self.chart_objects[trend_obj]:
                line = self.chart_objects[trend_obj].pop(selected)
                line.remove()
                if self.chart_objects[est_obj]:
                    est = self.chart_objects[est_obj].pop(selected)
                    est.remove()
                if self.chart_objects[bounce_obj]:
                    upper, lower = self.chart_objects[bounce_obj].pop(selected)
                    upper.remove()
                    lower.remove()

        else:
            item_objects = self.chart_objects[item_type + '_obj']
            if item_objects:
                obj = item_objects[selected]
                if obj:
                    line, text = item_objects.pop(selected)
                    line.remove()
                    text.remove()

        self.event_bus.emit('refresh_chart')

    def refresh(self):
        self.canvas.draw_idle()

    def new_chart(self, start_date):
        self.init_state(start_date=start_date)
        self.setup_layout()
        # Save current start date
        self.event_bus.emit("update_chart_data", ['start_date', self.Chart.start_date])

    def safe_float_convert(self, input):
        return self.manual_manager.safe_float_convert(input)

    def phase_undo_line(self):
        self.phase_manager.phase_undo_line()

    def phase_cleanup_temp_line(self):
        self.phase_manager.phase_cleanup_temp_line()

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_manager.plot_trend_temp_first_marker(x_i)

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_manager.plot_trend_temp_second_marker(x_i)

    def trend_date1_changed(self, new_date):
        self.trend_manager.trend_date1_changed(new_date)

    def trend_date2_changed(self, new_date):
        self.trend_manager.trend_date2_changed(new_date)

    def trend_adjust_dates(self):
        result = self.trend_manager.adjust_dates()
        if result:
            date, order = result
            return date, order

    def point_adjust_dates(self):
        result = self.manual_manager.adjust_dates()
        if result:
            date, order = result
            return date, order

    def aim_from_form(self, note, baseline, target, start, deadline):
        self.aim_manager.aim_from_form(note, baseline, target, start, deadline)

    def aim_cleanup(self):
        self.aim_manager.aim_cleanup()

    def aim_undo(self):
        self.aim_manager.aim_undo()

    def settings_test_angle(self, show):
        if self.test_angle:
            self.test_angle.remove()
            self.test_angle = False
        else:
            if show:
                xmin = self.Chart.xmin
                xmax = self.Chart.xmax
                ymin = self.Chart.a
                ymax = self.Chart.ymax
                self.test_angle, = self.ax.plot([xmin, xmax], [ymin, ymax], 'r')

        self.event_bus.emit('refresh_chart')

    def back_to_default(self):
        # Go back to default on everything except the active chart type
        chart_type = self.data_manager.chart_data['type']
        self.data_manager.chart_data = copy.deepcopy(self.data_manager.chart_data_default)
        self.data_manager.default_chart_assessment()
        self.data_manager.chart_data['type'] = chart_type

        # Clear data
        self.data_manager.df_raw = pd.DataFrame()
        self.data_manager.df_plot = pd.DataFrame()
        self.data_manager.plot_columns = {}

        self.event_bus.emit('new_chart', pd.to_datetime('today').normalize())

    def fig_save_image(self, full_path, format, dpi):
        if not full_path.endswith('.' + format):
            full_path += '.' + format
        try:
            plt.savefig(full_path, format=format, dpi=dpi)
        except PermissionError:
            raise PermissionError(
                f"Permission denied when saving to {full_path}. Please check file/directory permissions.")

    def get_thumbnail(self, data):
        """
        Generate a thumbnail of the current chart figure

        Parameters:
        data (dict): Contains size parameter (width, height) in pixels

        Returns:
        bytes: PNG image data of the thumbnail
        """
        try:
            # Save to BytesIO buffer
            buffer = io.BytesIO()

            # Similar to fig_save_image but save to buffer
            bbox = self.figure.axes[0].get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
            self.figure.savefig(buffer, format='png', dpi=100, bbox_inches=bbox)

            # Return the binary data
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None


class PhaseManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = EventBus()
        self.temp_phase_line = None
        self.temp_phase_line_text = None
        self.y_text_pos = None

        # Event bus subscriptions
        self.event_bus.subscribe('phase_line_handle_click', self.phase_line_handle_click, has_data=True)
        self.event_bus.subscribe('phase_line_from_form', self.phase_line_from_form, has_data=True)
        self.event_bus.subscribe('fix_phase_text_position', self.fix_phase_text_position, has_data=True)
        self.event_bus.subscribe('save_phase_text_pos', self.save_phase_text_pos, has_data=True)

    def save_phase_text_pos(self, data):
        """Called from DragManager when phase text is moved"""
        phase_data = data['save_obj']
        drop_y = data['drop_y']

        # Calculate relative position based on chart bounds
        ymin = self.figure_manager.Chart.ymin
        ymax = self.figure_manager.Chart.ymax

        if ymin is not None and ymax is not None and ymin > 0 and ymax > 0:
            # Calculate relative position (0 to 1)
            relative_pos = (np.log10(drop_y) - np.log10(ymin)) / (np.log10(ymax) - np.log10(ymin))

            phase_data['text_position'] = relative_pos

            # Save to the chart data - find and update the corresponding phase
            phases = self.figure_manager.event_bus.emit("get_chart_data", ['phase', []])
            phase_date_str = phase_data['date'].strftime(
                self.figure_manager.data_manager.standard_date_string) if hasattr(phase_data['date'], 'strftime') else \
            phase_data['date']

            for i, phase in enumerate(phases):
                if phase['date'] == phase_date_str and phase['text'] == phase_data['text']:
                    phases[i]['text_position'] = relative_pos
                    break

            self.figure_manager.event_bus.emit("update_chart_data", ['phase', phases])

    def fix_phase_text_position(self, phase):
        # Convert old string-based text_position to relative 0-1 value
        if isinstance(phase.get('text_position'), str):
            position_map = {'Top': 0.8, 'Center': 0.5, 'Bottom': 0.2}
            phase['text_position'] = position_map.get(phase['text_position'], 0.8)
        return phase

    def phase_line_from_form(self, data):
        text = data['text']
        date = data['date']

        date = pd.to_datetime(date, format='%d-%m-%Y')
        date = self.figure_manager.data_manager.find_closest_date(date, self.figure_manager.Chart.date_to_pos)
        if date:
            if self.temp_phase_line and self.temp_phase_line_text:
                self.temp_phase_line.remove()
                self.temp_phase_line_text.remove()
                self.temp_phase_line = None
                self.temp_phase_line_text = None

            phase = copy.deepcopy(self.figure_manager.event_bus.emit("get_user_preference", ['phase_style', {}]))
            phase['text_mode'] = self.figure_manager.event_bus.emit("get_user_preference", ['phase_text_type', 'Flag'])

            # Get text position and convert to float if it's a string
            text_position = self.figure_manager.event_bus.emit("get_user_preference", ['phase_text_position', 'Top'])
            if isinstance(text_position, str):
                position_map = {'Top': 0.8, 'Center': 0.5, 'Bottom': 0.2}
                text_position = position_map.get(text_position, 0.8)
            phase['text_position'] = text_position

            phase['date'] = date
            phase['text'] = text

            # Replot the phase line and text
            self.figure_manager.phase_replot(phase)

            # Make the phase text draggable (get the last added phase text)
            if self.figure_manager.chart_objects['phase_obj']:
                phase_line, phase_text = self.figure_manager.chart_objects['phase_obj'][-1]
                if phase_text:
                    self.event_bus.emit('make_draggable', data={
                        'objects': phase_text,
                        'save_obj': phase,
                        'save_event': 'save_phase_text_pos',
                        'horizontal': False,  # Only allow vertical movement
                        'vertical': True,
                    })

            # Save phase data
            self.figure_manager.data_manager.save_plot_item(item=phase, item_type='phase')
            self.event_bus.emit('refresh_chart')

    def phase_line_handle_click(self, data):
        event = data['event']
        text = data['text']

        if event.inaxes:
            if event.inaxes is not None:  # In case user clicks outside coordinate system
                x, y = int(event.xdata), round(event.ydata, 4)

                # Handling for Weekly chart
                x = self.figure_manager.data_manager.find_closest_x(x, self.figure_manager.Chart.date_to_pos)

                if self.temp_phase_line and self.temp_phase_line_text:
                    self.temp_phase_line.remove()
                    self.temp_phase_line_text.remove()
                    self.temp_phase_line = None
                    self.temp_phase_line_text = None

                phase_text_type = self.figure_manager.event_bus.emit("get_user_preference", ['phase_text_type', 'Flag'])
                relative_pos = self.figure_manager.event_bus.emit("get_user_preference", ['phase_text_position', 0.8])
                position_map = {'Top': 0.8, 'Center': 0.5, 'Bottom': 0.2}
                relative_pos = position_map.get(relative_pos, 0.5)

                # Calculate y text position using the same method as phase_replot
                ymin = self.figure_manager.Chart.ymin
                ymax = self.figure_manager.Chart.ymax

                if ymin is None or ymax is None or ymin <= 0 or ymax <= 0:
                    self.y_text_pos = 1000  # Default fallback
                else:
                    log_ymin = np.log10(ymin)
                    log_ymax = np.log10(ymax)
                    self.y_text_pos = 10 ** (log_ymin + relative_pos * (log_ymax - log_ymin))

                # Draw temporary phase line
                self.temp_phase_line = self.figure_manager.ax.vlines(x, ymax=ymax, ymin=0, color='magenta',
                                                                     linestyle="--", linewidth=1.5)

                if phase_text_type == 'Flag':
                    bbox = {'facecolor': 'white', 'edgecolor': 'magenta', 'linestyle': '--', 'linewidth': 1.5}
                    va = 'bottom'
                    rotation = 0
                elif phase_text_type == 'Banner':
                    bbox = None
                    # For Banner mode, use relative position to determine vertical alignment
                    if relative_pos >= 0.8:
                        va = 'top'
                    elif relative_pos <= 0.2:
                        va = 'bottom'
                    else:
                        va = 'center'
                    rotation = 90

                self.temp_phase_line_text = self.figure_manager.ax.text(x + 1,
                                                                        self.y_text_pos,
                                                                        text,
                                                                        ha="left",
                                                                        va=va,
                                                                        rotation=rotation,
                                                                        bbox=bbox,
                                                                        fontsize=self.figure_manager.event_bus.emit(
                                                                            "get_user_preference", ['phase_style', {}])[
                                                                            'font_size'])

                self.event_bus.emit('refresh_chart')

                return x, y

    def phase_undo_line(self):
        if self.figure_manager.chart_objects['phase_obj']:
            phases = self.figure_manager.event_bus.emit("get_chart_data", ['phase', []])
            phases.pop()
            self.figure_manager.event_bus.emit("update_chart_data", ['phase', phases])
            line, text = self.figure_manager.chart_objects['phase_obj'].pop()
            line.remove()
            text.remove()
            self.event_bus.emit('refresh_chart')

    def phase_cleanup_temp_line(self):
        if self.temp_phase_line and self.temp_phase_line_text:
            self.temp_phase_line.remove()
            self.temp_phase_line_text.remove()
            self.temp_phase_line = None
            self.temp_phase_line_text = None
        self.event_bus.emit('refresh_chart')


class AimManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = EventBus()
        self.aim_temp_line = None
        self.aim_temp_note = None
        self.aim_first_click_x = None
        self.aim_second_click_x = None
        self.aim_first_click_y = None
        self.aim_second_click_y = None
        self.aim_target = None
        self.aim_first_click_indicator = None
        self.slope = None

        # Event bus subscriptions
        self.event_bus.subscribe('aim_click_info', self.aim_click_info, has_data=True)

    def aim_from_form(self, text, baseline, target, start, deadline):
        try:
            target = float(target)
        except (ValueError, TypeError):
            return

        date_format = '%d-%m-%Y'
        xmin_date = self.figure_manager.data_manager.find_closest_date(start, self.figure_manager.Chart.date_to_pos, date_format=date_format)
        xmax_date = self.figure_manager.data_manager.find_closest_date(deadline, self.figure_manager.Chart.date_to_pos, date_format=date_format)

        if all(key in self.figure_manager.Chart.date_to_pos for key in [xmin_date, xmax_date]):
            if self.aim_temp_line:
                self.aim_temp_line.remove()
                self.aim_temp_line = None
            if self.aim_temp_note:
                self.aim_temp_note.remove()
                self.aim_temp_note = None

            aim = copy.deepcopy(self.figure_manager.event_bus.emit("get_user_preference", ['aim_style', {}]))
            aim['date1'] = xmin_date
            aim['date2'] = xmax_date
            aim['y'] = target
            aim['text'] = text
            aim['text_pos'] = self.figure_manager.event_bus.emit("get_user_preference", ['aim_text_position', 'Middle'])
            aim['baseline'] = None if baseline == '' else baseline
            aim['line_type'] = self.figure_manager.event_bus.emit("get_user_preference", ["aim_line_type", "Flat"])

            self.figure_manager.data_manager.save_plot_item(item=aim, item_type='aim')
            self.figure_manager.aim_replot(aim)
            self.event_bus.emit('refresh_chart')

    def aim_cleanup(self):
        self.aim_first_click_x = None
        self.aim_second_click_x = None
        self.aim_first_click_y = None
        self.aim_second_click_y = None
        self.slope = None

        if self.aim_temp_line:
            self.aim_temp_line.remove()
            self.aim_temp_line = None
        if self.aim_temp_note:
            self.aim_temp_note.remove()
            self.aim_temp_note = None
        if self.aim_first_click_indicator:
            self.aim_first_click_indicator.remove()
            self.aim_first_click_indicator = None

        self.event_bus.emit('refresh_chart')

    def aim_undo(self):
        if self.figure_manager.data_manager.chart_data['aim'] and self.figure_manager.chart_objects['aim_obj']:
            aims = self.figure_manager.event_bus.emit("get_chart_data", ['aim', []])
            aims.pop()
            self.figure_manager.event_bus.emit("update_chart_data", ['aim', aims])
            line, note = self.figure_manager.chart_objects['aim_obj'].pop()
            line.remove()
            note.remove()
            self.event_bus.emit('refresh_chart')

    def aim_get_text_pos(self, xmin, xmax, text_pos=None):
        if text_pos is None:
            text_pos = self.figure_manager.event_bus.emit("get_user_preference", ['aim_text_position', 'Middle'])

        if text_pos == 'Left':
            ha = 'left'
            text_x = xmin
        elif text_pos == 'Right':
            ha = 'right'
            text_x = xmax
        else:
            ha = 'center'
            text_x = (xmin + xmax) / 2

        return text_x, ha

    def aim_temp_line_n_text(self, xmin, xmax, note):
        text_mode = self.figure_manager.event_bus.emit("get_user_preference", ['aim_line_type', 'Flat'])
        font_size = copy.deepcopy(self.figure_manager.event_bus.emit("get_user_preference", ['aim_style', {}])['font_size'])
        if text_mode == 'Flat':
            text_x, ha = self.aim_get_text_pos(xmin, xmax)
            self.aim_temp_line = self.figure_manager.ax.hlines(xmin=xmin, xmax=xmax, y=self.aim_first_click_y, colors="magenta", linewidth=1.5, linestyle="--")
            self.aim_temp_note = self.figure_manager.ax.text(text_x, self.aim_first_click_y * 1.2, note, ha=ha, fontsize=font_size, color='magenta')
        else:
            if xmax > xmin:
                self.aim_temp_line, = self.figure_manager.ax.plot([xmin, xmax], [self.aim_first_click_y, self.aim_second_click_y], color='magenta', linewidth=1.5, linestyle='--')
                text_pos = self.figure_manager.event_bus.emit("get_user_preference", ['aim_text_position', 'Middle'])
                pos_x, pos_y, ha, angle, self.slope, text_offset_x, text_offset_y = self.figure_manager.data_manager.get_aim_slope_text(text_pos,
                                                                                                          xmin,
                                                                                                          xmax,
                                                                                                          self.aim_first_click_y,
                                                                                                          self.aim_second_click_y,
                                                                                                          self.figure_manager.Chart.x_to_day_count,
                                                                                                          )
                self.aim_temp_note = self.figure_manager.ax.annotate(self.slope, xy=(pos_x, pos_y), xytext=(text_offset_x, text_offset_y), textcoords='offset fontsize', ha=ha, va='bottom', rotation=angle, rotation_mode='anchor', color='magenta', fontsize=font_size)
            else:
                self.aim_cleanup()

    def aim_click_info(self, data):
        if self.figure_manager.pick_event:
            return

        event = data['event']
        note = data['note']
        if event.xdata is not None:

            # Handling for Weekly
            x_i = self.figure_manager.data_manager.find_closest_x(int(event.xdata), self.figure_manager.Chart.date_to_pos)

            if x_i is not None:
                if self.aim_temp_line:
                    self.aim_temp_line.remove()
                    self.aim_temp_line = None
                if self.aim_temp_note:
                    self.aim_temp_note.remove()
                    self.aim_temp_note = None

                self.aim_target = round(event.ydata, 4)
                if self.aim_first_click_x is None:
                    self.aim_first_click_x = x_i
                    self.aim_first_click_y = self.figure_manager.data_manager.format_y_value(event.ydata)
                    self.aim_first_click_indicator, = self.figure_manager.ax.plot(self.aim_first_click_x, self.aim_target, marker='o', color='magenta')
                    d1 = self.figure_manager.x_to_date[self.aim_first_click_x]
                    self.event_bus.emit('refresh_chart')
                    return 'first', self.aim_first_click_y, d1

                elif self.aim_second_click_x is None:
                    self.aim_second_click_x = x_i
                    self.aim_second_click_y = self.figure_manager.data_manager.format_y_value(event.ydata)

                    self.aim_temp_line_n_text(self.aim_first_click_x, self.aim_second_click_x, note)

                    if self.aim_second_click_x:
                        d2 = self.figure_manager.x_to_date[self.aim_second_click_x]
                    else:
                        return

                    self.aim_first_click_x = None
                    self.aim_second_click_x = None

                    if self.aim_first_click_indicator:
                        self.aim_first_click_indicator.remove()
                        self.aim_first_click_indicator = None

                    self.event_bus.emit('refresh_chart')

                    return 'second', d2, self.aim_first_click_y, self.aim_second_click_y


class TrendManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = EventBus()
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_current_temp_marker = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_elements = None
        self.trend_data = None

        # Event bus subscriptions
        self.event_bus.subscribe('plot_cel_trend', self.plot_cel_trend, has_data=True)
        self.event_bus.subscribe('trend_on_click', self.trend_on_click, has_data=True)
        self.event_bus.subscribe('save_cel_label_pos', self.save_cel_label_pos, has_data=True)
        self.event_bus.subscribe('get_trend_temp_marker_status', self.get_trend_temp_marker_status)
        self.event_bus.subscribe('trend_cleanup', self.trend_cleanup)
        self.event_bus.subscribe('trend_finalize', self.trend_finalize)

    def save_cel_label_pos(self, data):
        # Called from DragManager
        trend_data = data['save_obj']
        x_i = data['drop_x']
        y_i = data['drop_y']

        est_x = self.figure_manager.data_manager.find_closest_x(x_i, self.figure_manager.Chart.date_to_pos)
        if est_x in self.figure_manager.x_to_date.keys():
            est_date = self.figure_manager.x_to_date[est_x]
            trend_data['text_date'] = est_date.strftime(self.figure_manager.data_manager.standard_date_string)
            trend_data['text_y'] = y_i

    def get_trend_temp_marker_status(self):
        return self.trend_temp_first_marker, self.trend_temp_second_marker

    def trend_on_click(self, event):
        if self.figure_manager.pick_event:
            return

        # Handling for Weekly
        if event.xdata is not None:
            x = self.figure_manager.data_manager.find_closest_x(int(event.xdata), self.figure_manager.Chart.date_to_pos)
            if x is not None:
                if self.trend_first_click_x is None:
                    self.trend_second_click_x = None
                    self.trend_first_click_x = x
                elif self.trend_second_click_x is None:
                    self.trend_first_click_x = None
                    self.trend_second_click_x = x

                if self.trend_first_click_x is not None and self.trend_second_click_x is None:
                    self.plot_trend_temp_first_marker(self.trend_first_click_x)
                elif self.trend_second_click_x is not None:
                    self.plot_trend_temp_second_marker(self.trend_second_click_x)

                self.event_bus.emit('update_trend_button_state')

    def plot_cel_trend(self, temp):
        user_col = self.event_bus.emit('get_current_trend_column')
        conditions_satisfied = (
                self.trend_temp_first_marker and
                self.trend_temp_second_marker and
                user_col != ''
        )

        if conditions_satisfied:
            col_instance = self.figure_manager.data_manager.plot_columns[user_col]
            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]
            date1 = self.figure_manager.x_to_date[x1]
            date2 = self.figure_manager.x_to_date[x2]
            fit_method = self.figure_manager.event_bus.emit("get_user_preference", ['fit_method', 'Least-squares'])
            forecast = self.figure_manager.event_bus.emit("get_user_preference", ['forward_projection', 0])
            bounce_envelope = self.figure_manager.event_bus.emit("get_user_preference", ['bounce_envelope', 'None'])

            result = col_instance.plot_cel_trend(date1, date2, fit_method, forecast, bounce_envelope, temp)
            if result:
                self.trend_elements, self.trend_data = result
                self.trend_temp_fit_on = True

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_current_temp_marker = 'first'
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        self.trend_temp_first_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.event_bus.emit('refresh_chart')

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_current_temp_marker = 'second'
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()
        self.trend_temp_second_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--',
                                                                       linewidth=1)
        self.event_bus.emit('refresh_chart')

    def trend_date1_changed(self, new_date):
        new_date = pd.to_datetime(new_date.toString('dd-MM-yyyy'), format='%d-%m-%Y')
        if new_date in self.figure_manager.Chart.date_to_pos.keys():
            self.trend_second_click_x = None
            if self.trend_temp_first_marker:
                self.trend_first_click_x = self.figure_manager.Chart.date_to_pos[new_date]
                self.trend_temp_first_marker.set_xdata([self.trend_first_click_x])
            else:
                self.trend_first_click_x = self.figure_manager.Chart.date_to_pos[new_date]
                self.plot_trend_temp_first_marker(self.trend_first_click_x)

        self.event_bus.emit('refresh_chart')

    def trend_date2_changed(self, new_date):
        new_date = pd.to_datetime(new_date.toString('dd-MM-yyyy'), format='%d-%m-%Y')
        if new_date in self.figure_manager.Chart.date_to_pos.keys():
            self.trend_first_click_x = None
            if self.trend_temp_second_marker:
                self.trend_second_click_x = self.figure_manager.Chart.date_to_pos[new_date]
                self.trend_temp_second_marker.set_xdata([self.trend_second_click_x])
            else:
                self.trend_second_click_x = self.figure_manager.Chart.date_to_pos[new_date]
                self.plot_trend_temp_second_marker(self.trend_second_click_x)

        self.event_bus.emit('refresh_chart')

    def trend_finalize(self):
        if self.trend_elements and self.trend_data:
            new_trend_elements = {}
            for name, original in self.trend_elements.items():
                if 'line' in name:  # Keep all line elements including None values
                    if original:  # Create new Line2D only if original exists
                        new_line = Line2D(original.get_xdata(), original.get_ydata(),
                                          color=self.trend_data['line_color'],
                                          linestyle=self.trend_data['linestyle'],
                                          linewidth=self.trend_data['linewidth'])
                        new_trend_elements[name] = new_line
                        self.figure_manager.ax.add_line(new_line)
                    else:
                        new_trend_elements[name] = None  # Preserve None values
                elif 'label' in name and original:
                    # Position the cel label at a reasonable default position
                    est_x, est_y = original.get_position()
                    est_text = original.get_text()
                    new_text = Text(est_x, est_y,
                                    est_text, color=self.trend_data['line_color'],
                                    rotation=original.get_rotation(),
                                    verticalalignment=original.get_verticalalignment(),
                                    horizontalalignment=original.get_horizontalalignment(),
                                    clip_on=False,
                                    transform=self.figure_manager.ax.transData,
                                    fontweight=original.get_weight(),
                                    fontsize=self.trend_data['font_size']
                                    )
                    new_trend_elements[name] = new_text
                    self.figure_manager.ax.add_artist(new_text)

                    # Make the text draggable
                    self.event_bus.emit('make_draggable', data={
                        'objects': new_text,
                        'save_obj': self.trend_data,
                        'save_event': 'save_cel_label_pos'
                    })

            # Get text position for data
            est_x, est_y = self.trend_elements['cel_label'].get_position()
            est_x = self.figure_manager.data_manager.find_closest_x(est_x, self.figure_manager.Chart.date_to_pos)
            est_date = self.figure_manager.x_to_date[est_x]
            self.trend_data['text_date'] = est_date.strftime(self.figure_manager.data_manager.standard_date_string)
            self.trend_data['text_y'] = est_y

            # Save trend to json chart file
            trend_type = self.trend_data['type']
            self.figure_manager.data_manager.chart_data[trend_type].append(self.trend_data)

            user_col = self.event_bus.emit('get_current_trend_column')
            col_instance = self.figure_manager.data_manager.plot_columns[user_col]
            col_instance.save_trend(new_trend_elements, self.trend_data)

            self.trend_cleanup()

    def trend_cleanup(self):
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()

        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_current_temp_marker = None
        self.trend_temp_fit_on = False

        # Clear temp fit
        if self.trend_elements:
            for element in self.trend_elements.values():
                if element:
                    element.remove()

        self.trend_elements = None
        self.trend_data = None

        self.event_bus.emit('refresh_chart')

    def adjust_dates(self):
        if self.trend_current_temp_marker == 'first':
            x1 = self.trend_temp_first_marker.get_xdata()[0]
            d1 = self.figure_manager.x_to_date[x1]
            return d1, 'first'
        elif self.trend_current_temp_marker == 'second':
            x2 = self.trend_temp_second_marker.get_xdata()[0]
            d2 = self.figure_manager.x_to_date[x2]
            return d2, 'second'


class DragManager:
    def __init__(self, figure_manager, throttle_ms=25):
        self.figure_manager = figure_manager
        self.event_bus = figure_manager.event_bus

        # Drag state
        self.draggable_items = {}
        self.active_drag_id = None

        # Throttling
        self.throttle_ms = throttle_ms
        self.throttle_timer = QTimer()
        self.throttle_timer.setSingleShot(True)
        self.throttle_timer.timeout.connect(self._process_pending_update)

        self.update_pending = False
        self.last_mouse_event = None

        # Canvas connections
        self.pick_connection = None
        self.motion_connection = None
        self.release_connection = None

        # Blitting optimization
        self.drag_background = None

        # Event bus subscriptions
        self.event_bus.subscribe('make_draggable', self.make_draggable, has_data=True)
        self.event_bus.subscribe('refresh_drag_connections', self.refresh_drag_connections)

    def refresh_drag_connections(self):
        """Clean up and re-establish canvas connections"""
        self._cleanup_canvas_connections()
        if self.draggable_items:
            self._setup_canvas_connections()

    def make_draggable(self, data):
        """Make objects draggable"""
        objects = data['objects']
        save_obj = data['save_obj']
        save_event = data['save_event']
        drag_id = data.get('drag_id')
        picker_radius = data.get('picker_radius', 20)
        horizontal = data.get('horizontal', True)
        vertical = data.get('vertical', True)

        # Normalize to list
        if not isinstance(objects, (list, tuple)):
            objects = [objects]

        # Generate ID if not provided
        if drag_id is None:
            drag_id = f"drag_{len(self.draggable_items)}_{id(objects[0])}"

        # Make objects pickable
        for obj in objects:
            if hasattr(obj, 'set_picker'):
                obj.set_picker(picker_radius)

        # Store drag item
        self.draggable_items[drag_id] = {
            'objects': objects,
            'is_dragging': False,
            'start_pos': None,  # Store initial position
            'horizontal': horizontal,
            'vertical': vertical,
            'save_obj': save_obj,
            'save_event': save_event
        }

        # Set up canvas connections if this is the first item
        if self.pick_connection is None:
            self._setup_canvas_connections()

        return drag_id

    def remove_draggable(self, drag_id):
        """Remove draggable item"""
        if drag_id in self.draggable_items:
            item = self.draggable_items[drag_id]

            # Make objects non-pickable
            for obj in item['objects']:
                if hasattr(obj, 'set_picker'):
                    obj.set_picker(False)

            # Clean up if this was active
            if self.active_drag_id == drag_id:
                self.active_drag_id = None

            del self.draggable_items[drag_id]

        # Remove canvas connections if no items left
        if not self.draggable_items:
            self._cleanup_canvas_connections()

    def _setup_canvas_connections(self):
        """Set up canvas event connections"""
        canvas = self.figure_manager.canvas
        self.pick_connection = canvas.mpl_connect('pick_event', self._on_pick)
        self.motion_connection = canvas.mpl_connect('motion_notify_event', self._on_motion)
        self.release_connection = canvas.mpl_connect('button_release_event', self._on_release)

    def _cleanup_canvas_connections(self):
        """Clean up canvas event connections"""
        connections = [
            (self.pick_connection, 'pick_connection'),
            (self.motion_connection, 'motion_connection'),
            (self.release_connection, 'release_connection')
        ]

        for connection, attr_name in connections:
            if connection:
                self.figure_manager.canvas.mpl_disconnect(connection)
                setattr(self, attr_name, None)

    def _find_drag_item(self, artist):
        """Find which drag item contains the given artist"""
        for drag_id, item in self.draggable_items.items():
            if artist in item['objects']:
                return drag_id, item
        return None, None

    def _get_object_position(self, obj):
        """Get the current position of an object"""
        if hasattr(obj, 'get_position'):
            return obj.get_position()
        elif hasattr(obj, 'get_data'):
            # For line objects, use the first point
            xdata, ydata = obj.get_data()
            if len(xdata) > 0 and len(ydata) > 0:
                return xdata[0], ydata[0]
        return None, None

    def _save_background(self):
        """Save the background for blitting"""
        self.figure_manager.canvas.draw_idle()
        self.figure_manager.canvas.flush_events()
        self.drag_background = self.figure_manager.canvas.copy_from_bbox(
            self.figure_manager.figure.bbox
        )

    def _make_animated(self, objects, animated=True):
        """Make objects animated for blitting"""
        for obj in objects:
            if hasattr(obj, 'set_animated'):
                obj.set_animated(animated)

    def _on_pick(self, event):
        """Handle pick event - start dragging"""
        # Announce pick event
        self.figure_manager.pick_event = True

        drag_id, item = self._find_drag_item(event.artist)
        if not (drag_id and item):
            return

        # Start dragging
        self.active_drag_id = drag_id
        item['is_dragging'] = True

        # Make objects animated and save background
        self._make_animated(item['objects'], True)
        self._save_background()

        # Store initial position (mouse and object)
        item['start_pos'] = {
            'mouse_x': event.mouseevent.x,
            'mouse_y': event.mouseevent.y,
            'object_pos': self._get_object_position(event.artist)
        }

        # Stop any pending throttle timer
        self.throttle_timer.stop()
        self.update_pending = False

        # Initial draw
        self._blit_draw_objects(item['objects'])

    def _on_motion(self, event):
        """Handle motion event - update drag position"""
        if not self.active_drag_id:
            return

        item = self.draggable_items.get(self.active_drag_id)
        if not item or not item['is_dragging']:
            return

        # Store event for throttled processing
        self.last_mouse_event = event

        # Start throttle timer if not already pending
        if not self.update_pending:
            self.update_pending = True
            self.throttle_timer.start(self.throttle_ms)

    def _on_release(self, event):
        """Handle release event - finish dragging"""
        # Announce end of pick event
        self.figure_manager.pick_event = False

        if not self.active_drag_id:
            return

        item = self.draggable_items.get(self.active_drag_id)
        if not (item and item['is_dragging']):
            return

        # Make objects non-animated
        self._make_animated(item['objects'], False)

        # Get final position and save
        text_obj = item['objects'][0]
        final_x, final_y = text_obj.get_position()

        data = {
            'save_obj': item['save_obj'],
            'drop_x': final_x,
            'drop_y': final_y
        }
        self.event_bus.emit(item['save_event'], data)

        # Clean up drag state
        item['is_dragging'] = False
        self.active_drag_id = None

        # Stop throttling
        self.throttle_timer.stop()
        self.update_pending = False
        self.last_mouse_event = None

        # Final refresh
        self.figure_manager.event_bus.emit('refresh_chart')

    def _blit_draw_objects(self, objects):
        """Draw objects using blitting"""
        if not self.drag_background:
            return

        # Restore background
        self.figure_manager.canvas.restore_region(self.drag_background)

        # Draw the dragged objects
        for obj in objects:
            if obj:
                self.figure_manager.ax.draw_artist(obj)

        # Blit the result
        self.figure_manager.canvas.blit(self.figure_manager.figure.bbox)

    def _process_pending_update(self):
        """Process the most recent mouse event at the throttled rate"""
        if not self.last_mouse_event or not self.active_drag_id:
            self.throttle_timer.stop()
            self.update_pending = False
            return

        item = self.draggable_items.get(self.active_drag_id)
        if not (item and item['is_dragging'] and item['start_pos']):
            self.update_pending = False
            return

        event = self.last_mouse_event
        self.last_mouse_event = None

        # Calculate new position
        new_pos = self._calculate_new_position(event, item)
        if new_pos:
            # Update object positions
            for obj in item['objects']:
                if hasattr(obj, 'set_position'):
                    obj.set_position(new_pos)

            # Draw with blitting
            self._blit_draw_objects(item['objects'])

        # Continue throttling if still dragging
        if self.update_pending and self.active_drag_id:
            self.throttle_timer.start(self.throttle_ms)
        else:
            self.update_pending = False

    def _calculate_new_position(self, event, item):
        """Calculate new object position based on mouse movement"""
        start_pos = item['start_pos']
        original_x, original_y = start_pos['object_pos']

        if original_x is None or original_y is None:
            return None

        # Convert mouse positions to data coordinates
        display_to_data = self.figure_manager.ax.transData.inverted()
        current_mouse_data = display_to_data.transform((event.x, event.y))
        start_mouse_data = display_to_data.transform((start_pos['mouse_x'], start_pos['mouse_y']))

        # Calculate displacement
        dx = current_mouse_data[0] - start_mouse_data[0]

        # Handle y-axis movement (with log scale support)
        if self.figure_manager.ax.get_yscale() == 'log':
            # Work in log space for proportional movement
            if original_y > 0 and start_mouse_data[1] > 0 and current_mouse_data[1] > 0:
                log_ratio = current_mouse_data[1] / start_mouse_data[1]
                new_y = original_y * log_ratio
            else:
                new_y = original_y  # Fallback if any value <= 0
        else:
            # Linear scale - use regular displacement
            dy = current_mouse_data[1] - start_mouse_data[1]
            new_y = original_y + dy

        # Apply movement constraints
        new_x = original_x + dx if item['horizontal'] else original_x
        new_y = new_y if item['vertical'] else original_y

        # Ensure x is integer for grid alignment
        new_x = int(new_x)

        return (new_x, new_y)


class ViewManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = figure_manager.event_bus

        # Event subscriptions
        self.event_bus.subscribe('view_update_credit_lines', self.view_update_credit_lines)
        self.event_bus.subscribe('apply_all_grid_settings', self.apply_all_grid_settings)
        self.event_bus.subscribe('apply_all_misc_settings', self.apply_all_misc_settings)
        self.event_bus.subscribe('create_legend', self.create_legend)
        self.event_bus.subscribe('update_legend', self.update_legend)
        self.event_bus.subscribe('view_major_date_gridlines', self.view_major_date_gridlines, has_data=True)
        self.event_bus.subscribe('view_major_count_gridlines', self.view_major_count_gridlines, has_data=True)
        self.event_bus.subscribe('view_minor_gridlines', self.view_minor_gridlines, has_data=True)
        self.event_bus.subscribe('view_floor_grid', self.view_floor_grid, has_data=True)
        self.event_bus.subscribe('view_phase_lines_toggle', self.view_phase_lines_toggle, has_data=True)
        self.event_bus.subscribe('view_aims_toggle', self.view_aims_toggle, has_data=True)
        self.event_bus.subscribe('view_cel_fan_toggle', self.view_cel_fan_toggle, has_data=True)
        self.event_bus.subscribe('view_credit_lines_toggle', self.view_credit_lines_toggle, has_data=True)
        self.event_bus.subscribe('view_legend_toggle', self.view_legend_toggle, has_data=True)

    def legend_pick(self, event):
        if event.artist in self.figure_manager.chart_objects['legend_obj']:
            self.event_bus.emit('modify_columns')

    def create_legend(self):
        chart_type = self.figure_manager.event_bus.emit("get_chart_data", ['type', 'Daily'])
        is_minute_chart = 'Minute' in chart_type
        columns = self.figure_manager.data_manager.plot_columns
        handles, labels = [], []
        if columns:
            for user_col, column in columns.items():
                legend = column.get_legend()  # Returns  None if df_agg is empty

                # Skip floor if not minute chart
                if column.sys_col == 'm' and not is_minute_chart:
                    continue

                if legend:
                    handles.append(Line2D([0], [0],
                                          color=legend['line_color'],
                                          marker=legend['marker'],
                                          markeredgecolor=legend['edge_color'],
                                          markerfacecolor=legend['face_color'],
                                          linestyle=legend['line_style'],
                                          markersize=np.sqrt(legend['marker_size']),
                                          linewidth=legend['line_width']))
                    labels.append(legend['user_col'])

        legend = self.figure_manager.ax.legend(handles, labels, loc='best', framealpha=1)
        legend.set_picker(5)
        self.figure_manager.chart_objects['legend_obj'].append(legend)

    def update_legend(self):
        if self.figure_manager.chart_objects['legend_obj']:
            for legend in self.figure_manager.chart_objects['legend_obj']:
                legend.remove()
            self.figure_manager.chart_objects['legend_obj'] = []

        self.create_legend()
        self.view_legend_toggle(self.figure_manager.data_manager.chart_data['view']['chart']['legend'])

    def view_legend_toggle(self, show, refresh=True):
        if self.figure_manager.chart_objects['legend_obj']:
            self.figure_manager.event_bus.emit("update_chart_data", [['view', 'chart', 'legend'], bool(show)])
            for legend in self.figure_manager.chart_objects['legend_obj']:
                legend.set_visible(show)
            if refresh:
                self.event_bus.emit('refresh_chart')

    def apply_all_grid_settings(self):
        self.view_minor_gridlines(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'minor_grid'], False]), False)
        self.view_major_date_gridlines(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'major_grid_dates'], False]), False)
        self.view_major_count_gridlines(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'major_grid_counts'], False]), False)
        self.view_floor_grid(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'floor_grid'], False]), False)

    def apply_all_misc_settings(self):
        self.view_phase_lines_toggle(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'phase'], False]), False)
        self.view_aims_toggle(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'aims'], False]),False)
        self.view_cel_fan_toggle(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'cel_fan'], False]), False)
        self.view_credit_lines_toggle(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'credit'], False]), False)
        self.view_legend_toggle(self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'legend'], False]), False)

    def view_minor_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.minor_grid_lines(show)
        self.figure_manager.event_bus.emit("update_chart_data", [['view', 'chart', 'minor_grid'], bool(show)])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_major_date_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.major_grid_dates(show)
        self.figure_manager.event_bus.emit("update_chart_data", [['view', 'chart', 'major_grid_dates'], bool(show)])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_major_count_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.major_grid_counts(show)
        view = self.figure_manager.event_bus.emit("get_chart_data", ['view', {}])
        view['chart']['major_grid_counts'] = bool(show)
        self.figure_manager.event_bus.emit("update_chart_data", ['view', view])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_floor_grid(self, show, refresh=True):
        self.figure_manager.Chart.floor_grid_lines(show)
        view = self.figure_manager.event_bus.emit("get_chart_data", ['view', {}])
        view['chart']['floor_grid'] = bool(show)
        self.figure_manager.event_bus.emit("update_chart_data", ['view', view])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_aims_toggle(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['aim_obj']:
            if pair:
                line, text = pair
                line.set_visible(show)
                text.set_visible(show)
        view = self.figure_manager.event_bus.emit("get_chart_data", ['view', {}])
        view['chart']['aims'] = bool(show)
        self.figure_manager.event_bus.emit("update_chart_data", ['view', view])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_phase_lines_toggle(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['phase_obj']:
            if pair:
                line, text = pair
                line.set_visible(show)
                text.set_visible(show)
        view = self.figure_manager.event_bus.emit("get_chart_data", ['view', {}])
        view['chart']['phase'] = bool(show)
        self.figure_manager.event_bus.emit("update_chart_data", ['view', view])
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_cel_fan_toggle(self, status, refresh=True):
        self.figure_manager.event_bus.emit("update_chart_data", [['view', 'chart', 'cel_fan'], bool(status)])
        self.figure_manager.drag_fan_manager.update_visibility()

        # Adjust right y-label if dealing with a minute chart
        chart_type = self.figure_manager.event_bus.emit("get_chart_data", ['type', 'Daily'])
        if 'Minute' in chart_type:
            if status:
                self.figure_manager.Chart.ax.yaxis.set_label_coords(-0.1, 0.7)
            else:
                self.figure_manager.Chart.ax.yaxis.set_label_coords(-0.1, 0.5)

        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_credit_lines_toggle(self, status, refresh=True):
        view = self.figure_manager.event_bus.emit("get_chart_data", ['view', {}])
        view['chart']['credit'] = bool(status)
        self.figure_manager.event_bus.emit("update_chart_data", ['view', view])

        if self.figure_manager.credit_lines_object:
            self.figure_manager.credit_lines_object.set_visible(status)
            if refresh:
                self.event_bus.emit('refresh_chart')

    def view_on_credit_line_pick(self, event):
        if event.artist == self.figure_manager.credit_lines_object:
            self.event_bus.emit('view_credit_lines_popup')

    def view_update_credit_lines(self):
        rows = self.event_bus.emit("get_chart_data", ['credit', ('', '')])
        if rows:
            r1, r2 = rows
            # Reject revision if credit lines are completely empty
            if len(r1) + len(r2) == 0:
                return

            if self.figure_manager.credit_lines_object:
                self.figure_manager.credit_lines_object.remove()

            credit = r1 + '\n\n' + r2
            x_start = -5
            self.figure_manager.credit_lines_object = self.figure_manager.ax.text(
                x_start,
                self.figure_manager.Chart.credit_vert_pos,
                credit,
                transform=self.figure_manager.Chart.trans,
                fontsize=self.figure_manager.Chart.credit_fontsize,
                color=self.figure_manager.Chart.style_color,
                ha='left',
                va='center',
                picker=5,
            )
            self.event_bus.emit("update_chart_data", ['credit', (r1, r2)])


class StyleManager:
    def __init__(self, figure_manager):
        # Classes
        self.figure_manager = figure_manager
        self.event_bus = EventBus()

        # Control variables
        self.point_temp_first_marker = None
        self.point_temp_second_marker = None
        self.point_current_temp_marker = None
        self.point_first_click_x = None
        self.point_second_click_x = None

        # Event bus subscriptions
        self.event_bus.subscribe('style_point_on_click', self.style_point_on_click, has_data=True)
        self.event_bus.subscribe('update_point_styles', self.update_point_styles, has_data=True)
        self.event_bus.subscribe('apply_styles', self.apply_styles)
        self.event_bus.subscribe('style_cleanup', self.manual_cleanup)

    def apply_styles(self):
        data_point_styles = self.figure_manager.event_bus.emit("get_chart_data", ['data_point_styles', {}])
        plot_columns = self.figure_manager.data_manager.plot_columns
        for user_col, styles in data_point_styles.items():
            if user_col in plot_columns.keys():
                col_instance = plot_columns[user_col]
                col_instance.load_styles()
                col_instance.update_style()

    def update_point_styles(self, data):
        user_col = data['user_col']
        style_cat = data['style_cat']
        style_val = data['style_val']

        col_instance = self.figure_manager.data_manager.plot_columns[user_col]
        df = col_instance.get_df()
        if not df.empty:
            x_to_date = self.figure_manager.x_to_date

            # Specific date boundary
            if self.point_temp_first_marker and self.point_temp_second_marker:
                x1 = self.point_temp_first_marker.get_xdata()[0]
                x2 = self.point_temp_second_marker.get_xdata()[0]
                x1, x2 = min(x1, x2), max(x1, x2)  # Ensure order
                date_start, date_end = pd.to_datetime(x_to_date[x1]), pd.to_datetime(x_to_date[x2])
                mask = (df['d'] >= date_start) & (df['d'] <= date_end)
                df.loc[mask, style_cat] = style_val
                date_string_format = self.figure_manager.data_manager.standard_date_string
                date1 = date_start.strftime(date_string_format)
                date2 = date_end.strftime(date_string_format)
            else:  # No date boundary
                date1 = 'none'
                date2 = 'none'
                df[style_cat] = style_val

            col_instance.update_style()

            self.event_bus.emit('refresh_chart')

            data_point_styles = self.figure_manager.event_bus.emit("get_chart_data", ['data_point_styles', {}])
            if user_col not in data_point_styles:
                data_point_styles[user_col] = []

            user_col_style_list = data_point_styles[user_col]
            user_col_style_list_keys = [list(style_dict.keys())[0] for style_dict in user_col_style_list]

            key = f'{date1}, {date2}, {style_cat}'
            if key in user_col_style_list_keys:
                idx = user_col_style_list_keys.index(key)
                a_dict = user_col_style_list[idx]
                a_dict[key] = style_val
            else:
                a_dict = {key: style_val}
                user_col_style_list.append(a_dict)

    def adjust_dates(self):
        if self.point_current_temp_marker == 'first':
            x1 = self.point_temp_first_marker.get_xdata()[0]
            d1 = self.figure_manager.x_to_date[x1]
            return d1, 'first'
        elif self.point_current_temp_marker == 'second':
            x2 = self.point_temp_second_marker.get_xdata()[0]
            d2 = self.figure_manager.x_to_date[x2]
            return d2, 'second'

    def safe_float_convert(self, input):
        try:
            return float(input)
        except ValueError:
            return 0.0

    def plot_point_temp_first_marker(self, x_i):
        self.point_current_temp_marker = 'first'
        if self.point_temp_first_marker:
            self.point_temp_first_marker.remove()
        self.point_temp_first_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.event_bus.emit('refresh_chart')

    def plot_point_temp_second_marker(self, x_i):
        self.point_current_temp_marker = 'second'
        if self.point_temp_second_marker:
            self.point_temp_second_marker.remove()
        self.point_temp_second_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.event_bus.emit('refresh_chart')

    def style_point_on_click(self, event):
        if self.figure_manager.pick_event:
            return

        if event.xdata is not None:
            x = self.figure_manager.data_manager.find_closest_x(int(event.xdata), self.figure_manager.Chart.date_to_pos)
            if x is not None:
                if self.point_first_click_x is None:
                    self.point_second_click_x = None
                    self.point_first_click_x = x
                elif self.point_second_click_x is None:
                    self.point_first_click_x = None
                    self.point_second_click_x = x

                if self.point_first_click_x is not None and self.point_second_click_x is None:
                    self.plot_point_temp_first_marker(self.point_first_click_x)
                    return self.point_first_click_x, 0
                elif self.point_second_click_x is not None:
                    self.plot_point_temp_second_marker(self.point_second_click_x)
                    return self.point_second_click_x, 1

    def manual_cleanup(self):
        if self.point_temp_first_marker:
            self.point_temp_first_marker.remove()
        if self.point_temp_second_marker:
            self.point_temp_second_marker.remove()
        self.point_temp_first_marker = None
        self.point_temp_second_marker = None
        self.point_current_temp_marker = None
        self.point_first_click_x = None
        self.point_second_click_x = None

        self.event_bus.emit('refresh_chart')


class NoteManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = self.figure_manager.event_bus
        self.note_objects = None
        self.individual_note_object = None

        # Event subscriptions
        self.event_bus.subscribe('remove_note_locations', self.remove_note_locations)
        self.event_bus.subscribe('refresh_note_locations', self.refresh_note_locations)
        self.event_bus.subscribe('show_individual_note_locations', self.show_individual_note_location, has_data=True)
        self.event_bus.subscribe('clear_previous_individual_note_object', self.clear_previous_individual_note_object, has_data=True)

    def refresh_note_locations(self):
        self.remove_note_locations()
        self.show_note_locations()

    def show_note_locations(self):
        all_notes = self.figure_manager.event_bus.emit("get_chart_data", ['notes', []])
        xs, ys = [], []
        for note in all_notes:
            text, date_str, y_val = note.split('|')
            date_pd = self.figure_manager.data_manager.find_closest_date(date_str, self.figure_manager.Chart.date_to_pos)
            if date_pd in self.figure_manager.Chart.date_to_pos.keys():
                x_pos = self.figure_manager.Chart.date_to_pos[date_pd]
                xs.append(x_pos)
                ys.append(float(y_val))

        if xs and ys:
            self.note_objects = self.figure_manager.ax.scatter(xs, ys,
                                                        marker='s',
                                                        linestyle='',
                                                        facecolors='none',
                                                        edgecolors='purple',
                                                        s=100)
        if self.note_objects:
            self.event_bus.emit('refresh_chart')

    def remove_note_locations(self):
        if self.note_objects:
            self.note_objects.remove()
            self.note_objects = None
            self.event_bus.emit('refresh_chart')

    def show_individual_note_location(self, data):
        self.clear_previous_individual_note_object()
        date_pd = self.figure_manager.data_manager.find_closest_date(data['date_str'], self.figure_manager.Chart.date_to_pos)
        if date_pd in self.figure_manager.Chart.date_to_pos.keys():
            note_x = self.figure_manager.Chart.date_to_pos[date_pd]
            note_y = float(data['note_y'])
            self.individual_note_object = self.figure_manager.ax.scatter(note_x, note_y,
                                                               marker='s',
                                                               linestyle='',
                                                               facecolors='purple',
                                                               edgecolors='purple',
                                                               s=100)
            self.event_bus.emit('refresh_chart')

    def clear_previous_individual_note_object(self, data=None):
        if self.individual_note_object:
            self.individual_note_object.remove()
            self.individual_note_object = None
        if data and data['refresh']:
            self.event_bus.emit('refresh_chart')


class Hover:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager

        # Crosshair elements
        self.show_lines = True
        self.crosshair_vline = None
        self.crosshair_hline = None
        self.crosshair_background = None
        self.crosshair_annotation = None
        self.previous_cross_hair_x_y = (None, None)
        self.draw_crosshair = False
        self.note_annotations = []
        self.note_lines = []

        # Note-specific elements
        self.note_crosshair_connection = None
        self.note_dates = None
        self.max_stacked_allowed = 31

        # Timer for rate limiting
        self.crosshair_timer = QTimer()
        self.crosshair_timer.setSingleShot(True)
        self.crosshair_rate_limit = 25  # Rate limit in milliseconds

    def crosshair_blit(self, x, y):
        # Updates the crosshair position with rate limiting.
        if self.crosshair_timer.isActive():
            return  # Skip if the timer is still active

        # Execute the crosshair logic
        self._update_crosshair_blit(x, y)

        # Start the timer to enforce rate limiting
        self.crosshair_timer.start(self.crosshair_rate_limit)

    def _get_data_values(self, x_i):
        chart_type = self.figure_manager.event_bus.emit("get_chart_data", ['type', 'Daily']).lower()

        plot_columns = self.figure_manager.data_manager.plot_columns
        values = []
        values_total = []
        visibility = []
        user_cols = []
        sys_cols = []
        for user_col, column_instance in plot_columns.items():
            # Filter and get y numpy array
            sys_col = column_instance.sys_col
            y_df = column_instance.get_y_from_x(x_i).dropna()
            y = y_df[y_df.not_zero_counts][sys_col].values
            y_total = y_df[y_df.not_zero_counts][sys_col + '_total'].values

            if y.size > 0:
                if y.size > self.max_stacked_allowed:
                    y = [np.median(y)]
            else:
                y = [0]

            # Apply rounding to y values for display
            if sys_col != 'm':
                y = [self.figure_manager.data_manager.format_y_value(y_i) for y_i in y]

            # Determine visibility based on thresholds and view settings
            threshold = 0 if 'minute' in chart_type else 0.99
            show_y = any(freq > threshold for freq in y) and column_instance.view_settings['data']

            values.append(y)
            values_total.append(y_total)
            visibility.append(show_y)
            user_cols.append(user_col)
            sys_cols.append(sys_col)

        return values, values_total, visibility, user_cols, sys_cols

    def _format_date_label(self, x):
        date = self.figure_manager.x_to_date[int(x)]
        day = date.strftime('%a, %d')
        month = date.strftime('%b, %m')
        year = date.strftime("%Y")

        chart_type = self.figure_manager.event_bus.emit("get_chart_data", ['type', 'Daily']).lower()
        return date, day, month, year, chart_type

    def _format_data_label(self, day, month, year, x, y, values, values_total, visibility, user_cols, sys_cols):
        data_parts = []

        for val, val_tot, show, user_col, sys_col in zip(values, values_total, visibility, user_cols, sys_cols):
            if show:
                median = np.median(val)
                value = int(median) if median.is_integer() else median

                if sys_col == 'm':
                    value = f'{1 / value:.2f}'

                if sys_col == 'c':
                    # Add ratio if possible
                    c_exists = 'c' in sys_cols
                    i_exists = 'i' in sys_cols
                    has_columns = c_exists and i_exists
                    if has_columns:
                        c_idx = sys_cols.index('c')
                        i_idx = sys_cols.index('i')
                        c_visible = visibility[c_idx]
                        i_visible = visibility[i_idx]
                        c_tot = values_total[c_idx]
                        i_tot = values_total[i_idx]

                        values_present = len(c_tot) == 1 and len(i_tot) == 1
                        if c_visible and i_visible and values_present:
                            total = i_tot[0] + c_tot[0]
                            percentage = (c_tot[0] / total) * 100
                            value = f'{value} ({percentage:.0f}%)'

                col = user_col if len(user_col) < 12 else user_col[:12] + '...'
                data_parts.append(f"{col} = {value}")

        width = ' ' * 30
        base_str = (r"$\bf{Date}$" + f"\n{day}\n{month}\n{year}\n\n"
                                     r"$\bf{Cursor}$" + f"\nx = {x}\ny = {y}")

        if data_parts:
            return base_str + "\n\n" + r"$\bf{Data}$" + "\n" + "\n".join(data_parts) + f"\n{width}"
        return base_str + f"\n{width}"

    def _initialize_crosshair_elements(self, x, y):
        if self.crosshair_vline is None and self.crosshair_hline is None:
            self.crosshair_vline = self.figure_manager.ax.axvline(x=x, color='gray', linestyle='--', animated=True,
                                                                  linewidth=1)
            self.crosshair_hline = self.figure_manager.ax.axhline(y=y, color='gray', linestyle='--', animated=True,
                                                                  linewidth=1)

            x_ann = -0.1
            chart_type = self.figure_manager.event_bus.emit("get_chart_data", ['type', 'Daily']).lower()
            y_ann = 0.5 if 'minute' in chart_type else 0.22

            self.crosshair_annotation = self.figure_manager.ax.text(
                x_ann, y_ann, '', transform=self.figure_manager.ax.transAxes,
                ha='center', va='bottom', weight='normal',
                fontsize=self.figure_manager.Chart.general_fontsize * 0.7,
                color='black', animated=True, clip_on=False,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round, pad=0.5')
            )

            # Create markers dict based on sys_col prefixes
            self.markers = {}
            plot_columns = self.figure_manager.data_manager.plot_columns
            for column_instance in plot_columns.values():
                prefix = column_instance.sys_col[0].lower()
                if prefix not in self.markers:
                    marker_style = {
                        'c': ('o', 'green'),
                        'i': ('o', 'red'),
                        'm': ('v', 'purple'),
                        'o': ('s', 'orange')
                    }.get(prefix)

                    if marker_style:
                        marker, color = marker_style
                        self.markers[column_instance.sys_col] = self.figure_manager.ax.plot(
                            [], [], marker, color=color, alpha=0.4, animated=True,
                            markersize=10 if marker == 's' else (7 if marker == 'v' else 10)
                        )[0]

            # Create note elements
            max_notes = len(self.figure_manager.data_manager.chart_data['notes'])
            for _ in range(max_notes):
                note_ann = self.figure_manager.ax.text(
                    0, 0, '',
                    ha='center', va='center',
                    fontsize=self.figure_manager.Chart.general_fontsize * 0.8,
                    color='black', animated=True, clip_on=False,
                    bbox=dict(
                        facecolor='#FFFFA0',
                        edgecolor='#B8860B',
                        boxstyle='round,pad=0.5',
                        mutation_scale=1.2
                    )
                )
                self.note_annotations.append(note_ann)

                note_line, = self.figure_manager.ax.plot(
                    [], [], color='black', linestyle='-',
                    linewidth=1, animated=True)
                self.note_lines.append(note_line)

    def _handle_notes(self, date):
        hover_date_str = date.strftime(self.figure_manager.data_manager.standard_date_string)
        all_notes = self.figure_manager.event_bus.emit("get_chart_data", ['notes', []])

        hover_date_notes = []
        for note in all_notes:
            note_date_str = note.split('|')[1]
            # Snap dates if necessary
            closest_note_date_pd = self.figure_manager.data_manager.find_closest_date(note_date_str, self.figure_manager.Chart.date_to_pos)
            if closest_note_date_pd:  # Will be None if date is not in date_to_pos
                closest_note_date_str = closest_note_date_pd.strftime(self.figure_manager.data_manager.standard_date_string)
                if hover_date_str == closest_note_date_str:
                    hover_date_notes.append(note)

        for idx, date_note in enumerate(hover_date_notes):
            text, d, note_y = date_note.split('|')
            note_y = float(note_y)

            # Format text while preserving user added line breaks if any
            lines = text.split('\n')
            wrapped_lines = [textwrap.fill(line, width=40) for line in lines]
            wrapped_text = '\n'.join(wrapped_lines)
            self.note_annotations[idx].set_text(wrapped_text)
            self.note_annotations[idx].set_horizontalalignment('left')

            note_width = self.note_annotations[idx].get_window_extent().width
            note_height = self.note_annotations[idx].get_window_extent().height

            # Placement logic and calculations
            mid_x = self.figure_manager.Chart.xmax / 2
            mid_y = 10 ** ((np.log10(self.figure_manager.Chart.ymax) + np.log10(self.figure_manager.Chart.ymin)) / 2)
            note_x = self.figure_manager.Chart.date_to_pos[pd.to_datetime(hover_date_str)]
            x_adjust = note_width * 0.1 if (note_width * 0.1) > 10 else 10
            y_adjust = note_height * 0.2 if (note_height * 0.2) > 2.5 else 2.5
            note_x2 = note_x + x_adjust if note_x < mid_x else note_x - x_adjust
            note_y2 = note_y * y_adjust if note_y < mid_y else note_y / y_adjust

            self.note_annotations[idx].set_position((note_x2, note_y2))
            self.note_lines[idx].set_data([note_x, note_x2], [note_y, note_y2])

        # Clear unused elements
        for idx in range(len(hover_date_notes), len(self.note_annotations)):
            self.note_annotations[idx].set_text('')
            self.note_lines[idx].set_data([], [])

        return hover_date_str

    def _update_and_draw_elements(self, x, y, data_label, values, visibility, hover_date_str):
        self.crosshair_vline.set_xdata([x])
        self.crosshair_hline.set_ydata([y])

        # Update markers based on visibility and sys_col
        plot_columns = self.figure_manager.data_manager.plot_columns
        for (user_col, column_instance), freq, show in zip(
                plot_columns.items(),
                values,
                visibility
        ):
            marker = self.markers.get(column_instance.sys_col)
            if marker and show:
                marker.set_data([x] * len(freq), freq)
            elif marker:
                marker.set_data([], [])

        self.crosshair_annotation.set_text(data_label)

        # Draw process
        self.figure_manager.canvas.restore_region(self.crosshair_background)

        # Draw annotation and lines
        self.figure_manager.ax.draw_artist(self.crosshair_annotation)
        if self.show_lines:
            self.figure_manager.ax.draw_artist(self.crosshair_vline)
            self.figure_manager.ax.draw_artist(self.crosshair_hline)

        # Draw visible markers
        for marker in self.markers.values():
            if len(marker.get_data()[0]) > 0:
                self.figure_manager.ax.draw_artist(marker)

        # Draw notes if present
        if hover_date_str in self.note_dates:
            for note_line, note_ann in zip(self.note_lines, self.note_annotations):
                if note_ann.get_text():
                    self.figure_manager.ax.draw_artist(note_line)
                    self.figure_manager.ax.draw_artist(note_ann)

        self.figure_manager.canvas.blit(self.figure_manager.figure.bbox)

    def _update_crosshair_blit(self, x, y):
        values, values_total, visibility, user_cols, sys_cols = self._get_data_values(x)
        date, day, month, year, chart_type = self._format_date_label(x)
        data_label = self._format_data_label(day, month, year, x, y, values, values_total, visibility, user_cols, sys_cols)
        self._initialize_crosshair_elements(x, y)
        hover_date_str = self._handle_notes(date)
        self._update_and_draw_elements(x, y, data_label, values, visibility, hover_date_str)

    def save_crosshair_background(self):
        # Captures the figure background for blitting. Runs once when shift is pressed
        self.note_dates = []
        all_notes = self.figure_manager.event_bus.emit("get_chart_data", ['notes', []])
        for note in all_notes:
            t, d, y = note.split('|')
            # Snap dates if necessary
            closest_note_date_pd = self.figure_manager.data_manager.find_closest_date(d, self.figure_manager.Chart.date_to_pos)
            if closest_note_date_pd:  # Will be None if date not in date_to_pos
                closest_note_date_str = closest_note_date_pd.strftime(self.figure_manager.data_manager.standard_date_string)
                self.note_dates.append(closest_note_date_str)

        self.crosshair_background = self.figure_manager.canvas.copy_from_bbox(
            self.figure_manager.figure.bbox
        )

    def clear_crosshair_blit(self):
        if self.crosshair_vline is not None:
            self.crosshair_vline.set_xdata([None])
            self.crosshair_vline = None

        if self.crosshair_hline is not None:
            self.crosshair_hline.set_ydata([None])
            self.crosshair_hline = None

        # Clear all markers
        if hasattr(self, 'markers'):
            for marker in self.markers.values():
                marker.set_data([], [])
            self.markers = {}

        if self.crosshair_annotation is not None:
            self.crosshair_annotation.set_text('')
            self.crosshair_annotation = None

        # Clear note elements
        for note_ann in self.note_annotations:
            note_ann.set_text('')
        self.note_annotations = []

        for note_line in self.note_lines:
            note_line.set_data([], [])
        self.note_lines = []

        self.previous_cross_hair_x_y = (None, None)

        self.figure_manager.canvas.draw_idle()

    def note_crosshair_blit(self, x):
        # Draw a vertical purple line for note mode crosshair.
        if self.crosshair_timer.isActive():
            return  # Skip if the timer is still active

        # Execute the crosshair logic
        self._update_note_crosshair_blit(x)

        # Start the timer to enforce rate limiting
        self.crosshair_timer.start(self.crosshair_rate_limit)

    def _update_note_crosshair_blit(self, x):
        # Internal method to update note crosshair position.
        date = self.figure_manager.x_to_date[int(x)]
        day = date.strftime('%a, %d')
        month = date.strftime('%b, %m')
        year = date.strftime("%Y")

        width = ' ' * 20
        date_label = (r"$\bf{Date}$" + f"\n{day}\n{month}\n{year}\n{width}")

        # Create or update the crosshair and text annotation
        if self.crosshair_vline is None:
            self.crosshair_vline = self.figure_manager.ax.axvline(
                x=x, color='purple', linestyle='-', animated=True, linewidth=2, alpha=0.4
            )

            # Create a text annotation with white background
            self.crosshair_annotation = self.figure_manager.ax.text(
                -0.165, 0.5, '', transform=self.figure_manager.ax.transAxes,
                ha='center', va='bottom', weight='normal',
                fontsize=self.figure_manager.Chart.general_fontsize * 0.8,
                color='black', animated=True, clip_on=False,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round, pad=0.5')
            )

        # Update the position of the vertical line
        self.crosshair_vline.set_xdata([x])

        # Update the text annotation
        self.crosshair_annotation.set_text(date_label)

        # Restore the saved background
        self.figure_manager.canvas.restore_region(self.crosshair_background)

        # Redraw the crosshair and annotation
        self.figure_manager.ax.draw_artist(self.crosshair_vline)
        self.figure_manager.ax.draw_artist(self.crosshair_annotation)

        # Blit the entire figure
        self.figure_manager.canvas.blit(self.figure_manager.figure.bbox)

    def enable_note_crosshair(self):
        # Enable note mode crosshair.
        self.save_crosshair_background()
        self.note_crosshair_connection = self.figure_manager.canvas.mpl_connect(
            'motion_notify_event',
            self.update_note_hover_coordinates
        )

    def disable_note_crosshair(self):
        # Disable note mode crosshair.
        if hasattr(self, 'note_crosshair_connection'):
            self.figure_manager.canvas.mpl_disconnect(self.note_crosshair_connection)
            self.clear_crosshair_blit()

    def update_note_hover_coordinates(self, event):
        # Update crosshair position based on mouse movement in note mode.
        ax = event.inaxes
        if ax and event.xdata is not None:
            x = self.figure_manager.data_manager.find_closest_x(
                int(event.xdata),
                self.figure_manager.Chart.date_to_pos
            )
            self.note_crosshair_blit(x)


class DraggableFanManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = figure_manager.event_bus

        # Center point and fan properties
        self.y_mid = None
        self.x_mid = None
        self.fan_lines = []
        self.fan_texts = []
        self.base_text_distance_factor = 1.1
        self.ms_throttle = 25

        # Text labels for standard celeration and period
        self.standard_text = None
        self.period_text = None

        # Line data for transformation
        self.line_data = []

        # Drag state
        self.pressed = False
        self.drag_start_x = None
        self.drag_start_y = None
        self.drag_start_mid_x = None
        self.drag_start_mid_y = None

        # Blitting optimization
        self.drag_background = None
        self.use_blitting = True

        # Throttling mechanism
        self.update_pending = False
        self.last_mouse_event = None
        self.throttle_timer = QTimer()
        self.throttle_timer.setInterval(self.ms_throttle)
        self.throttle_timer.timeout.connect(self.process_pending_update)

        # Canvas connections
        self.pick_connection = None
        self.motion_connection = None
        self.release_connection = None

    def calculate_text_distance(self, label):
        # Adjust based on label length
        char_adjustment = 0.05 * len(label)  # 5% increase per character
        return self.base_text_distance_factor + char_adjustment

    def initialize_fan(self):
        # Initialize fan's midpoint
        chart_type = self.figure_manager.data_manager.chart_data['type']

        # Configure based on chart type
        is_minute_chart = 'Minute' in chart_type
        self.y_mid_offset = 22

        # Set midpoint and offset based on chart type
        if is_minute_chart:
            xmax_proportional_offset = -0.22
            self.y_mid = 0.01
            # Adjust right y-label
            self.figure_manager.ax.yaxis.set_label_coords(-0.1, 0.7)
        else:
            xmax_proportional_offset = 1.04
            self.y_mid = 1000

        self.x_mid = self.figure_manager.Chart.xmax * xmax_proportional_offset

        # Define text configurations by chart type
        fan_dict = {
            'DailyMinute': "per week",
            'WeeklyMinute': "per month",
            'MonthlyMinute': 'per 6 months',
            'YearlyMinute': 'per 5 years',
            'Daily': "per week",
            'Weekly': "per month",
            'Monthly': 'per 6 months',
            'Yearly': 'per 5 years',
        }

        self.per_unit_str = fan_dict[chart_type]

        # Create initial fan
        self.create_fan()

        # Set up canvas connections for picking
        self._setup_canvas_connections()

    def create_fan(self, fan_size=0.09):
        # Clear previous fan elements but keep text objects
        self.cleanup(keep_texts=True)

        # Celeration values
        cel_values = [16, 4, 2, 1.4, 1, 1 / 1.4, 1 / 2, 1 / 4, 1 / 16]
        labels = ['×16', '×4', '×2', '×1.4', '×1', '÷1.4', '÷2', '÷4', '÷16']

        # Get chart bounds
        x_min, x_max = self.figure_manager.ax.get_xlim()

        # Line length
        actual_line_length = (x_max - x_min) * fan_size

        # Get unit case
        chart_type = self.figure_manager.data_manager.chart_data['type'][0].lower()
        doubling = {'d': 7, 'w': 5, 'm': 6, 'y': 5}
        unit = doubling[chart_type]

        # Draw each line with picker enabled
        for cel, label in zip(cel_values, labels):
            # Calculate angle based on celeration
            angle = np.degrees(np.atan(np.log10(cel) / (np.log10(2) / np.tan(np.radians(34)))))
            angle_rad = np.radians(angle)

            # Calculate line endpoints
            dx = actual_line_length * np.cos(angle_rad)
            dy = actual_line_length * np.sin(angle_rad)
            x_end = self.x_mid + dx
            y_end = self.y_mid * (10 ** (np.log10(cel) * dx / unit))

            # Calculate text distance factor based on label length
            distance = self.calculate_text_distance(label)

            # Update line data
            self.line_data.append({
                'cel': cel,
                'angle': angle,
                'angle_rad': angle_rad,
                'dx': dx,
                'dy': dy,
                'unit': unit,
                'distance_factor': distance
            })

            # Calculate text position
            text_dx = dx * distance
            text_x = self.x_mid + text_dx
            text_y = self.y_mid * (10 ** (np.log10(cel) * text_dx / unit))

            # Create line with picker
            line = Line2D([self.x_mid, x_end], [self.y_mid, y_end],
                          linestyle='-', color=self.figure_manager.Chart.custom_grid_color,
                          linewidth=1, picker=True, pickradius=10, clip_on=False)
            self.figure_manager.ax.add_line(line)
            self.fan_lines.append(line)

            # Create label
            text = self.figure_manager.ax.text(
                text_x, text_y, label,
                ha='center', va='center',
                color=self.figure_manager.Chart.custom_grid_color,
                weight='bold', rotation=angle,
                fontsize=self.figure_manager.Chart.general_fontsize * 0.6
            )
            self.fan_texts.append(text)

        # Midpoint for the flat line (×1) to place labels
        middle_line_index = 4  # Index for the ×1 line in your arrays
        middle_line_data = self.line_data[middle_line_index]
        dx = middle_line_data['dx']
        x_text_position = self.x_mid + (dx / 2)

        # Add text annotations and store them as class attributes
        self.standard_text = self.figure_manager.ax.text(
            x_text_position, self.y_mid * self.y_mid_offset,
            f"Standard\n{self.figure_manager.data_manager.ui_cel_label}",
            color=self.figure_manager.Chart.custom_grid_color,
            weight='bold',
            ha='center', va='center',
            fontsize=self.figure_manager.Chart.general_fontsize * 0.7,
            picker=True
        )
        self.period_text = self.figure_manager.ax.text(
            x_text_position, self.y_mid / self.y_mid_offset,
            self.per_unit_str,
            color=self.figure_manager.Chart.custom_grid_color,
            weight='bold',
            ha='center', va='center',
            fontsize=self.figure_manager.Chart.general_fontsize * 0.7,
            picker=True
        )

        # Redraw
        self.event_bus.emit('refresh_chart')

    def _setup_canvas_connections(self):
        """Set up canvas event connections for fan dragging"""
        canvas = self.figure_manager.canvas
        self.pick_connection = canvas.mpl_connect('pick_event', self.on_pick)
        self.motion_connection = canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.release_connection = canvas.mpl_connect('button_release_event', self.on_release)

    def _cleanup_canvas_connections(self):
        """Clean up canvas event connections"""
        if self.pick_connection:
            self.figure_manager.canvas.mpl_disconnect(self.pick_connection)
            self.pick_connection = None
        if self.motion_connection:
            self.figure_manager.canvas.mpl_disconnect(self.motion_connection)
            self.motion_connection = None
        if self.release_connection:
            self.figure_manager.canvas.mpl_disconnect(self.release_connection)
            self.release_connection = None

    def _save_background(self):
        """Save the background for blitting"""
        if self.use_blitting:
            # Force a draw to ensure animated elements are removed from the display
            self.figure_manager.canvas.draw_idle()
            self.figure_manager.canvas.flush_events()

            # Now save the background without the animated elements
            self.drag_background = self.figure_manager.canvas.copy_from_bbox(
                self.figure_manager.figure.bbox
            )

    def _make_animated(self, animated=True):
        """Make fan elements animated for blitting"""
        for line in self.fan_lines:
            if hasattr(line, 'set_animated'):
                line.set_animated(animated)
        for text in self.fan_texts:
            if hasattr(text, 'set_animated'):
                text.set_animated(animated)
        if self.standard_text and hasattr(self.standard_text, 'set_animated'):
            self.standard_text.set_animated(animated)
        if self.period_text and hasattr(self.period_text, 'set_animated'):
            self.period_text.set_animated(animated)

    def _blit_draw_fan(self):
        """Draw fan elements using blitting for better performance"""
        if not self.use_blitting or not self.drag_background:
            return

        # Restore background
        self.figure_manager.canvas.restore_region(self.drag_background)

        # Draw all fan elements
        for line in self.fan_lines:
            if line:
                self.figure_manager.ax.draw_artist(line)
        for text in self.fan_texts:
            if text:
                self.figure_manager.ax.draw_artist(text)
        if self.standard_text:
            self.figure_manager.ax.draw_artist(self.standard_text)
        if self.period_text:
            self.figure_manager.ax.draw_artist(self.period_text)

        # Blit the result
        self.figure_manager.canvas.blit(self.figure_manager.figure.bbox)

    def update_fan_position(self):
        """Update fan position based on current x_mid and y_mid values"""
        # Use stored line_data for transformation
        for i, line_info in enumerate(self.line_data):
            cel = line_info['cel']
            dx = line_info['dx']
            unit = line_info['unit']
            distance_factor = line_info['distance_factor']

            # Update line position
            x_end = self.x_mid + dx
            y_end = self.y_mid * (10 ** (np.log10(cel) * dx / unit))
            self.fan_lines[i].set_data([self.x_mid, x_end], [self.y_mid, y_end])

            # Update text position
            text_dx = dx * distance_factor
            text_x = self.x_mid + text_dx
            text_y = self.y_mid * (10 ** (np.log10(cel) * text_dx / unit))
            self.fan_texts[i].set_position((text_x, text_y))

        # Update position of standard and period texts
        if self.standard_text and self.period_text:
            # Recalculate the midpoint for the ×1 line
            middle_line_index = 4  # Index for the ×1 line
            if len(self.line_data) > middle_line_index:
                middle_line_data = self.line_data[middle_line_index]
                dx = middle_line_data['dx']
                x_text_position = self.x_mid + (dx / 2)

                self.standard_text.set_position((x_text_position, self.y_mid * self.y_mid_offset))
                self.period_text.set_position((x_text_position, self.y_mid / self.y_mid_offset))

        # Use blitting for smooth updates during drag
        if self.pressed and self.use_blitting:
            self._blit_draw_fan()
        else:
            # Normal redraw when not dragging
            self.event_bus.emit('refresh_chart')

    def update_visibility(self):
        # Set visibility according to chart settings
        show_fan = self.figure_manager.event_bus.emit("get_chart_data", [['view', 'chart', 'cel_fan'], False])
        for line in self.fan_lines:
            line.set_visible(show_fan)
        for text in self.fan_texts:
            text.set_visible(show_fan)

        # Update visibility of standard and period texts
        if self.standard_text and self.period_text:
            self.standard_text.set_visible(show_fan)
            self.period_text.set_visible(show_fan)

    def on_pick(self, event):
        # Start drag when a fan line or text is picked
        if event.artist in self.fan_lines or event.artist in [self.standard_text, self.period_text]:
            self.pressed = True

            # Make elements animated for blitting
            self._make_animated(True)

            # Force canvas update and save background after making elements animated
            self._save_background()

            # Store the mouse position at click time in display coordinates
            self.drag_start_x = event.mouseevent.x
            self.drag_start_y = event.mouseevent.y

            # Store the current fan center
            self.drag_start_mid_x = self.x_mid
            self.drag_start_mid_y = self.y_mid

            # Stop any pending throttle timer
            self.throttle_timer.stop()
            self.update_pending = False

            # Initial blit draw
            if self.use_blitting:
                self._blit_draw_fan()

    def on_release(self, event):
        # End drag
        if self.pressed:
            self.pressed = False

            # Make elements non-animated
            self._make_animated(False)

            # Stop throttling
            self.throttle_timer.stop()
            self.update_pending = False
            self.last_mouse_event = None

            # Final refresh to show non-animated elements
            self.event_bus.emit('refresh_chart')

    def on_motion(self, event):
        # Handle dragging motion - continue even outside axes
        if not self.pressed:
            return

        # Store the event for later processing
        self.last_mouse_event = event

        # If no update is pending, start the timer
        if not self.update_pending:
            self.update_pending = True
            self.throttle_timer.start()

    def process_pending_update(self):
        """Process the most recent mouse event at the throttled rate"""
        if self.last_mouse_event is None or not self.pressed:
            self.throttle_timer.stop()
            self.update_pending = False
            return

        event = self.last_mouse_event
        self.last_mouse_event = None

        # Convert displacement to data coordinates
        display_to_data = self.figure_manager.ax.transData.inverted()

        # Get the data coordinates of the drag start point and current point
        start_data = display_to_data.transform((self.drag_start_x, self.drag_start_y))
        current_data = display_to_data.transform((event.x, event.y))

        # Calculate the displacement in data coordinates
        dx_data = current_data[0] - start_data[0]

        # Update fan center position
        new_x_mid = self.drag_start_mid_x + dx_data

        # Calculate the y-axis ratio
        if start_data[1] > 0 and current_data[1] > 0:  # Prevent divide by zero or negative logs
            y_ratio = current_data[1] / start_data[1]
            new_y_mid = self.drag_start_mid_y * y_ratio

            # Update the position without bounds checking to allow dragging outside
            self.x_mid = new_x_mid
            self.y_mid = new_y_mid
            self.update_fan_position()

        # Continue throttling if still dragging
        if self.update_pending and self.pressed:
            self.throttle_timer.start(self.ms_throttle)
        else:
            self.update_pending = False

    def cleanup(self, keep_texts=False):
        # Remove fan elements
        for line in self.fan_lines:
            line.remove()
        for text in self.fan_texts:
            text.remove()

        # Only remove text labels if keep_texts is False
        if not keep_texts:
            if self.standard_text:
                self.standard_text.remove()
                self.standard_text = None

            if self.period_text:
                self.period_text.remove()
                self.period_text = None

        self.fan_lines = []
        self.fan_texts = []
        self.line_data = []

        # Stop any pending updates
        self.throttle_timer.stop()

        # Clean up canvas connections
        self._cleanup_canvas_connections()
        

class PlotDrawManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = self.figure_manager.event_bus

        # Selected date line
        self.selected_date_line = None

        # Event subscriptions
        self.event_bus.subscribe('plot_cleanup', self.plot_cleanup)

    def plot_cleanup(self):
        if self.selected_date_line:
            self.selected_date_line.remove()
            self.selected_date_line = None

        self.event_bus.emit('refresh_chart')

    def draw_date_line(self, x_pos):
        self.plot_cleanup()  # Clear any existing line

        if x_pos is not None:
            self.selected_date_line = self.figure_manager.ax.axvline(x=x_pos, color='magenta', linestyle='-', linewidth=2, alpha=0.2)
            self.event_bus.emit('refresh_chart')

        return self.selected_date_line

