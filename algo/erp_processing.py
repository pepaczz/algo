import pandas as pd
import algo.constants as const
import os

# load erp data from excel file
erp_yearly = pd.read_excel('data/equity_risk_premium/equity_risk_premium.xlsx')

# add date column, using the last day of the Year column
erp_yearly['date'] = erp_yearly['Year'].apply(lambda x: pd.Timestamp(f'{x}-12-31'))

# create dataframe of dates from 2005 to today
dates = pd.DataFrame({'date': pd.date_range(start='2005-12-31', end=pd.Timestamp.now(), freq='D')})

# join erp on dates
erp = dates.merge(erp_yearly, on='date', how='left')

# for each column interpolate missing values using spline
cols = erp.columns.drop('date')
for column in cols:
    erp[column] = erp[column].interpolate(method='polynomial', order=3)
    erp[column] = erp[column].ffill().bfill()

# plot "Implied ERP (FCFE)" and "Implied Premium (DDM)" over time from 2020 to today
# add scatter plot with original data points (end of year)
import matplotlib.pyplot as plt
plt.plot(erp['date'], erp['Implied ERP (FCFE)'], label='Implied ERP (FCFE)')
plt.plot(erp['date'], erp['Implied Premium (DDM)'], label='Implied Premium (DDM)')
plt.scatter(erp_yearly['date'], erp_yearly['Implied ERP (FCFE)'], color='blue')
plt.scatter(erp_yearly['date'], erp_yearly['Implied Premium (DDM)'], color='red')
plt.legend()
plt.show()

# create dictionary with new column names for renaming
rename_dict = {
    'date': 'date',
    'Implied ERP (FCFE)': 'erp_fcfe',
    'Implied Premium (DDM)': 'erp_ddm',
    'Implied Premium (FCFE with sustainable Payout)': 'erp_fcfe_sustainable_payout',
    'Analyst Growth Estimate': 'analyst_growth_estimate'
}

# create new dataframe with renamed columns
erp_save = erp.rename(columns=rename_dict)

# save erp data to csv file
erp_save.to_csv(os.path.join(const.FLD_ERP, const.FILE_ERP), index=False)