import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QWidget, QVBoxLayout
import scc
from DataManager import DataManager
import pickle
import copy


class FigureManager(QWidget):
    def __init__(self, parent=None):
        super(FigureManager, self).__init__(parent)
        self.main_app = parent  # Assuming parent is an instance of ChartApp
        self.data_manager = DataManager()
        self.fig_init = False  # Control variable for replot

        self.chart_objects = {'corr_obj': None,
                              'err_obj': None,
                              'floor_obj': None,
                              'phase_obj': [],
                              'aim_obj': [],
                              'trend_corr_obj': [],
                              'trend_err_obj': [],
                              }

        # Ensure the figure and layout are correctly initialized
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()  # Properly initialize the layout
        self.setLayout(self.layout)  # Set the layout for this widget
        self.layout.addWidget(self.canvas)  # Add the canvas to the layout

        self.new_chart(start_date=pd.to_datetime('today'))

    def init_state(self, start_date=None):
        self.Chart = scc.Daily(floor_grid_on=True, start_date=start_date)
        self.figure, self.ax = self.Chart.get_figure()
        self.x_to_date = {v: k for k, v in self.Chart.date_to_pos.items()}
        self.credit_lines_object = None

        if self.fig_init:
            self.replot()
        else:
            self.fig_init = True
            # Enable default credit lines
            rows = self.data_manager.chart_data['credit']
            r1, r2, r3 = rows
            self.view_update_credit_lines(r1, r2, r3)
            self.Chart.floor_grid_lines(False)

        # Control variables
        self.temp_point = None
        self.point_type = True  # Dots if True, else X
        self.temp_phase_line = None
        self.temp_phase_line_text = None
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_current_temp_marker = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_temp_est = None
        self.trend_temp_line = None
        self.aim_first_click_x = None
        self.aim_second_click_x = None
        self.aim_y = None
        self.aim_temp_line = None
        self.aim_temp_note = None
        self.aim_first_click_indicator = None
        self.dpi = 200

    def setup_layout(self):
        # Clear existing canvas if it exists
        if hasattr(self, 'canvas'):
            self.layout.removeWidget(self.canvas)
            self.canvas.deleteLater()
            self.canvas = None

        # Create a new canvas and add it to the layout
        self.canvas = FigureCanvas(self.figure)
        if not hasattr(self, 'layout'):
            self.layout = QVBoxLayout()
            self.setLayout(self.layout)

        self.layout.addWidget(self.canvas)

        fig_width, fig_height = self.figure.get_size_inches()
        dpi = self.figure.get_dpi()
        self.canvas.setFixedSize(int(fig_width * dpi), int(fig_height * dpi))

        self.canvas.draw()  # Draw the initial state of the figure

    def replot(self):

        # Reset graph objects
        self.chart_objects = {'corr_obj': None,
                              'err_obj': None,
                              'floor_obj': None,
                              'phase_obj': [],
                              'aim_obj': [],
                              'trend_corr_obj': [],
                              'trend_err_obj': [],
                              }

        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
        self.plot_corr_points(x, y)

        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='i')
        self.plot_err_points(x, y)

        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='m')
        self.plot_floor_points(x, y)

        lines = self.data_manager.get_replot_phase(self.Chart.date_to_pos)
        for phase in lines:
            x, y, text = phase
            self.plot_phase_line(x, y, text)

        all_aims = self.data_manager.get_replot_aims(self.Chart.date_to_pos)
        for aim in all_aims:
            xmin, xmax, target, note = aim
            self.plot_aim_line(xmin, xmax, target, note)

        # Add trendlines if any
        for trend_type in [('trend_corr', True, 'green'), ('trend_err', False, 'red')]:
            key, kind, color = trend_type
            for dates in self.data_manager.chart_data[key]:
                x1_date, x2_date, est_date, est_y = dates
                if all(date in self.Chart.date_to_pos for date in [x1_date, x2_date]):
                    x1 = self.Chart.date_to_pos[x1_date]
                    x2 = self.Chart.date_to_pos[x2_date]
                    result = self.data_manager.get_trend(x1, x2, kind, self.Chart.date_to_pos)
                    if result:
                        x_slice, trend_vals, trend_est, x_slice_mean, trend_vals_mean = result
                        self.plot_trend_line(x_slice, trend_vals, color)
                        if est_date in self.Chart.date_to_pos.keys():
                            est_x = self.Chart.date_to_pos[est_date]
                            self.plot_trend_est(est_x, est_y, trend_est, color, adjust=1)
                        else:
                            self.plot_trend_est(x_slice_mean, trend_vals_mean, trend_est, color)
                        self.chart_objects[key + '_obj'].append((self.trend_temp_line, self.trend_temp_est))

        # # Add credit lines if any
        rows = self.data_manager.chart_data['credit']
        if rows:
            r1, r2, r3 = rows
            self.view_update_credit_lines(r1, r2, r3)

        # Enable view configurations
        if self.main_app:
            self.main_app.sync_view_settings()

    def plot_corr_points(self, x, y):
        # Assumes x are integers
        color = self.data_manager.chart_data['view_check']['dot_color']
        line = '-' if self.data_manager.chart_data['view_check']['dot_lines'] else ''
        corr_points = self.ax.plot(x, y, color=color, marker='o', linewidth=0.5, markersize=3, linestyle=line)
        if self.chart_objects['corr_obj']:
            self.chart_objects['corr_obj'].remove()
        self.chart_objects['corr_obj'] = corr_points[0]

    def plot_err_points(self, x, y):
        # Assumes x are integers
        color = self.data_manager.chart_data['view_check']['x_color']
        line = '-' if self.data_manager.chart_data['view_check']['x_lines'] else ''
        err_points = self.ax.plot(x, y, color=color, marker='x', linewidth=0.5, markersize=5.5, linestyle=line)
        if self.chart_objects['err_obj']:
            self.chart_objects['err_obj'].remove()
        self.chart_objects['err_obj'] = err_points[0]

    def plot_floor_points(self, x, y):
        # Assumes x are integers
        floor_points = self.ax.plot(x, y, linestyle="", color="black", marker="_", markersize=3, markeredgewidth=1.5)
        if self.chart_objects['floor_obj']:
            self.chart_objects['floor_obj'].remove()
        self.chart_objects['floor_obj'] = floor_points[0]

    def plot_phase_line(self, x_i, y_i, text):
        # Re-map to integers if x are dates
        if isinstance(x_i, pd.Timestamp):
            x_i = self.Chart.date_to_pos[x_i]

        phase_line = self.ax.vlines(x_i, ymax=y_i, ymin=0, color="k", linestyle="-", linewidth=1)
        phase_text = self.ax.text(x_i, y_i, text, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom")
        self.chart_objects['phase_obj'].append((phase_line, phase_text))

    def plot_aim_line(self, xmin, xmax, target, note):
        # Re-map to integers if x are dates
        if isinstance(xmin, pd.Timestamp):
            xmin = self.Chart.date_to_pos[xmin]
            xmax = self.Chart.date_to_pos[xmax]

        aim_line = self.ax.hlines(xmin=xmin, xmax=xmax, y=target, colors="black", linewidth=1, linestyle="-")
        aim_note = self.ax.text(xmax, target, note, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=8)
        self.chart_objects['aim_obj'].append((aim_line, aim_note))

    def refresh(self):
        self.canvas.draw()

    def new_chart(self, start_date):
        self.init_state(start_date=start_date)
        self.setup_layout()

    def safe_float_convert(self, input):
        try:
            return float(input)
        except ValueError:
            return 0.0

    def manual_plot_from_form(self, count, hour, min_, sec, date):
        count = self.safe_float_convert(count)
        hour = self.safe_float_convert(hour)
        min_ = self.safe_float_convert(min_)
        sec = self.safe_float_convert(sec)

        # Plot data point
        date = pd.to_datetime(date, format='%d-%m-%Y')
        total_minutes = hour * 60 + min_ + sec / 60
        if date in self.Chart.date_to_pos.keys() and total_minutes > 0:
            self.data_manager.update_dataframe(date, total_minutes, count, self.point_type)

            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
            self.plot_corr_points(x, y)

            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='i')
            self.plot_err_points(x, y)

            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='m')
            self.plot_floor_points(x, y)

            self.refresh()

    def manual_undo_point(self):
        df = self.data_manager.chart_data['raw_df']
        if not df.empty:
            # Pop the latest row
            self.data_manager.chart_data['raw_df'] = df[:-1]

            # Get new plot objects
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
            self.plot_corr_points(x, y)
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='i')
            self.plot_err_points(x, y)
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='m')
            self.plot_floor_points(x, y)

            self.refresh()

    def phase_line_from_form(self, y, text, date):
        try:
            y = float(y)
            date = pd.to_datetime(date, format='%d-%m-%Y')
            if date in self.Chart.date_to_pos.keys():
                x = self.Chart.date_to_pos[pd.to_datetime(date, format='%d-%m-%Y')]

                if self.temp_phase_line and self.temp_phase_line_text:
                    self.temp_phase_line.remove()
                    self.temp_phase_line_text.remove()
                    self.temp_phase_line = None
                    self.temp_phase_line_text = None

                phase_line = self.ax.vlines(x, ymax=y, ymin=0, color="k", linestyle="-", linewidth=1)
                phase_text = self.ax.text(x, y, text, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=8)
                self.data_manager.chart_data['phase'].append((date, y, text))
                self.chart_objects['phase_obj'].append((phase_line, phase_text))

                self.refresh()

        except ValueError:
            pass

    def phase_line_handle_click(self, event, text):
        if event.inaxes:
            if event.inaxes is not None:  # In case user clicks outside coordinate system
                x, y = int(event.xdata), round(event.ydata, 4)

                if self.temp_phase_line and self.temp_phase_line_text:
                    self.temp_phase_line.remove()
                    self.temp_phase_line_text.remove()
                    self.temp_phase_line = None
                    self.temp_phase_line_text = None

                self.temp_phase_line = self.ax.vlines(x, ymax=y, ymin=0, color='magenta', linestyle="--", linewidth=1)
                self.temp_phase_line_text = self.ax.text(x, y, text, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=8)
                self.refresh()

                return x, y

    def phase_undo_line(self):
        if self.chart_objects['phase_obj']:
            self.data_manager.chart_data['phase'].pop()
            line, text = self.chart_objects['phase_obj'].pop()
            line.remove()
            text.remove()
            self.refresh()

    def phase_cleanup_temp_line(self):
        if self.temp_phase_line and self.temp_phase_line_text:
            self.temp_phase_line.remove()
            self.temp_phase_line_text.remove()
            self.temp_phase_line = None
            self.temp_phase_line_text = None
        self.refresh()

    def view_minor_gridlines(self, show, refresh=True):
        self.Chart.minor_grid_lines(show)
        self.data_manager.update_view_check('minor_grid', show)
        if refresh:
            self.refresh()

    def view_major_gridlines(self, show, refresh=True):
        self.Chart.major_grid_lines(show)
        self.data_manager.update_view_check('major_grid', show)
        if refresh:
            self.refresh()

    def view_dots(self, show, refresh=True):
        if self.chart_objects['corr_obj']:
            self.chart_objects['corr_obj'].set_visible(show)
        self.data_manager.update_view_check('dots', show)
        if refresh:
            self.refresh()

    def view_xs(self, show, refresh=True):
        if self.chart_objects['err_obj']:
            self.chart_objects['err_obj'].set_visible(show)
        self.data_manager.update_view_check('xs', show)
        if refresh:
            self.refresh()

    def view_floor(self, show, refresh=True):
        if self.chart_objects['floor_obj']:
            self.chart_objects['floor_obj'].set_visible(show)
        self.data_manager.update_view_check('timing_floor', show)
        if refresh:
            self.refresh()

    def view_floor_grid(self, show, refresh=True):
        self.Chart.floor_grid_lines(show)
        self.data_manager.update_view_check('timing_grid', show)
        if refresh:
            self.refresh()

    def view_aims(self, show, refresh=True):
        for pair in self.chart_objects['aim_obj']:
            line, text = pair
            line.set_visible(show)
            text.set_visible(show)
        self.data_manager.update_view_check('aims', show)
        if refresh:
            self.refresh()

    def view_phase_lines(self, show, refresh=True):
        for pair in self.chart_objects['phase_obj']:
            line, text = pair
            line.set_visible(show)
            text.set_visible(show)
        self.data_manager.update_view_check('phase_lines', show)
        if refresh:
            self.refresh()

    def view_dot_trend(self, show, refresh=True):
        for pair in self.chart_objects['trend_corr_obj']:
            est, line = pair
            est.set_visible(show)
            line.set_visible(show)
        self.data_manager.update_view_check('dot_trends', show)
        if refresh:
            self.refresh()

    def view_x_trend(self, show, refresh=True):
        for pair in self.chart_objects['trend_err_obj']:
            est, line = pair
            est.set_visible(show)
            line.set_visible(show)
        self.data_manager.update_view_check('x_trends', show)
        if refresh:
            self.refresh()

    def view_dot_lines(self, show, refresh=True):
        lines = '-' if show else ''
        if self.chart_objects['corr_obj']:
            self.chart_objects['corr_obj'].set_linestyle(lines)
        self.data_manager.update_view_check('dot_lines', show)
        if refresh:
            self.refresh()

    def view_x_lines(self, show, refresh=True):
        lines = '-' if show else ''
        if self.chart_objects['err_obj']:
            self.chart_objects['err_obj'].set_linestyle(lines)
        self.data_manager.update_view_check('x_lines', show)
        if refresh:
            self.refresh()

    def view_update_credit_lines(self, row1, row2, row3):
        # Clean up previous credit lines
        if self.credit_lines_object:
            self.credit_lines_object.remove()

        credit = row1 + '\n\n' + row2 + '\n\n' + row3
        self.credit_lines_object = self.ax.text(0, - 0.22, credit, transform=self.Chart.trans, fontsize=self.Chart.credit_fontsize, color=self.Chart.style_color, ha='left', va='center')
        self.data_manager.chart_data['credit'] = (row1, row2, row3)

        if hasattr(self, 'canvas'):
            self.refresh()

    def trend_on_click(self, event):
        if event.xdata is not None:
            x = int(event.xdata)
            if self.trend_first_click_x is None:
                self.trend_second_click_x = None
                self.trend_first_click_x = x
            elif self.trend_second_click_x is None:
                self.trend_first_click_x = None
                self.trend_second_click_x = x

    def plot_trend_line(self, x_slice, trend_vals, color):
        self.trend_temp_line, = self.ax.plot(x_slice, trend_vals, linestyle="-", linewidth=1, color=color)
        self.refresh()

    def plot_trend_est(self, x_slice_mean, trend_vals_mean, cel_est, color, adjust=2):
        self.trend_temp_est = self.ax.text(int(x_slice_mean), trend_vals_mean * adjust, cel_est, fontsize=10, color=color, ha="center", weight="bold")
        self.refresh()

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_current_temp_marker = 'first'
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        self.trend_temp_first_marker = self.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.refresh()

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_current_temp_marker = 'second'
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()
        self.trend_temp_second_marker = self.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.refresh()

    def trend_move_temp_marker(self, direction):
        if not self.trend_temp_est:

            if self.trend_current_temp_marker == 'first':
                x = self.trend_temp_first_marker.get_xdata()[0]
                if direction == 'right':
                    x += 1
                elif direction == 'left':
                    x -= 1
                self.trend_temp_first_marker.set_xdata(x)

            elif self.trend_current_temp_marker == 'second':
                x = self.trend_temp_second_marker.get_xdata()[0]
                if direction == 'right':
                    x += 1
                elif direction == 'left':
                    x -= 1
                self.trend_temp_second_marker.set_xdata(x)

            self.refresh()

    def trend_move_temp_est_with_arrows(self, direction):
        if self.trend_temp_est:
            x, y = self.trend_temp_est.get_position()

            if direction == 'right':
                x += 1
            elif direction == 'left':
                x -= 1
            elif direction == 'up':
                y *= 1.1
            elif direction == 'down':
                y *= 0.9

            self.trend_temp_est.set_position((x, y))
            self.refresh()

    def trend_fit(self, corr):
        if self.trend_temp_first_marker and self.trend_temp_second_marker:
            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]

            result = self.data_manager.get_trend(x1, x2, corr, self.Chart.date_to_pos)
            if result:
                x_slice, trend_vals, trend_est, x_slice_mean, trend_vals_mean = result
                self.plot_trend_line(x_slice, trend_vals, 'magenta')
                self.plot_trend_est(x_slice_mean, trend_vals_mean, trend_est, 'magenta')
                self.refresh()

    def trend_date1_changed(self, new_date):
        new_date = pd.to_datetime(new_date.toString('dd-MM-yyyy'), format='%d-%m-%Y')
        if new_date in self.Chart.date_to_pos.keys():
            self.trend_second_click_x = None
            if self.trend_temp_first_marker:
                self.trend_first_click_x = self.Chart.date_to_pos[new_date]
                self.trend_temp_first_marker.set_xdata(self.trend_first_click_x)
            else:
                self.trend_first_click_x = self.Chart.date_to_pos[new_date]
                self.plot_trend_temp_first_marker(self.trend_first_click_x)

        self.refresh()

    def trend_date2_changed(self, new_date):
        new_date = pd.to_datetime(new_date.toString('dd-MM-yyyy'), format='%d-%m-%Y')
        if new_date in self.Chart.date_to_pos.keys():
            self.trend_first_click_x = None
            if self.trend_temp_second_marker:
                self.trend_second_click_x = self.Chart.date_to_pos[new_date]
                self.trend_temp_second_marker.set_xdata(self.trend_second_click_x)
            else:
                self.trend_second_click_x = self.Chart.date_to_pos[new_date]
                self.plot_trend_temp_second_marker(self.trend_second_click_x)

        self.refresh()

    def trend_undo(self, corr):
        if corr:
            data, obj = 'trend_corr', 'trend_corr_obj'
        else:
            data, obj = 'trend_err', 'trend_err_obj'

        if self.chart_objects[obj] and self.data_manager.chart_data[data]:
            self.data_manager.chart_data[data].pop()
            est, line = self.chart_objects[obj].pop()
            est.remove()
            line.remove()
            self.refresh()

    def trend_finalize(self, corr):
        if self.trend_temp_line and self.trend_temp_est:

            if corr:
                data, obj, color = 'trend_corr', 'trend_corr_obj', 'green'
            else:
                data, obj, color = 'trend_err', 'trend_err_obj', 'red'

            self.trend_temp_est.set_color(color)
            self.trend_temp_line.set_color(color)

            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]
            x1_date = self.x_to_date[x1]
            x2_date = self.x_to_date[x2]

            est_x, est_y = self.trend_temp_est.get_position()
            est_date = self.x_to_date[est_x]

            # Save data
            self.chart_objects[obj].append((self.trend_temp_est, self.trend_temp_line))
            self.data_manager.chart_data[data].append((x1_date, x2_date, est_date, est_y))

            # # Reset temp trend variables
            self.trend_temp_est = None
            self.trend_temp_line = None
            self.trend_first_click_x = None
            self.trend_second_click_x = None
            self.trend_temp_first_marker.remove()
            self.trend_temp_second_marker.remove()
            self.trend_temp_first_marker = None
            self.trend_temp_second_marker  = None
            self.trend_current_temp_marker = None

            self.refresh()

    def trend_cleanup(self):
        # # Reset temp trend variables
        self.trend_temp_est = None
        self.trend_temp_line = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_current_temp_marker = None

        self.refresh()

    def aim_from_form(self, note, target, start, deadline):
        try:
            target = float(target)
        except(ValueError, TypeError):
            return

        date_format = '%d-%m-%Y'
        xmin_date = pd.to_datetime(start, format=date_format)
        xmax_date = pd.to_datetime(deadline, format=date_format)

        # Check if both dates are actually in the chart date range
        if all(key in self.Chart.date_to_pos for key in [xmin_date, xmax_date]):

            # Clean up if temp
            if self.aim_temp_line:
                self.aim_temp_line.remove()
                self.aim_temp_line = None
            if self.aim_temp_note:
                self.aim_temp_note.remove()
                self.aim_temp_note = None

            xmin = self.Chart.date_to_pos[xmin_date]
            xmax = self.Chart.date_to_pos[xmax_date]

            aim_line = self.ax.hlines(xmin=xmin, xmax=xmax, y=target, colors="black", linewidth=1, linestyle="-")
            aim_note = self.ax.text(xmax, target, note, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=8)

            self.data_manager.chart_data['aim'].append((xmin_date, xmax_date, target, note))
            self.chart_objects['aim_obj'].append((aim_line, aim_note))

            self.refresh()

    def aim_cleanup(self):
        # Reset aim control variables
        self.aim_first_click_x = None
        self.aim_second_click_x = None

        # Clean up if temp
        if self.aim_temp_line:
            self.aim_temp_line.remove()
            self.aim_temp_line = None
        if self.aim_temp_note:
            self.aim_temp_note.remove()
            self.aim_temp_note = None
        if self.aim_first_click_indicator:
            self.aim_first_click_indicator.remove()
            self.aim_first_click_indicator = None

        self.refresh()

    def aim_undo(self):
        if self.data_manager.chart_data['aim'] and self.chart_objects['aim_obj']:
            self.data_manager.chart_data['aim'].pop()
            line, note = self.chart_objects['aim_obj'].pop()
            line.remove()
            note.remove()
            self.refresh()

    def aim_click_info(self, event, note):
        if event.xdata is not None:

            # Clean up if previous temp
            if self.aim_temp_line:
                self.aim_temp_line.remove()
                self.aim_temp_line = None
            if self.aim_temp_note:
                self.aim_temp_note.remove()
                self.aim_temp_note = None

            self.aim_y = round(event.ydata, 4)
            if self.aim_first_click_x is None:
                self.aim_first_click_x = int(event.xdata)

                # Add first click indicator
                self.aim_first_click_indicator, = self.ax.plot(self.aim_first_click_x, self.aim_y, marker='o', color='magenta')

                self.refresh()
                return None

            elif self.aim_second_click_x is None:
                self.aim_second_click_x = int(event.xdata)

                xmin = min(self.aim_first_click_x, self.aim_second_click_x)
                xmax= max(self.aim_first_click_x, self.aim_second_click_x)

                self.aim_temp_line = self.ax.hlines(xmin=xmin, xmax=xmax, y=self.aim_y, colors="magenta", linewidth=1.5, linestyle="--")
                self.aim_temp_note = self.ax.text(xmax, self.aim_y, note, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=8)

                d1 = self.x_to_date[xmin]
                d2 = self.x_to_date[xmax]

                # # Reset aim control variables
                self.aim_first_click_x = None
                self.aim_second_click_x = None

                if self.aim_first_click_indicator:
                    self.aim_first_click_indicator.remove()
                    self.aim_first_click_indicator = None

                self.refresh()

                return d1, d2, self.aim_y

    def settings_test_angle(self, show):
        self.Chart.toggle_test_angle(show)
        self.refresh()

    def view_color_dots(self, color):
        new_color = '#007f00' if color else 'black'
        self.data_manager.chart_data['view_check']['dot_color'] = new_color
        dot_color = self.data_manager.chart_data['view_check']['dot_color']
        if self.chart_objects['corr_obj']:
            self.chart_objects['corr_obj'].set_color(dot_color)
        self.refresh()

    def view_color_xs(self, color):
        new_color = '#cc0000' if color else 'black'
        self.data_manager.chart_data['view_check']['x_color'] = new_color
        dot_color = self.data_manager.chart_data['view_check']['x_color']
        if self.chart_objects['err_obj']:
            self.chart_objects['err_obj'].set_color(dot_color)
        self.refresh()

    def settings_change_start_date(self, new_start_date):
        new_start_date = new_start_date.toPyDate()  # Convert to Python datetime
        new_start_date = pd.to_datetime(new_start_date)
        self.new_chart(start_date=new_start_date)

    def fig_import_data(self, file_path, date_format='%m-%d-%y'):
        self.data_manager.data_import_data(file_path, date_format)
        initial_date = self.data_manager.chart_data['raw_df']['d'].min()
        self.new_chart(start_date=initial_date)

    def back_to_default(self):
        self.data_manager.chart_data = copy.deepcopy(self.data_manager.chart_data_default)
        self.new_chart(start_date=pd.to_datetime('today'))

    def fig_save_image(self, full_path):
        plt.savefig(full_path, dpi=self.dpi)

    def fig_save_chart(self, full_path):
        # Ensure the file has a .pkl extension
        if not full_path.endswith('.pkl'):
            full_path += '.pkl'

        # Save current start date
        self.data_manager.chart_data['start_date'] = self.Chart.start_date

        with open(full_path, 'wb') as file:
            pickle.dump(self.data_manager.chart_data, file)

    def fig_load_chart(self, full_path):
        with open(full_path, 'rb') as file:
            self.data_manager.chart_data = pickle.load(file)

        # Handling for setting the start date
        start_date = self.data_manager.chart_data['start_date']
        self.new_chart(start_date=start_date)




