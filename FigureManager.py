import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.text import Text
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer
import scc
from DataManager import DataManager, DataPointColumn
from EventBus import EventBus
import copy
import re
import textwrap


class FigureManager(QWidget):
    def __init__(self, parent=None):
        super(FigureManager, self).__init__(parent)
        self.main_app = parent  # Assuming parent is an instance of ChartApp
        self.data_manager = DataManager()
        self.event_bus = EventBus()

        # Event subscriptions
        self.event_bus.subscribe('new_chart', self.new_chart, has_data=True)
        self.event_bus.subscribe('refresh_chart', self.refresh)

        self.fig_init = False  # Control variables for replot
        self.test_angle = False
        self.fan_ax = None  # Control variable for celeration fan

        # Managers
        self.phase_manager = PhaseManager(self)
        self.aim_manager = AimManager(self)
        self.trend_manager = TrendManager(self)
        self.view_manager = ViewManager(self)
        self.manual_manager = ManualManager(self)

        self.chart_objects = {'phase_obj': [],
                              'aim_obj': [],
                              'legend_obj': []
                              }

        # Object styles
        self.default_phase_item = self.data_manager.user_preferences['phase_style']
        self.default_aim_item = self.data_manager.user_preferences['aim_style']
        self.default_trend_corr_item = self.data_manager.user_preferences['trend_corr_style']
        self.default_trend_err_item = self.data_manager.user_preferences['trend_err_style']
        self.default_trend_misc_item = self.data_manager.user_preferences['trend_misc_style']

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

        self.new_chart(start_date=pd.to_datetime('today').normalize())

        # Other managers for which self.ax is expected to be defined
        self.note_manager = NoteManager(self)
        self.hover_manager = Hover(self)

    def init_state(self, start_date=None):
        # Close any previously created figure
        if hasattr(self, 'figure') and self.figure:
            plt.close(self.figure)

        # Select chart type
        chart_type = self.data_manager.chart_data['type']
        chart_width = self.data_manager.user_preferences['width']
        chart_font_color = self.data_manager.user_preferences['chart_font_color']
        chart_grid_color = self.data_manager.user_preferences['chart_grid_color']

        self.credit_lines_space = self.data_manager.chart_data['view']['chart']['credit']

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

        # Add celeration fan
        self.fan_ax = self.Chart.add_cel_fan(chart_type, div_decrease=self.data_manager.user_preferences['div_deceleration'])

        self.figure, self.ax = self.Chart.get_figure()
        self.x_to_date = {v: k for k, v in self.Chart.date_to_pos.items()}
        self.credit_lines_object = None

        if self.fig_init:
            self.replot()
        else:
            self.fig_init = True
            self.event_bus.emit('view_update_credit_lines')
            self.Chart.floor_grid_lines(False)

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

    def replot(self):
        self.data_manager.plot_columns = {}  # Clear dict
        if not self.data_manager.df_raw.empty:
            column_map = self.data_manager.chart_data['column_map']
            all_view_settings = self.data_manager.chart_data['view']
            if column_map:
                for sys_col, user_col in column_map.items():
                    if sys_col != 'd':
                        view_key = f'{sys_col}|{user_col}'
                        view_settings = all_view_settings[view_key] if view_key in all_view_settings.keys() else None
                        data_point_column = DataPointColumn(ax=self.ax,
                                                            date_to_x=self.Chart.date_to_pos,
                                                            x_to_day_count=self.Chart.x_to_day_count,
                                                            sys_col=sys_col,
                                                            user_col=user_col,
                                                            view_settings=view_settings)
                        self.data_manager.plot_columns[user_col] = data_point_column
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
        self.event_bus.emit('refresh_view_dropdown')
        self.event_bus.emit('sync_data_checkboxes')
        self.event_bus.emit('sync_grid_checkboxes')
        self.event_bus.emit('sync_misc_checkboxes')
        self.event_bus.emit('apply_all_grid_settings')
        self.event_bus.emit('apply_all_misc_settings')
        self.event_bus.emit('refresh_chart')

    def replot_chart_objects(self):
        for phase in self.data_manager.chart_data['phase']:
            self.phase_replot(phase)

        for aim in self.data_manager.chart_data['aim']:
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

            # Set y text position:
            ymin = self.Chart.ymin
            ymax = self.Chart.ymax
            if phase['text_position'] == 'Top':
                y_text_pos = ymax / 3
            elif phase['text_position'] == 'Center':
                y_text_pos = (ymin * ymax) ** 0.5
            elif phase['text_position'] == 'Bottom':
                y_text_pos = ymin * 2

            phase_line = self.ax.vlines(x_i,
                                        ymax=ymax,
                                        ymin=0,
                                        color=phase['line_color'],
                                        linestyle=phase['linestyle'],
                                        linewidth=phase['linewidth'])

            # Add phase line text
            if phase['text_mode'] == 'Flag':
                bbox = {'facecolor': phase['bg_color'], 'edgecolor': phase['edge_color'], 'linestyle': '-', 'linewidth': 1.5}
                va = 'bottom'
                rotation = 0
            elif phase['text_mode'] == 'Banner':
                bbox = None
                va = phase['text_position'].lower()
                rotation = 90

            phase_text = self.ax.text(x_i + 1,
                                      y_text_pos,
                                      phase['text'],
                                      ha="left",
                                      va=va,
                                      rotation=rotation,
                                      fontsize=phase['font_size'],
                                      color=phase['font_color'])

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
        self.data_manager.chart_data['start_date'] = self.Chart.start_date

    def safe_float_convert(self, input):
        return self.manual_manager.safe_float_convert(input)

    def phase_line_from_form(self, text, date):
        self.phase_manager.phase_line_from_form(text, date)

    def phase_line_handle_click(self, event, text):
        return self.phase_manager.phase_line_handle_click(event, text)

    def phase_undo_line(self):
        self.phase_manager.phase_undo_line()

    def phase_cleanup_temp_line(self):
        self.phase_manager.phase_cleanup_temp_line()

    def point_on_click(self, event):
        self.manual_manager.point_on_click(event)

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_manager.plot_trend_temp_first_marker(x_i)

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_manager.plot_trend_temp_second_marker(x_i)

    def trend_move_temp_marker(self, direction):
        self.trend_manager.trend_move_temp_marker(direction)

    def trend_move_temp_est_with_arrows(self, direction):
        self.trend_manager.trend_move_temp_est_with_arrows(direction)

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

    def aim_click_info(self, event, note):
        return self.aim_manager.aim_click_info(event, note)

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


class PhaseManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = EventBus()
        self.temp_phase_line = None
        self.temp_phase_line_text = None
        self.y_text_pos = None

    def phase_line_from_form(self, text, date):
        date = pd.to_datetime(date, format='%d-%m-%Y')

        date = self.figure_manager.data_manager.find_closest_date(date, self.figure_manager.Chart.date_to_pos)
        if date:
            if self.temp_phase_line and self.temp_phase_line_text:
                self.temp_phase_line.remove()
                self.temp_phase_line_text.remove()
                self.temp_phase_line = None
                self.temp_phase_line_text = None

            phase = copy.deepcopy(self.figure_manager.data_manager.user_preferences['phase_style'])
            phase['text_mode'] = self.figure_manager.data_manager.user_preferences['phase_text_type']
            phase['text_position'] = self.figure_manager.data_manager.user_preferences['phase_text_position']
            phase['date'] = date
            phase['text'] = text

            self.figure_manager.phase_replot(phase)

            # Save phase data
            self.figure_manager.data_manager.save_plot_item(item=phase, item_type='phase')
            self.event_bus.emit('refresh_chart')

    def phase_line_handle_click(self, event, text):

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

                phase_text_type = self.figure_manager.data_manager.user_preferences['phase_text_type']
                phase_text_position = self.figure_manager.data_manager.user_preferences['phase_text_position']

                # Set y text position:
                ymin = self.figure_manager.Chart.ymin
                ymax = self.figure_manager.Chart.ymax
                if phase_text_position == 'Top':
                    self.y_text_pos = ymax / 3
                elif phase_text_position == 'Center':
                    self.y_text_pos = (ymin * ymax) ** 0.5
                elif phase_text_position == 'Bottom':
                    self.y_text_pos = ymin * 2

                # Draw temporary phase line
                self.temp_phase_line = self.figure_manager.ax.vlines(x, ymax=ymax, ymin=0, color='magenta', linestyle="--", linewidth=1.5)

                if phase_text_type == 'Flag':
                    bbox = {'facecolor': 'white', 'edgecolor': 'magenta', 'linestyle': '--', 'linewidth': 1.5}
                    va = 'bottom'
                    rotation = 0
                elif phase_text_type == 'Banner':
                    bbox = None
                    va = phase_text_position.lower()
                    rotation = 90

                self.temp_phase_line_text = self.figure_manager.ax.text(x + 1,
                                                                        self.y_text_pos,
                                                                        text,
                                                                        ha="left",
                                                                        va=va,
                                                                        rotation=rotation,
                                                                        fontsize=self.figure_manager.data_manager.user_preferences['phase_style']['font_size'])

                self.event_bus.emit('refresh_chart')

                return x, y

    def phase_undo_line(self):
        if self.figure_manager.chart_objects['phase_obj']:
            self.figure_manager.data_manager.chart_data['phase'].pop()
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

            aim = copy.deepcopy(self.figure_manager.data_manager.user_preferences['aim_style'])
            aim['date1'] = xmin_date
            aim['date2'] = xmax_date
            aim['y'] = target
            aim['text'] = text
            aim['text_pos'] = self.figure_manager.data_manager.user_preferences['aim_text_position']
            aim['baseline'] = None if baseline == '' else baseline
            aim['line_type'] = self.figure_manager.data_manager.user_preferences["aim_line_type"]

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
            self.figure_manager.data_manager.chart_data['aim'].pop()
            line, note = self.figure_manager.chart_objects['aim_obj'].pop()
            line.remove()
            note.remove()
            self.event_bus.emit('refresh_chart')

    def aim_get_text_pos(self, xmin, xmax, text_pos=None):
        if text_pos is None:
            text_pos = self.figure_manager.data_manager.user_preferences['aim_text_position']

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
        text_mode = self.figure_manager.data_manager.user_preferences['aim_line_type']
        font_size = copy.deepcopy(self.figure_manager.data_manager.user_preferences['aim_style']['font_size'])
        if text_mode == 'Flat':
            text_x, ha = self.aim_get_text_pos(xmin, xmax)
            self.aim_temp_line = self.figure_manager.ax.hlines(xmin=xmin, xmax=xmax, y=self.aim_first_click_y, colors="magenta", linewidth=1.5, linestyle="--")
            self.aim_temp_note = self.figure_manager.ax.text(text_x, self.aim_first_click_y * 1.2, note, ha=ha, fontsize=font_size, color='magenta')
        else:
            if xmax > xmin:
                self.aim_temp_line, = self.figure_manager.ax.plot([xmin, xmax], [self.aim_first_click_y, self.aim_second_click_y], color='magenta', linewidth=1.5, linestyle='--')
                text_pos = self.figure_manager.data_manager.user_preferences['aim_text_position']
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

    def aim_click_info(self, event, note):
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
        self.trend_temp_est = None
        # self.trend_temp_line = None
        self.upper_bounce_temp_line = None
        self.lower_bounce_temp_line = None
        self.trend_temp_fit_on = False
        self.trend_elements = None
        self.trend_data = None

        # Event bus subscriptions
        self.event_bus.subscribe('plot_cel_trend_temp', self.plot_cel_trend_temp, has_data=True)
        self.event_bus.subscribe('trend_on_click', self.trend_on_click, has_data=True)
        self.event_bus.subscribe('trend_cleanup', self.trend_cleanup)
        self.event_bus.subscribe('trend_finalize', self.trend_finalize)

    def trend_on_click(self, event):
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

            if self.trend_temp_fit_on:
                if event.ydata is not None:
                    y = event.ydata
                    self.trend_temp_est.set_position((x, y))
                    self.event_bus.emit('refresh_chart')
            else:
                if self.trend_first_click_x is not None and self.trend_second_click_x is None:
                    self.plot_trend_temp_first_marker(self.trend_first_click_x)
                elif self.trend_second_click_x is not None:
                    self.plot_trend_temp_second_marker(self.trend_second_click_x)

    def plot_cel_trend_temp(self, temp):
        if self.trend_temp_first_marker and self.trend_temp_second_marker and not self.trend_temp_fit_on:
            user_col = self.event_bus.emit('get_current_trend_column')
            col_instance = self.figure_manager.data_manager.plot_columns[user_col]
            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]
            date1 = self.figure_manager.x_to_date[x1]
            date2 = self.figure_manager.x_to_date[x2]
            fit_method = self.figure_manager.data_manager.user_preferences['fit_method']
            forecast = self.figure_manager.data_manager.user_preferences['forward_projection']
            bounce_envelope = self.figure_manager.data_manager.user_preferences['bounce_envelope']

            result = col_instance.plot_cel_trend(date1, date2, fit_method, forecast, bounce_envelope, temp)
            if result:
                self.trend_elements, self.trend_data = result
                self.trend_temp_fit_on = True
                self.trend_temp_est = self.trend_elements['cel_label']

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
        self.trend_temp_second_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.event_bus.emit('refresh_chart')

    def trend_move_temp_marker(self, direction):
        if not self.trend_temp_est:
            if self.trend_current_temp_marker == 'first':
                x = self.trend_temp_first_marker.get_xdata()[0]
                if direction == 'right':
                    x += 1
                    if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                        x += 1
                elif direction == 'left':
                    x -= 1
                    if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                        x -= 1

                if x < self.figure_manager.Chart.xmin:
                    x = self.figure_manager.Chart.xmin
                elif x > self.figure_manager.Chart.xmax - 1:
                    x = self.figure_manager.Chart.xmax - 1

                self.trend_temp_first_marker.set_xdata([x])

            elif self.trend_current_temp_marker == 'second':
                x = self.trend_temp_second_marker.get_xdata()[0]
                if direction == 'right':
                    x += 1
                    if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                        x += 1
                elif direction == 'left':
                    x -= 1
                    if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                        x -= 1

                if x < self.figure_manager.Chart.xmin:
                    x = self.figure_manager.Chart.xmin
                elif x > self.figure_manager.Chart.xmax - 1:
                    x = self.figure_manager.Chart.xmax - 1

                self.trend_temp_second_marker.set_xdata([x])

            self.event_bus.emit('refresh_chart')

    def trend_move_temp_est_with_arrows(self, direction):
        if self.trend_temp_est:
            x, y = self.trend_temp_est.get_position()

            if direction == 'right':
                x += 1
                if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                    x += 1
            elif direction == 'left':
                x -= 1
                if x not in self.figure_manager.Chart.date_to_pos.values():  # Handling for Weekly
                    x -= 1
            elif direction == 'up':
                y *= 1.1
            elif direction == 'down':
                y *= 0.9

            self.trend_temp_est.set_position((x, y))
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

    def trend_undo(self, corr):
        if corr:
            data, trend_obj, bounce_obj, est_obj = 'trend_corr', 'trend_corr_obj', 'trend_corr_bounce_obj', 'trend_corr_est_obj'
        else:
            data, trend_obj, bounce_obj, est_obj = 'trend_err', 'trend_err_obj', 'trend_err_bounce_obj', 'trend_err_est_obj'

        if self.figure_manager.chart_objects[trend_obj] and self.figure_manager.data_manager.chart_data[data]:
            self.figure_manager.data_manager.chart_data[data].pop()
            line = self.figure_manager.chart_objects[trend_obj].pop()
            line.remove()

            if self.figure_manager.chart_objects[est_obj]:
                est = self.figure_manager.chart_objects[est_obj].pop()
                est.remove()

            if self.figure_manager.chart_objects[bounce_obj]:
                upper, lower = self.figure_manager.chart_objects[bounce_obj].pop()
                upper.remove()
                lower.remove()

            self.event_bus.emit('refresh_chart')

        self.trend_cleanup()

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
                    new_text = Text(original.get_position()[0], original.get_position()[1],
                                    original.get_text(), color=self.trend_data['line_color'],
                                    rotation=original.get_rotation(),
                                    verticalalignment=original.get_verticalalignment(),
                                    horizontalalignment=original.get_horizontalalignment(),
                                    clip_on=False,
                                    transform=self.figure_manager.ax.transData,
                                    fontweight=original.get_weight()
                                    )
                    new_trend_elements[name] = new_text
                    self.figure_manager.ax.add_artist(new_text)

            # Revise cel label position
            est_x, est_y = self.trend_temp_est.get_position()
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
        if self.upper_bounce_temp_line:
            self.upper_bounce_temp_line.remove()
        if self.lower_bounce_temp_line:
            self.lower_bounce_temp_line.remove()
        self.trend_temp_est = None
        self.upper_bounce_temp_line = None
        self.lower_bounce_temp_line = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
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

    def create_legend(self):
        columns = self.figure_manager.data_manager.plot_columns
        handles, labels = [], []
        if columns:
            for user_col, column in columns.items():
                legend = column.get_legend()  # Returns  None if df_agg is empty
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

        legend = self.figure_manager.ax.legend(handles, labels, loc='upper right', framealpha=1)
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
            self.figure_manager.data_manager.chart_data['view']['chart']['legend'] = bool(show)
            for legend in self.figure_manager.chart_objects['legend_obj']:
                legend.set_visible(show)
            if refresh:
                self.event_bus.emit('refresh_chart')

    def apply_all_grid_settings(self):
        chart_data = self.figure_manager.data_manager.chart_data
        self.view_minor_gridlines(chart_data['view']['chart']['minor_grid'], False)
        self.view_major_date_gridlines(chart_data['view']['chart']['major_grid_dates'], False)
        self.view_major_count_gridlines(chart_data['view']['chart']['major_grid_counts'], False)
        self.view_floor_grid(chart_data['view']['chart']['floor_grid'], False)

    def apply_all_misc_settings(self):
        chart_data = self.figure_manager.data_manager.chart_data
        self.view_phase_lines_toggle(chart_data['view']['chart']['phase'], False)
        self.view_aims_toggle(chart_data['view']['chart']['aims'], False)
        self.view_cel_fan_toggle(chart_data['view']['chart']['cel_fan'], False)
        self.view_credit_lines_toggle(chart_data['view']['chart']['credit'], False)
        self.view_legend_toggle(chart_data['view']['chart']['legend'], False)

    def view_minor_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.minor_grid_lines(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['minor_grid'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_major_date_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.major_grid_dates(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['major_grid_dates'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_major_count_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.major_grid_counts(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['major_grid_counts'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_floor_grid(self, show, refresh=True):
        self.figure_manager.Chart.floor_grid_lines(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['floor_grid'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_aims_toggle(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['aim_obj']:
            if pair:
                line, text = pair
                line.set_visible(show)
                text.set_visible(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['aims'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_phase_lines_toggle(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['phase_obj']:
            if pair:
                line, text = pair
                line.set_visible(show)
                text.set_visible(show)
        self.figure_manager.data_manager.chart_data['view']['chart']['phase'] = bool(show)
        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_cel_fan_toggle(self, status, refresh=True):
        self.figure_manager.fan_ax.set_visible(status)
        self.figure_manager.data_manager.chart_data['view']['chart']['cel_fan'] = bool(status)

        # Adjust right y-label if dealing with a minute chart
        chart_type = self.figure_manager.data_manager.chart_data['type']
        if 'Minute' in chart_type:
            if status:
                self.figure_manager.Chart.ax.yaxis.set_label_coords(-0.1, 0.7)
            else:
                self.figure_manager.Chart.ax.yaxis.set_label_coords(-0.1, 0.5)

        if refresh:
            self.event_bus.emit('refresh_chart')

    def view_credit_lines_toggle(self, status, refresh=True):
        self.figure_manager.data_manager.chart_data['view']['chart']['credit'] = bool(status)
        if self.figure_manager.credit_lines_object:
            self.figure_manager.credit_lines_object.set_visible(status)
            if refresh:
                self.event_bus.emit('refresh_chart')

    def view_update_credit_lines(self):
        if self.figure_manager.credit_lines_object:
            self.figure_manager.credit_lines_object.remove()

        rows = self.figure_manager.data_manager.chart_data['credit']
        if rows:
            r1, r2 = rows
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
                va='center'
            )
            self.figure_manager.data_manager.chart_data['credit'] = (r1, r2)


class ManualManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.event_bus = EventBus()
        # Control variables
        self.point_temp_first_marker = None
        self.point_temp_second_marker = None
        self.point_current_temp_marker = None
        self.point_first_click_x = None
        self.point_second_click_x = None

        # Event bus subscriptions
        self.event_bus.subscribe('update_point_styles', self.update_point_styles, has_data=True)
        self.event_bus.subscribe('apply_styles', self.apply_styles)
        self.event_bus.subscribe('style_cleanup', self.manual_cleanup)

    def apply_styles(self):
        data_point_styles = self.figure_manager.data_manager.chart_data['data_point_styles']
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
            chart_data = self.figure_manager.data_manager.chart_data

            # Get slice boundaries
            x1 = self.point_temp_first_marker.get_xdata()[0] if self.point_temp_first_marker else 0
            x2 = self.point_temp_second_marker.get_xdata()[0] if self.point_temp_second_marker else max(x_to_date.keys())

            # Get start and end
            date_start = pd.to_datetime(x_to_date[min(x1, x2)])
            date_end = pd.to_datetime(x_to_date[max(x1, x2)])

            mask = (df['d'] >= date_start) & (df['d'] <= date_end)
            df.loc[mask, style_cat] = style_val

            col_instance.update_style()

            self.event_bus.emit('refresh_chart')

            # Save style configuration
            date_string_format = self.figure_manager.data_manager.standard_date_string
            date1 = date_start.strftime(date_string_format)
            date2 = date_end.strftime(date_string_format)

            data_point_styles = chart_data['data_point_styles']
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

    def point_on_click(self, event):
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
        all_notes = self.figure_manager.data_manager.chart_data['notes']
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
        chart_type = self.figure_manager.data_manager.chart_data['type'].lower()

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
                if y.size > 20:
                    y = [np.median(y)]
            else:
                y = [0]

            # Apply rounding to y values for display
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

        chart_type = self.figure_manager.data_manager.chart_data['type'].lower()
        return date, day, month, year, chart_type

    def _format_data_label(self, day, month, year, x, y, values, values_total, visibility, user_cols, sys_cols):
        data_parts = []

        for val, val_tot, show, user_col, sys_col in zip(values, values_total, visibility, user_cols, sys_cols):
            if show:
                median = np.median(val)
                if isinstance(val, float):
                    value = self.figure_manager.data_manager.format_y_value(1 / median)
                else:
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
            y_ann = 0.5 if 'minute' in self.figure_manager.data_manager.chart_data['type'].lower() else 0.22

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
        all_notes = self.figure_manager.data_manager.chart_data['notes']

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
        for note in self.figure_manager.data_manager.chart_data['notes']:
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


