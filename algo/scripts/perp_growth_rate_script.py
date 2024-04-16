"""
This script calculates the 50th percentile of the implied perpetual growth rates
It is used as the default growth rate
"""

import numpy as np
import pandas as pd
import algo.constants as const


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

# get 50th percentile per year and convert to dataframe
implied_rates_p50 = implied_rates.groupby('year')['implied_perp_g_rate'].quantile(0.5)
implied_rates_p50 = implied_rates_p50.reset_index()

# save to csv
implied_rates_p50.to_csv(const.PATH_IMPLIED_PERP_G_RATES_P50, index=False)

