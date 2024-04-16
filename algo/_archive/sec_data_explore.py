"""
Purpose of this script is to process SEC data for a given year.
Run this script separately to create .csv files with processed data into the 'data/sec_statements' folder.
"""
import pandas as pd
import algo.data_acquisition as da
import algo.utils as utils
from algo.constants import FLD_STATEMENTS, FLD_STATEMENTS_RAW
import os

fld_statements = utils.maybe_make_dir(FLD_STATEMENTS)
years = list(range(2020, 2024))
year = 2022

# process data for each year separately
year_folders = [str(year) + q for q in ['q1', 'q2', 'q3', 'q4']]

# get sp500 with their cik numbers
sp500_list = da.get_sp500_list()
sec_companies = da.get_sec_companies(keep_cik_num=True)
sp500_companies = sec_companies.loc[sec_companies['ticker'].isin(sp500_list['ticker']), :]
sp500_companies.loc[sp500_companies['ticker'] == 'ZTS', 'cik_num']

cik_now = 1018724
cik_now = 1555280

# get sub data for all quarters
year = 2023
year_folders = [str(year) + q for q in ['q1', 'q2', 'q3', 'q4']]
sub_list = []
for q in year_folders:
    sub_read_iter = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, q, 'sub.txt'), sep='\t', iterator=True, chunksize=1000)
    sub_list.append(pd.concat([chunk[chunk['cik'] == cik_now] for chunk in sub_read_iter]))



# filter sp500 companies only
sub = pd.concat(sub_list)
sub_filt = sub[sub['form'] == '10-K']
sp500_adsh = sub_filt.merge(sp500_companies, left_on='cik', right_on='cik_num', how='inner').adsh.drop_duplicates()

# get and filter num data for all quarters

year = 2023
year_folders = [str(year) + q for q in ['q1', 'q2', 'q3', 'q4']]
num_list = []
for q in year_folders:
    print(q)
    num_read_iter = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, q, 'num.txt'), sep='\t', iterator=True, chunksize=100000)

    # num0 = pd.read_table(os.path.join(FLD_STATEMENTS_RAW, q, 'num.txt'), sep='\t')
    # num0.loc[num0['adsh'].isin(sp500_adsh)]

    num_list.append(pd.concat([chunk[chunk['adsh'].isin(sp500_adsh)] for chunk in num_read_iter]))

# postprocess num data
num = pd.concat(num_list).sort_values(['adsh', 'tag'])
num['date'] = pd.to_datetime(num['ddate'], format='%Y%m%d')
num = num.loc[num['date'].dt.year == year, :]
num = (num
       .merge(sub[['adsh', 'cik']], on='adsh', how='inner')
       .merge(sec_companies[['cik_num', 'ticker']], left_on='cik', right_on='cik_num', how='inner'))

# save
cols_save = {
    'adsh': 'adsh',
    'date': 'date',
    'ticker': 'ticker',
    'cik': 'cik',
    'tag': 'concept',
    'value': 'val'
}
num = num.rename(columns=cols_save).loc[:, list(cols_save.values())]
num.to_csv(os.path.join(fld_statements, f'y{year}.csv'), index=False)
