import matplotlib.pyplot as plt
from matplotlib import transforms
import matplotlib.font_manager as font_manager
import platform
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import numpy as np
import pandas as pd


class Chart:
    def __init__(self, date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, style_color='#5a93cc', custom_grid_color='#71B8FF'):
        self.date_format = date_format
        self.start_date = start_date
        self.width = width
        self.major_grid_on = major_grid_on
        self.minor_grid_on = minor_grid_on
        self.floor_grid_on = floor_grid_on
        self.y_label = y_label
        self.style_color = style_color
        self.custom_grid_color = custom_grid_color
        self.minor_grid_width = 0.3
        self.major_grid_width = 0.1555 * width
        self.x_tick_length = width * 0.666
        self.style_color = style_color
        self.font = self.get_system_font()
        self.general_fontsize = width * 1.2
        self.general_fontsize_minor_scaling = 0.7
        self.credit_fontsize = width * 0.7
        self.right_y_axis_fontsize = width * 0.85
        self.top_x_label_pad = width * 1

        # Chart margin spacing
        self.space_left = 0.17
        self.space_right = 0.87
        self.space_top = 0.85
        self.space_bottom = 0.19

        # Fan control variables
        self.div_text_objects = []
        self.mult_text_objects = []

        self.major_grid_date_objects = []
        self.major_grid_count_objects = []
        self.floor_grid_line_objects = []

        if self.start_date is None:
            self.start_date = pd.to_datetime('today')
        else:
            if isinstance(self.start_date, str):
                if date_format:
                    self.start_date = pd.to_datetime(self.start_date, format=self.date_format)
                else:
                    self.start_date = pd.to_datetime(self.start_date)

    def get_system_font(self):
        os_name = platform.system()

        if os_name == "Windows":
            return "Tahoma"
        elif os_name == "Darwin":  # macOS
            return "Tahoma"
        elif os_name == "Linux":
            # Check if Tahoma is available in Matplotlib's font list
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            if "Tahoma" in available_fonts:
                return "Tahoma"
            else:
                return "DejaVu Sans"
        else:
            return "Sans-serif"

    def major_grid_dates(self, grid_on):
        for line in self.major_grid_date_objects:
            line.set_visible(grid_on)

    def major_grid_counts(self, grid_on):
        for line in self.major_grid_count_objects:
            line.set_visible(grid_on)

    def minor_grid_lines(self, grid_on):
        if grid_on:
            self.ax.grid(which="both", visible=grid_on, color=self.custom_grid_color, linewidth=0.3)
        else:
            self.ax.grid(which="both", visible=grid_on)

    def draw_floor_grid(self, tick_range):
        for tick in tick_range:
            floor_line = self.ax.axhline(tick, color=self.custom_grid_color, linewidth=self.minor_grid_width)
            self.floor_grid_line_objects.append(floor_line)

    def floor_grid_lines(self, grid_on):
        for floor_line in self.floor_grid_line_objects:
            floor_line.set_visible(grid_on)

    def get_figure(self):
        return self.fig, self.ax

    def count_month_clusters(self, dates):
        clusters = []
        current_month = None
        current_count = 0

        for date in dates:
            month_abbr = date.strftime('%b\n%y')

            if month_abbr == current_month:
                current_count += 1
            else:
                if current_month is not None:
                    clusters.append((current_month, current_count))
                current_month = month_abbr
                current_count = 1

        if current_month is not None:
            clusters.append((current_month, current_count))

        return [seq[0] for seq in clusters], [seq[1] for seq in clusters]

    def draw_major_grid(self, top_x_ticks):
        if self.major_grid_on:
            for month in top_x_ticks:
                g1 = self.ax.axvline(month, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_date_objects.append(g1)
            for power in [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]:
                g2 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_count_objects.append(g2)
            for power in [0.005, 0.05, 0.5, 5, 50, 500, 5000, 50000, 500000]:
                g3 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width * 0.5, visible=True, zorder=1)
                self.major_grid_count_objects.append(g3)

    def add_cel_fan(self, chart_type, div_decrease, line_length=0.95, text_pos=0.70):
        minute_x_pos = -0.1 * self.xmax
        minute_y_pos = 0.1
        non_minute_y_pos = 10**(np.log10(1) + 0.692 * (np.log10(self.ymax) - np.log10(1)))
        non_minute_x_pos = 1.16 * self.xmax
        fan_dict = {'DailyMinute': (minute_x_pos, minute_y_pos, "per week"),
                    'WeeklyMinute': (minute_x_pos, minute_y_pos, "per month"),
                    'MonthlyMinute': (minute_x_pos, minute_y_pos, 'per 6 months'),
                    'YearlyMinute': (minute_x_pos, minute_y_pos, 'per 5 years'),
                    'Daily': (non_minute_x_pos, non_minute_y_pos, "per week"),
                    'Weekly': (non_minute_x_pos, non_minute_y_pos, "per month"),
                    'Monthly': (non_minute_x_pos, non_minute_y_pos, 'per 6 months'),
                    'Yearly': (non_minute_x_pos, non_minute_y_pos, 'per 5 years'),
                    }

        # Clear any previous text objects
        self.div_text_objects = []
        self.mult_text_objects = []

        x, y, per_unit_str = fan_dict[chart_type]
        fig_width = self.width * 10

        # Convert (x, y) from data coordinates to figure coordinates
        fig_coords = self.ax.transData.transform((x, y))
        bbox_anchor = (fig_coords[0] / self.ax.figure.bbox.width, fig_coords[1] / self.ax.figure.bbox.height)

        # Calculate absolute size for the inset
        fig_height = fig_width * 2 / 1.1  # Based on xmin, xmax, ymin, ymax
        inset_width = fig_width / self.ax.figure.dpi
        inset_height = fig_height / self.ax.figure.dpi

        # Create an inset with the exact dimensions
        inset_ax = inset_axes(self.ax, width=inset_width,
                              height=inset_height,
                              bbox_to_anchor=bbox_anchor,
                              bbox_transform=self.ax.figure.transFigure,
                              borderpad=0)

        xmin = -0.1
        xmax = 1
        ymin = -1
        ymax = 1

        inset_ax.set_xlim(xmin, xmax)  # Set limits for x-axis.
        inset_ax.set_ylim(ymin, ymax)  # Set limits for y-axis.
        inset_ax.axis('off')  # Don't show the coordinate system.

        # Standard celeration values
        cels = [2 ** (1 / 2), 2, 4, 16]
        cels = cels + [1] + [1 / c for c in cels]

        # Celeration labels
        div_strs = ['x16', 'x4', 'x2', 'x1.4', 'x1', '÷1.4', '÷2', '÷4', '÷16']
        mult_strs = ['x16', 'x4', 'x2', 'x1.4', 'x1', 'x0.71', 'x0.5', 'x0.25', 'x0.06']
        cels = sorted(cels, reverse=True)

        for c, div_text, mult_text in zip(cels, div_strs, mult_strs):
            angle = np.degrees(np.atan(np.log10(c) / (np.log10(2) / np.tan(np.radians(34)))))
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            inset_ax.plot([0, line_length * x], [0, line_length * y], color=self.custom_grid_color, linewidth=1)

            div_text_obj = inset_ax.text(text_pos * x, text_pos * y, div_text.ljust(3), color=self.custom_grid_color, backgroundcolor='white',
                          weight='bold', ha='left', va='center',
                          rotation=round(angle), rotation_mode='anchor', fontsize=self.general_fontsize * 0.7)

            mult_text_obj = inset_ax.text(text_pos * x, text_pos * y, mult_text.ljust(3), color=self.custom_grid_color, backgroundcolor='white',
                          weight='bold', ha='left', va='center',
                          rotation=round(angle), rotation_mode='anchor', fontsize=self.general_fontsize * 0.7)

            div_text_obj.set_visible(div_decrease)
            mult_text_obj.set_visible(not div_decrease)
            self.div_text_objects.append(div_text_obj)
            self.mult_text_objects.append(mult_text_obj)

        inset_ax.text(0.15, 1.2, "Standard\nceleration", color=self.custom_grid_color, backgroundcolor='white',
                      weight='bold', ha='left', va='center', fontsize=self.general_fontsize * 0.7)
        inset_ax.text(0.15, -1.25, per_unit_str, color=self.custom_grid_color, backgroundcolor='white', weight='bold',
                      ha='left', va='center', fontsize=self.general_fontsize * 0.7)

        # Adjust right y-label if dealing with a minute chart
        if 'Minute' in chart_type:
            self.ax.yaxis.set_label_coords(-0.1, 0.7)

        return inset_ax

    def change_deceleration_symbol(self, div_decrease):
        for div_text, mult_text in zip(self.div_text_objects, self.mult_text_objects):
            div_text.set_visible(div_decrease)
            mult_text.set_visible(not div_decrease)


class DailyTemplate(Chart):
    def __init__(self, date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, a, b, c, ymin, ymax, style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, style_color, custom_grid_color)
        self.a = a
        self.b = b
        self.c = c
        self.angle = 34
        self.xmin = 0
        self.xmax = 140
        self.ymin = ymin
        self.ymax = ymax
        self.x = np.arange(self.xmin, self.xmax)
        self.y = self.a * pow(self.b, self.x / self.c)
        self.relative_width = self.space_right - self.space_left
        self.relative_height = self.space_top - self.space_bottom
        self.image_ratio = self.relative_width / self.relative_height
        self.y_axis_expansion = (np.log10(ymax) - np.log10(ymin)) / (np.log10(ymax) - np.log10(ymin / 0.69))
        self.height = self.image_ratio * self.width * np.tan(self.angle / 180 * np.pi) * self.y_axis_expansion

        self.vert_pos_scaling_dict = {
                                      6: 1.1,
                                      7: 1.1,
                                      8: 1.095,
                                      9: 1.09,
                                      10: 1.09,
                                      11: 1.09,
                                      12: 1.09,
                                      13: 1.09,
                                      14: 1.09,
                                      15: 1.09
        }

        self.credit_vert_pos = -0.23
        self.vert_pos = self.vert_pos_scaling_dict[width]
        self.underline = self.vert_pos - 0.012
        self.top_x_label_pad = width * 3.7

        self.top_x_ticks = np.arange(0, 141, 28)
        self.bottom_x_ticks = np.arange(0, 141, 1)

    def _setup_axes(self):
        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height))
        plt.subplots_adjust(left=self.space_left, right=self.space_right, bottom=self.space_bottom, top=self.space_top)

        self.first_sunday = self.start_date - pd.Timedelta(self.start_date.dayofweek + 1, unit="D")
        self.dates = pd.date_range(self.first_sunday, periods=21, freq="W").strftime("%d-%b-%y")
        self.month_dates = [self.dates[i] for i in range(0, len(self.dates), 4)]
        self.dates = [str(i) for i in range(0, len(self.dates), 4)]
        self.all_dates = pd.date_range(self.first_sunday, periods=141, freq="D", normalize=True)

        # For date to x-bottom mapping
        self.date_to_pos = {self.all_dates[i]: i for i in range(len(self.all_dates))}

        # For daily celeration mapping
        days_from_base = np.array([(ts - self.all_dates[0]).days for ts in self.all_dates])
        self.x_to_day_count = {}
        for x_i, day_count in zip(range(len(self.all_dates)), days_from_base):
            self.x_to_day_count[x_i] = day_count

        self.ax2 = plt.twiny()
        self.ax2.set_xticks(self.top_x_ticks)
        self.ax2.set_xticklabels(self.dates, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax2.tick_params(axis='both', which='both', color=self.style_color)
        self.ax2.set_xlabel("SUCCESSIVE CALENDAR WEEKS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold", labelpad=self.top_x_label_pad)

        self.trans = transforms.blended_transform_factory(self.ax.transData, self.ax.transAxes)
        for tick, date in zip(self.top_x_ticks, self.month_dates):
            self.ax.text(tick, self.vert_pos, date, transform=self.trans, fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, ha="center", weight='bold')
            line = plt.Line2D([tick - 9, tick + 9], [self.underline, self.underline], color=self.style_color, transform=self.ax.get_xaxis_transform(), clip_on=False)
            self.ax.add_line(line)

        self.ax.spines["bottom"].set_position(("axes", -0.03))
        self.ax2.spines["bottom"].set_visible(False)

        self.ax.set_yscale("log")
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.tick_params(axis='both', which='minor', length=0)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_xticks(self.bottom_x_ticks)
        bottom_x_tick_labels = [str(tick) if tick % 14 == 0 else '' for tick in self.bottom_x_ticks]
        self.ax.set_xticklabels(bottom_x_tick_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax.set_yticks(self.left_y_ticks)
        self.ax.set_yticklabels(self.left_y_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax.tick_params(axis="both", colors=self.style_color)

        if self.major_grid_on:
            for sun in [i for i in range(7, 140, 7)]:
                g1 = self.ax.axvline(sun, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_date_objects.append(g1)
            for power in [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]:
                g2 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_count_objects.append(g2)
            for power in [0.005, 0.05, 0.5, 5, 50, 500, 5000, 50000, 500000]:
                g3 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width * 0.5, visible=True, zorder=1)
                self.major_grid_count_objects.append(g3)

        if self.minor_grid_on:
            self.ax.grid(which="both", visible=self.minor_grid_on, color=self.custom_grid_color, linewidth=self.minor_grid_width)

        for position in self.ax.spines.keys():
            self.ax.spines[position].set_color(self.custom_grid_color)
            self.ax2.spines[position].set_color(self.custom_grid_color)
            self.ax.spines[position].set_linewidth(self.major_grid_width)

        self.ax.set_ylabel(self.y_label, fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.set_xlabel("SUCCESSIVE CALENDAR DAYS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.xaxis.set_label_coords(0.5, -0.1)

        for label in self.ax.get_yticklabels():
            if '5' in label.get_text():
                label.set_fontsize(self.general_fontsize * self.general_fontsize_minor_scaling)
            else:
                label.set_fontsize(self.general_fontsize)

        self.ax.tick_params(axis='both', color=self.custom_grid_color, length=5)
        for tick in self.ax.yaxis.get_major_ticks():
            ytick = tick.label1.get_text()
            if '5' in ytick:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)
            else:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)

        self.ax2.tick_params(axis='x', which='major', width=self.major_grid_width, length=self.x_tick_length, color=self.custom_grid_color)
        for tick in self.ax2.xaxis.get_major_ticks():
            tick.tick1line.set_markeredgewidth(self.major_grid_width)
            tick.tick2line.set_markeredgewidth(self.major_grid_width)

        self.ax.xaxis.set_tick_params(which='both', direction='inout', color=self.custom_grid_color)
        for tick in self.ax.xaxis.get_major_ticks():
            xtick = tick.label1.get_text()
            if xtick and xtick.isdigit() and int(xtick) % 14 == 0:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick1line.set_markersize(self.x_tick_length)
            else:
                tick.tick1line.set_markersize(0)


class Daily(DailyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER DAY", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]]
        self.left_y_labels = [f"{tick:,}" for tick in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]
        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label,
                         a=1,
                         b=2,
                         c=7,
                         ymin=1 * 0.69,
                         ymax=1000000,
                         style_color=style_color,
                         custom_grid_color=custom_grid_color)
        self._setup_axes()
        self.ax.yaxis.set_label_coords(-0.13, 0.5)


class DailyMinute(DailyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER MINUTE", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]]]
        self.left_y_labels = ["0.001", "0.005", "0.01", "0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1000"]
        self.right_y_ticks = [1 / m for m in [10 / 60, 15 / 60, 20 / 60, 30 / 60, 1, 2, 5, 10, 20, 60, 50, 100, 200, 500, 1000, 60 * 2, 60 * 4, 60 * 8, 60 * 16]]
        self.right_y_labels = ['10" sec', '15"', '20"', '30"', "1' min", "2'", "5'", "10'", "20'", "            – 1 h", "50'", "100'", "200'", "500'", "1000'",
                               "            – 2 h",
                               "            – 4 h",
                               "            – 8 h",
                               "            – 16 h"]

        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label,
                         a=0.001,
                         b=2,
                         c=7,
                         ymin=0.001 * 0.69,
                         ymax=1000,
                         style_color=style_color,
                         custom_grid_color=custom_grid_color)

        self._setup_axes()
        self.draw_floor_grid(self.right_y_ticks)
        self.setup_right_y_axis()
        self.ax.yaxis.set_label_coords(-0.1, 0.5)

    def setup_right_y_axis(self):
        self.ax3 = plt.twinx()
        self.ax3.set_ylim(self.ymin, self.ymax)
        self.ax3.set_yscale("log")
        self.ax3.set_yticks(self.right_y_ticks)
        self.ax3.set_yticklabels(self.right_y_labels, fontsize=self.right_y_axis_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax3.tick_params(axis='both', which='minor', length=0)
        self.ax3.tick_params(axis="both", colors=self.style_color)
        self.ax3.spines["top"].set_color(self.custom_grid_color)
        self.ax3.spines["left"].set_color(self.custom_grid_color)
        self.ax3.spines["right"].set_color(self.custom_grid_color)
        self.ax3.spines["bottom"].set_visible(False)
        self.ax3.set_ylabel('COUNTING TIMES', fontname=self.font, fontsize=self.general_fontsize * 0.8, color=self.style_color, weight="bold")
        self.ax3.yaxis.set_label_coords(1.03, 0.85)

        self.ax3.tick_params(color=self.custom_grid_color)
        for tick in self.ax3.yaxis.get_major_ticks():
            tick_value = tick.label1.get_text()
            if tick_value in ["1' min", "10'", "100'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick2line.set_markeredgewidth(self.major_grid_width)
            elif tick_value in ["20'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)
                tick.tick2line.set_markeredgewidth(self.major_grid_width * 0.5)
            elif 'h' in tick_value:
                tick.tick2line.set_markeredgewidth(0)

        # for tick in self.ax3.yaxis.get_major_ticks():
        #     tick_value = tick.label1.get_text()
        #     if tick_value in ['15"', '20"']:
        #         tick.label2.set_fontsize(self.right_y_axis_fontsize * 0.85)  # Shrink labels


class WeeklyTemplate(Chart):
    def __init__(self, date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, a, b, c, ymin, ymax, style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, style_color, custom_grid_color)
        self.a = a
        self.b = b
        self.c = c
        self.angle = 34
        self.xmin = 0
        self.xmax = 100
        self.ymin = ymin
        self.ymax = ymax
        self.x = np.arange(self.xmin, self.xmax)
        self.y = self.a * pow(self.b, self.x / self.c)
        self.relative_width = self.space_right - self.space_left
        self.relative_height = self.space_top - self.space_bottom
        self.image_ratio = self.relative_width / self.relative_height
        self.y_axis_expansion = (np.log10(ymax) - np.log10(ymin)) / (np.log10(ymax) - np.log10(ymin / 0.69))
        self.height = self.image_ratio * self.width * np.tan(self.angle / 180 * np.pi) * self.y_axis_expansion

        # Positioning
        self.credit_vert_pos = - 0.23
        self.top_x_labels_vert_pos = 1.01

        # Scaling
        self.month_label_size = 0.8 * width
        self.top_x_tick_length = 2.222 * width

    def get_sundays_for_months(self, months):
        result = {}
        index = 0

        for month in months:
            start_date = pd.to_datetime(month).normalize().replace(day=1)
            sundays = pd.date_range(start_date, periods=31, freq='W-SUN')
            sundays = [sunday for sunday in sundays if sunday.month == start_date.month]

            for i in range(5):
                if i < len(sundays):
                    result[index] = sundays[i]
                index += 1

        return result

    def _setup_axes(self):
        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height))
        self.ax.yaxis.set_label_coords(-0.11, 0.5)
        plt.subplots_adjust(left=self.space_left, right=self.space_right, bottom=self.space_bottom, top=self.space_top)

        # Date ranges
        self.weekday_of_previous_month = (self.start_date.replace(day=1) - pd.Timedelta(days=1)).replace(day=1).normalize()
        months_20 = pd.date_range(pd.to_datetime(self.weekday_of_previous_month).normalize().replace(day=1), periods=20, freq='MS')
        self.date_to_pos = {v: k for k, v in self.get_sundays_for_months(months_20).items()}
        self.all_dates = [date for date in self.date_to_pos.keys()]

        # Ticks
        self.bottom_x_ticks = [k for k in self.date_to_pos.values()]
        if 100 not in self.bottom_x_ticks:
            self.bottom_x_ticks.append(100)

        self.bottom_x_tick_labels = []
        self.bottom_x_tick_map = []
        for x_tick, x_label in zip(self.bottom_x_ticks, [i for i in range(0, len(self.bottom_x_ticks))]):
            if x_tick % 10 == 0:
                self.bottom_x_tick_labels.append(str(x_label))
            else:
                self.bottom_x_tick_labels.append('')

        # For daily celeration mapping (needed some special handling due to being Weekly)
        self.test_map = {tick: map_value for tick, map_value in zip([i for i in range(0, len(self.bottom_x_ticks))], self.bottom_x_ticks)}
        days_from_base = np.array([(ts - self.all_dates[0]).days for ts in self.all_dates])
        self.x_to_day_count = {}
        for x_i, day_count in zip(range(len(self.all_dates)), days_from_base):
            self.x_to_day_count[self.test_map[x_i]] = day_count

        # # Tick labels
        self.top_x_ticks = np.arange(0, 21)
        self.top_x_tick_labels = [str(int((x / 10) * 2)) if x % 10 == 0 else "" for x in self.bottom_x_ticks]
        self.month_labels = months_20.strftime('%b\n%y').tolist()

        # # Set up main axis
        self.ax.set_yscale("log")
        self.ax.spines["bottom"].set_position(("axes", -0.03))
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_xticks(self.bottom_x_ticks)
        self.ax.set_xticklabels(self.bottom_x_tick_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax.set_yticks(self.left_y_ticks)
        self.ax.set_yticklabels(self.left_y_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')

        self.ax.tick_params(axis='y', which='minor', length=0)
        self.ax.tick_params(axis="y", which='major', width=self.major_grid_width, color=self.custom_grid_color, length=5)
        self.ax.tick_params(axis='x', which='both', length=5, color=self.custom_grid_color, width=self.minor_grid_width)

        self.ax.set_ylabel(self.y_label, fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.set_xlabel("SUCCESSIVE CALENDAR WEEKS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.xaxis.set_label_coords(0.5, -0.1)

        for label in self.ax.get_yticklabels():
            if '5' in label.get_text():
                label.set_fontsize(self.general_fontsize * self.general_fontsize_minor_scaling)
            else:
                label.set_fontsize(self.general_fontsize)

        for tick in self.ax.yaxis.get_major_ticks():
            ytick = tick.label1.get_text()
            if '5' in ytick:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)

        self.ax.xaxis.set_tick_params(which='both', direction='inout')
        for tick in self.ax.xaxis.get_major_ticks():
            xtick = tick.label1.get_text()
            if xtick and xtick.isdigit() and xtick in self.bottom_x_tick_labels:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick1line.set_markersize(self.x_tick_length)
            else:
                tick.tick1line.set_markersize(0)

        # Set up top x-axis
        self.ax2 = self.ax.twiny()
        self.ax2.set_xticks(self.bottom_x_ticks)
        self.ax2.set_xticklabels(self.top_x_tick_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax2.tick_params(axis='both', which='both', color=self.custom_grid_color, length=self.top_x_tick_length, width=self.major_grid_width)
        self.ax2.set_xlabel("SUCCESSIVE CALENDAR MONTHS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold", labelpad=self.top_x_label_pad)
        self.trans = transforms.blended_transform_factory(self.ax.transData, self.ax.transAxes)
        for tick, label in zip(np.arange(0, 100, 5), self.month_labels):
            horizontal_off_set = 2.5
            self.ax.text(tick + horizontal_off_set, self.top_x_labels_vert_pos, label, transform=self.trans, fontname=self.font, fontsize=self.month_label_size, color=self.style_color, ha="center", weight='bold')

        tick_refs = [str(int((x / 10) * 2)) if x % 5 == 0 else "" for x in self.bottom_x_ticks]
        for ref, tick in zip(tick_refs, self.ax2.xaxis.get_major_ticks()):
            if ref == '':
                tick.tick2line.set_markersize(0)

        # Set spines for both axes
        for position in self.ax.spines.keys():
            self.ax.spines[position].set_color(self.custom_grid_color)
            self.ax.spines[position].set_linewidth(self.major_grid_width)
            self.ax2.spines[position].set_visible(False)

        # # Add grid lines
        self.draw_major_grid(np.arange(0, 101, 5))
        if self.minor_grid_on:
            self.ax.grid(which="both", visible=self.minor_grid_on, color=self.custom_grid_color, linewidth=self.minor_grid_width)


class Weekly(WeeklyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER WEEK", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=1,
            b=2,
            c=4,
            ymin=1 * 0.69,
            ymax=1000000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]]
        self.left_y_labels = [f"{tick:,}" for tick in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]

        self._setup_axes()
        self.ax.yaxis.set_label_coords(-0.13, 0.5)


class WeeklyMinute(WeeklyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER MINUTE", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.right_y_ticks = [1 / m for m in [10 / 60, 15 / 60, 20 / 60, 30 / 60, 1, 2, 5, 10, 20, 60, 50, 100, 200, 500, 1000, 60 * 2, 60 * 4, 60 * 8, 60 * 16]]
        self.right_y_labels = ['10" sec', '15"', '20"', '30"', "1' min", "2'", "5'", "10'", "20'", "            – 1 h", "50'", "100'", "200'", "500'", "1000'",
                               "            – 2 h",
                               "            – 4 h",
                               "            – 8 h",
                               "            – 16 h"]
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]]]
        self.left_y_labels = ["0.001", "0.005", "0.01", "0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1000"]
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=0.001,
            b=2,
            c=7,
            ymin=0.001 * 0.69,
            ymax=1000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self._setup_axes()
        self.draw_floor_grid(self.right_y_ticks)
        self.setup_right_y_axis()
        self.ax.yaxis.set_label_coords(-0.1, 0.5)

    def setup_right_y_axis(self):
        self.ax3 = plt.twinx()
        self.ax3.set_ylim(self.ymin, self.ymax)
        self.ax3.set_yscale("log")
        self.ax3.set_yticks(self.right_y_ticks)
        self.ax3.set_yticklabels(self.right_y_labels, fontsize=self.right_y_axis_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax3.tick_params(axis='both', which='minor', length=0)
        self.ax3.tick_params(axis="both", colors=self.style_color)
        self.ax3.spines["top"].set_color(self.custom_grid_color)
        self.ax3.spines["left"].set_color(self.custom_grid_color)
        self.ax3.spines["right"].set_color(self.custom_grid_color)
        self.ax3.spines["bottom"].set_visible(False)
        self.ax3.set_ylabel('COUNTING TIMES', fontname=self.font, fontsize=self.general_fontsize * 0.8, color=self.style_color, weight="bold")
        self.ax3.yaxis.set_label_coords(1.03, 0.85)

        self.ax3.tick_params(color=self.custom_grid_color)
        for tick in self.ax3.yaxis.get_major_ticks():
            tick_value = tick.label1.get_text()
            if tick_value in ["1' min", "10'", "100'", "1000'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick2line.set_markeredgewidth(self.major_grid_width)
            elif tick_value in ["20'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)
                tick.tick2line.set_markeredgewidth(self.major_grid_width * 0.5)
            elif 'h' in tick_value:
                tick.tick2line.set_markeredgewidth(0)


class MonthlyTemplate(Chart):
    def __init__(self, date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, a, b, c, ymin, ymax, style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, style_color, custom_grid_color)
        self.a = a
        self.b = b
        self.c = c
        self.angle = 34
        self.xmin = 0
        self.xmax = 120
        self.ymin = ymin
        self.ymax = ymax
        self.x = np.arange(self.xmin, self.xmax)
        self.y = self.a * pow(self.b, self.x / self.c)
        self.relative_width = self.space_right - self.space_left
        self.relative_height = self.space_top - self.space_bottom
        self.image_ratio = self.relative_width / self.relative_height
        self.y_axis_expansion = (np.log10(ymax) - np.log10(ymin)) / (np.log10(ymax) - np.log10(ymin / 0.69))
        self.height = self.image_ratio * self.width * np.tan(self.angle / 180 * np.pi) * self.y_axis_expansion

        # Positioning
        self.credit_vert_pos = - 0.23
        self.year_vert_pos = 1.025

        # Scaling
        self.year_font_size = 1.5 * width
        self.top_x_tick_length = 2.222 * width

    def _setup_axes(self):
        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height))
        plt.subplots_adjust(left=self.space_left, right=self.space_right, bottom=self.space_bottom, top=self.space_top)

        # Bottom x-axis ticks
        self.bottom_x_ticks = np.arange(0, 121, 1)
        self.bottom_x_tick_labels = self.bottom_x_ticks[::12]

        # Top x-axis ticks
        self.top_x_ticks = np.arange(0, 121, 12)
        self.top_x_tick_labels = [str(i) for i in range(len(self.top_x_ticks))]

        # Set up primary axis
        self.ax.yaxis.set_label_coords(-0.11, 0.5)
        self.ax.spines["bottom"].set_position(("axes", -0.03))
        self.ax.set_yscale("log")
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_xticks(self.bottom_x_ticks)
        self.ax.set_xticklabels([str(tick) if tick in self.bottom_x_tick_labels else '' for tick in self.bottom_x_ticks], fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax.set_yticks(self.left_y_ticks)
        self.ax.set_yticklabels(self.left_y_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')

        self.ax.tick_params(axis='y', which='minor', length=0)
        self.ax.tick_params(axis="y", which='major', width=self.major_grid_width, color=self.custom_grid_color, length=5)
        self.ax.tick_params(axis='x', which='both', length=5, color=self.custom_grid_color, width=self.minor_grid_width)

        # Create date reference
        self.start_date_of_previous_year = self.start_date.replace(year=self.start_date.year - 1, month=1, day=1).normalize()
        self.all_dates = pd.date_range(self.start_date_of_previous_year, periods=self.xmax + 1, freq="M", normalize=True)
        self.date_to_pos = {self.all_dates[i]: i for i in range(len(self.all_dates))}

        # For daily celeration mapping
        days_from_base = np.array([(ts - self.all_dates[0]).days for ts in self.all_dates])
        self.x_to_day_count = {}
        for x_i, day_count in zip(range(len(self.all_dates)), days_from_base):
            self.x_to_day_count[x_i] = day_count

        # Top x-axis
        self.ax2 = plt.twiny()
        self.ax2.set_xticks(self.top_x_ticks)
        self.ax2.set_xticklabels(self.top_x_tick_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax2.tick_params(axis='both', which='both', color=self.custom_grid_color, length=self.top_x_tick_length, width=self.major_grid_width)
        self.ax2.set_xlabel("SUCCESSIVE CALENDAR YEARS",
                            fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold", labelpad=self.top_x_label_pad)
        self.trans = transforms.blended_transform_factory(self.ax.transData, self.ax.transAxes)
        for tick in self.top_x_ticks[:-1]:
            year = self.all_dates[tick].year
            self.ax.text(tick + 6, self.year_vert_pos, str(year)[-2:], transform=self.trans, fontname=self.font, fontsize=self.year_font_size, color=self.style_color, ha="center", weight='bold')

        # Don't show spines for top x-axis
        for spine in self.ax2.spines.values():
            spine.set_visible(False)

        if self.major_grid_on:
            for month in np.arange(0, 120, 6):
                g1 = self.ax.axvline(month, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_date_objects.append(g1)
            for power in [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]:
                g2 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_count_objects.append(g2)
            for power in [0.005, 0.05, 0.5, 5, 50, 500, 5000, 50000, 500000]:
                g3 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width * 0.5, visible=True, zorder=1)
                self.major_grid_count_objects.append(g3)

        if self.minor_grid_on:
            self.ax.grid(which="both", visible=self.minor_grid_on, color=self.custom_grid_color, linewidth=self.minor_grid_width)

        for position in self.ax.spines.keys():
            self.ax.spines[position].set_color(self.custom_grid_color)
            self.ax.spines[position].set_linewidth(self.major_grid_width)

        self.ax.set_ylabel(self.y_label, fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.set_xlabel("SUCCESSIVE CALENDAR MONTHS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.xaxis.set_label_coords(0.5, -0.1)

        for label in self.ax.get_yticklabels():
            if '5' in label.get_text():
                label.set_fontsize(self.general_fontsize * self.general_fontsize_minor_scaling)
            else:
                label.set_fontsize(self.general_fontsize)

        for tick in self.ax.yaxis.get_major_ticks():
            ytick = tick.label1.get_text()
            if '5' in ytick:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)

        self.ax.xaxis.set_tick_params(which='both', direction='inout')
        for tick in self.ax.xaxis.get_major_ticks():
            xtick = tick.label1.get_text()
            if xtick and xtick.isdigit() and int(xtick) in self.bottom_x_tick_labels:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick1line.set_markersize(self.x_tick_length)
            else:
                tick.tick1line.set_markersize(0)


class Monthly(MonthlyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER MONTH", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=1,
            b=2,
            c=5,
            ymin=1 * 0.69,
            ymax=1000000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]]
        self.left_y_labels = [f"{tick:,}" for tick in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]
        self._setup_axes()
        self.ax.yaxis.set_label_coords(-0.13, 0.5)


class MonthlyMinute(MonthlyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER MINUTE", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=0.001,
            b=2,
            c=5,
            ymin=0.001 * 0.69,
            ymax=1000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.right_y_ticks = [1 / m for m in [10 / 60, 15 / 60, 20 / 60, 30 / 60, 1, 2, 5, 10, 20, 60, 50, 100, 200, 500, 1000, 60 * 2, 60 * 4, 60 * 8, 60 * 16]]
        self.right_y_labels = ['10" sec', '15"', '20"', '30"', "1' min", "2'", "5'", "10'", "20'", "            – 1 h", "50'", "100'", "200'", "500'", "1000'",
                               "            – 2 h",
                               "            – 4 h",
                               "            – 8 h",
                               "            – 16 h"]
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]]]
        self.left_y_labels = ["0.001", "0.005", "0.01", "0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1000"]

        self._setup_axes()
        self.draw_floor_grid(self.right_y_ticks)
        self.setup_right_y_axis()
        self.ax.yaxis.set_label_coords(-0.1, 0.5)

    def setup_right_y_axis(self):
        self.ax3 = plt.twinx()
        self.ax3.set_ylim(self.ymin, self.ymax)
        self.ax3.set_yscale("log")
        self.ax3.set_yticks(self.right_y_ticks)
        self.ax3.set_yticklabels(self.right_y_labels, fontsize=self.right_y_axis_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax3.tick_params(axis='both', which='minor', length=0)
        self.ax3.tick_params(axis="both", colors=self.style_color)
        self.ax3.spines["top"].set_color(self.custom_grid_color)
        self.ax3.spines["left"].set_color(self.custom_grid_color)
        self.ax3.spines["right"].set_color(self.custom_grid_color)
        self.ax3.spines["bottom"].set_visible(False)
        self.ax3.set_ylabel('COUNTING TIMES', fontname=self.font, fontsize=self.general_fontsize * 0.8, color=self.style_color, weight="bold")
        self.ax3.yaxis.set_label_coords(1.03, 0.85)

        self.ax3.tick_params(color=self.custom_grid_color)
        for tick in self.ax3.yaxis.get_major_ticks():
            tick_value = tick.label1.get_text()
            if tick_value in ["1' min", "10'", "100'", "1000'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick2line.set_markeredgewidth(self.major_grid_width)
            elif tick_value in ["20'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)
                tick.tick2line.set_markeredgewidth(self.major_grid_width * 0.5)
            elif 'h' in tick_value:
                tick.tick2line.set_markeredgewidth(0)


class YearlyTemplate(Chart):
    def __init__(self, date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, a, b, c, ymin, ymax, style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(date_format, start_date, width, major_grid_on, minor_grid_on, floor_grid_on, y_label, style_color, custom_grid_color)

        self.a = a
        self.b = b
        self.c = c
        self.angle = 34
        self.xmin = 0
        self.xmax = 100
        self.ymin = ymin
        self.ymax = ymax
        self.x = np.arange(self.xmin, self.xmax)
        self.y = self.a * pow(self.b, self.x / self.c)
        self.relative_width = self.space_right - self.space_left
        self.relative_height = self.space_top - self.space_bottom
        self.image_ratio = self.relative_width / self.relative_height
        self.y_axis_expansion = (np.log10(ymax) - np.log10(ymin)) / (np.log10(ymax) - np.log10(ymin / 0.69))
        self.height = self.image_ratio * self.width * np.tan(self.angle / 180 * np.pi) * self.y_axis_expansion

        # Positioning
        self.credit_vert_pos = - 0.23
        self.year_vert_pos = 1.025

        # Scaling
        self.year_font_size = 1.15 * width
        self.top_x_tick_length = 2.222 * width

    def _setup_axes(self):
        self.fig, self.ax = plt.subplots(figsize=(self.width, self.height))
        plt.subplots_adjust(left=self.space_left, right=self.space_right, bottom=self.space_bottom, top=self.space_top)

        # Bottom x-axis ticks
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.bottom_x_tick_labels = self.bottom_x_ticks[::10]

        # Top x-axis ticks
        self.top_x_ticks = np.arange(0, 101, 10)
        self.top_x_tick_labels = [str(i) if i % 5 == 0 else '' for i in range(len(self.top_x_ticks))]

        # # Set up primary axis
        self.ax.yaxis.set_label_coords(-0.11, 0.5)
        self.ax.spines["bottom"].set_position(("axes", -0.03))
        self.ax.set_yscale("log")
        self.ax.set_ylim(self.ymin, self.ymax)
        self.ax.set_xlim(self.xmin, self.xmax)
        self.ax.set_xticks(self.bottom_x_ticks)
        self.ax.set_xticklabels([str(tick) if tick in self.bottom_x_tick_labels else '' for tick in self.bottom_x_ticks], fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax.set_yticks(self.left_y_ticks)
        self.ax.set_yticklabels(self.left_y_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')

        self.ax.tick_params(axis='y', which='minor', length=0)
        self.ax.tick_params(axis="y", which='major', width=self.major_grid_width, color=self.custom_grid_color, length=5)
        self.ax.tick_params(axis='x', which='both', length=5, color=self.custom_grid_color, width=self.minor_grid_width)

        # Create date reference
        self.start_date_of_decade = self.start_date.replace(year=self.start_date.year - (self.start_date.year % 10), month=1, day=1).normalize()
        self.all_dates = pd.date_range(self.start_date_of_decade, periods=self.xmax + 1, freq="Y", normalize=True)
        self.date_to_pos = {self.all_dates[i]: i for i in range(len(self.all_dates))}

        # For daily celeration mapping
        days_from_base = np.array([(ts - self.all_dates[0]).days for ts in self.all_dates])
        self.x_to_day_count = {}
        for x_i, day_count in zip(range(len(self.all_dates)), days_from_base):
            self.x_to_day_count[x_i] = day_count

        # # Top x-axis
        self.ax2 = plt.twiny()
        self.ax2.set_xticks(self.top_x_ticks)
        self.ax2.set_xticklabels(self.top_x_tick_labels, fontsize=self.general_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax2.tick_params(axis='both', which='both', color=self.custom_grid_color, length=self.top_x_tick_length, width=self.major_grid_width)
        self.ax2.set_xlabel("SUCCESSIVE CALENDAR DECADES", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold", labelpad=self.top_x_label_pad)
        self.trans = transforms.blended_transform_factory(self.ax.transData, self.ax.transAxes)
        for tick in self.top_x_ticks[:-1]:
            year = self.all_dates[tick].year
            self.ax.text(tick + 5, self.year_vert_pos, str(year), transform=self.trans, fontname=self.font, fontsize=self.year_font_size, color=self.style_color, ha="center", weight='bold')

        # Don't show spines for top x-axis
        for spine in self.ax2.spines.values():
            spine.set_visible(False)

        if self.major_grid_on:
            for year in self.bottom_x_ticks[::5]:
                g1 = self.ax.axvline(year, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_date_objects.append(g1)
            for power in [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000]:
                g2 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width, visible=True, zorder=1)
                self.major_grid_count_objects.append(g2)
            for power in [0.005, 0.05, 0.5, 5, 50, 500, 5000, 50000, 500000]:
                g3 = self.ax.axhline(power, color=self.custom_grid_color, linewidth=self.major_grid_width * 0.5, visible=True, zorder=1)
                self.major_grid_count_objects.append(g3)

        if self.minor_grid_on:
            self.ax.grid(which="both", visible=self.minor_grid_on, color=self.custom_grid_color, linewidth=self.minor_grid_width)

        for position in self.ax.spines.keys():
            self.ax.spines[position].set_color(self.custom_grid_color)
            self.ax.spines[position].set_linewidth(self.major_grid_width)

        self.ax.set_ylabel(self.y_label, fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.set_xlabel("SUCCESSIVE CALENDAR YEARS", fontname=self.font, fontsize=self.general_fontsize, color=self.style_color, weight="bold")
        self.ax.xaxis.set_label_coords(0.5, -0.1)

        for label in self.ax.get_yticklabels():
            if '5' in label.get_text():
                label.set_fontsize(self.general_fontsize * self.general_fontsize_minor_scaling)
            else:
                label.set_fontsize(self.general_fontsize)

        for tick in self.ax.yaxis.get_major_ticks():
            ytick = tick.label1.get_text()
            if '5' in ytick:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)

        self.ax.xaxis.set_tick_params(which='both', direction='inout')
        for tick in self.ax.xaxis.get_major_ticks():
            xtick = tick.label1.get_text()
            if xtick and xtick.isdigit() and int(xtick) in self.bottom_x_tick_labels:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick1line.set_markersize(self.x_tick_length)
            else:
                tick.tick1line.set_markersize(0)


class Yearly(YearlyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER YEAR", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=1,
            b=2,
            c=5,
            ymin=1 * 0.69,
            ymax=1000000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]]
        self.left_y_labels = [f"{tick:,}" for tick in [1, 5, 10, 50, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000, 1000000]]

        self._setup_axes()
        self.ax.yaxis.set_label_coords(-0.13, 0.5)


class YearlyMinute(YearlyTemplate):
    def __init__(self, date_format=None, start_date=None, width=9, major_grid_on=True, minor_grid_on=True, floor_grid_on=False, y_label="COUNT PER MINUTE", style_color='#5a93cc', custom_grid_color='#71B8FF'):
        super().__init__(
            date_format=date_format,
            start_date=start_date,
            width=width,
            major_grid_on=major_grid_on,
            minor_grid_on=minor_grid_on,
            floor_grid_on=floor_grid_on,
            y_label=y_label,
            a=0.001,
            b=2,
            c=5,
            ymin=0.001 * 0.69,
            ymax=1000,
            style_color=style_color,
            custom_grid_color=custom_grid_color,
        )

        self.vert_pos = 1.03
        self.bottom_x_ticks = np.arange(0, 101, 1)
        self.right_y_ticks = [1 / m for m in [10 / 60, 15 / 60, 20 / 60, 30 / 60, 1, 2, 5, 10, 20, 60, 50, 100, 200, 500, 1000, 60 * 2, 60 * 4, 60 * 8, 60 * 16]]
        self.right_y_labels = ['10" sec', '15"', '20"', '30"', "1' min", "2'", "5'", "10'", "20'", "            – 1 h", "50'", "100'", "200'", "500'", "1000'",
                               "            – 2 h",
                               "            – 4 h",
                               "            – 8 h",
                               "            – 16 h"]
        self.left_y_ticks = [10 ** e for e in [np.log10(i) for i in [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1000]]]
        self.left_y_labels = ["0.001", "0.005", "0.01", "0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1000"]

        self._setup_axes()
        self.draw_floor_grid(self.right_y_ticks)
        self.setup_right_y_axis()
        self.ax.yaxis.set_label_coords(-0.1, 0.5)

    def setup_right_y_axis(self):
        self.ax3 = plt.twinx()
        self.ax3.set_ylim(self.ymin, self.ymax)
        self.ax3.set_yscale("log")
        self.ax3.set_yticks(self.right_y_ticks)
        self.ax3.set_yticklabels(self.right_y_labels, fontsize=self.right_y_axis_fontsize, fontname=self.font, color=self.style_color, weight='bold')
        self.ax3.tick_params(axis='both', which='minor', length=0)
        self.ax3.tick_params(axis="both", colors=self.style_color)
        self.ax3.spines["top"].set_color(self.custom_grid_color)
        self.ax3.spines["left"].set_color(self.custom_grid_color)
        self.ax3.spines["right"].set_color(self.custom_grid_color)
        self.ax3.spines["bottom"].set_visible(False)
        self.ax3.set_ylabel('COUNTING TIMES', fontname=self.font, fontsize=self.general_fontsize * 0.8, color=self.style_color, weight="bold")
        self.ax3.yaxis.set_label_coords(1.03, 0.85)

        self.ax3.tick_params(color=self.custom_grid_color)
        for tick in self.ax3.yaxis.get_major_ticks():
            tick_value = tick.label1.get_text()
            if tick_value in ["1' min", "10'", "100'", "1000'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width)
                tick.tick2line.set_markeredgewidth(self.major_grid_width)
            elif tick_value in ["20'"]:
                tick.tick1line.set_markeredgewidth(self.major_grid_width * 0.5)
                tick.tick2line.set_markeredgewidth(self.major_grid_width * 0.5)
            elif 'h' in tick_value:
                tick.tick2line.set_markeredgewidth(0)


if __name__ == '__main__':
    chart = DailyMinute()
    plt.show()