"""
Purpose of this script is to process SEC data for a given year.
Steps:
1. Download and extract the data from the SEC website https://www.sec.gov/dera/data/financial-statement-data-sets.
2. Move the extracted data to the 'data/sec_statements_raw' folder.
3. Run this script to create .csv files with processed data into the 'data/sec_statements' folder.
"""
import glob
import pandas as pd
import algo.data_acquisition as da
import algo.utils as utils
from algo.constants import FLD_STATEMENTS, FLD_STATEMENTS_RAW, YEARS_QUARTERS, FLD_STATEMENTS_PROCES
import algo.constants as const
import algo.fetched_data as fd
import os

# get sp500 with their cik numbers
sp500_list = da.get_sp500_list()


sec_companies = fd.fetch_sec_companies(keep_cik_num=True)
# sec_companies = da.get_sec_companies(keep_cik_num=True)
sp500_companies = sec_companies.loc[sec_companies['ticker'].isin(sp500_list['ticker']), :]
cik_sp500 = sp500_companies['cik_num'].values

# PART 1
# data extraction from SEC raw data
# yq='2010q2'   # debug

for idx, yq in enumerate(YEARS_QUARTERS):
    print(f'processing year/quarter {yq} out of {len(YEARS_QUARTERS)}')

    # get relevant adsh identifiers (10K forms only for sp500 companies)
    sub_read_iter = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, yq, 'sub.txt'), sep='\t',
                                  iterator=True, chunksize=1000)
    sub_sp500 = pd.concat([chunk[(chunk['form'] == '10-K') &
                                 (chunk['cik'].isin(cik_sp500))] for chunk in sub_read_iter])
    adsh_sp500 = sub_sp500.adsh.drop_duplicates()

    # fetch data with values
    num_read_iter = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, yq, 'num.txt'), sep='\t',
                                  iterator=True, chunksize=1000000, low_memory=False)
    num = pd.concat([chunk[chunk['adsh'].isin(adsh_sp500)] for chunk in num_read_iter])

    # postprocess num data
    num['date'] = pd.to_datetime(num['ddate'], format='%Y%m%d')
    num['source_yq'] = yq
    num = (num
           .merge(sub_sp500[['adsh', 'cik', 'accepted']], on='adsh', how='inner')
           .merge(sec_companies[['cik_num', 'ticker']], left_on='cik', right_on='cik_num', how='inner'))

    # save
    cols_save = {
        'adsh': 'adsh',
        'date': 'date',
        'accepted': 'accepted',
        'ticker': 'ticker',
        'cik': 'cik',
        'tag': 'concept',
        'source_yq': 'source_yq',
        'value': 'val'
    }
    num_save = num.rename(columns=cols_save).loc[:, list(cols_save.values())]

    # convert datetime columns to date
    # num_save['date'] = num_save['date'].dt.date
    # num_save['accepted'] = num_save['accepted'].dt.date

    # iterate over each ticker and save
    for ticker in num['ticker'].unique():
        fld_save = utils.maybe_make_dir(os.path.join(FLD_STATEMENTS_PROCES, ticker))
        num_save_ticker = num_save.loc[num_save['ticker'] == ticker, :]
        num_save_ticker.to_csv(os.path.join(fld_save, f'{yq}.csv'), index=False)

# PART 2
# data cleaning and filtering

# get list of all tickers in FLD_STATEMENTS_PROCES folder
tickers = [f for f in os.listdir(FLD_STATEMENTS_PROCES) if os.path.isdir(os.path.join(FLD_STATEMENTS_PROCES, f))]
utils.maybe_make_dir(FLD_STATEMENTS)

# ticker='MSFT'  # debug
for idx, ticker in enumerate(tickers):

    # print progress every nth iteration
    if idx % 100 == 0:
        print(f'processing ticker {idx} out of {len(tickers)}')

    # load and concatenate all files for a given ticker
    all_files = glob.glob(os.path.join(FLD_STATEMENTS_PROCES, ticker, "*.csv"))
    df_raw = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True) \
        .sort_values(['ticker', 'date', 'concept', 'source_yq'], ascending=False)
    df_raw['date'] = pd.to_datetime(df_raw['date'], format='%Y-%m-%d')

    # filter only the last observation for each date
    df_raw['row_number_date'] = df_raw.groupby(['ticker', 'date', 'concept']).cumcount(ascending=False) + 1
    df_filt1 = df_raw.loc[df_raw['row_number_date'] == 1, :]

    # get number of observations for each ticker and date
    # filter only those with more than N_MIN_STATEMENT_RECORDS (i.e. we assume that fin.statements are complete)
    df_n_obs = df_filt1.loc[:, ['ticker', 'date']].copy()
    df_n_obs['n_obs'] = 1
    df_n_obs = df_n_obs.groupby(['ticker', 'date']).count().reset_index(drop=False)
    df_n_obs_min = df_n_obs.copy().loc[df_n_obs['n_obs'] > const.N_MIN_STATEMENT_RECORDS, :]

    # filter only the last observation for each year
    df_n_obs_min['year'] = df_n_obs_min['date'].dt.year
    df_n_obs_min['row_number_year'] = df_n_obs_min.groupby(['ticker', 'year']).cumcount(ascending=False) + 1
    df_n_obs_min2 = df_n_obs_min.loc[df_n_obs_min['row_number_year'] == 1, :]
    df_filt2 = df_filt1.merge(df_n_obs_min2[['ticker', 'date']], on=['ticker', 'date'], how='inner')
    df_filt2 = df_filt2.drop(columns=['row_number_date'])

    # write to csv
    df_filt2.to_csv(f'{FLD_STATEMENTS}/{ticker}.csv', index=False)

############################
# ACCEPTED DATE PROCESSING

# get sp500 with their cik numbers
sp500_list = da.get_sp500_list()
sec_companies = fd.fetch_sec_companies(keep_cik_num=True)
# sec_companies = da.get_sec_companies(keep_cik_num=True)
sp500_companies = sec_companies.loc[sec_companies['ticker'].isin(sp500_list['ticker']), :]

accepted_dates_list = []
usecols = ['adsh', 'cik', 'form', 'period', 'accepted']

for idx, yq in enumerate(YEARS_QUARTERS):
    print(f'processing year/quarter {yq} out of {len(YEARS_QUARTERS)}')

    # get relevant adsh identifiers (10K forms only for sp500 companies)
    data_now_iter = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, yq, 'sub.txt'), sep='\t',
                                  iterator=True, chunksize=1000, usecols=usecols)
    data_now = pd.concat([chunk[(chunk['form'] == '10-K') &
                                 (chunk['cik'].isin(cik_sp500))] for chunk in data_now_iter])
    data_now['date'] = pd.to_datetime(data_now['period'].astype(int), format='%Y%m%d')

    if data_now.shape[0] > 0:
        accepted_dates_list.append(data_now.merge(sec_companies[['cik_num', 'ticker']], left_on='cik', right_on='cik_num', how='inner'))

accepted_dates = pd.concat(accepted_dates_list)

# group by ticker and date and get the first accepted date
accepted_dates_min = accepted_dates.groupby(['ticker', 'date']).agg({'accepted': 'min'}).reset_index(drop=False)

# convert accepted date to datetime
accepted_dates_min['accepted'] = pd.to_datetime(accepted_dates_min['accepted'])

# map da.get_share_price_around_date on each row of accepted_dates_min
accepted_dates_min['share_price_-1d'] = accepted_dates_min.apply(
    lambda x: da.get_share_price_around_date(x['ticker'], x['accepted'], direction='before', n_days=1), axis=1)

# map da.get_share_price_around_date on each row of accepted_dates_min
accepted_dates_min['share_price_1d'] = accepted_dates_min.apply(
    lambda x: da.get_share_price_around_date(x['ticker'], x['accepted'], direction='after', n_days=1), axis=1)

accepted_dates_min['days_dif'] = (pd.to_datetime(accepted_dates_min['accepted']) - pd.to_datetime(accepted_dates_min['date'])).dt.days

accepted_dates_min.to_csv(const.PATH_ACCEPTED_DATES, index=False)




