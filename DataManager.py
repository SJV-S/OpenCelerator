import pandas as pd
import numpy as np
import os
import copy
import json
import platform
from datetime import datetime
import math


class DataManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):

            self.default_corr_point_style = {'marker_face_color': 'black',
                                             'marker_edge_color': 'black',
                                             'marker': 'o',
                                             'linewidth': 0.5,
                                             'markersize': 8,
                                             'linestyle': '-',
                                             'line_color': 'black'
                                             }

            self.default_err_point_style = {'marker_face_color': 'black',
                                             'marker_edge_color': 'black',
                                             'marker': 'x',
                                             'linewidth': 0.5,
                                             'markersize': 35,
                                             'linestyle': '-',
                                             'line_color': 'black'
                                            }

            self.default_floor_point_style = {'marker_face_color': 'black',
                                             'marker_edge_color': 'black',
                                             'marker': '_',
                                             'linewidth': 0.5,
                                             'markersize': 5,
                                             'markeredgewidth': 1.5,
                                             'linestyle': '',
                                             'line_color': 'black'
                                              }

            self.default_misc_point_style = {'marker_face_color': 'black',
                                             'marker_edge_color': 'black',
                                             'marker': 'v',
                                             'linewidth': 0.5,
                                             'markersize': 8,
                                             'linestyle': '-',
                                             'line_color': 'black'
                                             }

            self.default_phase_style = {
                'date': None,
                'y_line': None,
                'y_text': None,
                'text': None,
                'font_size': 12,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',
                'edge_color': '#000000',
                'line_color': '#000000',
                'linewidth': 1,
                'linestyle': '-',
                'text_mode': None,
                'text_position': None,
            }

            self.default_aim_style = {
                'date1': None,
                'date2': None,
                'y': None,
                'baseline': None,
                'text': None,
                'text_pos': None,
                'line_type': 'Flat',
                'font_size': 10,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',
                'edge_color': '#000000',
                'line_color': '#000000',
                'linewidth': 1,
                'linestyle': '-',
            }

            self.default_corr_trend_style = {
                'date1': None,
                'date2': None,
                'text': None,
                'text_date': None,
                'forward_projection': 0,
                'font_size': 10,
                'font_color': '#008000',
                'bg_color': '#FFFFFF',
                'edge_color': '#000000',
                'line_color': '#008000',
                'linewidth': 1,
                'linestyle': '-',
            }

            self.default_err_trend_style = {
                'date1': None,
                'date2': None,
                'y': None,
                'text': None,
                'text_y': None,
                'text_date': None,
                'forward_projection': 0,
                'font_size': 10,
                'font_color': '#EE4B2B',
                'bg_color': '#FFFFFF',
                'edge_color': '#000000',
                'line_color': '#EE4B2B',
                'linewidth': 1,
                'linestyle': '-',
            }

            self.user_preferences = {
                'div_deceleration': True,
                'place_below_floor': False,
                'chart_data_agg': 'sum',
                'chart_type': 'DailyMinute',
                'chart_font_color': '#05c3de',
                'chart_grid_color': '#6ad1e3',
                'width': 10,
                'phase_text_type': 'Flag',
                'phase_text_position': 'Top',
                'aim_line_type': 'Flat',
                'aim_text_position': 'Middle',
                'fit_method': 'Least-squares',
                'bounce_envelope': 'None',
                'celeration_unit': 'Weekly (standard)',
                'forward_projection': 0,
                'home_folder': os.path.expanduser("~"),
                'corr_style': self.default_corr_point_style,
                'err_style': self.default_err_point_style,
                'floor_style': self.default_floor_point_style,
                'misc_style': self.default_misc_point_style,
                'phase_style': self.default_phase_style,
                'aim_style': self.default_aim_style,
                'trend_corr_style': self.default_corr_trend_style,
                'trend_err_style': self.default_err_trend_style,
                'recent_imports': [],
                'recent_charts': [],
                'autosave': True,
            }

            self.chart_data = {
                'type': 'DailyMinute',
                'raw_data': {'d': [], 'm': [], 'c': [], 'i': []},
                'raw_df': pd.DataFrame(columns=['d', 'm', 'c', 'i', 'o']),
                'import_path': None,
                'phase': [],
                'aim': [],
                'trend_corr': [],
                'trend_err': [],
                'credit': ('SUPERVISOR: ________________    DIVISION: ________________       TIMER: ________________     COUNTED: ________________',
                           'ORGANIZATION: ________________     MANAGER: ________________     COUNTER: ________________     CHARTER: ________________',
                           'ADVISOR: ________________        ROOM: ________________   PERFORMER: ________________        NOTE: ________________'),
                'start_date': None,
                'data_point_styles': {},
                'view_check': {
                    'minor_grid': True,
                    'major_grid': True,
                    'dots': True,
                    'xs': True,
                    'dot_trends': True,
                    'x_trends': True,
                    'dot_bounce': True,
                    'x_bounce': True,
                    'dot_est': True,
                    'x_est': True,
                    'timing_floor': True,
                    'timing_grid': False,
                    'phase_lines': True,
                    'aims': True,
                    'fan': True,
                    'credit_spacing': True,
                    'misc': True,
                }
            }

            # Necessary for backwards compatibility corrections
            # Also used for not trigger autosave in some cases
            self.default_chart = copy.deepcopy(self.chart_data)

            # Celeration unit dictionary
            self.cel_unit_dict = {'Daily': 1,
                                  'Weekly (standard)': 7,
                                  'Monthly (Weekly x4)': 28,
                                  'Yearly (Weekly x52)': 365,
                                  }

            # Support classes
            self.trend_fitter = TrendFitter(self)

            # Control variables
            self.initialized = True  # Set this attribute after initializing
            self.chart_data_default = copy.deepcopy(self.chart_data)

            # Boolean arrays for preventing trendlines to be affected by zero counts
            self.mask_corr_zero_counts = None
            self.mask_err_zero_counts = None

            self.standard_date_string = '%Y-%m-%d'
            self.df_plot = None  # df created from raw data for plotting

            # Apply settings
            self.get_user_preferences()

    def ensure_backwards_compatibility(self, sample_dict, default_dict):
        for key, value in default_dict.items():
            if key not in sample_dict:
                sample_dict[key] = value
            elif isinstance(value, dict) and isinstance(sample_dict[key], dict):
                # Apply recursively if value in default_dict and sample_dict are dictionaries
                self.ensure_backwards_compatibility(sample_dict[key], value)
        return sample_dict

    def format_y_value(self, y_value):
        if y_value >= 10:
            return int(y_value)
        elif y_value >= 1:
            return round(y_value, 1)
        elif y_value >= 0.1:
            return round(y_value, 2)
        elif y_value >= 0.01:
            return round(y_value, 3)
        else:
            return round(y_value, 4)

    def get_aim_slope_text(self, text_pos, xmin, xmax, ymin, ymax, x_to_day_count):
        # Convert dimensionless x-values to days and get celeration label
        daily_slope = (np.log10(ymin) - np.log10(ymax)) / (x_to_day_count[xmin] - x_to_day_count[xmax])
        cel_label = self.trend_fitter.get_trend_label(daily_slope)

        chart_type = self.user_preferences['chart_type'][0].lower()
        doubling = {'d': 7, 'w': 5, 'm': 6, 'y': 5}
        unit = doubling[chart_type]
        celeration = (ymax / ymin) ** (unit / (xmax - xmin))
        angle = np.degrees(np.atan(np.log10(celeration) / (np.log10(2) / np.tan(np.radians(34)))))

        if text_pos == 'Left':
            ha = 'left'
            rel_pos = 0
        elif text_pos == 'Right':
            ha = 'right'
            rel_pos = 1
        else:
            ha = 'center'
            rel_pos = 0.5

        pos_x = xmin + rel_pos * (xmax - xmin)
        pos_y = ymin * (ymax / ymin) ** rel_pos

        # Get text offset
        text_distance_to_line = 0.3
        text_offset_x = -text_distance_to_line * np.sin(np.radians(angle))
        text_offset_y = text_distance_to_line * np.cos(np.radians(angle))

        return pos_x, pos_y, ha, angle, cel_label, text_offset_x, text_offset_y

    def find_closest_date(self, date_str, date_to_pos, date_format=None):
        if date_format is None:
            date_format = self.standard_date_string

        date = pd.to_datetime(date_str, format=date_format)
        min_date = min(date_to_pos.keys())
        max_date = max(date_to_pos.keys())

        if date in date_to_pos:
            return date
        elif min_date <= date <= max_date:
            closest_date = min(date_to_pos.keys(), key=lambda d: abs(d - date))
            return closest_date
        else:
            return None

    def find_closest_x(self, x, date_to_pos):
        if x is not None:
            if x in date_to_pos.values():
                return x
            elif (x - 1) in date_to_pos.values():
                return x - 1
            elif (x + 1) in date_to_pos.values():
                return x + 1
            else:
                return None
        else:
            return None

    def get_replot_points(self, date_to_x):
        df = copy.deepcopy(self.chart_data['raw_df'])

        # Index will be an object dtype otherwise and return a string, causing errors in point styling
        df.index = pd.to_numeric(df.index, errors='coerce')

        # Currently just a patch to handle manual entries
        if not pd.api.types.is_datetime64_any_dtype(df['d']):
            df['d'] = pd.to_datetime(df['d'])

        chart_type = self.user_preferences['chart_type']
        agg_type = chart_type[0]
        df['d'] = pd.to_datetime(df['d'])

        if self.user_preferences['chart_data_agg'] == "stack":
            if 'D' != agg_type:
                date_keys = pd.Series(list(date_to_x.keys()))
                date_keys = sorted(date_keys)
                bins = pd.cut(df['d'], bins=date_keys, right=True, labels=date_keys[1:])
                df['d'] = bins  # Assign the corresponding upper bound to each row
                df.dropna(subset=['d'], inplace=True)  # Drop rows where 'd' is None (those that were discarded)
        else:
            # Aggregating the values as per user preferences.
            df.set_index('d', inplace=True)
            df = df.resample(agg_type).agg(self.user_preferences['chart_data_agg']).reset_index()

            # Drop padded dates (they are introduced during resampling)
            df = df.loc[~(((df['m'] == 0) | df['m'].isna()) &
                          ((df['c'] == 0) | df['c'].isna()) &
                          ((df['i'] == 0) | df['i'].isna()))]

        # Filter data points based on current date range / chart window
        df = df[df['d'].isin(date_to_x.keys())]

        # Get plot variables
        df['x'] = pd.to_datetime(df['d']).map(date_to_x)
        df['floor'] = 1 / df['m']

        # Replace 0 in 'm' with NaN for safety or everything in m with 1
        if 'Minute' in chart_type:
            m_safe = df['m'].replace(0, np.nan)
        else:
            m_safe = df['m'].apply(lambda x: 1)
        df['corr_freq'] = df['c'] / m_safe
        df['err_freq'] = df['i'] / m_safe

        # Store bool array for any necessary trend filtering
        self.mask_corr_zero_counts = df['corr_freq'] != 0
        self.mask_err_zero_counts = df['err_freq'] != 0

        if self.user_preferences['place_below_floor']:
            # Place zero counts below timing floor
            df['corr_freq'] = np.where(df['corr_freq'] == 0, (1 / m_safe) * 0.8, df['corr_freq'])
            df['err_freq'] = np.where(df['err_freq'] == 0, (1 / m_safe) * 0.8, df['err_freq'])
        else:
            # Do not display zero counts
            df['corr_freq'] = df['corr_freq'].apply(lambda x: np.nan if x == 0 else x)
            df['err_freq'] = df['err_freq'].apply(lambda x: np.nan if x == 0 else x)

        # Sort data points just in case it was manually plotted out of order
        df = df.sort_values(by='d')

        # Necessary to ensure styling alignment
        df = df.reset_index(drop=True)

        # Used for plotting, styling, and trend fitting
        self.df_plot = df

    def data_import_raw(self, file_path):
        data_cols = ['m', 'h', 's', 'c', 'i', 'd', 'o']
        # Determine file type
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xls') or file_path.endswith('.xlsx') or file_path.endswith('.ods'):
            df = pd.read_excel(file_path)

        df = df[df.columns[:7]]  # Only first 7 columns
        df.columns = [col.lower()[0] for col in df.columns]  # Lower case, first letter
        filtered_cols = [col for col in df.columns if col in data_cols]  # Filter columns
        df = df[filtered_cols]

        # Loop over each column and add it with zeros if it's not present
        for col in ['s', 'm', 'h', 'c', 'i', 'o']:
            if col not in df.columns:
                df[col] = 0  # Add the column with zeros

        # Clean up any malformed entries
        df['c'] = pd.to_numeric(df['c'], errors='coerce').fillna(0)
        df['i'] = pd.to_numeric(df['i'], errors='coerce').fillna(0)
        df['o'] = pd.to_numeric(df['o'], errors='coerce').fillna(0)
        df['s'] = pd.to_numeric(df['s'], errors='coerce').fillna(1)
        df['m'] = pd.to_numeric(df['m'], errors='coerce').fillna(1)
        df['h'] = pd.to_numeric(df['h'], errors='coerce').fillna(1)

        # Set negative values to zero
        df.loc[:, 'c'] = df['c'].apply(lambda x: x if x >= 0 else 0)
        df.loc[:, 'i'] = df['i'].apply(lambda x: x if x >= 0 else 0)
        df.loc[:, 'o'] = df['o'].apply(lambda x: x if x >= 0 else 0)
        df.loc[:, 's'] = df['s'].apply(lambda x: x if x >= 0 else 1)
        df.loc[:, 'm'] = df['m'].apply(lambda x: x if x >= 0 else 1)
        df.loc[:, 'h'] = df['h'].apply(lambda x: x if x >= 0 else 1)

        # Get total amount of minutes
        df['m'] = (df['s'] / 60) + df['m'] + (df['h'] * 60)
        # Handling if there was no timing columns of any kind
        has_zeros = (df['m'] == 0).any()
        if has_zeros:
            df['m'] = 1  # Add 'm' column with all values set to 1

        # Discard hour and second columns
        df.drop(columns=['h', 's'], inplace=True)

        # Convert 'd' column to datetime if not already in datetime format
        if not pd.api.types.is_datetime64_any_dtype(df['d']):
            df['d'] = pd.to_datetime(df['d']).dt.date
        df['d'] = pd.to_datetime(df['d'])  # Convert back to a datetime column with no time or timezone information

        # Store imported raw data (also clears any previous data points)
        self.chart_data['raw_df'] = df

    def update_view_check(self, setting, state):
        self.chart_data['view_check'][setting] = bool(state)

    def get_trend(self, x1, x2, corr, x_to_day_count, fit_method=None, bounce_envelope=None, forward_projection=None):
        result = self.trend_fitter.get_trend(x1, x2, corr, x_to_day_count, fit_method, bounce_envelope, forward_projection)
        return result

    def set_chart_type(self, new_type):
        if self.chart_data['type'] != new_type:
            self.chart_data['type'] = new_type
            self.type_changed.emit(new_type)  # Emit signal when type changes

    def save_user_preferences(self):
        system = platform.system()
        home_dir = os.path.expanduser("~")

        if system == "Linux" or system == "Darwin":  # Darwin is macOS
            config_dir = os.path.join(home_dir, '.config', 'OpenCelerator')
        elif system == "Windows":
            config_dir = os.path.join(home_dir, 'AppData', 'Local', 'OpenCelerator')
        else:
            raise OSError("Unsupported operating system")

        filename = 'preferences.json'

        # Ensure the config directory exists
        os.makedirs(config_dir, exist_ok=True)

        filepath = os.path.join(config_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(self.user_preferences, f, indent=4)

    def delete_user_preferences(self):
        system = platform.system()
        home_dir = os.path.expanduser("~")

        if system == "Linux" or system == "Darwin":  # Darwin is macOS
            config_dir = os.path.join(home_dir, '.config', 'OpenCelerator')
        elif system == "Windows":
            config_dir = os.path.join(home_dir, 'AppData', 'Local', 'OpenCelerator')
        else:
            raise OSError("Unsupported operating system")

        filename = 'preferences.json'
        filepath = os.path.join(config_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)

    def get_user_preferences(self):
        system = platform.system()
        home_dir = os.path.expanduser("~")

        if system == "Linux" or system == "Darwin":  # Darwin is macOS
            config_dir = os.path.join(home_dir, '.config', 'OpenCelerator')
        elif system == "Windows":
            config_dir = os.path.join(home_dir, 'AppData', 'Local', 'OpenCelerator')
        else:
            raise OSError("Unsupported operating system")

        filename = 'preferences.json'

        # Ensure the config directory exists
        os.makedirs(config_dir, exist_ok=True)

        filepath = os.path.join(config_dir, filename)

        # If error, delete current file and replace with defaults
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    loaded_pref = json.load(f)
                    self.user_preferences = self.ensure_backwards_compatibility(loaded_pref, self.user_preferences)
            except:
                # Reset malformed json to default
                with open(filepath, 'w') as f:
                    json.dump(self.user_preferences, f, indent=4)
        else:
            with open(filepath, 'w') as f:
                json.dump(self.user_preferences, f, indent=4)

    def save_plot_item(self, item, item_type):
        if item_type == 'phase':
            item['date'] = item['date'].strftime(self.standard_date_string)
            self.chart_data['phase'].append(item)
        elif item_type == 'aim':
            item['date1'] = item['date1'].strftime(self.standard_date_string)
            item['date2'] = item['date2'].strftime(self.standard_date_string)
            self.chart_data['aim'].append(item)
        elif 'trend' in item_type:
            item['date1'] = item['date1'].strftime(self.standard_date_string)
            item['date2'] = item['date2'].strftime(self.standard_date_string)
            item['text_date'] = item['text_date'].strftime(self.standard_date_string)
            self.chart_data[item_type].append(item)
        elif 'bounce' in item_type:
            item['date1'] = item['date1'].strftime(self.standard_date_string)
            item['date2'] = item['date2'].strftime(self.standard_date_string)
            item['text_date'] = item['text_date'].strftime(self.standard_date_string)
            self.chart_data[item_type].append(item)

    def save_chart(self, full_path, start_date):
        # Ensure the file has a .pkl extension
        if not full_path.endswith('.json'):
            full_path += '.json'

        json_to_save = copy.deepcopy(self.chart_data)

        # Replace df with raw data dictionary and covert dates to ISO format
        df = copy.deepcopy(json_to_save['raw_df'])
        if pd.api.types.is_datetime64_any_dtype(df['d']):
            df['d'] = df['d'].dt.strftime(self.standard_date_string)
        del json_to_save['raw_df']
        json_to_save['raw_data'] = df.to_dict()

        # Ensure that the current chart type is saved
        json_to_save['type'] = self.user_preferences['chart_type']

        # Save current start date in ISO format
        json_to_save['start_date'] = start_date.strftime(self.standard_date_string) if isinstance(start_date, datetime) else start_date

        with open(full_path, 'w') as file:
            json.dump(json_to_save, file, indent=4)


class TrendFitter:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def filter_zero_counts_and_below_floor(self, x, y, corr):
        # Prevents trends from being pulled by zero counts

        if corr:
            y = y[self.data_manager.mask_corr_zero_counts]
            x = x[self.data_manager.mask_corr_zero_counts]
        else:
            y = y[self.data_manager.mask_err_zero_counts]
            x = x[self.data_manager.mask_err_zero_counts]

        return x, y

    def get_trend_label(self, slope):
        unit = self.data_manager.user_preferences['celeration_unit']
        unit_case = unit[0].lower()  # First letter of unit
        day_unit_multiple = self.data_manager.cel_unit_dict[unit]
        cel = np.power(10, slope * day_unit_multiple)

        if unit_case == 'm':
            unit_case = '4w'

        if self.data_manager.user_preferences['div_deceleration']:
            if cel < 1:
                symbol = '÷'
                cel = 1 / cel
            else:
                symbol = 'x'
        else:
            symbol = 'x'

        cel_label = f'c = {symbol}{cel:.2f} / {unit_case}'

        return cel_label

    def quarter_intersect_fit(self, x, y):
        # Get dates and rates
        mid_date = np.median(x)
        x1 = np.median(x[x < mid_date])
        x2 = np.median(x[x > mid_date])
        y1 = np.median(y[x < mid_date])
        y2 = np.median(y[x > mid_date])

        # Get trend line
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        return slope, intercept

    def split_middle_line_fit(self, x, y, iter_num=1000):
        # Get quarter intersect fit
        slope, intercept = self.quarter_intersect_fit(x, y)
        quarter_intersect_trend_line = slope * x + intercept

        # Get min and max values for iteration range
        differences = y - quarter_intersect_trend_line
        max_diff = np.max(differences)
        min_diff = np.min(differences)

        # Fit possibilities
        results = np.zeros((iter_num, 3))
        for i, itr in enumerate(np.linspace(min_diff, max_diff, iter_num)):
            adjusted_trend = slope * x + (intercept + itr)

            # Calculate mean squared error
            errors = y - adjusted_trend
            sse = np.mean(errors ** 2)

            # Get rate counts above and below line
            above = np.sum(y > adjusted_trend)
            below = np.sum(y < adjusted_trend)
            abs_diff = abs(above - below)

            results[i] = [itr, abs_diff, sse]

        # Find best fit within most even count
        min_abs_diff = np.min(results[:, 1])
        filtered_results = results[results[:, 1] == min_abs_diff]
        min_sse_row = filtered_results[np.argmin(filtered_results[:, 2])]
        best_itr = min_sse_row[0]
        intercept = intercept + best_itr

        return slope, intercept

    def extract_trend(self, x, y, x_to_day_count, fit_method, bounce_envelope, forward_projection):
        x = np.array(x)
        y = np.array(y)

        # Sort x and y based on the values of x
        sorted_indices = np.argsort(x)
        x = x[sorted_indices]
        y = y[sorted_indices]

        # Boundaries
        x_min_lim = x[0]
        x_max_lin = x[-1]

        # Used to obtain daily slope regardless of chart type
        x_as_day_count = np.array([x_to_day_count[x_i] for x_i in list(x)])

        if forward_projection is None:
            # Plotting trend for the first time
            extended_x = np.arange(x[0], x[-1] + self.data_manager.user_preferences['forward_projection'] + 1)
        else:
            # Loading a finalized trend
            extended_x = np.arange(x[0], x[-1] + forward_projection + 1)

        if fit_method is None:
            fit_method = self.data_manager.user_preferences['fit_method']

        if fit_method == 'Quarter-intersect':
            daily_slope, intercept = self.quarter_intersect_fit(x_as_day_count, np.log10(y))
            slope, intercept = self.quarter_intersect_fit(x, np.log10(y))
            trend = slope * extended_x + intercept
        elif fit_method == 'Split-middle-line':
            daily_slope, intercept = self.quarter_intersect_fit(x_as_day_count, np.log10(y))
            slope, intercept = self.split_middle_line_fit(x, np.log10(y))
            trend = slope * extended_x + intercept
        elif fit_method == 'Least-squares':
            daily_slope, intercept = np.polyfit(x_as_day_count, np.log10(y), 1)
            slope, intercept = np.polyfit(x, np.log10(y), 1)
            trend = np.polyval((slope, intercept), extended_x)

        trend = np.power(10, trend)
        celeration_slope_label = self.get_trend_label(daily_slope)

        if bounce_envelope is None:
            bounce_envelope = self.data_manager.user_preferences['bounce_envelope']
        # Calculate bounce envelope
        if bounce_envelope != 'None':
            residuals = np.log10(y) - (slope * x + intercept)

            if bounce_envelope == '5-95 percentile':
                upper_percentile = np.percentile(residuals, 95)
                lower_percentile = np.percentile(residuals, 5)
                log_upper_bound = slope * extended_x + intercept + upper_percentile
                log_lower_bound = slope * extended_x + intercept + lower_percentile
                upper_bounce = np.power(10, log_upper_bound)
                lower_bounce = np.power(10, log_lower_bound)

            elif bounce_envelope == 'Interquartile range':
                q75, q25 = np.percentile(residuals, 75), np.percentile(residuals, 25)
                iqr = q75 - q25
                log_upper_bound = slope * extended_x + intercept + q75
                log_lower_bound = slope * extended_x + intercept + q25 - iqr
                upper_bounce = np.power(10, log_upper_bound)
                lower_bounce = np.power(10, log_lower_bound)

            elif bounce_envelope == 'Standard deviation':
                std_dev = np.std(residuals)
                mean_residual = np.mean(residuals)
                log_upper_bound = slope * extended_x + intercept + mean_residual + std_dev
                log_lower_bound = slope * extended_x + intercept + mean_residual - std_dev
                upper_bounce = np.power(10, log_upper_bound)
                lower_bounce = np.power(10, log_lower_bound)

            bounce_ratio = upper_bounce[0] / lower_bounce[0]
            bounce_est_label = f'b = x{bounce_ratio:.2f}'
            celeration_slope_label = celeration_slope_label + ', ' + bounce_est_label

        else:
            upper_bounce = None
            lower_bounce = None
            bounce_est_label = None

        return trend, celeration_slope_label, extended_x, upper_bounce, lower_bounce, bounce_est_label, x_min_lim, x_max_lin

    def get_trend(self, x1, x2, corr, x_to_day_count, fit_method=None, bounce_envelope=None, forward_projection=None):
        min_x = min(x1, x2)
        max_x = max(x1, x2)

        df = self.data_manager.df_plot
        x = df['x'].to_numpy()
        y = df['corr_freq' if corr else 'err_freq'].to_numpy()
        x, y = self.filter_zero_counts_and_below_floor(x, y, corr)

        # Get median y for each x if stacking
        point_dict = {val: np.median(y[x == val]) for val in np.unique(x)}

        min_sample = 4
        if len(x) >= min_sample:
            # Filter
            selected_range_set = set(np.arange(min_x, max_x + 1))  # Create a set from the range
            keys_set = set(x)  # Get keys from dictionary as a set
            x_slice = list(selected_range_set & keys_set)  # Find intersection of both sets
            y_slice = [point_dict[x_i] for x_i in x_slice]
        else:
            return

        if len(y_slice) >= min_sample and x1 in x_to_day_count.keys() and x2 in x_to_day_count.keys():
            return self.extract_trend(x_slice, y_slice, x_to_day_count, fit_method, bounce_envelope, forward_projection)










