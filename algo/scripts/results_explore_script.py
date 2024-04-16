import os
from importlib import reload
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import algo.data_acquisition as da
reload(da)
import algo.constants as const
reload(const)
import algo.utils as utils
import algo.modelling as model
reload(model)

results_raw = pd.read_csv(const.PATH_RESULTS_INTRINSIC_VALUES)
results = results_raw[['ticker', 'date', 'intrinsic_value', 'share_price']].copy()
results = results.replace([np.inf, -np.inf], np.nan)
results = results.dropna()
results['year'] = pd.to_datetime(results['date']).dt.year

# filter only years larger than 2019
results = results[results['year'].isin(range(2009, 2024))]

# drop outliers
max_val = 1500
results = results[results['intrinsic_value'] < max_val]
results = results[results['share_price'] < max_val]
results = results[results['intrinsic_value'] > -1000]


fig, ax = plt.subplots()

plt.xlim(-500, 1500)
plt.ylim(-500, 1500)

# scatter plot and regression line per year, one color per year
x_range = np.arange(-500, 1500)
years_plot = range(2019, 2024)

for year in years_plot:
    results_year = results[results['year'] == year]
    x = results_year['intrinsic_value']
    y = results_year['share_price']
    model = LinearRegression().fit(x.values.reshape(-1, 1), y)
    y_range = model.predict(x_range.reshape(-1, 1))
    plt.scatter(x, y, label=f'{year} || beta: {round(model.coef_[0], 2)}', alpha=0.4, linewidths=0, s=15)
    plt.plot(x_range, y_range)

# plt.plot(x_range, y_range, color='red')
plt.xlabel('Intrinsic Value')
plt.ylabel('Share Price')
plt.title('Intrinsic Value vs Share Price')
plt.grid()
plt.legend()
plt.savefig('docs/images/scatter_intrinsic_market.png', dpi=300)
plt.show()


#######

years_plot_corr = range(2009, 2024)
correlations = []

for year in years_plot_corr:
    results_year = results[results['year'] == year]
    x = results_year['intrinsic_value']
    y = results_year['share_price']

    # calculate correlation between intrinsic value and share price
    correlations.append(np.corrcoef(x, y)[0, 1])

# plot correlations over years
fig, ax = plt.subplots()
plt.plot(years_plot_corr, correlations)
plt.xlabel('Year')
plt.ylabel('Correlation')
plt.title('Correlation between Intrinsic Value and Share Price')
plt.grid()
plt.savefig('docs/images/correlation_intrinsic_market.png', dpi=300)
plt.show()




#######

# get all tickers in results
tickers = da.get_available_tickers()
acc_dates = []

acc_dates = pd.read_csv(const.PATH_ACCEPTED_DATES)

# filter:
# days_dif < 100
# days_dif >= 0
# share_price_-1d is not null
# share_price_1d is not null
acc_dates = acc_dates[(acc_dates['days_dif'] < 100) & (acc_dates['days_dif'] >= 0)]
acc_dates = acc_dates[~acc_dates['share_price_-1d'].isnull()]
acc_dates = acc_dates[~acc_dates['share_price_1d'].isnull()]

merged = acc_dates.merge(results, on=['ticker', 'date'], how='inner')

# get price 100 after
merged['share_price_100d'] = merged.apply(
    lambda x: da.get_share_price_around_date(x['ticker'], x['accepted'], direction='after', n_days=100), axis=1)

# get price 365 after
merged['share_price_365d'] = merged.apply(
    lambda x: da.get_share_price_around_date(x['ticker'], x['accepted'], direction='after', n_days=365), axis=1)

# filter only rows where intrinsic value is either larger or smaller than share price share_price_1d
higher_intrinsic = merged.loc[merged['intrinsic_value'] > merged['share_price_1d'], :].copy()
lower_intrinsic = merged.loc[merged['intrinsic_value'] < merged['share_price_1d'], :].copy()


def calculate_returns(df, days=[100, 365]):

    result = pd.DataFrame(data=None, columns=['days', 'mean_log_return', 'std_log_return'])

    # iterate over each day in days
    for day in days:

        # calculate log return between share_price_-1d and share_price_{days}d
        returns = np.log(df[f'share_price_{day}d'] / df['share_price_-1d'])

        # calculate mean and std of log returns
        mean_log_return = returns.mean()
        std_log_return = returns.std()

        # append to result as last row using .loc
        result.loc[len(result)] = [day, mean_log_return, std_log_return]

    return result

###########################

# load sp500 returns
sp500_raw = pd.read_csv(const.PATH_SP500_RETURNS)
sp500_raw['date'] = pd.to_datetime(sp500_raw['Date'])
sp500_raw['value'] = sp500_raw['Close']

# filter only years larger than 2005
sp500_returns = sp500_raw[['date', 'value']].copy()
sp500_returns = sp500_returns[sp500_returns['date'].dt.year >= 2005]

# generate returns and log returns
sp500_returns['return'] = sp500_returns['value'].pct_change()
sp500_returns['log_return'] = np.log(sp500_returns['value'] / sp500_returns['value'].shift(1))

# generate return and log return (with respect to the value at period 0)
sp500_returns['return_normalized'] = sp500_returns['value'] / sp500_returns['value'].iloc[0]
sp500_returns['value_normalized'] = sp500_returns['value'] / sp500_returns['value'].iloc[0]

# shift values by one year
sp500_returns['value_1y'] = sp500_returns['value'].shift(252)

# calculate return and log return for 1 year
sp500_returns['return_1y'] = sp500_returns['value'] / sp500_returns['value_1y']
sp500_returns['log_return_1y'] = np.log(sp500_returns['value'] / sp500_returns['value_1y'])

# get average log return for 1 year
sp500_returns['log_return_1y'].mean()

# get average yearly log return for each year, use groupby
sp500_returns['year'] = sp500_returns['date'].dt.year
sp500_returns_yearly = sp500_returns.groupby('year').agg({'log_return_1y': 'mean'}).reset_index()

#####################

returns_higher_intrinsic = calculate_returns(higher_intrinsic)
returns_lower_intrinsic = calculate_returns(lower_intrinsic)

# plt mean log return for both dataframes on the same plot using column plot
# plot columns side by side
fig, ax = plt.subplots()
bar_width = 0.35
bar_positions = np.arange(2)
plt.bar(bar_positions, returns_higher_intrinsic['mean_log_return'], bar_width, label='intrinsic value higher than market')
plt.bar(bar_positions + bar_width, returns_lower_intrinsic['mean_log_return'], bar_width, label='intrinsic value lower than market')
plt.xticks(bar_positions + bar_width / 2, returns_higher_intrinsic['days'])
plt.ylabel('Mean Log Return')
plt.xlabel('Days')
plt.title('Mean Log Return after 100 and 365 days')
# add legend to top left
plt.legend(loc='upper left')
plt.savefig('docs/images/mean_log_return_bars.png', dpi=300)
plt.show()

##############

# add year_accepted to higher_intrinsic
# add one to year_accepted to reflect that the return is calculated after the year
higher_intrinsic['year_accepted'] = pd.to_datetime(higher_intrinsic['accepted']).dt.year + 1
lower_intrinsic['year_accepted'] = pd.to_datetime(lower_intrinsic['accepted']).dt.year + 1
yearly_results_list = []
years_range = range(2009, 2025)

# iterate over each year
for year in years_range:

    # filter only data for the year from higher_intrinsic and lower_intrinsic
    hi_intrinsic_year = higher_intrinsic[higher_intrinsic['year_accepted'] == year]
    lo_intrinsic_year = lower_intrinsic[lower_intrinsic['year_accepted'] == year]

    # calculate returns for the year
    returns_year_hi = calculate_returns(hi_intrinsic_year)
    returns_year_lo = calculate_returns(lo_intrinsic_year)

    # add yar and number of observations to returns_year
    returns_year_hi['year'] = year
    returns_year_hi['n_obs'] = len(hi_intrinsic_year)
    returns_year_hi['is_higher'] = True
    returns_year_lo['year'] = year
    returns_year_lo['n_obs'] = len(lo_intrinsic_year)
    returns_year_lo['is_higher'] = False

    # append to yearly_results_list
    yearly_results_list.append(returns_year_hi)
    yearly_results_list.append(returns_year_lo)


# concatenate all dataframes in yearly_results_list
yearly_results = pd.concat(yearly_results_list)

# filter for 365 days return only and separate higher and lower intrinsic
# plot the results
# add sp500_returns_yearly to the plot
# plot from 2009 to 2023
# use whole numbers for years
yearly_results_365_higher = yearly_results.loc[(yearly_results['days'] == 365) & (yearly_results['is_higher'] == True), :]
yearly_results_365_lower = yearly_results.loc[(yearly_results['days'] == 365) & (yearly_results['is_higher'] == False), :]

fig, ax = plt.subplots()
plt.plot(yearly_results_365_higher['year'], yearly_results_365_higher['mean_log_return'],
         label='Intrinsic Value Higher', color='blue')
plt.plot(yearly_results_365_lower['year'], yearly_results_365_lower['mean_log_return'], label='Intrinsic Value Lower',
         color='orange')
plt.plot(sp500_returns_yearly['year'], sp500_returns_yearly['log_return_1y'], label='SP500', color='black', ls='--')
plt.xticks(years_range, years_range)
plt.ylabel('Mean Log Return')
plt.xlabel('Year')

plt.title('Mean Log Return after 365 days')
plt.xlim(list(years_range)[0], list(years_range)[-1])
plt.ylim(-0.15, 0.35)
plt.legend()
plt.grid()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('docs/images/yearly_mean_returns_comparison.png', dpi=300)


########

companied_dates_list = []
available_tickers = da.get_available_tickers()
# iterate over all available tickers
for idx, ticker in enumerate(available_tickers):  # [:10]):
    # ticker = available_tickers[0]  # debug
    print(ticker)

    # get all dates for the ticker
    dates = da.get_ticker_dates(ticker)
    companied_dates_list.append({'ticker': ticker, 'n_dates': len(dates)})

# convert to dataframe
n_companied_dates = pd.DataFrame(companied_dates_list)

# drop rows where there are multiple variants of the same ticker
# e.g. ticker "PCG" has variations "PCG-PA", "PCG-PB", etc.
n_companied_dates = n_companied_dates[~n_companied_dates['ticker'].str.contains('-')]

# get total number of dates
n_companied_dates['n_dates'].sum()

#########
# AVERAGE PERPETUITY GROWTH RATE IN EACH YEAR

# load implied perpetual growth rates
implied_perp_g_rates = pd.read_csv(const.PATH_IMPLIED_PERP_G_RATES)

# add year column
implied_perp_g_rates['year'] = pd.to_datetime(implied_perp_g_rates['date']).dt.year

# filter only years larger than 2009
implied_perp_g_rates = implied_perp_g_rates[implied_perp_g_rates['year'].isin(range(2009, 2024))]

# calculate 75th percentile for each year
implied_rates_p75 = implied_perp_g_rates.groupby('year')['implied_perp_g_rate'].quantile(0.75)
implied_rates_p50 = implied_perp_g_rates.groupby('year')['implied_perp_g_rate'].quantile(0.50)
implied_rates_p25 = implied_perp_g_rates.groupby('year')['implied_perp_g_rate'].quantile(0.25)

# plot all three percentiles on the same plot
fig, ax = plt.subplots()
# plt.plot(implied_rates_p75, label='75th percentile', color='blue')
plt.plot(implied_rates_p50, label='50th percentile', color='orange')
# plt.plot(implied_rates_p25, label='25th percentile', color='red')
plt.xlabel('Year')
plt.ylabel('Implied Perpetuity Growth Rate')
plt.title('Median Implied Perpetuity Growth Rate')
plt.legend()
plt.grid()
plt.savefig('docs/images/implied_perp_growth_rate.png', dpi=300)
plt.show()

# share of growth rates higher than C
C = 0.5
implied_perp_g_rates[implied_perp_g_rates['implied_perp_g_rate'] > C].shape[0] / implied_perp_g_rates.shape[0]