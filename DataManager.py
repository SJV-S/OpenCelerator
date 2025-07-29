from app_imports import *
from EventStateManager import EventBus
from database import SQLiteManager


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
                'font_size': 10,
                'font_color': '#000000',
                'bg_color': '#FFFFFF',
                'edge_color': '#000000',
                'line_color': '#000000',
                'linewidth': 0.5,
                'linestyle': '-',
                'text_mode': None,
                'text_position': 0.8,
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
                'machine_id': self.get_machine_id(),
                'user_name': self.get_default_user_name(),
                'db_location': {'local': self.get_config_directory(as_str=True), 'cloud': ''},
                'last_open_tab': 'local',
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
                'home_folder': str(Path.home()),
                'import_data_folder': '',
                'chart_export_folder': '',
                'export_csv_folder': '',
                'phase_style': self.default_phase_style,
                'aim_style': self.default_aim_style,
                'trend_corr_style': self.default_corr_trend_style,
                'trend_err_style': self.default_err_trend_style,
                'trend_misc_style': self.default_misc_trend_style,
                'recent_imports': [],
                'recent_charts': [],
                'autosave': False,
                'update': 'Off',
                'last_update_check': '',
                'last_vacuum': 0,
                'version': '',
            }

            self.chart_data = {
                'type': 'Daily',
                'created': int(time.time()),
                'data_modified': '',  # Will be a unix timestamp
                'import_path': {},
                'chart_file_path': None,
                'column_map': {'d': 'dates',
                               'm': 'minutes',
                               'c': 'corrects',
                               'i': 'incorrects',
                               'o1': 'other'},
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
                'raw_data': {},
            }

            # Necessary for backwards compatibility corrections
            # Also used for not trigger autosave in some cases
            self.default_chart = copy.deepcopy(self.chart_data)
            self.default_user_preferences = copy.deepcopy(self.user_preferences)

            # Celeration unit dictionary
            self.cel_unit_dict = {'Daily': 1,
                                  'Weekly': 7,
                                  'Monthly (Weekly x4)': 28,
                                  'Six-monthly (Weekly x26)': 182,
                                  'Yearly (Weekly x52)': 365,
                                  'Five-yearly (Yearly x5)': 1825,
                                  }
            # Support classes
            self.event_bus = EventBus()
            self.file_manager = FileManager(self)
            self.sqlite_manager = SQLiteManager(self)

            # Control variables
            self.initialized = True  # Set this attribute after initializing
            self.chart_data_default = copy.deepcopy(self.chart_data)

            # Boolean arrays for preventing trendlines to be affected by zero counts
            self.mask_corr_zero_counts = None
            self.mask_err_zero_counts = None

            self.standard_date_string = '%Y-%m-%d'
            self.df_raw = pd.DataFrame()
            self.plot_columns = {}
            self.ui_column_label = 'Series'
            self.ui_cel_label = 'Change'

            # Apply settings
            self.get_user_preferences()

            # Event bus subscriptions
            self.event_bus.subscribe('column_mapped_raw_data_import', self.column_mapped_raw_data_import, has_data=True)
            self.event_bus.subscribe('direct_data_entry', self.direct_data_entry, has_data=True)
            self.event_bus.subscribe('sync_column_view_settings', self.sync_column_view_settings, has_data=True)
            self.event_bus.subscribe('remove_latest_entry', self.remove_latest_entry, has_data=False)

    def direct_data_entry(self, data):
        # Process time data once
        hours = float(data['hour_str']) if data['hour_str'] else 0
        minutes = float(data['minute_str']) if data['minute_str'] else 0
        seconds = float(data['second_str']) if data['second_str'] else 0
        total_minutes = hours * 60 + minutes + seconds / 60
        total_minutes = 1 if total_minutes == 0 else total_minutes

        # Define states once
        raw_data_exists = not self.df_raw.empty
        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        is_minute_chart = 'Minute' in chart_type
        column_map = self.event_bus.emit("get_chart_data", ['column_map', {}])

        # Create a single row dictionary to gather all data
        new_row = {'d': pd.to_datetime(data['date_str']),
                   'm': total_minutes}

        # Create new row
        for sys_col, count_str in zip(data['sys_col'], data['count_str']):
            count = int(count_str) if count_str else np.nan
            new_row[sys_col] = count

        # Add new row
        if not raw_data_exists:
            self.df_raw = pd.DataFrame([new_row])
        else:
            # Add the new consolidated row to df
            new_df_row = pd.DataFrame([new_row])
            self.df_raw = pd.concat([self.df_raw, new_df_row], ignore_index=True)

        # Update plot_column dict
        for user_col, sys_col in zip(data['user_col'], data['sys_col']):
            column_name_in_plot_columns = user_col in self.plot_columns.keys()
            if not column_name_in_plot_columns:
                # If new column
                self.plot_columns[user_col] = self.event_bus.emit('get_data_point_column', {'sys_col': sys_col, 'user_col': user_col})

        # Update agg dfs for all involved columns
        plot_column_keys_except_floor = [v for k, v in column_map.items() if k not in ['d', 'm']]
        for user_col in plot_column_keys_except_floor:
            self.plot_columns[user_col].refresh_view()

        # # Refresh minute column if needed
        if is_minute_chart:
            minute_col_name = column_map['m']
            if minute_col_name not in self.plot_columns.keys():
                self.plot_columns[minute_col_name] = self.event_bus.emit('get_data_point_column', {'sys_col': 'm', 'user_col': minute_col_name})
            self.plot_columns[minute_col_name].refresh_view()

        # Refresh chart and save (only once)
        self.event_bus.emit('update_legend')
        self.event_bus.emit('refresh_chart')
        self.event_bus.emit('save_complete_chart')

    def remove_latest_entry(self):
        # Check if dataframe is not empty
        if not self.df_raw.empty:
            # Remove the last row using iloc
            self.df_raw = self.df_raw.iloc[:-1]

            # Refresh data visualization
            for col_name in self.plot_columns.keys():
                self.plot_columns[col_name].refresh_view()

            self.event_bus.emit('refresh_chart')
            self.event_bus.emit('save_complete_chart')

    def ensure_backwards_compatibility(self, sample_dict, default_dict):
        # Skip special fields that should not be modified
        skip_fields = ['column_map']

        for key, value in default_dict.items():
            if key in skip_fields:
                continue

            if key not in sample_dict:
                sample_dict[key] = copy.deepcopy(value)
            elif isinstance(value, dict) and isinstance(sample_dict[key], dict):
                # Apply recursively if value in default_dict and sample_dict are dictionaries
                self.ensure_backwards_compatibility(sample_dict[key], value)

        return sample_dict

    def format_y_value(self, y_value):
        if y_value >= 100:
            return int(y_value)
        elif y_value >= 10:
            return round(y_value, 1)
        elif y_value >= 1:
            return round(y_value, 2)
        elif y_value >= 0.1:
            return round(y_value, 3)
        else:
            return round(y_value, 4)

    def get_aim_slope_text(self, text_pos, xmin, xmax, ymin, ymax, x_to_day_count):
        # Convert dimensionless x-values to days and get celeration label
        daily_slope = (np.log10(ymin) - np.log10(ymax)) / (x_to_day_count[xmin] - x_to_day_count[xmax])
        unit = self.event_bus.emit("get_user_preference", ['celeration_unit', 'Weekly (standard)'])

        # Unit_case mapping
        if unit.startswith('Monthly'):
            unit_case = '4w'
        elif unit.startswith('Six-monthly'):
            unit_case = '26w'
        elif unit.startswith('Five-yearly'):
            unit_case = '5y'
        else:
            unit_case = unit[0].lower()

        day_unit_multiple = self.cel_unit_dict.get(unit, 7)
        cel = np.power(10, daily_slope * day_unit_multiple)
        symbol = 'x'
        if cel < 1:
            symbol = '÷'
            cel = 1 / cel
        cel_label = f'{symbol}{cel:.2f} / {unit_case}'

        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])[0].lower()
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

    def find_closest_date(self, date, date_to_pos, date_format=None):
        if date_format is None:
            date_format = self.standard_date_string

        # Check if already a pandas datetime
        if not isinstance(date, pd.Timestamp):
            date = pd.to_datetime(date, format=date_format)

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
        if x is None:
            print('find_closest_x returned None')
            return None

        if isinstance(x, float):
            x = int(x)

        valid_x_values = list(date_to_pos.values())

        # Fast path: check exact and adjacent matches first
        for candidate in [x, x - 1, x + 1]:
            if candidate in valid_x_values:
                return candidate

        # Slow path: find closest match
        return min(valid_x_values, key=lambda valid_x: abs(valid_x - x))

    def _complete_partial_date(self, value_str):
        value_str = str(value_str).strip()
        min_valid_year = pd.Timestamp.min.year
        max_valid_year = pd.Timestamp.max.year

        # Year-only format
        if value_str.isdigit() and len(value_str) == 4:
            year = int(value_str)
            if min_valid_year <= year <= max_valid_year:
                return f"{year}-12-31"  # Changed from 01-01 to 12-31

        # Year/month or month/year format
        parts = value_str.replace('/', '-').replace('.', '-').split('-')
        if len(parts) == 2:
            try:
                if len(parts[0]) == 4:  # YYYY/MM
                    year, month = int(parts[0]), int(parts[1])
                    if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                        # Get last day of the specified month
                        last_day = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(1)
                        return last_day.strftime("%Y-%m-%d")
                elif len(parts[1]) == 4:  # MM/YYYY
                    month, year = int(parts[0]), int(parts[1])
                    if 1 <= month <= 12 and min_valid_year <= year <= max_valid_year:
                        # Get last day of the specified month
                        last_day = pd.Timestamp(year, month, 1) + pd.offsets.MonthEnd(1)
                        return last_day.strftime("%Y-%m-%d")
            except ValueError:
                pass

        return value_str

    def _validate_column_map(self, df):
        column_map = {} if not isinstance(self.chart_data['column_map'], dict) else self.chart_data['column_map']
        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        is_minute_chart = 'Minute' in chart_type
        valid_keys = column_map.keys() if is_minute_chart else [k for k in column_map.keys() if k != 'm']
        valid_column_map = {k: column_map[k] for k in valid_keys}

        return valid_column_map and all(col in df.columns for col in valid_column_map.values())

    def read_file_safely(self, file_path, read_function, row_limit=None):
        try:
            return read_function(file_path, row_limit)
        except Exception:
            return None

    def read_excel(self, file_path, row_limit=None):
        return pd.read_excel(file_path, nrows=row_limit)

    def read_csv(self, file_path, row_limit=None):
        return pd.read_csv(file_path, nrows=row_limit)

    def get_df_from_data_file(self, file_path, row_limit=None):
        if file_path:
            ext = Path(file_path).suffix
            if ext in ['.xlsx', '.xls', '.ods']:
                df = self.read_file_safely(file_path, self.read_excel, row_limit)
                if df is None:
                    df = self.read_file_safely(file_path, self.read_csv, row_limit)
            else:
                df = self.read_file_safely(file_path, self.read_csv, row_limit)

            if df is None:
                raise Warning('Failed to read data file.')

            return df

    def column_mapped_raw_data_import(self, file_path):
        # Read data sample
        df = self.get_df_from_data_file(file_path, row_limit=20)
        if df is None:
            print('df is none')
            return

        # In column_mapped_raw_data_import:
        if not self._validate_column_map(df):
            # Prompt user to create new column map
            self.event_bus.emit('column_map_dialog', file_path)

            # Check again after user updated the column map
            if not self._validate_column_map(df):
                print('Column map rejected.')
                return False

        # df approved, read all data
        df = self.get_df_from_data_file(file_path, row_limit=None)

        # Rename user column names to system column names
        column_map = self.event_bus.emit("get_chart_data", ['column_map', {}])
        df = df.rename(columns=dict(zip(column_map.values(), column_map.keys())))

        # Add missing columns if any
        if 'm' not in df.columns:
            df['m'] = 1
            # Add to column map as well
            if 'm' not in column_map.keys():
                self.event_bus.emit("update_chart_data", [['column_map', 'm'], 'minutes'])

        # Drop all non-system columns
        o_cols = [col for col in df.columns if re.match(r'^o\d+$', col)]
        standard_cols = [col for col in df.columns if col in ['m', 'c', 'i', 'd']]
        data_cols = standard_cols + o_cols
        df = df[data_cols]

        # Clean columns misc
        for col in [c for c in df.columns if c.startswith('o')]:

            # Strip whitespace before numeric conversion
            if df[col].dtype == 'object':  # Only for string columns
                df[col] = df[col].astype(str).str.strip()

            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].apply(lambda x: np.nan if x < 0 else x)

        # Clean standard columns
        for col in ['c', 'i', 'm']:
            if col in df.columns:
                # Strip whitespace before numeric conversion
                if df[col].dtype == 'object':  # Only for string columns
                    df[col] = df[col].astype(str).str.strip()

                df.loc[:, col] = pd.to_numeric(df[col], errors='coerce')
                df.loc[:, col] = df[col].apply(lambda x: np.nan if x < 0 else x)

        # Convert 'd' column to datetime if not already in datetime format
        date_format = self.event_bus.emit("get_chart_data", ['date_format', None])
        if not pd.api.types.is_datetime64_any_dtype(df['d']):

            # If dates are incomplete
            df['d'] = df['d'].astype(str).apply(self._complete_partial_date)

            # Replace any invalid dates with NaN, then drop them
            try:
                df.loc[:, 'd'] = pd.to_datetime(df['d'], format=date_format, errors='coerce')
            except ValueError:
                df['d'] = pd.to_datetime(df['d'], errors='coerce').dt.date
            df = df.dropna(subset=['d'])

        df['d'] = pd.to_datetime(df['d'])
        df['d'] = df['d'].dt.tz_localize(None)  # Remove timezone info

        # Remove rows where all values are NaN
        df = df.dropna(how='all').reset_index(drop=True)

        # Store imported raw data (also clears any previous data points)
        self.df_raw = df

        return True

    def default_chart_assessment(self):
        recent_charts = self.event_bus.emit("get_user_preference", ['recent_charts', []])

        chart_settings = {
            'type': [],
            'major_grid_dates': [],
            'major_grid_counts': [],
            'minor_grid': [],
            'floor_grid': [],
            'cel_fan': [],
            'credit': [],
            'legend': []
        }

        if len(recent_charts) <= 4:
            return

        # Ensure database connection
        if not self.sqlite_manager.initialized:
            if not self.sqlite_manager.connect():
                return

        processed_charts = 0

        for chart_id in recent_charts:
            try:
                # Load metadata from database
                self.sqlite_manager.cursor.execute(
                    f"SELECT metadata FROM {self.sqlite_manager.TABLE_CHART_METADATA} WHERE chart_id = ?",
                    (chart_id,)
                )
                result = self.sqlite_manager.cursor.fetchone()

                if not result:
                    continue

                loaded_chart = json.loads(result[0])

            except (json.JSONDecodeError, Exception):
                continue

            # Check essential keys exist
            essential_keys = {'type', 'view'}
            if not essential_keys.issubset(loaded_chart.keys()):
                continue

            # Extract chart type
            chart_settings['type'].append(loaded_chart.get('type'))

            # Extract view settings
            if 'view' not in loaded_chart or 'chart' not in loaded_chart['view']:
                continue

            chart_view = loaded_chart['view']['chart']

            for key in chart_settings.keys():
                if key != 'type':
                    chart_settings[key].append(chart_view.get(key))

            processed_charts += 1

        if processed_charts == 0:
            return

        # Get most frequent values for each setting
        most_common_settings = {}
        for key in chart_settings:
            values = [v for v in chart_settings[key] if v is not None]

            if values:
                most_common_settings[key] = max(set(values), key=values.count)
            else:
                most_common_settings[key] = None

        # Apply most common settings to chart_data
        if 'type' in most_common_settings and most_common_settings['type']:
            self.chart_data['type'] = most_common_settings['type']

        for key in chart_settings.keys():
            if key != 'type' and key in most_common_settings and most_common_settings[key] is not None:
                self.chart_data['view']['chart'][key] = most_common_settings[key]

    def get_default_user_name(self):
        if platform.system() == "Windows":
            return os.environ.get('USERNAME', '')
        else:  # Linux, macOS
            return os.environ.get('USER', '')

    def get_machine_id(self):
        identifiers = [
            platform.system(),
            platform.machine(),
            platform.release(),
            platform.node(),
            os.environ.get('USER', os.environ.get('USERNAME', ''))
        ]

        combined_id = ":".join(filter(None, identifiers))
        return hashlib.md5(combined_id.encode()).hexdigest()

    def get_config_directory(self, as_str=False):
        system = platform.system()
        home_dir = Path.home()

        if system == "Linux" or system == "Darwin":  # Darwin is macOS
            config_dir = home_dir / '.config' / 'OpenCelerator'
        elif system == "Windows":
            config_dir = home_dir / 'AppData' / 'Local' / 'OpenCelerator'
        else:
            config_dir = home_dir / 'OpenCelerator'  # Fallback

        if as_str:
            return str(config_dir)
        else:
            return config_dir

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

    def sync_column_view_settings(self, user_col):
        column_instance = self.plot_columns.get(user_col)
        if column_instance:
            key = f'{column_instance.sys_col}|{user_col}'
            self.chart_data['view'][key] = copy.deepcopy(column_instance.view_settings)

    def save_user_preferences(self):
        filepath = self.get_preferences_path()
        with open(filepath, 'w') as f:
            json.dump(self.user_preferences, f, indent=4)

    def delete_user_preferences(self):
        filepath = self.get_preferences_path()
        if os.path.exists(filepath):
            os.remove(filepath)

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

    def prevent_blank_chart(self):
        df = self.df_raw
        if df is None or df.empty:
            return self.chart_data['start_date']

        max_date = df['d'].max()
        min_date = df['d'].min()
        chart_start_date = pd.to_datetime(self.event_bus.emit("get_chart_data", ['start_date', None]))

        data_exists_in_date_range = min_date <= chart_start_date <= max_date
        if data_exists_in_date_range:
            start_date = chart_start_date
        else:
            # Get the chart type to determine how to align the start date
            chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])

            if 'Daily' in chart_type:
                # For Daily charts, align to the previous Sunday
                start_date = min_date - pd.Timedelta(min_date.dayofweek + 1, unit="D")
            elif 'Weekly' in chart_type:
                # For Weekly charts, align to the previous month's start
                prev_month = (min_date.replace(day=1) - pd.Timedelta(days=1)).replace(day=1)
                start_date = prev_month
            elif 'Monthly' in chart_type:
                # For Monthly charts, align to the previous year's start
                start_date = min_date.replace(year=min_date.year - 1, month=1, day=1)
            elif 'Yearly' in chart_type:
                # For Yearly charts, align to the previous decade
                start_year = min_date.year - (min_date.year % 10)
                start_date = min_date.replace(year=start_year, month=1, day=1)
            else:
                start_date = min_date

            # Normalize to midnight
            start_date = start_date.normalize()

        return start_date


class DataPointColumn:
    def __init__(self, ax, date_to_x, x_to_day_count, sys_col, user_col, view_settings=None):
        # Classes
        self.event_bus = EventBus()

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
            'o': 'trend_misc',
            'm': 'trend_misc'
        }
        self.style_type_map = {
            'c': self.data_manager.default_corr_point_style,
            'i': self.data_manager.default_err_point_style,
            'm': self.data_manager.default_floor_point_style,
            'o': self.data_manager.default_misc_point_style
        }

        chart_type = self.event_bus.emit("get_chart_data", ['type', 'Daily'])
        default_view_settings = {
            'calendar_group': chart_type[0],
            'agg_type': 'raw',
            'data': True,
            'trend_line': True,
            'bounce': True,
            'cel_label': True
        }
        self.view_settings = view_settings if view_settings else default_view_settings

        # Style and data processing
        self.column_default_style = self.style_type_map[self.sys_col[0]]

        self.raw_df = None
        self.df_agg = self.agg_data_column()

        # Visualization objects
        self.highlight_objects = []
        self.is_highlighting = False
        self.column_line_objects = []
        self.column_marker_objects = []
        self.trend_sets = []

    def agg_data_column(self):
        # Copy latest raw df from data manager
        self.df_raw = self.data_manager.df_raw.copy()

        # # If rows x columns is zero (no data whatsoever)
        if self.df_raw.size == 0:
            columns = ['d', 'm', self.sys_col] if self.sys_col != 'm' else ['d', 'm']
            self.df_raw = pd.DataFrame(columns=columns)
        else:
            # Necessary when adding new column and previous data already exist
            if self.sys_col not in self.df_raw.columns:
                self.df_raw[self.sys_col] = 0

        # Ensure consistent datetime conversion
        self.df_raw['d'] = pd.to_datetime(self.df_raw['d'])

        # Ensure 'm' column exists
        if 'm' not in self.df_raw.columns:
            self.df_raw['m'] = 1

        # Filter columns based on sys_col
        col_filter = ["m", "d", self.sys_col] if self.sys_col != 'm' else ['d', 'm']
        self.df_raw = self.df_raw[col_filter]

        # Initialize aggregated dataframe
        df_agg = self.df_raw.copy()

        # Convert sys_col to float to allow division for frequency calculation
        df_agg[self.sys_col] = df_agg[self.sys_col].astype('float64')

        agg_type = self.view_settings['agg_type']
        calendar_unit = self.view_settings['calendar_group']

        # Calculate frequency values
        df_agg[self.sys_col + '_total'] = df_agg[self.sys_col]  # Add separate total count column
        chart_type = self.data_manager.event_bus.emit("get_chart_data", ['type', 'Daily'])
        if 'Minute' in chart_type:
            self._calculate_frequency(df_agg)

        # Perform calendar aggregation
        df_agg = self._aggregate_by_calendar(df_agg, calendar_unit, agg_type)

        # Handle zero counts if not floor column
        if self.sys_col != 'm':
            self._handle_zero_counts(df_agg)

        # Apply styling
        df_agg = self._apply_styling(df_agg)

        # Add x values
        df_agg.loc[:, 'x'] = pd.to_datetime(df_agg['d']).map(self.date_to_x)

        return df_agg

    def _calculate_frequency(self, df):
        if self.sys_col != 'm':
            df.loc[:, self.sys_col] = (df[self.sys_col] / df['m'])
        else:
            df.loc[:, self.sys_col] = (1 / df['m'])

    def _handle_zero_counts(self, df):
        m = df['m'] if 'Minute' in self.data_manager.chart_data['type'] else 1
        if self.data_manager.event_bus.emit("get_chart_data", ['place_below_floor', True]):
            df.loc[:, self.sys_col] = np.where(df[self.sys_col] == 0, (1 / m) * 0.8, df[self.sys_col])
        else:
            df.loc[:, self.sys_col] = df[self.sys_col].apply(lambda x: np.nan if x == 0 else x)

    def _aggregate_by_calendar(self, df, calendar_unit, agg_type):
        df = df.copy()  # Eliminates SettingWithCopyWarning

        if agg_type != 'raw':
            df['d'] = pd.to_datetime(df['d'])
            df['point_count'] = 1
            df = df.set_index('d')
            agg_dict = {col: 'sum' if '_total' in col or col == 'point_count' else agg_type for col in df.columns}
            df = df.resample(calendar_unit[0]).agg(agg_dict).reset_index()

        # Snap dates and clean up
        date_keys = sorted(list(self.date_to_x.keys()))
        bins = pd.cut(df['d'], bins=date_keys, right=False, labels=date_keys[:-1])
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
        y_style = self.style_type_map[self.sys_col[0]]

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

        # Check what's going into the dataframe
        result_df = df.assign(**style_cols)

        return result_df

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

    def get_data_point_metrics(self, x_i):
        # Defaults
        rows = None
        points = None

        df_slice = self.df_agg[self.df_agg['x'] == x_i]
        if not df_slice.empty:
            if self.view_settings['agg_type'] == 'raw':
                rows = df_slice.shape[0]
                points = None
            elif 'point_count' in df_slice.columns:
                rows = df_slice.shape[0]
                points = df_slice['point_count'].sum()

        # Condition flags
        rows_none = rows is None
        points_none = points is None
        is_raw = points is None and rows is not None
        multi_points = False if points is None else bool(points > 1)
        multi_rows = False if rows is None else bool(rows > 1)
        is_max_min = self.view_settings['agg_type'] in ["max", "min"]

        # View settings
        calendar_unit = self.view_settings['calendar_group']
        calendar_map = {'D': 'Daily', 'W': 'Weekly', 'M': 'Monthly', 'Y': 'Yearly'}
        calendar_group = calendar_map[calendar_unit[0]]
        agg_type = self.view_settings['agg_type']

        key = (rows_none, points_none, is_raw, multi_points, multi_rows, is_max_min)
        if key == (True, True, False, False, False, False):
            metrics = ''
        elif key == (False, True, True, False, False, False):
            metrics = f'\n{rows} individual {"entries" if rows > 1 else "entry"}'
        elif key == (False, False, False, True, True, True):
            metrics = f'{rows} {calendar_group} {agg_type} values of\n{points} total entries'
        elif key == (False, False, False, True, True, False):
            metrics = f'{rows} {calendar_group} {agg_type}s of\n{points} total entries'
        elif key == (False, False, False, True, False, True):
            metrics = f'{calendar_group} {agg_type} of\n{points} entries'
        elif key == (False, False, False, True, False, False):
            metrics = f'{calendar_group} {agg_type} of\n{points} entries'
        elif key == (False, False, False, False, True, False):
            metrics = f'{rows} {calendar_group} of\n1 total entry'
        elif key == (False, False, False, False, False, False):
            metrics = f'{calendar_group}\n1 entry'
        elif key == (False, False, False, False, False, True):
            metrics = f'{calendar_group} {agg_type} of\n1 entry'
        else:
            metrics = '\n'

        return metrics

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

                # Check if dates are 'none' - apply style universally
                if date1.lower() == 'none' or date2.lower() == 'none':
                    self.df_agg[style_cat] = style_val
                else:
                    # Convert to datetime and apply with mask
                    date1 = pd.to_datetime(date1)
                    date2 = pd.to_datetime(date2)
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
        if isinstance(trend_elements, dict):
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

                        # Make the cel label draggable
                        self.event_bus.emit('make_draggable', data={
                            'objects': trend_elements['cel_label'],
                            'save_obj': trend_data,
                            'save_event': 'save_cel_label_pos'
                        })
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
            trend_data = copy.deepcopy(self.data_manager.event_bus.emit("get_user_preference", [trend_type + '_style', {}]))
            trend_data.update({
                'sys_col': self.sys_col,
                'user_col': self.user_col,
                'date1': self.x_to_date[x_min_lim].strftime(self.data_manager.standard_date_string),
                'date2': self.x_to_date[x_max_lim].strftime(self.data_manager.standard_date_string),
                'text': cel_label,
                'text_date': est_date.strftime(self.data_manager.standard_date_string),
                'text_y': est_y,
                'fit_method': self.data_manager.event_bus.emit("get_user_preference", ['fit_method', 'Least-squares']),
                'bounce_envelope': self.data_manager.event_bus.emit("get_user_preference", ['bounce_envelope', 'None']),
                'forward_projection': self.data_manager.event_bus.emit("get_user_preference", ['forward_projection', 0])
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

    def highlight(self, duration_ms=500, size_factor=10):
        # Highlight data points by superimposing yellow squares
        if not self.column_marker_objects or self.is_highlighting:
            return

        self.is_highlighting = True
        self.highlight_objects = []

        # For each original marker, create a superimposed yellow square
        for marker in self.column_marker_objects:
            # Get offset coordinates
            offsets = marker.get_offsets()

            # Instead of using mean size, get the individual sizes from the data frame
            # This ensures we respect the configured sizes for each point
            marker_sizes = self.df_agg['marker_sizes'].values

            # Create superimposed yellow squares with individual sizes
            highlight_marker = self.ax.scatter(
                offsets[:, 0], offsets[:, 1],  # x and y coordinates from offsets
                s=marker_sizes * size_factor,  # Apply size factor to individual marker sizes
                marker='s',  # Square marker
                color='yellow',
                alpha=0.3,
                zorder=marker.get_zorder() + 1  # Ensure it's on top
            )

            self.highlight_objects.append(highlight_marker)

        # Draw the updated plot
        self.ax.figure.canvas.draw_idle()

        # Store timer as instance variable to prevent garbage collection
        self._restore_timer = QTimer()
        self._restore_timer.setSingleShot(True)
        self._restore_timer.timeout.connect(self.remove_highlight)
        self._restore_timer.start(duration_ms)

    def remove_highlight(self):
        # Remove the superimposed highlight markers
        if hasattr(self, 'highlight_objects'):
            for highlight_marker in self.highlight_objects:
                highlight_marker.remove()

            self.highlight_objects = []
            self.ax.figure.canvas.draw()

        self.is_highlighting = False

        # Clean up timer reference
        if hasattr(self, '_restore_timer'):
            self._restore_timer.stop()
            del self._restore_timer

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
        self.sync_visibility()

    def delete(self):
        # Remove all line objects
        for line in self.column_line_objects:
            line.remove()
        self.column_line_objects = []

        # Remove all marker objects
        for marker in self.column_marker_objects:
            marker.remove()
        self.column_marker_objects = []

        # Remove all trend sets
        while self.trend_sets:
            self.remove_trend(0, delete_from_json=True)

        # Remove any highlight objects
        if hasattr(self, 'highlight_objects'):
            for highlight_marker in self.highlight_objects:
                highlight_marker.remove()
            self.highlight_objects = []
            self.is_highlighting = False

        # Clean up timer if it exists
        if hasattr(self, '_restore_timer'):
            self._restore_timer.stop()
            del self._restore_timer


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

    def _split_middle_line_fit(self, x, y):
        # Optimizes the Mean Absolute Deviation (MAD) under the constraint
        # that equal numbers of points are above and below the line

        # Get the initial slope and intercept using the quarter-intersect method
        slope, intercept = self._quarter_intersect_fit(x, y)
        quarter_intersect_trend = slope * x + intercept

        # Calculate the residuals
        differences = y - quarter_intersect_trend

        # Ensure half the points are above and half below the line
        median_diff = np.median(differences)

        return slope, intercept + median_diff

    def _get_trend_label(self, slope, fit_method, trend_value):
        if fit_method in ['Mean', 'Median']:
            return f'{fit_method.lower()} = {self.data_manager.format_y_value(trend_value)}'

        unit = self.data_manager.event_bus.emit("get_user_preference", ['celeration_unit', 'Weekly (standard)'])

        # Updated unit_case mapping
        if unit.startswith('Monthly'):
            unit_case = '4w'
        elif unit.startswith('Six-monthly'):
            unit_case = '26w'
        elif unit.startswith('Five-yearly'):
            unit_case = '5y'
        else:
            unit_case = unit[0].lower()

        day_unit_multiple = self.data_manager.cel_unit_dict.get(unit, 7)
        cel = np.power(10, slope * day_unit_multiple)

        symbol = 'x'
        if cel < 1:
            symbol = '÷'
            cel = 1 / cel

        return f'{symbol}{cel:.2f} / {unit_case}'

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

        return upper_bounce, lower_bounce, f'x{bounce_ratio:.2f}'


class FileManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.event_bus = data_manager.event_bus
        self.standard_date_string = '%Y-%m-%d'

        # Event subscription events
        self.event_bus.subscribe('load_chart', self.load_chart_file, has_data=True)
        self.event_bus.subscribe("export_json_from_database", self.export_json_from_database, has_data=True)

    def chart_cleaning(self, loaded_chart, file_path):
        default_chart = self.data_manager.default_chart
        new_chart_data = self.data_manager.ensure_backwards_compatibility(loaded_chart, default_chart)

        # Fix phase text positions
        for phase in new_chart_data['phase']:
            self.event_bus.emit('fix_phase_text_position', phase)

        # Reset credit lines if older version
        if len(new_chart_data['credit']) == 3:
            new_chart_data['credit'] = default_chart['credit']

        # Clean out view keys that don't have corresponding values in column_map
        for key in list(new_chart_data['view'].keys()):
            # Check if key has the expected format and value is not in column_map values
            parts = key.split('|')
            if new_chart_data['column_map']:
                if len(parts) == 2 and parts[1] not in list(new_chart_data['column_map'].values()):
                    del new_chart_data['view'][key]

        # Keep only trend fits that have 'user_col' key and the value exists in column_map values
        for trend_key in ['trend_corr', 'trend_err', 'trend_misc']:
            new_chart_data[trend_key] = [pairs for pairs in new_chart_data[trend_key]
                                            if 'user_col' in pairs and
                                            pairs['user_col'] in new_chart_data['column_map'].values()]

        # If loaded chart file have an old file path
        if file_path != new_chart_data['chart_file_path']:
            new_chart_data['chart_file_path'] = file_path

        # Other backwards compatibility fixes
        if new_chart_data['import_path'] is None or isinstance(new_chart_data['import_path'], (list, str)):
            new_chart_data['import_path'] = {}

        return new_chart_data

    def _repair_corrupted_chart_file(self, file_path):
        # Attempts to repair a corrupted chart file by patching missing or invalid fields
        # with default values from chart_data.
        try:
            # Read the file content
            with open(file_path, 'r') as file:
                content = file.read()

            # Try to find where the JSON is incomplete
            # Start by assuming it's valid up to the last complete field
            last_valid_json = None
            for i in range(len(content), 0, -1):
                try:
                    # Try parsing with added closing brace
                    test_json = content[:i] + "}"
                    parsed = json.loads(test_json)
                    last_valid_json = parsed
                    break
                except:
                    continue

            if last_valid_json:
                # We found a parseable subset of the file
                print(f"Repairing corrupted chart file: {file_path}")

                # Start with default values
                default_chart = copy.deepcopy(self.data_manager.default_chart)

                # Update with the valid parts we found
                default_chart.update(last_valid_json)

                # Ensure db_location is set and is a string
                if 'db_location' not in default_chart or default_chart['db_location'] is None:
                    default_chart['db_location'] = str(self.data_manager.get_config_directory())
                elif isinstance(default_chart['db_location'], Path):
                    default_chart['db_location'] = str(default_chart['db_location'])

                # Set the chart file path
                default_chart['chart_file_path'] = file_path

                return default_chart
            else:
                # If we couldn't find any valid JSON, return a default chart
                print(f"Could not repair chart file, using defaults: {file_path}")
                default_chart = copy.deepcopy(self.data_manager.default_chart)
                default_chart['chart_file_path'] = file_path
                default_chart['db_location'] = str(self.data_manager.get_config_directory())
                return default_chart

        except Exception as e:
            print(f"Error attempting to repair chart file: {e}")
            # Fall back to defaults
            default_chart = copy.deepcopy(self.data_manager.default_chart)
            default_chart['chart_file_path'] = file_path
            default_chart['db_location'] = str(self.data_manager.get_config_directory())
            return default_chart

    def load_chart_file(self, file):
        # Detect if this is a file path or just a chart ID
        is_json_file = isinstance(file, str) and file.endswith('.json')
        path_exists = Path(file).exists() if isinstance(file, str) else False

        # If it's a JSON file that exists, import it to the database first
        if is_json_file and path_exists:
            chart_id = Path(file).stem
            if not self.import_json_to_database(file, chart_id):
                return False  # Failed to import JSON to database
        else:
            # Extract chart_id from filename if a path is provided
            chart_id = Path(file).stem if is_json_file else file

        # Always load from the database
        return self.load_chart_from_db(chart_id)

    def import_json_to_database(self, json_file_path, chart_id):
        """Import JSON file to database via event bus"""
        return self.event_bus.emit('json_import_to_database', {
            'json_file_path': json_file_path,
            'chart_id': chart_id
        })

    def export_json_from_database(self, data):
        """Export chart from database to JSON file via event bus"""
        return self.event_bus.emit('json_export_from_database', data)

    def load_chart_from_db(self, chart_id):
        # Make sure the database connection is initialized
        if not self.data_manager.sqlite_manager.initialized:
            if not self.data_manager.sqlite_manager.connect():
                return False

        # Load data points from database (this also loads metadata via _load_chart_metadata)
        df = self.data_manager.sqlite_manager.load_chart_data(chart_id)
        if df is None or df.empty:
            print(f"No data points found in database for chart ID: {chart_id}")
            self.data_manager.df_raw = pd.DataFrame()
        else:
            self.data_manager.df_raw = df

        # Apply chart cleaning AFTER metadata has been loaded but BEFORE finalization
        self.data_manager.chart_data = self.chart_cleaning(self.data_manager.chart_data, chart_id)
        self.data_manager.chart_data['chart_file_path'] = chart_id

        # Finalize the loading process
        self._finalize_chart_loading(chart_id)
        return True

    def _prompt_for_manual_import(self, title, message):
        data = {'title': title, 'message': message, 'choice': True}
        if self.event_bus.emit('trigger_user_prompt', data):
            import_path = self.event_bus.emit('select_import_path')
            return self.event_bus.emit('column_mapped_raw_data_import', import_path)
        return False

    def _finalize_chart_loading(self, file_path):
        # Generate chart
        self.event_bus.emit('new_chart', self.data_manager.chart_data['start_date'])

        # Save to recents and refresh list
        self.event_bus.emit('save_chart_as_recent', data={'file_path': file_path, 'recent_type': 'recent_charts'})
        self.event_bus.emit('refresh_recent_charts_list')

        # Switch to view mode
        self.event_bus.emit('view_mode_selected')





