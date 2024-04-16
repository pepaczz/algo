import numpy as np
import pandas as pd
import algo.constants as const
import matplotlib.pyplot as plt
import seaborn as sns

# load growth rate results
implied_rates = pd.read_csv(const.PATH_IMPLIED_PERP_G_RATES)

# take only after 2020
# implied_rates = implied_rates[implied_rates['date'] >= '2020-01-01']

# drop values larger than 1
implied_rates = implied_rates[implied_rates['implied_perp_g_rate'] < 1]

# add year column
implied_rates['year'] = pd.to_datetime(implied_rates['date']).dt.year

# get number of records per year
implied_rates.groupby('year').size()

# get 75th percentile
implied_rates_p75 = implied_rates.groupby('year')['implied_perp_g_rate'].quantile(0.75)
implied_rates_p75

# TODO: some issue with memory??? Why?
# data2 = implied_rates[['implied_perp_g_rate', 'year']].copy()
# # plot histogram of implied growth rates
# # use color to show year
# plt.figure(figsize=(10, 6))
# sns.histplot(data=data2, x='implied_perp_g_rate')  #, hue='year', common_norm=False, kde=True)
# # sns.histplot(data=implied_rates, x='implied_perp_g_rate', hue='year', common_norm=False, kde=True)
# plt.xlabel('Implied perpetual growth rate')
# plt.ylabel('Number of records')
# plt.title('Implied perpetual growth rate distribution')
# plt.show()

# get 50th percentile per year and convert to dataframe
implied_rates_p50 = implied_rates.groupby('year')['implied_perp_g_rate'].quantile(0.5)
implied_rates_p50 = implied_rates_p50.reset_index()

# save to csv
implied_rates_p50.to_csv(const.PATH_IMPLIED_PERP_G_RATES_P50, index=False)

