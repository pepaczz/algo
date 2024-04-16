
import os
from importlib import reload
import sys
import traceback
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
available_tickers = ['MAAI']

download_share_prices = False
if download_share_prices:
    da.download_all_share_prices(available_tickers)

# shares outstanding are now taken from SEC rather than from yfinance
# download_shares_outstanding = False
# if download_shares_outstanding:
#     da.download_all_shares_outstanding(available_tickers)

download_betas = False
if download_betas:
    da.download_all_betas(available_tickers)

download_sp500_returns = False
if download_sp500_returns:
    da.download_sp500_returns()