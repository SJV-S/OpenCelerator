import pandas as pd
import numpy as np
import os
import copy
import json
from datetime import datetime


class DataManager:
    _instance = None  # Private class variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):

            self.chart_data = {
                'type': 'DailyMinute',
                'raw_data': {'d': [], 'm': [], 'c': [], 'i': []},
                'raw_df': pd.DataFrame(columns=['d', 'm', 'c', 'i']),
                'phase': [],
                'aim': [],
                'trend_corr': [],
                'trend_err': [],
                'credit': ('SUPERVISOR: ________________    DIVISION: ________________       TIMER: ________________     COUNTED: ________________',
                           'ORGANIZATION: ________________     MANAGER: ________________     COUNTER: ________________     CHARTER: ________________',
                           'ADVISOR: ________________        ROOM: ________________   PERFORMER: ________________        NOTE: ________________'),
                'start_date': None,
                'view_check': {
                    'minor_grid': True,
                    'major_grid': True,
                    'dots': True,
                    'xs': True,
                    'dot_trends': True,
                    'x_trends': True,
                    'timing_floor': True,
                    'timing_grid': False,
                    'phase_lines': True,
                    'aims': True,
                    'dot_lines': False,
                    'x_lines': False,
                    'x_color': 'black',
                    'dot_color': 'black',
                }
            }

            self.user_preferences = {
                'place_below_floor': False,
                'chart_data_agg': 'sum',
                'chart_type': 'DailyMinute',
                'chart_font_color': '#5a93cc',
                'chart_grid_color': '#71B8FF',
                'width': 9,
                'fit_method': 'Least-squares',
                'forward_projection': 0,
                'home_folder': os.path.expanduser("~")
            }

            # Support classes
            self.trend_fitter = TrendFitter(self)

            self.initialized = True  # Set this attribute after initializing
            self.chart_data_default = copy.deepcopy(self.chart_data)

            # Apply settings
            self.get_user_preferences()

    def get_replot_points(self, date_to_x, kind):
        df = copy.deepcopy(self.chart_data['raw_df'])

        chart_type = self.user_preferences['chart_type']
        if chart_type == 'DailyMinute':
            x, y = self.get_daily_minute_points(df, kind, date_to_x)
        elif chart_type == 'Daily':
            x, y = self.get_daily_points(df, kind, date_to_x)
        elif chart_type == 'Weekly':
            x, y = self.get_weekly_points(df, kind, date_to_x)
        elif chart_type == 'WeeklyMinute':
            x, y = self.get_weekly_minute_points(df, kind, date_to_x)
        elif chart_type == 'MonthlyMinute':
            x, y = self.get_monthly_minute_points(df, kind, date_to_x)
        elif chart_type == 'Monthly':
            x, y = self.get_monthly_minute_points(df, kind, date_to_x)

        return x, y

    def get_replot_phase(self, date_to_x,):
        phase_lines = []
        for phase in self.chart_data['phase']:
            date, y, text = phase
            if date in date_to_x.keys():
                x = date_to_x[date]
                phase_lines.append((x, y, text))
        return phase_lines
    
    def get_replot_aims(self, date_to_x):
        all_aims = []
        for aim in self.chart_data['aim']:
            # Maybe make it so that date order doesn't matter?
            start, deadline, target, note = aim
            if all(date in date_to_x.keys() for date in (start, deadline)):
                xmin = date_to_x[start]
                xmax = date_to_x[deadline]
                all_aims.append((xmin, xmax, target, note))
        
        return all_aims

    def data_import_data(self, file_path, date_format):
        # Determine how to read the file based on its extension
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, usecols=[0, 1, 2, 3])  # Only look at the first 4 columns
            df.columns = [col.lower()[0] for col in df.columns]  # Make it all lower case, and only look at the first letter
            df['d'] = pd.to_datetime(df['d'])

            # If user wrote "errors" or "wrong" instead of incorrects
            for alt in ['e', 'w']:
                if alt in df.columns:
                    df = df.rename(columns={alt: 'i'})

            # If user wrote "accurate" or "right" instead of corrects
            for alt in ['a', 'r']:
                if alt in df.columns:
                    df = df.rename(columns={alt: 'c'})

        elif file_path.endswith('.xls') or file_path.endswith('.xlsx') or file_path.endswith('.ods'):
            df = pd.read_excel(file_path)
            df.columns = [col.lower() for col in df.columns]
            # df['d'] = df['d'].astype(str)  # Ensure date column is treated as a string
        else:
            return  # Exit function if wrong file type

        # Average entries if stacked on the same date
        df['d'] = pd.to_datetime(df['d']).dt.normalize()
        df['c'] = pd.to_numeric(df['c'], errors='coerce').apply(lambda x: max(x, 0) if pd.notnull(x) else 0)
        df['i'] = pd.to_numeric(df['i'], errors='coerce').apply(lambda x: max(x, 0) if pd.notnull(x) else 0)
        df['m'] = pd.to_numeric(df['m'], errors='coerce').apply(lambda x: max(x, 1) if pd.notnull(x) else 1)
        df = df.groupby('d', as_index=False).mean()

        # Store imported raw data (also clears any previous data points)
        self.chart_data['raw_df'] = df

    def create_export_file(self, file_path):
        df = copy.deepcopy(self.chart_data['raw_df'])

        # Discard times
        df['d'] = pd.to_datetime(df.d).dt.date

        if not file_path.endswith('.csv'):
            file_path += '.csv'

        full_names = {'c': 'Corrects', 'i': 'Errors', 'm': 'Minutes', 'd': 'Dates'}
        df.rename(columns=full_names, inplace=True)
        df.to_csv(file_path, index=False)

    def update_view_check(self, setting, state):
        self.chart_data['view_check'][setting] = bool(state)

    def get_trend(self, x1, x2, corr, date_to_x, min_sample=4):
        result = self.trend_fitter.get_trend(x1, x2, corr, date_to_x, min_sample)
        return result

    def update_dataframe(self, date, total_minutes, count, point_type):
        df = self.chart_data['raw_df']
        kind = 'c' if point_type else 'i'
        other_kind = 'i' if kind == 'c' else 'c'

        # Create a mask for existing date
        mask = df['d'] == date

        if mask.any():
            # Update the values for the existing row with the matching date
            df.loc[mask, kind] = count
            df.loc[mask, 'm'] = total_minutes
        else:
            # Create a new row as a DataFrame and append it
            new_data = {'d': [date], kind: [count], 'm': [total_minutes], other_kind: [0]}
            new_row = pd.DataFrame(new_data)
            new_row = new_row.reindex(columns=df.columns, fill_value=0).astype(df.dtypes.to_dict())
            self.chart_data['raw_df'] = pd.concat([df, new_row], ignore_index=True)

    def set_chart_type(self, new_type):
        if self.chart_data['type'] != new_type:
            self.chart_data['type'] = new_type
            self.type_changed.emit(new_type)  # Emit signal when type changes

    def save_user_preferences(self):
        run_dir = os.path.dirname(os.path.abspath(__file__))
        filename = 'preferences.json'
        with open(os.path.join(run_dir, filename), 'w') as f:
            json.dump(self.user_preferences, f, indent=4)

    def handle_zero_counts_unit(self, y):
        # Handling for zero counts
        if self.user_preferences['place_below_floor']:
            # Place below timing floor
            y = np.where(y == 0, 0.8, y)
        else:
            # Don't display
            y = y.apply(lambda x: np.where(x == 0, np.nan, x))
        return y

    def handle_zero_counts_minutes(self, df, kind):
        # Handling for zero counts for minute charts
        y = df[kind] / df['m']  # Get frequency for kind
        if self.user_preferences['place_below_floor']:
            # Place below timing floor
            m_safe = df['m'].replace(0, np.nan)  # Replace 0 in 'm' with NaN for safety
            y = np.where(df[kind] == 0, (1 / m_safe) * 0.8, df[kind] / m_safe)
        else:
            # Don't display
            y = y.apply(lambda x: np.where(x == 0, np.nan, x))
        return y

    def get_user_preferences(self):
        run_dir = os.path.dirname(os.path.abspath(__file__))
        filename = 'preferences.json'

        # If error, delete current file and replace with defaults
        if filename in os.listdir(run_dir):
            try:
                with open(os.path.join(run_dir, filename), 'r') as f:
                    loaded_pref = json.load(f)
                    if self.user_preferences.keys() == loaded_pref.keys():
                        # Load save preferences
                        self.user_preferences = loaded_pref
                    else:
                        # Reset json to default due to missing keys
                        with open(os.path.join(run_dir, filename), 'w') as f:
                            json.dump(self.user_preferences, f, indent=4)
            except:
                # Reset malformed json to default
                with open(os.path.join(run_dir, filename), 'w') as f:
                    json.dump(self.user_preferences, f, indent=4)
        else:
            with open(os.path.join(run_dir, filename), 'w') as f:
                json.dump(self.user_preferences, f, indent=4)

    def get_daily_minute_points(self, df, kind, date_to_x):
        x = df['d'].map(date_to_x)  # Convert date to x position

        if kind == 'm':
            y = 1 / df[kind]  # Get timing floor
        else:
            y = self.handle_zero_counts_minutes(df, kind)

        return x, y

    def get_daily_points(self, df, kind, date_to_x):
        x = df['d'].map(date_to_x)  # Convert date to x position
        y = self.handle_zero_counts_unit(df[kind])

        return x, y

    def get_weekly_points(self, df, kind, date_to_x):
        # Aggregate daily entries
        df['d'] = pd.to_datetime(df.d)
        df.set_index('d', inplace=True)
        df = df.resample('W').agg(self.user_preferences['chart_data_agg']).reset_index()

        x = df['d'].map(date_to_x)  # Convert date to x position
        y = self.handle_zero_counts_unit(df[kind])

        return x, y

    def get_weekly_minute_points(self, df, kind, date_to_x):
        # Aggregate daily entries
        df['d'] = pd.to_datetime(df.d)
        df.set_index('d', inplace=True)
        df = df.resample('W').agg(self.user_preferences['chart_data_agg']).reset_index()

        x = df['d'].map(date_to_x)  # Convert date to x position
        if kind == 'm':
            y = 1 / df[kind]  # Get timing floor
        else:
            y = self.handle_zero_counts_minutes(df, kind)

        return x, y

    def get_monthly_points(self, df, kind, date_to_x):
        # Aggregate daily entries
        df['d'] = pd.to_datetime(df.d)
        df.set_index('d', inplace=True)
        df = df.resample('ME').agg(self.user_preferences['chart_data_agg']).reset_index()

        x = df['d'].map(date_to_x)  # Convert date to x position
        y = self.handle_zero_counts_unit(df[kind])

        return x, y

    def get_monthly_minute_points(self, df, kind, date_to_x):
        # Aggregate daily entries
        df['d'] = pd.to_datetime(df.d)
        df.set_index('d', inplace=True)
        df = df.resample('ME').agg(self.user_preferences['chart_data_agg']).reset_index()

        x = df['d'].map(date_to_x)  # Convert date to x position
        if kind == 'm':
            y = 1 / df[kind]  # Get timing floor
        else:
            y = self.handle_zero_counts_minutes(df, kind)

        return x, y

    def save_chart(self, full_path, start_date):
        # Ensure the file has a .pkl extension
        if not full_path.endswith('.json'):
            full_path += '.json'

        # Save current start date in ISO format
        self.chart_data['start_date'] = start_date.isoformat() if isinstance(start_date, datetime) else start_date

        # Convert df date column to iso format and update raw_data dictionary
        df = copy.deepcopy(self.chart_data['raw_df'])
        if pd.api.types.is_datetime64_any_dtype(df['d']):
            df['d'] = df['d'].dt.strftime('%Y-%m-%d')

        self.chart_data['raw_data'] = df.to_dict()

        # Remove df from dictionary
        json_to_save = copy.deepcopy(self.chart_data)
        del json_to_save['raw_df']

        with open(full_path, 'w') as file:
            json.dump(json_to_save, file, indent=4)


class TrendFitter:
    def __init__(self, data_manager):
        self.data_manager = data_manager

    def filter_zero_counts_and_below_floor(self, x, y):
        # Haven't added handling for below floor yet
        nan_mask = ~np.isnan(y)
        y = y[nan_mask]
        x = x[nan_mask]
        return x, y

    def get_trend_label(self, slope):
        cel_unit = 7  # Change to specific chart type variable?
        cel_label = np.power(10, slope * cel_unit)

        if cel_label < 1:
            cel_label = "÷" + str(round(1 / cel_label, 1))
        else:
            cel_label = "x" + str(round(cel_label, 1))

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

    def extract_trend(self, x, y):
        x = np.array(x)
        y = np.array(y)

        x, y = self.filter_zero_counts_and_below_floor(x, y)
        extended_x = np.arange(x[0], x[-1] + self.data_manager.user_preferences['forward_projection'] + 1)

        fit_method = self.data_manager.user_preferences['fit_method']
        if fit_method == 'Quarter-intersect':
            slope, intercept = self.quarter_intersect_fit(x, np.log10(y))
            trend = slope * extended_x + intercept
        elif fit_method == 'Split-middle-line':
            slope, intercept = self.split_middle_line_fit(x, np.log10(y))
            trend = slope * extended_x + intercept
        else:
            # Least squares
            slope, intercept = np.polyfit(x, np.log10(y), 1)
            trend = np.polyval((slope, intercept), extended_x)

        trend = np.power(10, trend)
        cel_label = self.get_trend_label(slope)

        return trend, cel_label, extended_x

    def get_trend(self, x1, x2, corr, date_to_x, min_sample=4):
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        kind = 'c' if corr else 'i'

        x, y = self.data_manager.get_replot_points(date_to_x, kind)
        point_dict = {x_i: y_i for x_i, y_i in zip(x, y)}

        selected_range_set = set(np.arange(min_x, max_x + 1))  # Create a set from the range
        keys_set = set(x)  # Get keys from dictionary as a set

        if len(x) >= min_sample:
            x_slice = list(selected_range_set & keys_set)  # Find intersection of both sets
            y_slice = [point_dict[x_i] for x_i in x_slice]
        else:
            return

        if len(y_slice) >= min_sample:
            trend_vals, cel_est, extended_x = self.extract_trend(x_slice, y_slice)

            return extended_x, trend_vals, cel_est, np.mean(x_slice), np.mean(trend_vals)









