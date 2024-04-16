import os

SEC_USER_AGENT = 'muj_email@gmail.com'
SEC_HEADERS = {'User-Agent': SEC_USER_AGENT}

REQUESTS_HEADERS = {'User-agent': 'Mozilla/5.0'}
YFINANCE_HEADERS = {'User-agent': 'Mozilla/5.0'}

YEARS = list(range(2009, 2024))
# YEARS = list(range(2020, 2023))
QUARTERS = ['q1', 'q2', 'q3', 'q4']
YEARS_QUARTERS = [f'{year}{quarter}' for year in YEARS for quarter in QUARTERS]

N_MIN_STATEMENT_RECORDS = 100

# assumptions
PERP_GROWTH_RATE = 0.04
GROWTH_RATE = 0.1

FETCH_MIN_YEAR = 2008

# folders
FLD_STATEMENTS_RAW = 'data/sec_statements_raw'
FLD_STATEMENTS_PROCES = 'data/sec_statements_proces'
FLD_STATEMENTS = 'data/sec_statements'

FLD_RESULTS_INTRINSIC_VALUES = 'data/results/intrinsic_values'
FILE_RESULTS_INTRINSIC_VALUES = 'intrinsic_values.csv'
PATH_RESULTS_INTRINSIC_VALUES = os.path.join(FLD_RESULTS_INTRINSIC_VALUES, FILE_RESULTS_INTRINSIC_VALUES)

FLD_IMPLIED_PERP_G_RATES = 'data/results/implied_perp_growth_rates'
FILE_IMPLIED_PERP_G_RATES = 'implied_perp_growth_rates.csv'
PATH_IMPLIED_PERP_G_RATES = os.path.join(FLD_IMPLIED_PERP_G_RATES, FILE_IMPLIED_PERP_G_RATES)
FILE_IMPLIED_PERP_G_RATES_P50 = 'implied_perp_growth_rates_p50.csv'
PATH_IMPLIED_PERP_G_RATES_P50 = os.path.join(FLD_IMPLIED_PERP_G_RATES, FILE_IMPLIED_PERP_G_RATES_P50)

FLD_SHARE_PRICES = 'data/share_prices'
FILE_SHARE_PRICES = 'share_prices.csv'

FLD_BETAS = 'data/betas'
FILE_BETAS = 'betas.csv'

FLD_SHARES_OUTSTANDING = 'data/shares_outstanding'
FILE_SHARES_OUTSTANDING = 'shares_outstanding.csv'

FLD_SP500_RETURNS = 'data/sp500_returns'
FILE_SP500_RETURNS = 'sp500_returns.csv'
PATH_SP500_RETURNS = os.path.join(FLD_SP500_RETURNS, FILE_SP500_RETURNS)

FLD_TNOTES = 'data/tnotes'
FILE_TNOTES = 'tnotes.csv'

FLD_ERP = 'data/equity_risk_premium'
FILE_ERP = 'equity_risk_premium.csv'
PATH_ERP = os.path.join(FLD_ERP, FILE_ERP)

FLD_ACCEPTED_DATES = 'data/accepted_dates'
FILE_ACCEPTED_DATES = 'accepted_dates.csv'
PATH_ACCEPTED_DATES = os.path.join(FLD_ACCEPTED_DATES, FILE_ACCEPTED_DATES)



