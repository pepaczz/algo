"""
This module contains functions to fetch frequently used datasets to keep them in memory.
"""

import numpy as np
import pandas as pd
import os
import algo.constants as const
import requests


def fetch_erp_data(fetch_col):
    """Fetch ERP data from CSV file. Limit data to minimum year."""
    # load erp data from csv file and limit data to minimum year
    erp_data = pd.read_csv(const.PATH_ERP)
    erp_data = erp_data[erp_data['date'] >= f'{const.FETCH_MIN_YEAR}-01-01']

    return erp_data[['date'] + [fetch_col]]


erp_rates = fetch_erp_data('erp_fcfe_sustainable_payout')
growth_rates = fetch_erp_data('analyst_growth_estimate')


def fetch_sec_companies(keep_cik_num=False):
    """Retrieves the list of companies from the SEC"""

    # create request header and get all companies data
    response = requests.get("https://www.sec.gov/files/company_tickers.json", headers=const.SEC_HEADERS)

    # convert to dataframe and format columns
    company_data = pd.DataFrame.from_dict(response.json(), orient='index')
    company_data['cik_str'] = company_data['cik_str'].astype(str).str.zfill(10)

    if keep_cik_num:
        company_data['cik_num'] = company_data['cik_str'].astype(int)

    return company_data


sec_companies = fetch_sec_companies()


def fetch_rf_rates():
    """Get the risk-free rate (10Y US TREASURY NOTES) at a given date."""
    tnotes = pd.read_csv(os.path.join(const.FLD_TNOTES, const.FILE_TNOTES))
    tnotes = tnotes[['Date', 'DGS10']].dropna().loc[tnotes['Date'] >= f'{const.FETCH_MIN_YEAR}-01-01']
    tnotes.columns = ['date', 'rf_rate']
    return tnotes


rf_rates = fetch_rf_rates()


def fetch_implied_perp_g_rates():
    """Fetch implied perpetual growth rates."""
    res = pd.read_csv(const.PATH_IMPLIED_PERP_G_RATES)
    # convert date to datetime
    res['date'] = pd.to_datetime(res['date'])
    return res


implied_perp_g_rates = fetch_implied_perp_g_rates()


def fetch_implied_perp_g_rates_p50():
    """Fetch implied perpetual growth rates."""
    return pd.read_csv(const.PATH_IMPLIED_PERP_G_RATES_P50)


implied_perp_g_rates_p50 = fetch_implied_perp_g_rates_p50()
mean_implied_perp_g_rates_p50 = np.mean(implied_perp_g_rates_p50['implied_perp_g_rate'])


def get_rf_rate_at_date(date):
    """Get the risk-free rate (10Y US TREASURY NOTES) at a given date."""
    return rf_rates.loc[rf_rates['date'] <= date, 'rf_rate'].iloc[-1] / 100


def get_growth_rate_at_date(date):
    """Get the growth rate at a given date."""
    return growth_rates.loc[growth_rates['date'] <= date, 'analyst_growth_estimate'].iloc[-1]


def get_erp_at_date(date):
    """Get the equity risk premium at a given date."""
    return erp_rates.loc[erp_rates['date'] <= date, 'erp_fcfe_sustainable_payout'].iloc[-1]


