import ntpath
import glob
import os
from io import StringIO
import requests
import datetime as dt
import pandas as pd
import numpy as np
import yahoo_fin.stock_info as si
import algo.constants as const
import algo.utils as utils
import yfinance as yf
from algo.fetched_data import sec_companies


def get_sp500_list():
    """Gets the list of S&P 500 companies"""

    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    data = pd.read_html(url)

    current_stocks = data[0][['Symbol', 'Date added']].copy()
    current_stocks.columns = ['ticker', 'date_added']
    current_stocks['date_added'] = pd.to_datetime(current_stocks['date_added'])

    return current_stocks


def get_sp500_history():
    """Gets the list of S&P 500 companies and their date added to the index."""

    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    data = pd.read_html(url)

    current_stocks = data[0][['Symbol', 'Date added']].copy()
    current_stocks.columns = ['ticker', 'date_added']
    current_stocks['date_added'] = pd.to_datetime(current_stocks['date_added'])

    changes = data[1].copy()
    changes.columns = ['_'.join(col) for col in changes.columns]
    changes['Date'] = pd.to_datetime(changes['Date_Date'])

    additions = changes[['Added_Ticker', 'Date']].loc[changes['Added_Ticker'].notnull()]
    additions.columns = ['ticker', 'date_added_changes']

    removals = changes[['Removed_Ticker', 'Date']].loc[changes['Removed_Ticker'].notnull()]
    removals.columns = ['ticker', 'date_removed']

    tickers_set = list(set(current_stocks['ticker'].to_list() +\
                      additions['ticker'].to_list() +\
                      removals['ticker'].to_list()))

    tickers_all = (
        pd.DataFrame(tickers_set, columns=['ticker'])
        .merge(current_stocks, how='left', on='ticker')
        .merge(additions, how='left', on='ticker')
        .merge(removals, how='left', on='ticker')
    )

    # # get records where date_added differs from date_added_changes
    # added_differs = tickers_all.loc[tickers_all['date_added'].notnull() &
    #                                 tickers_all['date_added_changes'].notnull() &
    #                                 (tickers_all['date_added'] != tickers_all['date_added_changes'])]
    #
    # # get difference in days
    # added_differs.loc[:, 'diff'] = (added_differs['date_added'].copy() - added_differs['date_added_changes'].copy()).dt.days.abs()
    # added_differs.sort_values(by='diff', ascending=False)

    # replace date_added with date_added_changes if date_added is missing or date_added_changes < date_added
    tickers_all.loc[tickers_all['date_added'].isnull() |
                    (tickers_all['date_added_changes'] < tickers_all['date_added']), 'date_added'] = tickers_all['date_added_changes']

    # define default dates
    default_date_added = dt.datetime(1995, 1, 1)

    # add default dates
    tickers_all['date_added'] = tickers_all['date_added'].fillna(default_date_added)
    tickers_all = tickers_all.drop(columns=['date_added_changes'])

    return tickers_all


def get_analysts_info(ticker, headers=const.YFINANCE_HEADERS):
    """Scrapes the Analysts page from Yahoo Finance for an input ticker."""

    analysts_site = "https://finance.yahoo.com/quote/" + ticker + \
                    "/analysts?p=" + ticker
    tables = pd.read_html(StringIO(requests.get(analysts_site, headers=headers).text))
    table_names = [table.columns[0] for table in tables]
    table_mapper = {key: val for key, val in zip(table_names, tables)}
    return table_mapper


def get_live_price(ticker):
    """Gets the live price of input ticker"""
    df = si.get_data(ticker, end_date=pd.Timestamp.today() + pd.DateOffset(10))
    return df.close.iloc[-1]


def get_10k_dates(ticker, concept='OperatingIncomeLoss', year_from=None, year_to=None):
    """Gets available dates by calling Concept API for a given ticker and concept
    Not used - data are retrieved from .csv archive files
    """
    df = get_concept_by_ticker(ticker, concept)

    # filter for relevant year only if required
    if year_from is not None:
        df = df.loc[df['end'] >= f'{year_from}-01-01', :]

    if year_to is not None:
        df = df.loc[df['end'] <= f'{year_to}-12-31', :]

    return df.loc[df['form'] == '10-K', ['end', 'form']].drop_duplicates().sort_values('end').reset_index(drop=True)


def get_concept_by_ticker(ticker, concept, headers=const.SEC_HEADERS):
    """Downloads data from SEC for ticker and concept
    Not used - data are retrieved from .csv archive files
    """
    cik = sec_companies.loc[sec_companies['ticker'] == ticker, 'cik_str'].to_list()[0]
    try:
        concept_response = requests.get(f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json',
                                        headers=headers)
        return pd.DataFrame.from_dict(concept_response.json()['units']['USD'])
    except requests.exceptions.JSONDecodeError:
        return None


def get_single_observation_api(ticker, concept, year, return_value=True):
    """Gets single observation for ticker, concept and year from SEC api
    Not used - data are retrieved from .csv archive files
    On the other hand the most recent data might not be available in the archive (? check)
    """
    df = get_concept_by_ticker(ticker, concept)
    if df is None:
        return None
    df = df.loc[df['form'] == '10-K', :].sort_values(['end', 'filed']).groupby('end').last().reset_index()
    df['year'] = pd.to_datetime(df['end']).dt.year
    df['concept'] = concept
    df['ticker'] = ticker
    res = df.loc[df['year'] == year, ['concept', 'val', 'year', 'end', 'form']]

    if res.shape[0] == 0:
        return None

    if return_value:
        return res['val'].values[0]
    else:
        return res


def get_single_observation(ticker, concept, year, return_value=True):
    """Gets a single observation for ticker, concept and year. Uses csv data.
    Parameter return_value is kept for backward compatibility with get_single_observation_api
    """
    data_raw = pd.read_csv(f'{const.FLD_STATEMENTS}/{ticker}.csv')
    data_raw['year'] = pd.to_datetime(data_raw['date']).dt.year
    res = data_raw.loc[(data_raw['ticker'] == ticker) &
                       (data_raw['concept'] == concept) &
                       (data_raw['year'] == year), 'val']

    if res.shape[0] == 0:
        return None
    elif res.shape[0] > 1:
        raise ValueError(f'Multiple observations for {ticker} and {concept} in year {year}')
    else:
        return res.values[0]


def get_single_observation_non_usd(ticker, concept, year, return_value=True, units='shares'):
    """Equivalent of get_single_observation for non-USD units.
    Not used - data are retrieved from .csv archive files
    On the other hand the most recent data might not be available in the archive (? check)
    """
    headers = {'User-Agent': const.SEC_USER_AGENT}
    cik = sec_companies.loc[sec_companies['ticker'] == ticker, 'cik_str'].to_list()[0]
    try:
        concept_response = requests.get(f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json',
                                        headers=headers)
        df = pd.DataFrame.from_dict(concept_response.json()['units'][units])
    except requests.exceptions.JSONDecodeError:
        return None

    df = df.loc[df['form'] == '10-K', :].sort_values(['end', 'filed']).groupby('end').last().reset_index()
    df['year'] = pd.to_datetime(df['end']).dt.year
    df['concept'] = concept
    df['ticker'] = ticker
    res = df.loc[df['year'] == year, ['concept', 'val', 'year', 'end', 'form']]

    if res.shape[0] == 0:
        return None

    if return_value:
        return res['val'].values[0]
    else:
        return res


def download_ticker_beta(ticker, headers=const.YFINANCE_HEADERS):
    """Gets the beta for a given ticker"""
    site = "https://finance.yahoo.com/quote/" + ticker + "?p=" + ticker
    # price_data = pd.read_html(StringIO(requests.get(site, headers=headers).text))[0]
    response = pd.read_html(StringIO(requests.get(site, headers=headers).text))
    if len(response) < 2:
        return None
    else:
        metrics = response[1]
    beta = metrics.loc[metrics[0] == 'Beta (5Y Monthly)', 1].values[0]
    return float(beta)


def download_all_betas(tickers_list, headers=const.YFINANCE_HEADERS):
    """Downloads betas for a list of tickers."""
    # tickers_list = available_tickers
    downloads_list = []
    for ticker in tickers_list:
        print(ticker)
        beta = download_ticker_beta(ticker, headers=headers)
        downloads_list.append({'ticker': ticker, 'beta': beta})
    downloads = pd.DataFrame(downloads_list)

    utils.upsert_into_df(downloads, const.FLD_BETAS, const.FILE_BETAS, index_cols=['ticker'])
    return None


def get_beta(ticker):
    """Gets the beta for a given ticker."""
    betas = pd.read_csv(f'{const.FLD_BETAS}/{const.FILE_BETAS}')
    return betas.loc[betas['ticker'] == ticker, 'beta'].values[0]


def download_ticker_shares_outstanding(ticker, date):
    """Gets the number of shares outstanding for a given ticker and date.
    Not used - data are retrieved from .csv archive files
    Also there is a short history, e.g. MSFT only back to 2022
    """
    yf_ticker = yf.Ticker(ticker)
    shares_full = yf_ticker.get_shares_full().sort_index()
    last_value = shares_full.loc[shares_full.index <= date].iloc[-1]
    return last_value


def download_all_shares_outstanding(tickers_list):
    """Downloads shares outstanding for a list of tickers.
    Not used - data are retrieved from .csv archive files
    """
    # tickers_list = get_available_tickers()
    for idx, ticker in enumerate(tickers_list):

        # retrieve share price history from Yahoo Finance
        yf_ticker = yf.Ticker(ticker)
        try:
            history = yf_ticker.get_shares_full().sort_index()
            history = history.reset_index(drop=False)
            history.columns = ['Date', 'Shares_Outstanding']
            history['Date'] = history['Date'].dt.date
        except AttributeError:
            print(f'{ticker} no data')
            continue

        # write to csv
        utils.maybe_make_dir(const.FLD_SHARES_OUTSTANDING)
        history.to_csv(f'{const.FLD_SHARES_OUTSTANDING}/{ticker}.csv', index=False)
        print(f'{ticker} ok')

    return None


def get_share_price(ticker, date):
    """Gets share price for a given ticker and date."""
    # load history from csv
    try:
        history = pd.read_csv(f'{const.FLD_SHARE_PRICES}/{ticker}.csv')
    except FileNotFoundError:
        return np.nan

    try:
        closes_before_date = history.loc[history['Date'] <= date, 'Close']
    except KeyError:
        return np.nan

    if closes_before_date.shape[0] == 0:
        return np.nan
    else:
        return closes_before_date.iloc[-1]


def get_share_price_around_date(ticker, date, direction='before', n_days=1):
    """Gets share price for a given ticker and date."""
    # shift date by n_days
    date_shifted = pd.to_datetime(date) + pd.DateOffset(days=n_days)

    # load history from csv
    try:
        history = pd.read_csv(f'{const.FLD_SHARE_PRICES}/{ticker}.csv')
        # convert date to datetime
        history['Date'] = pd.to_datetime(history['Date'])
    except (FileNotFoundError, KeyError) as e:
        return np.nan

    try:
        if direction == 'before':
            closes_filtered = history.loc[history['Date'] <= date_shifted, 'Close']
        elif direction == 'after':
            closes_filtered = history.loc[history['Date'] >= date_shifted, 'Close']
        else:
            raise ValueError('direction must be either before or after')

    except KeyError:
        return np.nan

    if closes_filtered.shape[0] == 0:
        return np.nan
    else:
        if direction == 'before':
            return closes_filtered.iloc[-1]
        elif direction == 'after':
            return closes_filtered.iloc[0]


def get_shares_outstanding_yf_data(ticker, date):
    """Gets the number of shares outstanding for a given ticker and date."""
    shares_outstanding = pd.read_csv(f'{const.FLD_SHARES_OUTSTANDING}/{ticker}.csv')
    shares_before_date = shares_outstanding.loc[shares_outstanding['Date'] <= date, 'Shares']

    if shares_before_date.shape[0] == 0:
        return None
    else:
        return shares_before_date.iloc[-1]


def get_growth_estimate(ticker):
    """Gets the 5-year growth estimate for a given ticker."""
    analysts_info = get_analysts_info(ticker)['Growth Estimates']
    growth_5y_str = analysts_info.loc[analysts_info['Growth Estimates'] == 'Next 5 Years (per annum)', ticker].values[0]
    return float(growth_5y_str.strip('%'))/100


def get_ticker_dates(ticker, limit_to_defined_years=True):
    """Returns list of available dates for a given ticker."""
    res = pd.read_csv(os.path.join(const.FLD_STATEMENTS, f'{ticker}.csv'))['date'] \
        .drop_duplicates() \
        .sort_values()\
        .to_list()
    # limit to years from constants module
    if limit_to_defined_years:
        res = [date for date in res if pd.to_datetime(date).year in const.YEARS]

    return res


def get_available_tickers(start_from=None):
    """Returns list of available tickers."""
    all_files = glob.glob(os.path.join(const.FLD_STATEMENTS, "*.csv"))
    tickers = [ntpath.basename(f).replace('.csv', '') for f in all_files]

    # start from a specific ticker if required
    if start_from is not None:
        start_idx = tickers.index(start_from)
        tickers = tickers[start_idx:]

    return tickers


def download_all_share_prices(tickers_list):
    # tickers_list = get_available_tickers()
    """Downloads all share prices for available tickers."""

    for idx, ticker in enumerate(tickers_list):
        # retrieve share price history from Yahoo Finance
        yf_ticker = yf.Ticker(ticker)
        history = yf_ticker.history(period="30y").sort_index()
        history = history.reset_index(drop=False)
        try:
            history['Date'] = history['Date'].dt.date
        except AttributeError:
            print(f'{ticker} no data')
            continue

        # write to csv
        utils.maybe_make_dir(const.FLD_SHARE_PRICES)
        history.to_csv(f'{const.FLD_SHARE_PRICES}/{ticker}.csv', index=False)
        print(f'{ticker} ok')
    return None


def download_sp500_returns():
    """Downloads S&P 500 Y-O-Y returns for the last 30 years."""
    sp500 = yf.Ticker('^GSPC')
    history = sp500.history(period="30y").sort_index()
    history = history.reset_index(drop=False)
    history['Date'] = history['Date'].dt.date
    history['year'] = pd.to_datetime(history['Date']).dt.year
    history['return'] = history['Close'].pct_change(periods=252)

    # save to csv
    utils.maybe_make_dir(const.FLD_SP500_RETURNS)
    history.to_csv(f'{const.FLD_SP500_RETURNS}/{const.FILE_SP500_RETURNS}', index=False)
    return None


def get_sp500_return(date):
    """Gets the S&P 500 year-over-year returns for a given date."""
    returns = pd.read_csv(f'{const.FLD_SP500_RETURNS}/{const.FILE_SP500_RETURNS}')

    # get the last available observation before the date
    returns_before_date = returns.loc[returns['Date'] <= date, 'return']
    if returns_before_date.shape[0] == 0:
        return None
    else:
        return returns_before_date.iloc[-1]


def get_accepted_date(ticker, drop_count_col=True):
    """Gets accepted date for each statement date given ticker."""
    res = pd.read_csv(os.path.join(const.FLD_STATEMENTS, f'{ticker}.csv'))[['accepted', 'date']]

    # count number of rows per date
    res['count'] = res.groupby('date')['accepted'].transform('count')

    # sort by count descending
    res = res.sort_values('count', ascending=False)

    # within each date get only the first row (i.e. the most frequent one)

    if drop_count_col:
        return res.groupby('date').first().reset_index().drop(columns=['count'])
    else:
        return res.groupby('date').first().reset_index()


def materialize_accepted_dates_DEPREC():
    """Materialize the accepted dates for all tickers.
    NOT USED - use sec_data_processing_script.py instead
    """
    # get all tickers in results
    tickers = get_available_tickers()
    acc_dates = []

    # iterate over each ticker
    for ticker in tickers:

        # get accepted dates for the ticker
        try:
            acc_dates_now = get_accepted_date(ticker)
        except FileNotFoundError:
            print(f'Error: file for {ticker} not found')
            continue

        acc_dates_now['ticker'] = ticker

        # append to the list
        acc_dates.append(acc_dates_now)

    # concatenate all results
    acc_dates = pd.concat(acc_dates)[['ticker', 'date', 'accepted']]

    # save to file
    acc_dates.to_csv(const.PATH_ACCEPTED_DATES, index=False)