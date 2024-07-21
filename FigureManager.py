import matplotlib.pyplot as plt

from matplotlib.markers import MarkerStyle
import numpy as np
import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
import scc
from DataManager import DataManager
import copy
import json
import re


class FigureManager(QWidget):
    def __init__(self, parent=None):
        super(FigureManager, self).__init__(parent)
        self.main_app = parent  # Assuming parent is an instance of ChartApp
        self.data_manager = DataManager()

        self.fig_init = False  # Control variables for replot
        self.test_angle = False

        # Mode managers
        self.phase_manager = PhaseManager(self)
        self.aim_manager = AimManager(self)
        self.trend_manager = TrendManager(self)
        self.view_manager = ViewManager(self)
        self.manual_manager = ManualManager(self)

        self.chart_objects = {'corr_obj': [],
                              'err_obj': [],
                              'floor_obj': [],
                              'phase_obj': [],
                              'aim_obj': [],
                              'trend_corr_obj': [],
                              'trend_err_obj': [],
                              'trend_corr_est_obj': [],
                              'trend_err_est_obj': [],
                              'trend_corr_bounce_obj': [],
                              'trend_err_bounce_obj': []
                              }

        # Object styles
        self.default_phase_item = self.data_manager.user_preferences['phase_style']
        self.default_aim_item = self.data_manager.user_preferences['aim_style']
        self.default_trend_corr_item = self.data_manager.user_preferences['trend_corr_style']
        self.default_trend_err_item = self.data_manager.user_preferences['trend_err_style']

        # Ensure the figure and layout are correctly initialized
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.layout = QVBoxLayout()  # Properly initialize the layout
        self.setLayout(self.layout)  # Set the layout for this widget
        self.layout.addWidget(self.canvas)  # Add the canvas to the layout

        # For eval
        self.date_tuple_pattern = re.compile(r"\('(\d{4}-\d{2}-\d{2})', '(\d{4}-\d{2}-\d{2})'\)")
        self.style_tuple_pattern = re.compile(r"\('([A-Za-z_]{1,30})', '([A-Za-z_]{1,30})'\)")

        # Fonts sizes
        self.aim_font = 8
        self.phase_font = 8
        self.trend_est_font = 10

        # Data point styling control variables
        self.data_point_x1 = None
        self.data_point_x2 = None
        self.x_style_array = None

        self.new_chart(start_date=pd.to_datetime('today'))

    def init_state(self, start_date=None):

        # Close any previously created figure
        if hasattr(self, 'figure') and self.figure:
            plt.close(self.figure)

        # Select chart type
        chart_type = self.data_manager.user_preferences['chart_type']
        chart_width = self.data_manager.user_preferences['width']
        chart_font_color = self.data_manager.user_preferences['chart_font_color']
        chart_grid_color = self.data_manager.user_preferences['chart_grid_color']

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
        # Reset graph objects
        self.chart_objects = {'corr_obj': [],
                              'err_obj': [],
                              'floor_obj': [],
                              'phase_obj': [],
                              'aim_obj': [],
                              'trend_corr_obj': [],
                              'trend_err_obj': [],
                              'trend_corr_est_obj': [],
                              'trend_err_est_obj': [],
                              'trend_corr_bounce_obj': [],
                              'trend_err_bounce_obj': [],
                              }

        self.create_point_style_arrays()
        self.point_styles_replot()

        for phase in self.data_manager.chart_data['phase']:
            self.phase_replot(phase)

        for aim in self.data_manager.chart_data['aim']:
            self.aim_replot(aim)

        for trend in self.data_manager.chart_data['trend_corr']:
            self.trend_replot(trend, corr=True)

        for trend in self.data_manager.chart_data['trend_err']:
            self.trend_replot(trend, corr=False)

        # # Add credit lines if any
        rows = self.data_manager.chart_data['credit']
        if rows:
            r1, r2, r3 = rows
            self.view_update_credit_lines(r1, r2, r3)

        # Enable view configurations
        if self.main_app:
            self.main_app.sync_view_settings()

    def plot_corr_points(self, x, y):
        # Remove any previous plot and scatter objects
        for corr_obj in self.chart_objects['corr_obj']:
            corr_obj.remove()
        self.chart_objects['corr_obj'] = []

        # Plot lines without markers
        for i in range(len(x)):
            corr_points = self.ax.plot(x[i:i + 2], y[i:i + 2], linestyle=self.corr_line_styles[i], color=self.corr_line_colors[i], linewidth=self.corr_line_width[i])
            self.chart_objects['corr_obj'].append(corr_points[0])

        # Add chart markers
        corr_scatter = self.ax.scatter(x,
                                      y,
                                      zorder=2,
                                      facecolors=self.corr_face_colors,
                                        edgecolors=self.corr_edge_colors,
                                      marker='o',
                                      s=self.corr_marker_sizes)
        # Selectively set marker styles
        corr_scatter.set_paths([MarkerStyle(marker).get_path().transformed(MarkerStyle(marker).get_transform()) for marker in self.corr_markers])

        self.chart_objects['corr_obj'].append(corr_scatter)

    def create_point_style_arrays(self):
        corr_style = self.data_manager.default_corr_point_style
        err_style = self.data_manager.default_err_point_style
        floor_style = self.data_manager.default_floor_point_style

        x, _ = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
        self.x_style_array = np.array(x)

        # Set all default styles for corr
        self.corr_face_colors = np.full(x.shape, corr_style['marker_face_color'], dtype=object)
        self.corr_edge_colors = np.full(x.shape, corr_style['marker_edge_color'], dtype=object)
        self.corr_markers = np.full(x.shape, corr_style['marker'], dtype=object)
        self.corr_marker_sizes = np.full(x.shape, corr_style['markersize'], dtype=float)
        self.corr_line_styles = np.full(x.shape, corr_style['linestyle'], dtype=object)
        self.corr_line_colors = np.full(x.shape, corr_style['line_color'], dtype=object)
        self.corr_line_width = np.full(x.shape, corr_style['linewidth'], dtype=object)

        # Set all default styles for err
        self.err_face_colors = np.full(x.shape, err_style['marker_face_color'], dtype=object)
        self.err_edge_colors = np.full(x.shape, err_style['marker_edge_color'], dtype=object)
        self.err_markers = np.full(x.shape, err_style['marker'], dtype=object)
        self.err_marker_sizes = np.full(x.shape, err_style['markersize'], dtype=float)
        self.err_line_styles = np.full(x.shape, err_style['linestyle'], dtype=object)
        self.err_line_colors = np.full(x.shape, err_style['line_color'], dtype=object)
        self.err_line_width = np.full(x.shape, err_style['linewidth'], dtype=object)

        # Set all default styles for floor
        self.floor_face_colors = np.full(x.shape, floor_style['marker_face_color'], dtype=object)
        self.floor_edge_colors = np.full(x.shape, floor_style['marker_edge_color'], dtype=object)
        self.floor_markers = np.full(x.shape, floor_style['marker'], dtype=object)
        self.floor_marker_sizes = np.full(x.shape, floor_style['markersize'], dtype=float)
        self.floor_line_styles = np.full(x.shape, floor_style['linestyle'], dtype=object)
        self.floor_line_colors = np.full(x.shape, floor_style['line_color'], dtype=object)
        self.floor_line_width = np.full(x.shape, floor_style['linewidth'], dtype=object)

    def safe_eval_tuple(self, date_tuple_str):
        # Check if the string matches either of the expected patterns
        if self.date_tuple_pattern.fullmatch(date_tuple_str) or self.style_tuple_pattern.fullmatch(date_tuple_str):
            return eval(date_tuple_str)
        else:
            raise ValueError("Invalid tuple string format")

    def point_styles_replot(self):
        for date_pair_str in self.data_manager.chart_data['data_point_styles'].keys():
            date1, date2 = self.safe_eval_tuple(date_pair_str)

            d1 = pd.to_datetime(date1)
            d2 = pd.to_datetime(date2)
            if d1 in self.Chart.date_to_pos.keys() or d2 in self.Chart.date_to_pos.keys():

                # If one of the dates are outside the range
                if d1 not in self.Chart.date_to_pos.keys():
                    d1 = min(self.Chart.date_to_pos.keys())
                if d2 not in self.Chart.date_to_pos.keys():
                    d2 = max(self.Chart.date_to_pos.keys())

                x_min = self.Chart.date_to_pos[d1]
                x_max = self.Chart.date_to_pos[d2]

                # Get slice
                subset_mask = (self.x_style_array >= x_min) & (self.x_style_array <= x_max)
                subset_mask_non_inclusive = (self.x_style_array >= x_min) & (self.x_style_array < x_max)

                for tuple_str, value in self.data_manager.chart_data['data_point_styles'][date_pair_str].items():
                    point_category, input_field = self.safe_eval_tuple(tuple_str)

                    if point_category == 'Dot':
                        if input_field == 'marker_face_color':
                            self.corr_face_colors[subset_mask] = value
                        elif input_field == 'marker_edge_color':
                            self.corr_edge_colors[subset_mask] = value
                        elif input_field == 'marker':
                            self.corr_markers[subset_mask] = value
                        elif input_field == 'markersize':
                            self.corr_marker_sizes[subset_mask] = value
                        elif input_field == 'linewidth':
                            self.corr_line_width[subset_mask] = value
                        elif input_field == 'line_color':
                            self.corr_line_colors[subset_mask] = value
                        elif input_field == 'linestyle':
                            self.corr_line_styles[subset_mask_non_inclusive] = value

                    elif point_category == 'X':
                        if input_field == 'marker_face_color':
                            self.err_face_colors[subset_mask] = value
                        elif input_field == 'marker_edge_color':
                            self.err_edge_colors[subset_mask] = value
                        elif input_field == 'marker':
                            self.err_markers[subset_mask] = value
                        elif input_field == 'markersize':
                            self.err_marker_sizes[subset_mask] = value
                        elif input_field == 'linewidth':
                            self.err_line_width[subset_mask] = value
                        elif input_field == 'line_color':
                            self.err_line_colors[subset_mask] = value
                        elif input_field == 'linestyle':
                            self.err_line_styles[subset_mask_non_inclusive] = value

                    elif point_category == 'Floor':
                        if input_field == 'marker_face_color':
                            self.floor_face_colors[subset_mask] = value
                        elif input_field == 'marker_edge_color':
                            self.floor_edge_colors[subset_mask] = value
                        elif input_field == 'marker':
                            self.floor_markers[subset_mask] = value
                        elif input_field == 'markersize':
                            self.floor_marker_sizes[subset_mask] = value
                        elif input_field == 'linewidth':
                            self.floor_line_width[subset_mask] = value
                        elif input_field == 'line_color':
                            self.floor_line_colors[subset_mask] = value
                        elif input_field == 'linestyle':
                            self.floor_line_styles[subset_mask_non_inclusive] = value

        # Apply styles
        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
        if len(y) > 0:
            self.plot_corr_points(x, y)

        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='i')
        if len(y) > 0:
            self.plot_err_points(x, y)

        x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='m')
        if len(y) > 0:
            self.plot_floor_points(x, y)

    def update_point_styles(self, point_category, input_field, value):
        # Get slice boundaries
        x1 = self.data_point_x1 if self.data_point_x1 is not None else 0
        x2 = self.data_point_x2 if self.data_point_x2 is not None else max(self.Chart.date_to_pos.values())
        x_min = min(x1, x2)
        x_max = max(x1, x2)

        # Get slices
        subset_mask = (self.x_style_array >= x_min) & (self.x_style_array <= x_max)
        subset_mask_non_inclusive = (self.x_style_array >= x_min) & (self.x_style_array < x_max)

        if point_category == 'Dot':
            if input_field == 'marker_face_color':
                self.corr_face_colors[subset_mask] = value
            elif input_field == 'marker_edge_color':
                self.corr_edge_colors[subset_mask] = value
            elif input_field == 'marker':
                self.corr_markers[subset_mask] = value
            elif input_field == 'markersize':
                self.corr_marker_sizes[subset_mask] = value
            elif input_field == 'linewidth':
                self.corr_line_width[subset_mask] = value
            elif input_field == 'line_color':
                self.corr_line_colors[subset_mask] = value
            elif input_field == 'linestyle':
                self.corr_line_styles[subset_mask_non_inclusive] = value

            # Apply corr style changes
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='c')
            self.plot_corr_points(x, y)

        if point_category == 'X':
            if input_field == 'marker_face_color':
                self.err_face_colors[subset_mask] = value
            elif input_field == 'marker_edge_color':
                self.err_edge_colors[subset_mask] = value
            elif input_field == 'marker':
                self.err_markers[subset_mask] = value
            elif input_field == 'markersize':
                self.err_marker_sizes[subset_mask] = value
            elif input_field == 'linewidth':
                self.err_line_width[subset_mask] = value
            elif input_field == 'line_color':
                self.err_line_colors[subset_mask] = value
            elif input_field == 'linestyle':
                self.err_line_styles[subset_mask_non_inclusive] = value

            # Apply err style changes
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='i')
            self.plot_err_points(x, y)

        if point_category == 'Floor':
            if input_field == 'marker_face_color':
                self.floor_face_colors[subset_mask] = value
            elif input_field == 'marker_edge_color':
                self.floor_edge_colors[subset_mask] = value
            elif input_field == 'marker':
                self.floor_markers[subset_mask] = value
            elif input_field == 'markersize':
                self.floor_marker_sizes[subset_mask] = value
            elif input_field == 'linewidth':
                self.floor_line_width[subset_mask] = value
            elif input_field == 'line_color':
                self.floor_line_colors[subset_mask] = value
            elif input_field == 'linestyle':
                self.floor_line_styles[subset_mask_non_inclusive] = value

            # Apply floor style changes
            x, y = self.data_manager.get_replot_points(self.Chart.date_to_pos, kind='m')
            self.plot_floor_points(x, y)

        self.refresh()

        # Save style configuration
        date1 = self.x_to_date[x1].strftime(self.data_manager.standard_date_string)
        date2 = self.x_to_date[x2].strftime(self.data_manager.standard_date_string)
        date1_date2_str = str((date1, date2))
        point_category_input_field_str = str((point_category, input_field))
        if date1_date2_str not in self.data_manager.chart_data['data_point_styles'].keys():
            self.data_manager.chart_data['data_point_styles'][date1_date2_str] = {}
        self.data_manager.chart_data['data_point_styles'][date1_date2_str][point_category_input_field_str] = value

    def plot_err_points(self, x, y):
        # Assumes x are integers
        # Remove any previous plot and scatter objects
        for err_obj in self.chart_objects['err_obj']:
            err_obj.remove()
        self.chart_objects['err_obj'] = []

        # Plot lines without markers
        for i in range(len(x)):
            floor_points = self.ax.plot(x[i:i + 2], y[i:i + 2], linestyle=self.err_line_styles[i], color=self.err_line_colors[i], linewidth=self.err_line_width[i])
            self.chart_objects['err_obj'].append(floor_points[0])

        # Add chart markers
        edge = None if 'x' in self.err_markers else self.err_edge_colors  # Avoid edge color warnings
        err_scatter = self.ax.scatter(x,
                                      y,
                                      zorder=2,
                                      facecolors=self.err_face_colors,
                                      edgecolors=edge,
                                      marker='x',
                                      s=self.err_marker_sizes,
                                      linewidth=1)  # Marker thickness, not point lines
        # Selectively set marker styles
        err_scatter.set_paths([MarkerStyle(marker).get_path().transformed(MarkerStyle(marker).get_transform()) for marker in self.err_markers])

        self.chart_objects['err_obj'].append(err_scatter)

    def plot_floor_points(self, x, y):
        if "Minute" in self.data_manager.user_preferences['chart_type']:
            # Remove any previous plot and scatter objects
            for floor_obj in self.chart_objects['floor_obj']:
                floor_obj.remove()
            self.chart_objects['floor_obj'] = []

            # Plot lines without markers
            for i in range(len(x)):
                floor_points = self.ax.plot(x[i:i + 2], y[i:i + 2], linestyle=self.floor_line_styles[i], color=self.floor_line_colors[i], linewidth=self.floor_line_width[i])
                self.chart_objects['floor_obj'].append(floor_points[0])

            # Add chart markers
            edge = None if '_' in self.floor_markers else self.floor_edge_colors  # Avoid edge color warnings
            floor_scatter = self.ax.scatter(x,
                                          y,
                                          zorder=2,
                                          facecolors=self.floor_face_colors,
                                          edgecolors=edge,
                                          marker='_',
                                          s=self.floor_marker_sizes,
                                          linewidth=self.data_manager.default_floor_point_style['markeredgewidth'])  # Marker thickness, not point lines
            # Selectively set marker styles
            floor_scatter.set_paths([MarkerStyle(marker).get_path().transformed(MarkerStyle(marker).get_transform()) for marker in self.floor_markers])

            self.chart_objects['floor_obj'].append(floor_scatter)

    def phase_replot(self, phase):
        date = self.data_manager.find_closest_date(phase['date'], self.Chart.date_to_pos)
        if date:
            x_i = self.Chart.date_to_pos[date]

            # Set y text position:
            ymin = self.Chart.ymin
            ymax = self.Chart.ymax
            if phase['text_position'] == 'Top':
                y_text_pos = ymax / 2
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
                                      bbox=bbox,
                                      ha="left",
                                      va=va,
                                      rotation=rotation,
                                      fontsize=phase['font_size'],
                                      color=phase['font_color'])

            self.chart_objects['phase_obj'].append((phase_line, phase_text))


    def aim_replot(self, aim):
        date1 = self.data_manager.find_closest_date(aim['date1'], self.Chart.date_to_pos)
        date2 = self.data_manager.find_closest_date(aim['date2'], self.Chart.date_to_pos)
        if all(key in self.Chart.date_to_pos for key in [date1, date2]):
            xmin = self.Chart.date_to_pos[date1]
            xmax = self.Chart.date_to_pos[date2]
            y_i = float(aim['y'])

            aim_line = self.ax.hlines(xmin=xmin,
                                      xmax=xmax,
                                      y=y_i,
                                      colors=aim['line_color'],
                                      linewidth=aim['linewidth'],
                                      linestyle=aim['linestyle'])
            aim_note = self.ax.text(xmax,
                                    y_i,
                                    aim['text'],
                                    color=aim['font_color'],
                                    bbox=dict(facecolor=aim['bg_color'],
                                              edgecolor=aim['edge_color']),
                                    ha="left",
                                    va="bottom",
                                    fontsize=aim['font_size'])

            self.chart_objects['aim_obj'].append((aim_line, aim_note))

    def plot_aim_line(self, xmin, xmax, target, note):
        # Runs only on replot
        aim_line = self.ax.hlines(xmin=xmin, xmax=xmax, y=target, colors="black", linewidth=1, linestyle="-")
        aim_note = self.ax.text(xmax, target, note, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom", fontsize=self.aim_font)
        self.chart_objects['aim_obj'].append((aim_line, aim_note))

    def trend_replot(self, trend, corr=True):
        date1 = pd.to_datetime(trend['date1'])
        date2 = pd.to_datetime(trend['date2'])
        text_date = pd.to_datetime(trend['text_date'])
        if all(key in self.Chart.date_to_pos for key in [date1, date2, text_date]):
            trend_type = 'trend_corr' if corr else 'trend_err'
            xmin = self.Chart.date_to_pos[date1]
            xmax = self.Chart.date_to_pos[date2]
            xtext = self.Chart.date_to_pos[text_date]

            result = self.data_manager.get_trend(xmin, xmax, corr, self.Chart.date_to_pos, self.Chart.x_to_day_count, trend['fit_method'], trend['bounce_envelope'])
            if result:
                trend_vals, trend_est, x_slice, upper_bounce, lower_bounce, bounce_est_label = result

                trend_line, = self.ax.plot(x_slice,
                                           trend_vals,
                                           color=trend['line_color'],
                                           linewidth=trend['linewidth'],
                                           linestyle=trend['linestyle'])

                trend_est = self.ax.text(xtext,
                                         trend['text_y'],
                                         trend['text'],
                                         fontsize=trend['font_size'],
                                         color=trend['font_color'],
                                         ha="center",
                                         weight="bold")

                self.chart_objects[trend_type + '_obj'].append(trend_line)
                self.chart_objects[trend_type + '_est_obj'].append(trend_est)

                if upper_bounce is not None and lower_bounce is not None:
                    upper_bounce_line, = self.ax.plot(x_slice,
                                               upper_bounce,
                                               color=trend['line_color'],
                                               linewidth=trend['linewidth'],
                                               linestyle=trend['linestyle'])
                    lower_bounce_line, = self.ax.plot(x_slice,
                                               lower_bounce,
                                               color=trend['line_color'],
                                               linewidth=trend['linewidth'],
                                               linestyle=trend['linestyle'])

                    self.chart_objects[trend_type + '_bounce' + '_obj'].append((upper_bounce_line, lower_bounce_line))

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
                line, text = item_objects.pop(selected)
                line.remove()
                text.remove()

        self.refresh()

    def refresh(self):
        self.canvas.draw()

    def new_chart(self, start_date):
        self.init_state(start_date=start_date)
        self.setup_layout()
        # Save current start date
        self.data_manager.chart_data['start_date'] = self.Chart.start_date

    def safe_float_convert(self, input):
        return self.manual_manager.safe_float_convert(input)

    def manual_plot_form_minutes(self, count, hour, min_, sec, date):
        self.manual_manager.manual_plot_form_minutes(count, hour, min_, sec, date)

    def manual_plot_form_date(self, count, date):
        self.manual_manager.manual_plot_form_date(count, date)

    def manual_undo_point(self):
        self.manual_manager.manual_undo_point()

    def phase_line_from_form(self, text, date):
        self.phase_manager.phase_line_from_form(text, date)

    def phase_line_handle_click(self, event, text):
        return self.phase_manager.phase_line_handle_click(event, text)

    def phase_undo_line(self):
        self.phase_manager.phase_undo_line()

    def phase_cleanup_temp_line(self):
        self.phase_manager.phase_cleanup_temp_line()

    def view_minor_gridlines(self, show, refresh=True):
        self.view_manager.view_minor_gridlines(show, refresh)

    def view_major_gridlines(self, show, refresh=True):
        self.view_manager.view_major_gridlines(show, refresh)

    def view_dots(self, show, refresh=True):
        self.view_manager.view_dots(show, refresh)

    def view_xs(self, show, refresh=True):
        self.view_manager.view_xs(show, refresh)

    def view_floor(self, show, refresh=True):
        self.view_manager.view_floor(show, refresh)

    def view_floor_grid(self, show, refresh=True):
        self.view_manager.view_floor_grid(show, refresh)

    def view_aims(self, show, refresh=True):
        self.view_manager.view_aims(show, refresh)

    def view_phase_lines(self, show, refresh=True):
        self.view_manager.view_phase_lines(show, refresh)

    def view_dot_trend(self, show, refresh=True):
        self.view_manager.view_dot_trend(show, refresh)

    def view_x_trend(self, show, refresh=True):
        self.view_manager.view_x_trend(show, refresh)

    def view_dot_bounce(self, show, refresh=True):
        self.view_manager.view_dot_bounce(show, refresh)

    def view_x_bounce(self, show, refresh=True):
        self.view_manager.view_x_bounce(show, refresh)

    def view_dot_est(self, show, refresh=True):
        self.view_manager.view_dot_est(show, refresh)

    def view_x_est(self, show, refresh=True):
        self.view_manager.view_x_est(show, refresh)

    def view_update_credit_lines(self, row1, row2, row3):
        self.view_manager.view_update_credit_lines(row1, row2, row3)

    def trend_on_click(self, event):
        self.trend_manager.trend_on_click(event)

    def point_on_click(self, event):
        result = self.manual_manager.point_on_click(event)
        if result:
            x_i, num = result
            if num == 0:
                self.data_point_x1 = x_i
            else:
                self.data_point_x2 = x_i

    def plot_trend_line(self, x_slice, trend_vals, color):
        trend_line = self.trend_manager.plot_trend_line(x_slice, trend_vals, color)
        return trend_line

    def plot_trend_est(self, x_slice_mean, trend_vals_mean, cel_est, color, adjust=2):
        est_label = self.trend_manager.plot_trend_est(x_slice_mean, trend_vals_mean, cel_est, color, adjust)
        return est_label

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_manager.plot_trend_temp_first_marker(x_i)

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_manager.plot_trend_temp_second_marker(x_i)

    def trend_move_temp_marker(self, direction):
        self.trend_manager.trend_move_temp_marker(direction)

    def trend_move_temp_est_with_arrows(self, direction):
        self.trend_manager.trend_move_temp_est_with_arrows(direction)

    def trend_fit(self, corr):
        self.trend_manager.trend_fit(corr)

    def trend_date1_changed(self, new_date):
        self.trend_manager.trend_date1_changed(new_date)

    def trend_date2_changed(self, new_date):
        self.trend_manager.trend_date2_changed(new_date)

    def trend_undo(self, corr):
        self.trend_manager.trend_undo(corr)

    def trend_finalize(self, corr):
        self.trend_manager.trend_finalize(corr)

    def trend_cleanup(self):
        self.trend_manager.trend_cleanup()

    def trend_adjust_dates(self):
        result = self.trend_manager.adjust_dates()
        if result:
            date, order = result
            return date, order

    def aim_from_form(self, note, target, start, deadline):
        self.aim_manager.aim_from_form(note, target, start, deadline)

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

        self.refresh()

    def settings_change_start_date(self, new_start_date):
        self.data_manager.chart_data['start_date'] = new_start_date
        new_start_date = pd.to_datetime(new_start_date, format='%d-%m-%Y')
        self.new_chart(start_date=new_start_date)

    def settings_change_chart_width(self):
        self.new_chart(start_date=self.Chart.start_date)

    def fig_import_data(self, file_path, keep_current_start_date=False):
        self.data_manager.data_import_data(file_path)

        if keep_current_start_date:
            start_date = self.data_manager.chart_data['start_date']
        else:
            start_date = self.data_manager.chart_data['raw_df']['d'].min()

        self.new_chart(start_date=start_date)




    def back_to_default(self):
        self.data_manager.chart_data = copy.deepcopy(self.data_manager.chart_data_default)
        self.new_chart(start_date=pd.to_datetime('today'))

    def fig_save_image(self, full_path, format, dpi):
        if not full_path.endswith('.' + format):
            full_path += '.' + format
        plt.savefig(full_path, format=format, dpi=dpi)

    def fig_load_chart(self, full_path):
        with open(full_path, 'r') as file:
            self.data_manager.chart_data = json.load(file)

        # Handling for ensuring backwards compatibility with older chart files that might be missing certain keys
        # Delete incompatible phase lines
        self.data_manager.chart_data['phase'] = [phase for phase in self.data_manager.chart_data['phase'] if 'y' not in phase.keys()]

        # Handling for setting the start date
        start_date = self.data_manager.chart_data['start_date']
        # Set chart type
        self.data_manager.user_preferences['chart_type'] = self.data_manager.chart_data['type']

        # Create raw_df
        df = pd.DataFrame.from_dict(self.data_manager.chart_data["raw_data"])
        df['d'] = pd.to_datetime(df['d'])  # Convert back to a datetime column with no time or timezone information
        self.data_manager.chart_data['raw_df'] = df

        # Generate chart
        self.new_chart(start_date=start_date)

    def change_chart_type(self, new_type):
        self.data_manager.chart_data['type'] = new_type
        self.data_manager.user_preferences['chart_type'] = new_type
        self.new_chart(start_date=self.data_manager.chart_data['start_date'])

    def update_chart(self):
        self.new_chart(start_date=self.data_manager.chart_data['start_date'])

    def data_styling_cleanup(self):
        self.manual_manager.manual_clean_up()


class PhaseManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
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
            self.figure_manager.refresh()

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
                    self.y_text_pos = ymax / 2
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
                                                                        bbox=bbox,
                                                                        ha="left",
                                                                        va=va,
                                                                        rotation=rotation,
                                                                        fontsize=self.figure_manager.data_manager.user_preferences['phase_style']['font_size'])

                self.figure_manager.refresh()

                return x, y

    def phase_undo_line(self):
        if self.figure_manager.chart_objects['phase_obj']:
            self.figure_manager.data_manager.chart_data['phase'].pop()
            line, text = self.figure_manager.chart_objects['phase_obj'].pop()
            line.remove()
            text.remove()
            self.figure_manager.refresh()

    def phase_cleanup_temp_line(self):
        if self.temp_phase_line and self.temp_phase_line_text:
            self.temp_phase_line.remove()
            self.temp_phase_line_text.remove()
            self.temp_phase_line = None
            self.temp_phase_line_text = None
        self.figure_manager.refresh()


class AimManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.aim_temp_line = None
        self.aim_temp_note = None
        self.aim_first_click_x = None
        self.aim_second_click_x = None
        self.aim_y = None
        self.aim_first_click_indicator = None

    def aim_from_form(self, text, target, start, deadline):
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

            self.figure_manager.data_manager.save_plot_item(item=aim, item_type='aim')
            self.figure_manager.aim_replot(aim)
            self.figure_manager.refresh()

    def aim_cleanup(self):
        self.aim_first_click_x = None
        self.aim_second_click_x = None

        if self.aim_temp_line:
            self.aim_temp_line.remove()
            self.aim_temp_line = None
        if self.aim_temp_note:
            self.aim_temp_note.remove()
            self.aim_temp_note = None
        if self.aim_first_click_indicator:
            self.aim_first_click_indicator.remove()
            self.aim_first_click_indicator = None

        self.figure_manager.refresh()

    def aim_undo(self):
        if self.figure_manager.data_manager.chart_data['aim'] and self.figure_manager.chart_objects['aim_obj']:
            self.figure_manager.data_manager.chart_data['aim'].pop()
            line, note = self.figure_manager.chart_objects['aim_obj'].pop()
            line.remove()
            note.remove()
            self.figure_manager.refresh()

    def aim_click_info(self, event, note):
        # Handling for Weekly
        x_i = self.figure_manager.data_manager.find_closest_x(int(event.xdata), self.figure_manager.Chart.date_to_pos)
        if x_i is not None:
            if self.aim_temp_line:
                self.aim_temp_line.remove()
                self.aim_temp_line = None
            if self.aim_temp_note:
                self.aim_temp_note.remove()
                self.aim_temp_note = None

            self.aim_y = round(event.ydata, 4)
            if self.aim_first_click_x is None:
                self.aim_first_click_x = x_i

                self.aim_first_click_indicator, = self.figure_manager.ax.plot(self.aim_first_click_x, self.aim_y, marker='o', color='magenta')

                self.figure_manager.refresh()
                return None

            elif self.aim_second_click_x is None:
                self.aim_second_click_x = x_i

                xmin = min(self.aim_first_click_x, self.aim_second_click_x)
                xmax = max(self.aim_first_click_x, self.aim_second_click_x)

                self.aim_temp_line = self.figure_manager.ax.hlines(xmin=xmin, xmax=xmax, y=self.aim_y, colors="magenta", linewidth=1.5, linestyle="--")
                self.aim_temp_note = self.figure_manager.ax.text(xmax, self.aim_y, note, bbox=dict(facecolor='white', edgecolor='magenta', linestyle='--'), ha="left", va="bottom", fontsize=self.figure_manager.aim_font)

                d1 = self.figure_manager.x_to_date[xmin]
                d2 = self.figure_manager.x_to_date[xmax]

                self.aim_first_click_x = None
                self.aim_second_click_x = None

                if self.aim_first_click_indicator:
                    self.aim_first_click_indicator.remove()
                    self.aim_first_click_indicator = None

                self.figure_manager.refresh()

                return d1, d2, self.aim_y


class TrendManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_current_temp_marker = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_temp_est = None
        self.trend_temp_line = None
        self.upper_bounce_temp_line = None
        self.lower_bounce_temp_line = None
        self.trend_temp_fit_on = False

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
                y = event.ydata
                self.trend_temp_est.set_position((x, y))
                self.figure_manager.refresh()
            else:
                if self.trend_first_click_x is not None and self.trend_second_click_x is None:
                    self.plot_trend_temp_first_marker(self.trend_first_click_x)
                elif self.trend_second_click_x is not None:
                    self.plot_trend_temp_second_marker(self.trend_second_click_x)

    def plot_trend_line(self, x_slice, trend_vals, color):
        self.trend_temp_line, = self.figure_manager.ax.plot(x_slice, trend_vals, linestyle="-", linewidth=1, color=color)
        self.figure_manager.refresh()
        return self.trend_temp_line

    def plot_trend_est(self, x_slice_mean, trend_vals_mean, cel_est, color, adjust=2):
        self.trend_temp_est = self.figure_manager.ax.text(int(x_slice_mean), trend_vals_mean * adjust, cel_est, fontsize=self.figure_manager.trend_est_font, color=color, ha="center", weight="bold")
        self.figure_manager.refresh()
        return self.trend_temp_est

    def plot_trend_temp_first_marker(self, x_i):
        self.trend_current_temp_marker = 'first'
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        self.trend_temp_first_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.figure_manager.refresh()

    def plot_trend_temp_second_marker(self, x_i):
        self.trend_current_temp_marker = 'second'
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()
        self.trend_temp_second_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.figure_manager.refresh()

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

            self.figure_manager.refresh()

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
            self.figure_manager.refresh()

    def trend_fit(self, corr):
        if self.trend_temp_first_marker and self.trend_temp_second_marker and self.trend_temp_line is None:

            self.trend_temp_fit_on = True

            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]

            result = self.figure_manager.data_manager.get_trend(x1, x2, corr, self.figure_manager.Chart.date_to_pos, self.figure_manager.Chart.x_to_day_count)
            if result:
                trend_vals, cel_slope_label, x_slice, upper_bounce, lower_bounce, bounce_est_label = result

                # Will tightened the date range
                self.trend_temp_first_marker.set_xdata([x_slice[0]])
                self.trend_temp_second_marker.set_xdata([x_slice[-1]])

                self.plot_trend_line(x_slice, trend_vals, 'magenta')
                self.plot_trend_est(np.mean(x_slice), np.mean(trend_vals), cel_slope_label, 'magenta')

                if upper_bounce is not None and lower_bounce is not None:
                    self.upper_bounce_temp_line, = self.figure_manager.ax.plot(x_slice, upper_bounce, linestyle="--", linewidth=1, color='magenta')
                    self.lower_bounce_temp_line, = self.figure_manager.ax.plot(x_slice, lower_bounce, linestyle="--", linewidth=1, color='magenta')

                self.figure_manager.refresh()

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

        self.figure_manager.refresh()

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

        self.figure_manager.refresh()

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

            self.figure_manager.refresh()

        self.trend_cleanup()

    def trend_finalize(self, corr):
        if self.trend_temp_line and self.trend_temp_est:
            if corr:
                data, obj = 'trend_corr', 'trend_corr_obj'
            else:
                data, obj = 'trend_err', 'trend_err_obj'

            x1 = self.trend_temp_first_marker.get_xdata()[0]
            x2 = self.trend_temp_second_marker.get_xdata()[0]
            est_x, est_y = self.trend_temp_est.get_position()
            # Correct x if it fell between the cracks on Weekly
            est_x = self.figure_manager.data_manager.find_closest_x(est_x, self.figure_manager.Chart.date_to_pos)
            est_date = self.figure_manager.x_to_date[est_x]

            trend = copy.deepcopy(self.figure_manager.data_manager.user_preferences[data + '_style'])
            trend['date1'] = self.figure_manager.x_to_date[x1]
            trend['date2'] = self.figure_manager.x_to_date[x2]
            trend['text'] = self.trend_temp_est.get_text()
            trend['text_date'] = est_date
            trend['text_y'] = est_y
            trend['fit_method'] = self.figure_manager.data_manager.user_preferences['fit_method']
            trend['bounce_envelope'] = self.figure_manager.data_manager.user_preferences['bounce_envelope']

            self.figure_manager.data_manager.save_plot_item(item=trend, item_type=data)
            self.trend_cleanup()  # Remove all temp stuff
            self.figure_manager.trend_replot(trend, corr)  # Add finalized trend
            self.figure_manager.refresh()

    def trend_cleanup(self):
        if self.trend_temp_first_marker:
            self.trend_temp_first_marker.remove()
        if self.trend_temp_second_marker:
            self.trend_temp_second_marker.remove()
        if self.trend_temp_line:
            self.trend_temp_line.remove()
        if self.trend_temp_est:
            self.trend_temp_est.remove()
        if self.upper_bounce_temp_line:
            self.upper_bounce_temp_line.remove()
        if self.lower_bounce_temp_line:
            self.lower_bounce_temp_line.remove()
        self.trend_temp_est = None
        self.trend_temp_line = None
        self.upper_bounce_temp_line = None
        self.lower_bounce_temp_line = None
        self.trend_first_click_x = None
        self.trend_second_click_x = None
        self.trend_temp_first_marker = None
        self.trend_temp_second_marker = None
        self.trend_current_temp_marker = None
        self.trend_temp_fit_on = False

        self.figure_manager.refresh()

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

    def view_dot_est(self, show, refresh=True):
        for est in self.figure_manager.chart_objects['trend_corr_est_obj']:
            est.set_visible(show)
        self.figure_manager.data_manager.update_view_check('dot_est', show)
        if refresh:
            self.figure_manager.refresh()

    def view_x_est(self, show, refresh=True):
        for est in self.figure_manager.chart_objects['trend_err_est_obj']:
            est.set_visible(show)
        self.figure_manager.data_manager.update_view_check('x_est', show)
        if refresh:
            self.figure_manager.refresh()

    def view_dot_bounce(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['trend_corr_bounce_obj']:
            upper, lower = pair
            upper.set_visible(show)
            lower.set_visible(show)
        self.figure_manager.data_manager.update_view_check('dot_bounce', show)
        if refresh:
            self.figure_manager.refresh()

    def view_x_bounce(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['trend_err_bounce_obj']:
            upper, lower = pair
            upper.set_visible(show)
            lower.set_visible(show)
        self.figure_manager.data_manager.update_view_check('x_bounce', show)
        if refresh:
            self.figure_manager.refresh()

    def view_minor_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.minor_grid_lines(show)
        self.figure_manager.data_manager.update_view_check('minor_grid', show)
        if refresh:
            self.figure_manager.refresh()

    def view_major_gridlines(self, show, refresh=True):
        self.figure_manager.Chart.major_grid_lines(show)
        self.figure_manager.data_manager.update_view_check('major_grid', show)
        if refresh:
            self.figure_manager.refresh()

    def view_dots(self, show, refresh=True):
        for corr_obj in self.figure_manager.chart_objects['corr_obj']:
            corr_obj.set_visible(show)
        self.figure_manager.data_manager.update_view_check('dots', show)
        if refresh:
            self.figure_manager.refresh()

    def view_xs(self, show, refresh=True):
        for err_obj in self.figure_manager.chart_objects['err_obj']:
            err_obj.set_visible(show)
        self.figure_manager.data_manager.update_view_check('xs', show)
        if refresh:
            self.figure_manager.refresh()

    def view_floor(self, show, refresh=True):
        for floor_obj in self.figure_manager.chart_objects['floor_obj']:
            floor_obj.set_visible(show)
        self.figure_manager.data_manager.update_view_check('timing_floor', show)
        if refresh:
            self.figure_manager.refresh()

    def view_floor_grid(self, show, refresh=True):
        self.figure_manager.Chart.floor_grid_lines(show)
        self.figure_manager.data_manager.update_view_check('timing_grid', show)
        if refresh:
            self.figure_manager.refresh()

    def view_aims(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['aim_obj']:
            line, text = pair
            line.set_visible(show)
            text.set_visible(show)
        self.figure_manager.data_manager.update_view_check('aims', show)
        if refresh:
            self.figure_manager.refresh()

    def view_phase_lines(self, show, refresh=True):
        for pair in self.figure_manager.chart_objects['phase_obj']:
            line, text = pair
            line.set_visible(show)
            text.set_visible(show)
        self.figure_manager.data_manager.update_view_check('phase_lines', show)
        if refresh:
            self.figure_manager.refresh()

    def view_dot_trend(self, show, refresh=True):
        for line in self.figure_manager.chart_objects['trend_corr_obj']:
            line.set_visible(show)
        self.figure_manager.data_manager.update_view_check('dot_trends', show)
        if refresh:
            self.figure_manager.refresh()

    def view_x_trend(self, show, refresh=True):
        for line in self.figure_manager.chart_objects['trend_err_obj']:
            line.set_visible(show)
        self.figure_manager.data_manager.update_view_check('x_trends', show)
        if refresh:
            self.figure_manager.refresh()

    def view_update_credit_lines(self, row1, row2, row3):
        # Clean up previous credit lines
        if self.figure_manager.credit_lines_object:
            self.figure_manager.credit_lines_object.remove()

        credit = row1 + '\n\n' + row2 + '\n\n' + row3
        self.figure_manager.credit_lines_object = self.figure_manager.ax.text(0, self.figure_manager.Chart.credit_vert_pos, credit, transform=self.figure_manager.Chart.trans, fontsize=self.figure_manager.Chart.credit_fontsize, color=self.figure_manager.Chart.style_color, ha='left', va='center')
        self.figure_manager.data_manager.chart_data['credit'] = (row1, row2, row3)

        if hasattr(self.figure_manager, 'canvas'):
            self.figure_manager.refresh()


class ManualManager:
    def __init__(self, figure_manager):
        self.figure_manager = figure_manager
        # Control variables
        self.point_temp_first_marker = None
        self.point_temp_second_marker = None
        self.point_current_temp_marker = None
        self.point_first_click_x = None
        self.point_second_click_x = None

    def safe_float_convert(self, input):
        try:
            return float(input)
        except ValueError:
            return 0.0

    def manual_plot_form_minutes(self, count, hour, min_, sec, date):
        count = self.safe_float_convert(count)
        hour = self.safe_float_convert(hour)
        min_ = self.safe_float_convert(min_)
        sec = self.safe_float_convert(sec)

        # Plot data point
        date = pd.to_datetime(date, format='%d-%m-%Y')

        total_minutes = hour * 60 + min_ + sec / 60

        if date in self.figure_manager.Chart.date_to_pos.keys() and total_minutes > 0:
            self.figure_manager.data_manager.update_dataframe(date, total_minutes, count, self.figure_manager.point_type)
            self.figure_manager.create_point_style_arrays()

            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='c')
            self.figure_manager.plot_corr_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='i')
            self.figure_manager.plot_err_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='m')
            self.figure_manager.plot_floor_points(x, y)

            self.figure_manager.refresh()

    def manual_plot_form_date(self, count, date):
        # Plot data point
        date = pd.to_datetime(date, format='%d-%m-%Y')
        count = self.safe_float_convert(count)
        total_minutes = 1

        if date in self.figure_manager.Chart.date_to_pos.keys():
            self.figure_manager.data_manager.update_dataframe(date, total_minutes, count, self.figure_manager.point_type)
            self.figure_manager.create_point_style_arrays()

            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='c')
            self.figure_manager.plot_corr_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='i')
            self.figure_manager.plot_err_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='m')
            self.figure_manager.plot_floor_points(x, y)

            self.figure_manager.refresh()

    def manual_undo_point(self):
        df = self.figure_manager.data_manager.chart_data['raw_df']
        if not df.empty:
            # Pop the latest row
            self.figure_manager.data_manager.chart_data['raw_df'] = df[:-1]
            self.figure_manager.create_point_style_arrays()

            # Get new plot objects
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='c')
            self.figure_manager.plot_corr_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='i')
            self.figure_manager.plot_err_points(x, y)
            x, y = self.figure_manager.data_manager.get_replot_points(self.figure_manager.Chart.date_to_pos, kind='m')
            self.figure_manager.plot_floor_points(x, y)

            self.figure_manager.refresh()

    def plot_point_temp_first_marker(self, x_i):
        self.point_current_temp_marker = 'first'
        if self.point_temp_first_marker:
            self.point_temp_first_marker.remove()
        self.point_temp_first_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.figure_manager.refresh()

    def plot_point_temp_second_marker(self, x_i):
        self.point_current_temp_marker = 'second'
        if self.point_temp_second_marker:
            self.point_temp_second_marker.remove()
        self.point_temp_second_marker = self.figure_manager.ax.axvline(x_i, color='magenta', linestyle='--', linewidth=1)
        self.figure_manager.refresh()

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

    def manual_clean_up(self):
        if self.point_temp_first_marker:
            self.point_temp_first_marker.remove()
        if self.point_temp_second_marker:
            self.point_temp_second_marker.remove()
        self.point_temp_first_marker = None
        self.point_temp_second_marker = None
        self.point_current_temp_marker = None
        self.point_first_click_x = None
        self.point_second_click_x = None
        self.figure_manager.data_point_x1 = None
        self.figure_manager.data_point_x2 = None

        self.figure_manager.refresh()




