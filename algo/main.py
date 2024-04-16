# taylo rule: https://www.kaggle.com/code/aradhanasaha/taylor-s-rule
# https://www.sec.gov/dera/data/financial-statement-data-sets
# https://www.wallstreetprep.com/knowledge/cost-of-equity/

import os
from importlib import reload
import pandas as pd
import numpy as np
import algo.data_acquisition as da
import algo.constants as const
import algo.utils as utils
import algo.modelling as model

reload(model)
reload(da)
reload(const)
reload(utils)

available_tickers = da.get_available_tickers()
# available_tickers = available_tickers[20:40]
# available_tickers = ['A', 'AAL', 'AAPL', 'ABBV', 'ABNB']
# available_tickers = ['AAPL']

optimize_perp_g_rate = False  # False  # True

# iterate over all available tickers
for idx, ticker in enumerate(available_tickers):  # [:10]):
    # ticker = available_tickers[0]  # debug
    print(ticker)

    # get all dates for the ticker
    dates = da.get_ticker_dates(ticker)

    # case: estimate implied perpetual growth rate
    if optimize_perp_g_rate:
        results_g_rates = pd.DataFrame(data=None, columns=['ticker', 'date', 'implied_perp_g_rate'])
        for date in dates:
            # date = dates[0]  # debug
            results_g_rates = model.get_optimized_perp_g_rate(ticker, date, results_g_rates)
        utils.upsert_into_df(results_g_rates, const.FLD_IMPLIED_PERP_G_RATES,
                             const.FILE_IMPLIED_PERP_G_RATES, ['ticker', 'date'])

    # case: get intrinsic value
    else:
        results_values = pd.DataFrame(data=None,
                                      columns=['ticker', 'date', 'intrinsic_value', 'share_price', 'error_message'])
        for date in dates:
            # date = dates[0]  # debug
            results_values = model.get_intrinsic_value_wrapper(ticker, date, results_values)
        utils.upsert_results(results_values)


