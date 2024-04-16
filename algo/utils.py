import traceback
import os
import algo.constants as const
import pandas as pd
import numpy as np


def if_none(val, default):
    """Returns default if val is None, otherwise returns val."""
    return default if val is None else val


def if_nan_none(val, default):
    """Returns default if val is None or NaN, otherwise returns val."""
    if (val is None) or (np.isnan(val)):
        return default
    else:
        return val


def maybe_make_dir(directory):
    """Creates directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def upsert_results(df, add_timestamp=True):
    """Upsert results to csv file. If file does not exist, create it. If it exists, upserts new results."""
    # add created column
    if add_timestamp:
        df['created'] = pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')

    fld_save = maybe_make_dir(const.FLD_RESULTS_INTRINSIC_VALUES)
    full_path = os.path.join(fld_save, const.FILE_RESULTS_INTRINSIC_VALUES)
    if const.FILE_RESULTS_INTRINSIC_VALUES not in os.listdir(fld_save):
        df.to_csv(full_path, index=False)
    else:
        # load existing results
        result = pd.read_csv(full_path)

        # upsert
        result = pd.concat([result, df])
        result = result.drop_duplicates(subset=['ticker', 'date'], keep='last')
        result.to_csv(full_path, index=False)
    return None


def upsert_into_df(df, save_fld, save_file, index_cols, add_created=True):
    """Upserts data into dataframe."""
    # add created column
    if add_created:
        df['created'] = pd.Timestamp.now().strftime(format='%Y-%m-%d %H:%M:%S')

    # do nothing if df is empty
    if df.shape[0] == 0:
        return None

    # make sure folder exists
    _ = maybe_make_dir(save_fld)
    full_path = os.path.join(save_fld, save_file)

    if save_file not in os.listdir(save_fld):
        df.to_csv(full_path, index=False)
    else:
        # load existing results
        result = pd.read_csv(full_path)

        # upsert
        result = pd.concat([result, df])
        result = result.drop_duplicates(subset=index_cols, keep='last')
        result.to_csv(full_path, index=False)
    return None


def elu(x):
    """Exponential Linear Unit.
    # x = np.linspace(-3, 3, 101)
    # y = [elu(val-1)+1 for val in x]
    #
    # # plot
    # import matplotlib.pyplot as plt
    # plt.plot(x, y)
    # plt.grid()
    # plt.show()
    """
    return x if x >= 0 else (np.exp(x) - 1)


def get_assignment_part_error_message():
    error_message = traceback.format_exc().split('\n')
    assignment_lines = [x for x in error_message if '=' in x]
    if len(assignment_lines) == 0:
        return 'Other error'
    else:
        return 'Error line: ' + assignment_lines[-1].strip()

