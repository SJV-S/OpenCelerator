import matplotlib.pyplot as plt
from matplotlib import transforms
import os
import numpy as np
import pandas as pd
import re

# ax.text(0.95, 0.96, 'By SJV', transform=plt.gcf().transFigure, fontname=font, fontsize=7, color=style_color)

class Daily(object):
    def __init__(self,
                 date_format=None,  # For example: "%d-%m-%y" (day, month, year)
                 start_date=None,
                 width=9,
                 major_grid_on=True,
                 minor_grid_on=True,
                 floor_grid_on=False,
                 y_label="COUNT PER MINUTE",
                 style_color='#5a93cc',
                 custom_grid_color="#71B8FF",
                 space_bottom=None):

        # Class variables for default values
        # Definition of a, b and c of the exponential function y = ab^(x/c).
        self.a = 0.001  # y-intercept.
        self.b = 2  # y-increase factor.
        self.c = 7  # x-increase per y-increase factor.
        self.angle = 34  # desired visual slope of the function graph, in degrees.
        self.xmin = 0  # x-axis minimum value.
        self.xmax = 140  # x-axis maximum value.
        self.ymin = 0.00069  # y-axis minimum value.
        self.ymax = 1000  # y-axis maximum value.
        self.x = np.arange(self.xmin, self.xmax)
        self.y = self.a * pow(self.b, self.x / self.c)  # Calculate y-values for visual angle testing.

        # Calculate and set height of the figure based on selected width and margins.
        self.space_bottom = space_bottom if space_bottom else 0.21
        self.space_top = 0.86
        self.space_left = 0.1
        self.space_right = 0.9
        self.relative_width = self.space_right - self.space_left
        self.relative_height = self.space_top - self.space_bottom
        self.image_ratio = self.relative_width / self.relative_height  # Width to height ratio

        # Fonts
        self.general_fontsize = 12
        self.right_y_axis_fontsize = 9
        self.font = "Liberation sans"

        # Define axis ticks and labels
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]]]
        self.left_y_labels = ["0.001", "0.005", "0.01", "0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1000"]
        self.right_y_ticks = [1 / m for m in [10 / 60, 15 / 60, 20 / 60, 30 / 60, 1, 2, 5, 10, 20, 60, 60 * 2, 60 * 4, 60 * 8, 60 * 16]]
        self.right_y_labels = ['10" sec', '15"', '20"', '30"', "1' min", "2'", "5'", "10'", "20'", "1 - h", "2 - h", "4 - h", "8 - h", "16 - h"]
        self.bottom_x_ticks = np.arange(0, 141, 14)
        self.top_x_ticks = np.arange(0, 141, 28)

        # Start date and date format
        self.start_date = start_date
        self.date_format = date_format

        if self.start_date is None:
            self.start_date = pd.to_datetime('today')
        else:
            if isinstance(self.start_date, str):
                # Convert to pandas datetime format.
                if date_format:
                    self.start_date = pd.to_datetime(self.start_date, format=self.date_format)
                else:
                    self.start_date = pd.to_datetime(self.start_date)

        # Settings
        self.width = width
        self.y_label = y_label
        self.style_color = style_color
        self.custom_grid_color = custom_grid_color
        self.major_grid_line_objects = []
        self.floor_grid_line_objects = []
        self.major_grid_on = major_grid_on
        self.minor_grid_on = minor_grid_on
        self.floor_grid_on = floor_grid_on

        # Credit line rows
        self.credit_row1 = 'SUPERVISOR: ________________    DIVISION: ________________       TIMER: ________________     COUNTED: ________________'
        self.credit_row2 = 'ORGANIZATION: ________________     MANAGER: ________________     COUNTER: ________________     CHARTER: ________________'
        self.credit_row3 = 'ADVISOR: ________________        ROOM: ________________   PERFORMER: ________________        NOTE: ________________'

        # Calculator height based on width
        self.height = self.image_ratio * self.width * np.tan(self.angle / 180 * np.pi) * np.log10(self.ymax / self.ymin) / (self.xmax - self.xmin) * self.c / np.log10(self.b)

        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height))
        plt.subplots_adjust(left=self.space_left, right=self.space_right, bottom=self.space_bottom, top=self.space_top)  # Surround plot with more white space

        # Get all dates
        self.first_sunday = self.start_date - pd.Timedelta(self.start_date.dayofweek + 1, unit="D")  # Find last Sunday.
        self.dates = pd.date_range(self.first_sunday, periods=21, freq="W").strftime("%d-%b-%y")  # Get date labels for top x-axis.
        self.month_dates = [self.dates[i] for i in range(0, len(self.dates), 4)]
        self.dates = [str(i) for i in range(0, len(self.dates), 4)]
        self.all_dates = pd.date_range(self.first_sunday, periods=141, freq="D", normalize=True)  # Used as reference when plotting with dates.

        # Get date positions
        self.date_to_pos = {}
        for i in range(len(self.all_dates)):
            self.date_to_pos[self.all_dates[i]] = i

        # Set up top x-axis.
        self.ax2 = plt.twiny()
        self.ax2.set_xticks(self.top_x_ticks)
        self.ax2.set_xticklabels(self.dates, fontsize=self.general_fontsize, fontname=self.font, color=style_color)
        self.ax2.tick_params(axis='both', which='both', color=style_color)
        self.ax2.set_xlabel("SUCCESSIVE                       CALENDAR                        WEEKS",
                            fontname=self.font, fontsize=self.general_fontsize, color=style_color, weight="bold",
                            labelpad=34)

        # Add date displays for top x-axis.
        self.trans = transforms.blended_transform_factory(self.ax.transData, self.ax.transAxes)
        self.vert_pos = 1.07
        self.underline = self.vert_pos - 0.0067
        for tick, date in zip(self.top_x_ticks, self.month_dates):
            self.ax.text(tick, self.vert_pos, date, transform=self.trans, fontname=self.font,
                         fontsize=self.general_fontsize, color=self.style_color, ha="center")
            self.ax.text(tick, self.underline, len(date) * "_", transform=self.trans, fontname=self.font,
                         fontsize=self.general_fontsize, color=self.style_color, ha="center")

        # Set up right y-axis.
        self.ax3 = plt.twinx()
        self.ax3.set_ylim(self.ymin, self.ymax)
        self.ax3.set_yscale("log")
        self.ax3.set_yticks(self.right_y_ticks)
        self.ax3.set_yticklabels(self.right_y_labels, fontsize=self.right_y_axis_fontsize, fontname=self.font,
                                 color=self.style_color)
        self.ax3.tick_params(axis='both', which='minor', length=0)
        self.ax3.tick_params(axis="both", colors=self.style_color)

        # Move bottom x-axis down slightly for ax and remove bottom spine for ax2 and ax3.
        self.ax.spines["bottom"].set_position(("axes", -0.03))  # Move down.
        self.ax2.spines["bottom"].set_visible(False)  # Delete ax2 spine.
        self.ax3.spines["bottom"].set_visible(False)  # Delete ax3 spine.

        # Set up main axes: left y and bottom x.
        self.ax.set_yscale("log")
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.tick_params(axis='both', which='minor', length=0)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_xticks(self.bottom_x_ticks)
        self.ax.set_xticklabels([str(tick) for tick in self.bottom_x_ticks], fontsize=self.general_fontsize,
                                fontname=self.font, color=style_color)
        self.ax.set_yticks(self.left_y_ticks)
        self.ax.set_yticklabels(self.left_y_labels, fontsize=self.general_fontsize, fontname=self.font,
                                color=self.style_color)
        self.ax.tick_params(axis="both", colors=self.style_color)

        if self.major_grid_on:
            for sun in [i for i in range(7, 140, 7)]:
                g1 = self.ax.axvline(sun, color=self.custom_grid_color, linewidth=1.4, visible=True)
                self.major_grid_line_objects.append(g1)
            for power in [0.001, 0.01, 0.1, 1, 10, 100, 1000]:
                g2 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=1.4, visible=True)
                self.major_grid_line_objects.append(g2)
            for power in [0.005, 0.05, 0.5, 5, 50, 500]:
                g3 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=0.7, visible=True)
                self.major_grid_line_objects.append(g3)

        if self.minor_grid_on:
            self.ax.grid(which="both", visible=self.minor_grid_on, color=self.custom_grid_color, linewidth=0.3)

        if self.floor_grid_on:
            for y_i in self.right_y_ticks:
                g4 = self.ax.axhline(y_i, color=self.custom_grid_color, linewidth=0.3, visible=True)
                self.floor_grid_line_objects.append(g4)

        # Color spines (the frame around the plot). The axes all have their own spines, so we have to color each.
        self.spine_color = self.style_color
        for position in self.ax.spines.keys():
            self.ax.spines[position].set_color(self.spine_color)
            self.ax2.spines[position].set_color(self.spine_color)
            self.ax3.spines[position].set_color(self.spine_color)

        # Set axis labels and title
        self.ax.set_ylabel(y_label, fontname=self.font, fontsize=self.general_fontsize, color=style_color,
                           weight="bold")
        self.ax.set_xlabel("SUCCESSIVE CALENDAR DAYS", fontname=self.font, fontsize=self.general_fontsize,
                           color=style_color, weight="bold")

        # Testing for a 34 degree visual angle.)
        self.angle_test, = self.ax.plot(self.x, self.y, 'r')
        self.angle_test.set_visible(False)  # Don't show by default

    def major_grid_lines(self, grid_on):
        # Toggle the visibility of each custom grid line
        for line in self.major_grid_line_objects:
            line.set_visible(grid_on)

    def minor_grid_lines(self, grid_on):
        # Toggle grid visibility directly
        if grid_on:
            self.ax.grid(which="both", visible=grid_on, color=self.custom_grid_color, linewidth=0.3)
        else:
            self.ax.grid(which="both", visible=grid_on)

    def floor_grid_lines(self, grid_on):
        for floor_line in self.floor_grid_line_objects:
            floor_line.set_visible(grid_on)

    def get_trend(self, x, y):
        # Assumes x have been converted to integers
        fit = np.polyfit(x, np.log10(y), 1)
        trend = np.polyval(fit, x)
        trend = np.power(10, trend)

        cel_unit = 7
        cel_line = np.power(10, fit[0] * cel_unit)

        if cel_line < 1:
            cel_line = "÷" + str(round(1 / cel_line, 1))
        else:
            cel_line = "x" + str(round(cel_line, 1))

        return trend, cel_line

    def plot_trend(self, x1: int, x2: int, data, corr=True):
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        selected_range_set = set(np.arange(min_x, max_x + 1))  # Create a set from the range

        if corr:
            if self.chart_settings['corr_freq_x_avg']:
                keys_set = set(self.chart_settings['corr_freq_x_avg'].keys())  # Get keys from dictionary as a set
                x_slice = list(selected_range_set & keys_set)  # Find intersection of both sets
                y_slice = [self.chart_settings['corr_freq_x_avg'][x_i] for x_i in x_slice]
            else:
                y_slice = []
        else:
            if self.chart_settings['err_freq_x_avg']:
                keys_set = set(self.chart_settings['err_freq_x_avg'].keys())  # Get keys from dictionary as a set
                x_slice = list(selected_range_set & keys_set)  # Find intersection of both sets
                y_slice = [self.chart_settings['err_freq_x_avg'][x_i] for x_i in x_slice]
            else:
                y_slice = []

        if y_slice:
            trend_vals, cel_est = self.get_trend(x_slice, y_slice)
            color = 'green' if corr else 'red'
            trend_line, = self.ax.plot(x_slice, trend_vals, linestyle="-", linewidth=1, color=color)
            est = self.ax.text(np.median(x_slice), np.median(trend_vals) * 2, cel_est, fontname=self.font, fontsize=self.general_fontsize, color=color, ha="center", weight="bold")
            return trend_line, trend_vals, est
        else:
            return None

    def plot_corr(self,
                  x,
                  y,
                  avg_xi_stack=False,
                  cor_label="Correct freq",
                  linestyle="",
                  color="black",
                  marker="o",
                  linewidth=0.5,
                  markersize=3
                  ):

        df = pd.DataFrame(list(zip(pd.to_datetime(x), y)), columns=['x', 'y'])
        df["x"] = df.x.map(self.date_to_pos)  # Map the dates to their numerical x-coordinate

        # y-values on the same x-value be averaged instead of stacked
        if avg_xi_stack:
            df = df.groupby('x', as_index=False)['y'].mean()

        data_points_object = self.ax.plot(df.x, df.y,
                     markersize=markersize,
                     label=cor_label,
                     linestyle=linestyle,
                     linewidth=linewidth,
                     marker=marker,
                     color=color)

        return data_points_object[0]

    def plot_err(self,
                 x,
                 y,
                 avg_xi_stack=False,
                 err_label="Error freq",
                 linestyle="",
                 color="black",
                 marker="x",
                 linewidth=0.5,
                 markersize=5
                 ):

        df = pd.DataFrame(list(zip(pd.to_datetime(x), y)), columns=['x', 'y'])
        df["x"] = df.x.map(self.date_to_pos)  # Map the dates to their numerical x-coordinate

        # y-values on the same x-value be averaged instead of stacked
        if avg_xi_stack:
            df = df.groupby('x', as_index=False)['y'].mean()

        data_points_object = self.ax.plot(df.x, df.y,
                     markersize=markersize,
                     label=err_label,
                     linestyle=linestyle,
                     linewidth=linewidth,
                     marker=marker,
                     color=color)

        return data_points_object[0]

    def plot_record_floor(self,
        x,
        y,
        avg_xi_stack = False,
        linestyle = "",
        color = "black",
        marker="_",
        markersize = 5,
        markeredgewidth = 1.5
        ):

        # y values will be minutes, x will be dates

        df = pd.DataFrame(list(zip(pd.to_datetime(x), y)), columns=['x', 'y'])
        df["x"] = df.x.map(self.date_to_pos)  # Map the dates to their numerical x-coordinate

        # y-values on the same x-value be averaged instead of stacked
        if avg_xi_stack:
            df = df.groupby('x', as_index=False)['y'].mean()

        data_points_object = self.ax.plot(df.x, df.y,
                     marker=marker,
                     markersize=markersize,
                     color=color,
                     linestyle=linestyle,
                     markeredgewidth=markeredgewidth)

        return data_points_object[0]

    def phase_line(self, phase_lines):
        # phase_lines are expected to be a list of tuples: (x, y, text)
        # x coordinates are expected to be dates pandas dates

        for phase in phase_lines:
            x_cor, y_cor, text = phase
            x_cor = self.date_to_pos[x_cor]
            self.ax.vlines(x_cor, ymax=y_cor, ymin=0, color="k", linestyle="-", linewidth=1)
            self.ax.text(x_cor, y_cor, text, fontname=self.font, bbox=dict(facecolor='white', edgecolor='black'), ha="left", va="bottom")

    def fluency_target(self, x_start, x_end, target):
        x_start = self.date_to_pos[pd.to_datetime(x_start, format=self.date_format)]
        x_end = self.date_to_pos[pd.to_datetime(x_end, format=self.date_format)]
        self.ax.hlines(xmin=x_start, xmax=x_end, y=target, colors="firebrick", linewidth=1.5, linestyle="--")

    def display(self):
        plt.show()

    def save(self, chart_path, dpi=1200):
        plt.savefig(chart_path, dpi=dpi)

    def toggle_test_angle(self, show):
        # Testing for a 34 degree visual angle.)
        self.angle_test.set_visible(show)

    def get_figure(self):
        return self.fig, self.ax

    # ax.plot(position, record_floor_freq, marker="_", markersize=5, color="k", linestyle="", label="Record floor", markeredgewidth=1.5)

    # pos, dur = PosDur
    #     ax.plot(pos, dur, marker="_", markersize=5, color="k", linestyle="", label="Duration",
    #             markeredgewidth=2)


