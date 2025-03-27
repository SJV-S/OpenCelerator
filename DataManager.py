from PySide6.QtCore import QTimer
from matplotlib.markers import MarkerStyle
import pandas as pd
import colorsys
import numpy as np
import os
import copy
import json
import platform
import time
import re
from datetime import datetime
from EventBus import EventBus


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
                'user_col': None,
                'sys_col': None,
                'type': 'trend_corr',
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
                'user_col': None,
                'sys_col': None,
                'type': 'trend_err',
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

            self.default_misc_trend_style = {
                'user_col': None,
                'sys_col': None,
                'type': 'trend_misc',
                'date1': None,
                'date2': None,
                'text': None,
                'text_date': None,
                'forward_projection': 0,
                'font_size': 10,
                'font_color': 'black',
                'bg_color': 'black',
                'edge_color': 'black',
                'line_color': 'black',
                'linewidth': 1,
                'linestyle': '-',
            }

            self.default_temp_trend_style = {
                'type': 'temp_trend',
                'font_size': 10,
                'font_color': 'magenta',
                'bg_color': 'magenta',
                'edge_color': 'magenta',
                'line_color': 'magenta',
                'linewidth': 1,
                'linestyle': '--',
            }

            self.user_preferences = {
                'unix_id': str(int(time.time())),
                'div_deceleration': True,
                'chart_font_color': '#05c3de',
                'chart_grid_color': '#6ad1e3',
                'width': 11,
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
                'trend_misc_style': self.default_misc_trend_style,
                'recent_imports': [],
                'recent_charts': [],
                'autosave': False,
            }

            self.chart_data = {
                'type': 'Daily',
                'import_path': {},
                'chart_file_path': None,
                'column_map': {},
                'date_format': None,
                'phase': [],
                'aim': [],
                'trend_corr': [],
                'trend_err': [],
                'trend_misc': [],
                'credit': ('SUPERVISOR: ________________    PERFORMER: ________________       TIMER: ________________     COUNTED: ________________     ADVISOR: ________________',
                           'ORGANIZATION: ________________     MANAGER: ________________     COUNTER: ________________     CHARTER: ________________     ROOM: ________________'),
                'start_date': None,
                'place_below_floor': True,
                'data_point_styles': {},
                'notes': [],
                'view': {'chart': {'major_grid_dates': False,
                                   'major_grid_counts': False,
                                   'minor_grid': False,
                                   'floor_grid': False,
                                   'phase': True,
                                   'aims': True,
                                   'cel_fan': True,
                                   'credit': False,
                                   'legend': False,
                                   }
                         },  # Uses sys and user cols as keys for specific columns
            }

            # Necessary for backwards compatibility corrections
            # Also used for not trigger autosave in some cases
            self.default_chart = copy.deepcopy(self.chart_data)
            self.default_user_preferences = copy.deepcopy(self.user_preferences)

            # Celeration unit dictionary
            self.cel_unit_dict = {'Daily': 1,
                                  'Weekly (standard)': 7,
                                  'Monthly (Weekly x4)': 28,
                                  'Yearly (Weekly x52)': 365,
                                  }

            # Support classes
            self.file_monitor = FileMonitor(self)
            self.event_bus = EventBus()

            # Control variables
            self.initialized = True  # Set this attribute after initializing
            self.chart_data_default = copy.deepcopy(self.chart_data)

            # Boolean arrays for preventing trendlines to be affected by zero counts
            self.mask_corr_zero_counts = None
            self.mask_err_zero_counts = None

            self.standard_date_string = '%Y-%m-%d'
            self.df_raw = pd.DataFrame()
            self.plot_columns = {}

            # Apply settings
            self.get_user_preferences()

            # Event bus subscriptions
            self.event_bus.subscribe('column_mapped_raw_data_import', self.column_mapped_raw_data_import, has_data=True)

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
        unit = self.user_preferences['celeration_unit']
        unit_case = unit[0].lower() if unit[0].lower() != 'm' else '4w'
        day_unit_multiple = self.cel_unit_dict[unit]
        cel = np.power(10, daily_slope * day_unit_multiple)
        symbol = 'x'
        if self.user_preferences['div_deceleration'] and cel < 1:
            symbol = '÷'
            cel = 1 / cel
        cel_label = f'c = {symbol}{cel:.2f} / {unit_case}'

        chart_type = self.chart_data['type'][0].lower()
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

    def _complete_partial_date(self, value_str):
        """
        Completes partial dates by adding default month/day values.
        Handles year-only (YYYY) and year-month (YYYY/MM or MM/YYYY) formats.
        Preserves the original value if no partial date pattern is detected.
        """
        value_str = str(value_str).strip()
        min_valid_year = pd.Timestamp.min.year
        max_valid_year = pd.Timestamp.max.year

        # Year-only format
        if value_str.isdigit() and len(value_str) == 4:
            year = int(value_str)
            if min_valid_year <= year <= max_valid_year:
                return f"{year}-01-01"

        # Year/month or month/year format
        parts = value_str.replace('/', '-').replace('.', '-').split('-')
        if len(parts) == 2:
            try:
                if len(parts[0]) == 4:  # YYYY/MM
                    year, month = int(parts[0]), int(parts[1])
                    if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                        return f"{year}-{month:02d}-01"
                elif len(parts[1]) == 4:  # MM/YYYY
                    month, year = int(parts[0]), int(parts[1])
                    if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                        return f"{year}-{month:02d}-01"
            except ValueError:
                pass

        return value_str

    def column_mapped_raw_data_import(self, file_path):
        # Determine file type
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith(('.xls', '.xlsx', '.ods')):
            df = pd.read_excel(file_path)
        else:
            # Will trigger if user cancels import
            return

        # Recreate column map if missing or expired
        column_map = self.chart_data['column_map']
        if not column_map or any(col not in df.columns for col in column_map.values()):
            # Prompt user to create new column map
            self.event_bus.emit('column_map_dialog', file_path)
            column_map = self.chart_data['column_map']

            # Final check
            if not column_map or any(col not in df.columns for col in column_map.values()):
                return False

        # Rename user column names to system column names
        df = df.rename(columns=dict(zip(column_map.values(), column_map.keys())))

        # Add missing columns if any
        if 'm' not in df.columns:
            df['m'] = 1

        # Drop all non-system columns
        o_cols = [col for col in df.columns if re.match(r'^o\d+$', col)]
        standard_cols = [col for col in df.columns if col in ['m', 'c', 'i', 'd']]
        data_cols = standard_cols + o_cols
        df = df[data_cols]

        # Clean columns starting with 'o' - set negatives to 0
        for col in [c for c in df.columns if c.startswith('o')]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = df[col].apply(lambda x: x if x >= 0 else 0)

        # Clean specific columns with defaults
        defaults = {'c': 0, 'i': 0, 'm': 1}
        for col, default in defaults.items():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(default)
                df[col] = df[col].apply(lambda x: x if x >= 0 else default)

        # Convert 'd' column to datetime if not already in datetime format
        date_format = self.chart_data['date_format']  # Will infer if this value is None
        if not pd.api.types.is_datetime64_any_dtype(df['d']):

            # If dates are incomplete
            df['d'] = df['d'].apply(self._complete_partial_date)

            # Replace any invalid dates with NaN, then drop them
            try:
                df['d'] = pd.to_datetime(df['d'], format=date_format, errors='coerce')
            except ValueError:
                df['d'] = pd.to_datetime(df['d'], errors='coerce').dt.date
            df = df.dropna(subset=['d'])

        df['d'] = pd.to_datetime(df['d'])
        df['d'] = df['d'].dt.tz_localize(None)  # Remove timezone info

        # Will clean up any empty rows
        df = df.dropna().reset_index()

        # Store imported raw data (also clears any previous data points)
        self.df_raw = df

        return True

    def validate_raw_data_format(self, file_path):
        # Check before auto importing
        try:
            # Check file type and read
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx', '.ods')):
                df = pd.read_excel(file_path)
            else:
                return False, "Unsupported file type"

            # Verify mapped columns exist
            column_map = self.chart_data['column_map']
            if not column_map or any(col not in df.columns for col in column_map.values()):
                return False, "Column mapping is invalid"

            # Verify date column
            date_col = column_map['d']
            date_format = self.chart_data['date_format']
            try:
                if date_format:
                    pd.to_datetime(df[date_col], format=date_format)
                else:
                    pd.to_datetime(df[date_col])
            except:
                return False, "Invalid date format"

            return True, ""

        except Exception as e:
            return False, str(e)

    def load_chart_file(self, file_path):
        with open(file_path, 'r') as file:
            default_chart = self.default_chart
            loaded_chart = json.load(file)
            loaded_chart = self.ensure_backwards_compatibility(loaded_chart, default_chart)
            self.chart_data = loaded_chart

            # Reset credit lines if older version
            if len(self.chart_data['credit']) == 3:
                self.chart_data['credit'] = default_chart['credit']

        # If loaded chart file have an old file path
        if file_path != self.chart_data['chart_file_path']:
            self.chart_data['chart_file_path'] = file_path

        # Other backwards compatibility fixes
        if self.chart_data['import_path'] is None or isinstance(self.chart_data['import_path'], (list, str)):
            self.chart_data['import_path'] = {}

        # Find import path specific to unix id
        unix_id = self.user_preferences['unix_id']
        all_import_paths = self.chart_data['import_path']
        if unix_id in all_import_paths.keys() and os.path.exists(all_import_paths[unix_id]):
            import_path = all_import_paths[unix_id]
            approved = self.event_bus.emit('column_mapped_raw_data_import', import_path)
            if not approved:
                return
        else:
            # Manually select import path
            data = {'title': "Data not found",
                    'message': 'This chart is not connected to a data set. Click OK to select one.',
                    'choice': True}
            accepted = self.event_bus.emit('trigger_user_prompt', data)
            if accepted:
                import_path = self.event_bus.emit('select_import_path')
                self.event_bus.emit('column_mapped_raw_data_import', import_path)

        # Final check
        if unix_id in all_import_paths.keys() and os.path.exists(all_import_paths[unix_id]) and self.chart_data['column_map']:
            # Generate chart
            self.event_bus.emit('new_chart', self.chart_data['start_date'])

            # Save to recents and refresh list
            self.event_bus.emit('save_chart_as_recent', data={'file_path': file_path, 'recent_type': 'recent_charts'})
            self.event_bus.emit('refresh_recent_charts_list')

            # Switch back to view mode by default
            self.event_bus.emit('view_mode_selected')

            # Monitor data set for updates
            self.file_monitor.start_monitoring(import_path)

    def get_preferences_path(self):
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

        return os.path.join(config_dir, filename)

    def save_user_preferences(self):
        filepath = self.get_preferences_path()
        with open(filepath, 'w') as f:
            json.dump(self.user_preferences, f, indent=4)

    def delete_user_preferences(self):
        filepath = self.get_preferences_path()
        if os.path.exists(filepath):
            os.remove(filepath)

        # Replace with defaults but keep unix id
        unix_id = self.user_preferences['unix_id']
        self.default_user_preferences['unix_id'] = unix_id
        with open(filepath, 'w') as f:
            json.dump(self.default_user_preferences, f, indent=4)

    def get_user_preferences(self):
        filepath = self.get_preferences_path()

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

        # Backwards compatibility cleanup
        if 'raw_df' in json_to_save.keys():
            del json_to_save['raw_df']
        if 'raw_data' in json_to_save.keys():
            del json_to_save['raw_data']

        # Ensure that the current chart type is saved
        json_to_save['type'] = self.chart_data['type']

        # Save current start date in ISO format
        json_to_save['start_date'] = start_date.strftime(self.standard_date_string) if isinstance(start_date, datetime) else start_date

        with open(full_path, 'w') as file:
            json.dump(json_to_save, file, indent=4)

    def prevent_blank_chart(self):
        df = self.df_raw
        if df is None or df.empty:
            return self.chart_data['start_date']

        max_date = df['d'].max()
        min_date = df['d'].min()
        chart_start_date = pd.to_datetime(self.chart_data['start_date'])

        data_exists_in_date_range = min_date <= chart_start_date <= max_date
        if data_exists_in_date_range:
            start_date = self.chart_data['start_date']
        else:
            start_date = min_date

        return start_date


class FileMonitor:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.timer = QTimer()
        self.timer.setInterval(2000)  # 2 second interval
        self.timer.timeout.connect(self.check_file)
        self.last_modified_time = None
        self.current_path = None

    def start_monitoring(self, import_path):
        if not os.path.exists(import_path):
            return False

        self.current_path = import_path
        self.last_modified_time = os.path.getmtime(import_path)
        self.timer.start()
        return True

    def stop_monitoring(self):
        self.timer.stop()
        self.current_path = None
        self.last_modified_time = None

    def check_file(self):
        if not self.current_path or not os.path.exists(self.current_path):
            self.stop_monitoring()
            return

        current_modified_time = os.path.getmtime(self.current_path)
        if current_modified_time != self.last_modified_time:
            self.last_modified_time = current_modified_time
            self.handle_file_changed(self.current_path)

    def handle_file_changed(self, path):
        approved, message = self.data_manager.validate_raw_data_format(path)
        if approved:
            self.data_manager.event_bus.emit('column_mapped_raw_data_import', path)
            self.data_manager.event_bus.emit('new_chart', self.data_manager.chart_data['start_date'])


class DataPointColumn:
    def __init__(self, ax, date_to_x, x_to_day_count, sys_col, user_col, view_settings=None):
        # Core visualization components
        self.ax = ax

        # Date mapping
        self.date_to_x = date_to_x
        self.x_to_date = {v: k for k, v in date_to_x.items()}
        self.x_to_day_count = x_to_day_count

        # Column identifiers
        self.sys_col = sys_col
        self.user_col = user_col

        # Data handling
        self.data_manager = DataManager()
        self.trend_fitter = TrendFitter(x_to_day_count, self.data_manager)

        # Mapping dictionaries
        self.trend_type_map = {
            'c': 'trend_corr',
            'i': 'trend_err',
            'o': 'trend_misc'
        }
        self.style_type_map = {
            'c': 'corr_style',
            'i': 'err_style',
            'm': 'floor_style',
            'o': 'misc_style'
        }

        default_view_settings = {
            'calendar_group': self.data_manager.chart_data['type'][0],
            'agg_type': 'median',
            'data': True,
            'trend_line': True,
            'bounce': True,
            'cel_label': True
        }
        self.view_settings = view_settings if view_settings else default_view_settings

        # Style and data processing
        self.column_default_style = self.data_manager.user_preferences[self.style_type_map[self.sys_col[0]]]
        cols = ["m", "d", self.sys_col] if self.sys_col != 'm' else ['d', 'm']
        self.df_raw = self.data_manager.df_raw.copy()[cols]
        self.df_agg = self.agg_data_column()

        # Visualization objects
        self.highlight_objects = []
        self.is_highlighting = False
        self.column_line_objects = []
        self.column_marker_objects = []
        self.trend_sets = []

    def agg_data_column(self):
        # Initialize aggregated dataframe
        df_agg = self.df_raw.copy()
        agg_type = self.view_settings['agg_type']
        calendar_unit = self.view_settings['calendar_group']

        # Calculate frequency values
        df_agg[self.sys_col + '_total'] = df_agg[self.sys_col]  # Add separate total count column
        if agg_type != 'sum':
            self._calculate_frequency(df_agg)

        # Perform calendar aggregation
        df_agg = self._aggregate_by_calendar(df_agg, calendar_unit, agg_type)

        # Handle zero counts if not floor column
        if self.sys_col != 'm':
            self._handle_zero_counts(df_agg)

        # Apply styling
        df_agg = self._apply_styling(df_agg)

        # Add x values
        df_agg['x'] = pd.to_datetime(df_agg['d']).map(self.date_to_x)

        return df_agg

    def _calculate_frequency(self, df):
        if self.sys_col != 'm':
            df[self.sys_col] = round(df[self.sys_col] / df['m'], 5)
        else:
            df[self.sys_col] = round(1 / df[self.sys_col] / df['m'], 5)

    def _handle_zero_counts(self, df):
        m = df['m'] if 'Minute' in self.data_manager.chart_data['type'] else 1
        if self.data_manager.chart_data['place_below_floor']:
            df[self.sys_col] = np.where(df[self.sys_col] == 0, (1 / m) * 0.8, df[self.sys_col])
        else:
            df[self.sys_col] = df[self.sys_col].apply(lambda x: np.nan if x == 0 else x)

    def _aggregate_by_calendar(self, df, calendar_unit, agg_type):
        if agg_type != 'raw':
            df['d'] = pd.to_datetime(df['d'])
            df = df.set_index('d')
            agg_dict = {col: 'sum' if 'total' in col else agg_type for col in df.columns}
            df = df.resample(calendar_unit[0]).agg(agg_dict).reset_index()

        # Snap dates and clean up
        date_keys = sorted(list(self.date_to_x.keys()))
        bins = pd.cut(df['d'], bins=date_keys, right=True, labels=date_keys[1:])
        df['d'] = bins
        df.dropna(subset=['d'], inplace=True)
        df = df.dropna()
        df.reset_index(drop=True, inplace=True)

        df['d'] = df['d'].astype(str)  # Get out of categorical type
        df['d'] = pd.to_datetime(df['d'])  # Now convert to datetime

        # Add zero counts mask
        df['not_zero_counts'] = ~(df[self.sys_col].isna() | (df[self.sys_col] == 0))

        return df

    def _apply_styling(self, df):
        y_style = self.data_manager.user_preferences[self.style_type_map[self.sys_col[0]]]

        style_cols = {
            'face_colors': y_style['marker_face_color'],
            'edge_colors': y_style['marker_edge_color'],
            'markers': y_style['marker'],
            'marker_sizes': y_style['markersize'],
            'line_styles': y_style['linestyle'],
            'line_colors': y_style['line_color'],
            'line_width': y_style['linewidth']
        }

        # In _apply_styling, replace RGB assignment with hex:
        if self.sys_col.startswith('o'):
            num = int(self.sys_col[1:])
            hue = (num * 0.618034) % 1
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
            hex_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            for col in ['face_colors', 'line_colors', 'edge_colors']:
                style_cols[col] = [hex_color] * df.shape[0]

            self.column_default_style['marker_face_color'] = hex_color
            self.column_default_style['marker_edge_color'] = hex_color
            self.column_default_style['line_color'] = hex_color

        return df.assign(**style_cols)

    def get_df(self):
        return self.df_agg

    def get_y_from_x(self, x_i):
        if x_i in self.x_to_date.keys():
            date = self.x_to_date[x_i]
            row = self.df_agg[self.df_agg['d'] == date]
            y_i = row[[self.sys_col, self.sys_col + '_total', 'not_zero_counts']]
            return y_i

    def get_trend_set(self):
        return self.trend_sets

    def get_default_trend_style(self):
        return self.trend_type_map[self.sys_col[0]]

    def get_legend(self):
        if not self.df_agg.empty:
            return {
                'user_col': self.user_col,
                'marker': self.df_agg['markers'].mode()[0],
                'line_color': self.df_agg['line_colors'].mode()[0],
                'edge_color': self.df_agg['edge_colors'].mode()[0],
                'face_color': self.df_agg['face_colors'].mode()[0],
                'line_style': self.df_agg['line_styles'].mode()[0],
                'marker_size': self.df_agg['marker_sizes'].mode()[0],
                'line_width': self.df_agg['line_width'].mode()[0]
            }

    def plot(self):
        x = self.df_agg['x']
        y = self.df_agg[self.sys_col]
        self.load_styles()

        # Plot line by line without markers
        df_agg_median = self.df_agg.copy().groupby('x').first().reset_index()
        for i in range(len(df_agg_median) - 1):
            corr_points = self.ax.plot(df_agg_median['x'][i:i + 2],
                                       df_agg_median[self.sys_col][i:i + 2],
                                       linestyle=df_agg_median.loc[i, 'line_styles'],
                                       color=df_agg_median.loc[i, 'line_colors'],
                                       linewidth=df_agg_median.loc[i, 'line_width'])
            self.column_line_objects.append(corr_points[0])

        # Add chart markers
        corr_scatter = self.ax.scatter(
            x,
            y,
            zorder=3,
            facecolors=self.df_agg['face_colors'],
            edgecolors=self.df_agg['edge_colors'],
            marker='o',  # Placeholder, revising this with MarkerStyle
            s=self.df_agg['marker_sizes']
        )

        # Selectively set marker styles
        corr_scatter.set_paths([MarkerStyle(marker).get_path().transformed(MarkerStyle(marker).get_transform()) for marker in self.df_agg['markers']])
        self.column_marker_objects.append(corr_scatter)

    def update_style(self):
        # Update line styles
        df_agg_median = self.df_agg.copy().groupby('x').first().reset_index()
        for i, line in enumerate(self.column_line_objects):
            if i < len(df_agg_median) - 1:  # Check to prevent index errors
                line.set_linestyle(df_agg_median.loc[i, 'line_styles'])
                line.set_color(df_agg_median.loc[i, 'line_colors'])
                line.set_linewidth(df_agg_median.loc[i, 'line_width'])

        # Update markers
        scatter = self.column_marker_objects[0]
        scatter.set_facecolors(self.df_agg['face_colors'])
        scatter.set_edgecolors(self.df_agg['edge_colors'])
        scatter.set_sizes(self.df_agg['marker_sizes'])
        scatter.set_paths([MarkerStyle(m).get_path().transformed(MarkerStyle(m).get_transform()) for m in self.df_agg['markers']])

    def load_styles(self):
        chart_data = self.data_manager.chart_data
        data_point_styles = chart_data.get('data_point_styles', {})

        if self.user_col in data_point_styles.keys():
            for style_dict in data_point_styles[self.user_col]:
                key = list(style_dict.keys())[0]
                style_val = style_dict[key]
                date1, date2, style_cat = [x.strip() for x in key.split(',')]
                date1 = pd.to_datetime(date1)
                date2 = pd.to_datetime(date2)

                # Apply style dict
                mask = (self.df_agg['d'] >= date1) & (self.df_agg['d'] <= date2)
                self.df_agg.loc[mask, style_cat] = style_val

    def remove_trend(self, index=None, delete_from_json=True):
        if not self.trend_sets:
            return

        # Use last trend if no index given, otherwise validate index
        idx = -1 if index is None else index
        if idx >= len(self.trend_sets):
            return

        # Remove from chart
        trend_elements = self.trend_sets[idx][0]
        for element in trend_elements.values():
            if element is not None:
                try:
                    element.remove()
                except ValueError as e:
                    print(e)

        self.trend_sets.pop(idx)

        if delete_from_json:
            trend_type = self.trend_type_map[self.sys_col[0]]
            trend_list = self.data_manager.chart_data[trend_type]
            if trend_list:
                trend_list.pop(idx)

    def save_trend(self, trend_elements, trend_data):
        self.trend_sets.append((trend_elements, trend_data))

    def replot_cel_trends(self):
        if self.sys_col[0] in self.trend_type_map:
            trend_type = self.trend_type_map[self.sys_col[0]]
            for trend in self.data_manager.chart_data[trend_type]:
                if 'user_col' in trend.keys() and trend['user_col'] == self.user_col:
                    result = self.plot_cel_trend(
                        date1=datetime.strptime(trend['date1'], self.data_manager.standard_date_string),
                        date2=datetime.strptime(trend['date2'], self.data_manager.standard_date_string),
                        fit_method=trend['fit_method'],
                        forecast=trend['forward_projection'],
                        bounce_envelope=trend['bounce_envelope'],
                        trend_data=trend,
                    )
                    if result:
                        trend_elements, trend_data = result
                        self.save_trend(trend_elements, trend_data)
                else:
                    # Necessary index alignment when selectively deleting
                    self.save_trend(None, None)

    def plot_cel_trend(self, date1, date2, fit_method, forecast, bounce_envelope, trend_data=None):
        result = self._get_celeration_trend(date1, date2,
                                            fit_method=fit_method,
                                            forecast=forecast,
                                            bounce_envelope=bounce_envelope)

        if result is None:
            return

        if trend_data is not None:
            if not pd.to_datetime(trend_data['text_date']) in self.date_to_x.keys():
                return

        trend_vals, cel_label, x_slice, upper_bounce, lower_bounce, x_min_lim, x_max_lim = result
        trend_elements = {
            'trend_line': None,
            'upper_line': None,
            'lower_line': None,
            'cel_label': None
        }

        if not trend_data:
            style = self.data_manager.default_temp_trend_style
        else:
            style = trend_data

        trend_line, = self.ax.plot(x_slice, trend_vals,
                                   linestyle=style['linestyle'],
                                   linewidth=style['linewidth'],
                                   color=style['line_color'])
        trend_elements['trend_line'] = trend_line

        if upper_bounce is not None:
            upper_line, = self.ax.plot(x_slice, upper_bounce,
                                       linestyle=style['linestyle'],
                                       linewidth=style['linewidth'],
                                       color=style['line_color'])
            lower_line, = self.ax.plot(x_slice, lower_bounce,
                                       linestyle=style['linestyle'],
                                       linewidth=style['linewidth'],
                                       color=style['line_color'])
            trend_elements['upper_line'] = upper_line
            trend_elements['lower_line'] = lower_line

        if trend_data is None:
            x_slice_mean = int(np.mean(x_slice))
            est_x = self.data_manager.find_closest_x(x_slice_mean, self.date_to_x)
            est_date = self.x_to_date[est_x]
            est_y = np.mean(trend_vals) * 2
        else:
            est_x = self.date_to_x[pd.to_datetime(trend_data['text_date'])]
            est_y = trend_data['text_y']
            cel_label = trend_data['text']

        cel_label_obj = self.ax.text(est_x,
                            est_y,
                            cel_label,
                            fontsize=style['font_size'],
                            color=style['font_color'],
                            ha="center",
                            weight="bold")
        trend_elements['cel_label'] = cel_label_obj

        if trend_data is None:
            trend_type = self.trend_type_map[self.sys_col[0]]
            trend_data = copy.deepcopy(self.data_manager.user_preferences[trend_type + '_style'])
            trend_data.update({
                'sys_col': self.sys_col,
                'user_col': self.user_col,
                'date1': self.x_to_date[x_min_lim].strftime(self.data_manager.standard_date_string),
                'date2': self.x_to_date[x_max_lim].strftime(self.data_manager.standard_date_string),
                'text': cel_label,
                'text_date': est_date.strftime(self.data_manager.standard_date_string),
                'text_y': est_y,
                'fit_method': self.data_manager.user_preferences['fit_method'],
                'bounce_envelope': self.data_manager.user_preferences['bounce_envelope'],
                'forward_projection': self.data_manager.user_preferences['forward_projection']
            })

        return trend_elements, trend_data

    def _get_celeration_trend(self, date1, date2, fit_method, forecast=0, bounce_envelope=None):
        df = self._prepare_trend_data(date1, date2)
        if df is None or len(df) < 3:
            return None

        x_slice = pd.to_datetime(df['d']).map(self.date_to_x).to_numpy()
        y_slice = df[self.sys_col].to_numpy()

        sorted_idx = np.argsort(x_slice)
        x, y = x_slice[sorted_idx], y_slice[sorted_idx]
        x_min_lim, x_max_lim = x[0], x[-1]

        result = self.trend_fitter.fit_trend(x, y, fit_method, forecast, bounce_envelope)

        return (*result, x_min_lim, x_max_lim)

    def _prepare_trend_data(self, date1, date2):
        date1, date2 = pd.to_datetime(date1), pd.to_datetime(date2)
        start_date, end_date = min(date1, date2), max(date1, date2)

        df = self.df_agg.copy()
        df['d'] = pd.to_datetime(df['d'])
        df = df[(df['d'] >= start_date) & (df['d'] <= end_date)]
        df = df[df['not_zero_counts']][['d', self.sys_col]]

        df.set_index('d', inplace=True)
        df = df.resample('D').median()
        df.reset_index(inplace=True)

        return df[~df[self.sys_col].isna()]

    def highlight(self, duration_ms=500):
        if not self.column_marker_objects or self.is_highlighting:
            return
        self.is_highlighting = True

        # Store original marker sizes
        self.original_sizes = [marker.get_sizes() for marker in self.column_marker_objects]

        # Temporarily increase marker sizes
        for marker in self.column_marker_objects:
            marker.set_sizes(marker.get_sizes() * 3)

        self.ax.figure.canvas.draw()
        QTimer.singleShot(duration_ms, self.remove_highlight)

    def remove_highlight(self):
        # Restore original marker sizes
        for marker, orig_size in zip(self.column_marker_objects, self.original_sizes):
            marker.set_sizes(orig_size)
        self.ax.figure.canvas.draw()
        self.is_highlighting = False

    def sync_visibility(self):
        for element_type, show in self.view_settings.items():
            if isinstance(show, bool):
                self.set_visibility(element_type, show)

    def set_visibility(self, element_type, show):
        # Update status
        if element_type in self.view_settings.keys():
            self.view_settings[element_type] = bool(show)

        if element_type == 'data':
            for line in self.column_line_objects:
                line.set_visible(show)
            for marker in self.column_marker_objects:
                marker.set_visible(show)
        else:
            for trend_elements, _ in self.trend_sets:
                if trend_elements:
                    if element_type == 'bounce' and trend_elements['upper_line']:
                        trend_elements['upper_line'].set_visible(show)
                        trend_elements['lower_line'].set_visible(show)
                    elif trend_elements.get(element_type):
                        trend_elements[element_type].set_visible(show)

    def refresh_view(self):
        # Clear existing plot elements
        for line in self.column_line_objects:
            line.remove()
        for marker in self.column_marker_objects:
            marker.remove()
        while self.trend_sets:
            self.remove_trend(0, delete_from_json=False)

        self.column_line_objects = []
        self.column_marker_objects = []

        # Re-aggregate and replot
        self.df_agg = self.agg_data_column()
        self.plot()
        self.replot_cel_trends()


class TrendFitter:
    def __init__(self, x_to_day_count, data_manager):
        self.x_to_day_count = x_to_day_count
        self.data_manager = data_manager

    def fit_trend(self, x, y, fit_method='Quarter-intersect', forecast=0, bounce_envelope=None):
        x_as_day_count = np.array([self.x_to_day_count[x_i] for x_i in list(x)])
        extended_x = np.arange(x[0], x[-1] + forecast + 1)

        if fit_method in ['Quarter-intersect', 'Split-middle-line']:
            daily_slope, intercept = self._quarter_intersect_fit(x_as_day_count, np.log10(y))
            if fit_method == 'Split-middle-line':
                slope, intercept = self._split_middle_line_fit(x, np.log10(y))
            else:
                slope, intercept = self._quarter_intersect_fit(x, np.log10(y))
            trend = slope * extended_x + intercept
        elif fit_method == 'Least-squares':
            daily_slope, intercept = np.polyfit(x_as_day_count, np.log10(y), 1)
            slope, intercept = np.polyfit(x, np.log10(y), 1)
            trend = np.polyval((slope, intercept), extended_x)
        else:
            # Mean or Median
            central_tendency = np.mean(np.log10(y)) if fit_method == 'Mean' else np.median(np.log10(y))
            trend = np.full(len(extended_x), central_tendency)
            daily_slope = slope = 0
            intercept = central_tendency

        trend = np.power(10, trend)
        cel_label = self._get_trend_label(daily_slope, fit_method, trend[0])

        bounce_result = self._calculate_bounce(bounce_envelope, y, slope, extended_x, intercept)
        if bounce_result:
            upper_bounce, lower_bounce, bounce_label = bounce_result
            cel_label = cel_label + '\n' + bounce_label
        else:
            upper_bounce, lower_bounce = None, None

        return trend, cel_label, extended_x, upper_bounce, lower_bounce

    def _quarter_intersect_fit(self, x, y):
        mid_date = np.median(x)
        x1 = np.median(x[x < mid_date])
        x2 = np.median(x[x > mid_date])
        y1 = np.median(y[x < mid_date])
        y2 = np.median(y[x > mid_date])

        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        return slope, intercept

    def _split_middle_line_fit(self, x, y, iter_num=1000):
        slope, intercept = self._quarter_intersect_fit(x, y)
        quarter_intersect_trend = slope * x + intercept

        differences = y - quarter_intersect_trend
        max_diff, min_diff = np.max(differences), np.min(differences)

        results = np.zeros((iter_num, 3))
        for i, itr in enumerate(np.linspace(min_diff, max_diff, iter_num)):
            adjusted_trend = slope * x + (intercept + itr)
            errors = y - adjusted_trend
            sse = np.mean(errors ** 2)

            above = np.sum(y > adjusted_trend)
            below = np.sum(y < adjusted_trend)
            results[i] = [itr, abs(above - below), sse]

        min_abs_diff = np.min(results[:, 1])
        filtered_results = results[results[:, 1] == min_abs_diff]
        best_itr = filtered_results[np.argmin(filtered_results[:, 2])][0]

        return slope, intercept + best_itr

    def _get_trend_label(self, slope, fit_method, trend_value):
        if fit_method in ['Mean', 'Median']:
            return f'{fit_method.lower()} = {self.data_manager.format_y_value(trend_value)}'

        unit = self.data_manager.user_preferences['celeration_unit']
        unit_case = unit[0].lower() if unit[0].lower() != 'm' else '4w'
        day_unit_multiple = self.data_manager.cel_unit_dict[unit]
        cel = np.power(10, slope * day_unit_multiple)

        symbol = 'x'
        if self.data_manager.user_preferences['div_deceleration'] and cel < 1:
            symbol = '÷'
            cel = 1 / cel

        return f'c = {symbol}{cel:.2f} / {unit_case}'

    def _calculate_bounce(self, bounce_envelope, y, slope, extended_x, intercept):
        if bounce_envelope == 'None':
            return None

        trend_orig = slope * extended_x[:len(y)] + intercept
        residuals = np.log10(y) - trend_orig

        if bounce_envelope == '5-95 percentile':
            upper_p = np.percentile(residuals, 95)
            lower_p = np.percentile(residuals, 5)
            bounds = (upper_p, lower_p)
        elif bounce_envelope == 'Interquartile range':
            q75, q25 = np.percentile(residuals, [75, 25])
            iqr = q75 - q25
            bounds = (q75, q25 - iqr)
        elif bounce_envelope == 'Standard deviation':
            std = np.std(residuals)
            mean = np.mean(residuals)
            bounds = (mean + std, mean - std)
        else:  # 90% confidence interval
            mean = np.mean(residuals)
            std_error = np.std(residuals) / np.sqrt(len(residuals))
            margin = 1.645 * std_error
            bounds = (mean + margin, mean - margin)

        log_upper = slope * extended_x + intercept + bounds[0]
        log_lower = slope * extended_x + intercept + bounds[1]
        upper_bounce = np.power(10, log_upper)
        lower_bounce = np.power(10, log_lower)
        bounce_ratio = upper_bounce[0] / lower_bounce[0]

        return upper_bounce, lower_bounce, f'b = x{bounce_ratio:.2f}'

