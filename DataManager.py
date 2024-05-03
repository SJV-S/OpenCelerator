import pandas as pd
import numpy as np

class DataManager:
    _instance = None  # Private class variable to hold the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DataManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):

            # Default credit line rows
            self.credit_row1 = 'SUPERVISOR: ________________    DIVISION: ________________       TIMER: ________________     COUNTED: ________________'
            self.credit_row2 = 'ORGANIZATION: ________________     MANAGER: ________________     COUNTER: ________________     CHARTER: ________________'
            self.credit_row3 = 'ADVISOR: ________________        ROOM: ________________   PERFORMER: ________________        NOTE: ________________'

            self.chart_data = {
                'raw_df': pd.DataFrame(columns=['d', 'm', 'c', 'i']),
                'phase': [],
                'aim': [],
                'trend_corr': [],
                'trend_err': [],
                'credit': (self.credit_row1, self.credit_row2, self.credit_row3),
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
                    'x_lines': False
                }
            }
            self.initialized = True  # Set this attribute after initializing

    def get_replot_points(self, date_to_x, kind):
        df = self.chart_data['raw_df']
        x = df['d'].map(date_to_x)  # Convert date to x position

        if kind == 'm':
            y = 1 / df[kind]  # Get timing floor
        else:
            y = df[kind] / df['m']  # Get frequency for kind

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

    def adjust_per_minute(self, row):
        if row['corr_freq'] == 0:
            row['corr_freq'] = row['floor'] * 0.7
        if row['err_freq'] == 0:
            row['err_freq'] = row['floor'] * 0.7
        return row

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

        # Store imported raw data (also clears any previous data points)
        self.chart_data['raw_df'] = df

    def create_export_file(self, file_path):
        try:
            df = self.chart_data['raw_df']
            print(df['d'].dtypes)
            df['d'] = df['d'].dt.date  # Discard times

            if not file_path.endswith('.csv'):
                file_path += '.csv'

            full_names = {'c': 'Corrects', 'i': 'Errors', 'm': 'Minutes', 'd': 'Dates'}
            df.rename(columns=full_names, inplace=True)
            df.to_csv(file_path, index=False)
        except Exception as e:
            print(e)

    def update_view_check(self, setting, state):
        self.chart_data['view_check'][setting] = bool(state)

    def fit_trend(self, x, y):
        # Assumes x are integers
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

    def get_trend(self, x1, x2, corr, date_to_x):
        min_x = min(x1, x2)
        max_x = max(x1, x2)
        kind = 'c' if corr else 'i'

        x, y = self.get_replot_points(date_to_x, kind)
        point_dict = {x_i: y_i for x_i, y_i in zip(x, y)}

        selected_range_set = set(np.arange(min_x, max_x + 1))  # Create a set from the range
        keys_set = set(x)  # Get keys from dictionary as a set

        if len(x) > 0:
            x_slice = list(selected_range_set & keys_set)  # Find intersection of both sets
            y_slice = [point_dict[x_i] for x_i in x_slice]
        else:
            return

        if y_slice:
            trend_vals, cel_est = self.fit_trend(x_slice, y_slice)
            return x_slice, trend_vals, cel_est, np.mean(x_slice), np.mean(trend_vals)

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













