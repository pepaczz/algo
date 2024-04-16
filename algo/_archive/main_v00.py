# taylo rule: https://www.kaggle.com/code/aradhanasaha/taylor-s-rule
import numpy_financial as npf

import algo.data_acquisition as da
from importlib import reload
reload(da)

from algo.utils import if_none
import pandas as pd
import algo.constants as const
reload(const)


headers = {'User-Agent': const.SEC_USER_AGENT}

sp500_list = da.get_sp500_list()
sec_companies = da.get_sec_companies()

# filter only companies in S&P 500
sp500_ciks = sec_companies.loc[sec_companies['ticker'].isin(sp500_list['ticker']), 'cik_str'].to_list()

# for cik in sp500_ciks:
#     print(cik)
#
#     cík = '0001717307'
#     concept = 'OperatingIncomeLoss'
#
#     concept_response = requests.get(f'https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{concept}.json',
#                                   headers=headers)
#
#     # get all filings data
#     df = pd.DataFrame.from_dict(concept_response.json()['units']['USD'])
#     # filtered = df[df.form == '10-Q']
#     filtered = filtered.reset_index(drop=True).sort_values(['end', 'start'])
#     # filtered.loc[filtered['end']=='2011-09-30' ,['start', 'end', 'val', 'fy']]

#####

concept = 'OperatingIncomeLoss'
concept = 'InterestExpense'

concept = 'LongTermDebtNoncurrent'
concept = 'msft_AcquisitionsNetOfCashAcquiredAndPurchasesOfIntangibleAndOtherAssets'
concept = 'ShareBasedCompensation'
concept = 'NetCashProvidedByUsedInOperatingActivities'

da.get_concept_by_ticker('MSFT', concept)
da.get_concept_by_ticker('AMZN', concept)
da.get_concept_by_ticker('SNOW', concept)
da.get_concept_by_ticker('UBX', concept)
da.get_concept_by_ticker('ILPT', concept)
da.get_concept_by_ticker('MGNX', concept)
da.get_concept_by_ticker('UBER', concept)

###############################

concept_pretax_income1 = 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments'
concept_pretax_income2 = 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'


# date = '2023-06-30'
# extract year from date
# ticker = 'MSFT'
# ticker = 'SNOW'
ticker = 'MMM'
ticker = 'NVDA'
dates_10k = da.get_10k_dates(ticker)
dates_10k
date = dates_10k.iloc[-1]['end']
date = '2016-12-31'
year = pd.to_datetime(date).year

interest_expense = da.get_single_observation(ticker, concept='InterestExpense', year=year)
income_tax = da.get_single_observation(ticker, concept='IncomeTaxExpenseBenefit', year=year)
pretax_income1 = da.get_single_observation(ticker, concept=concept_pretax_income1, year=year)
pretax_income2 = da.get_single_observation(ticker, concept=concept_pretax_income2, year=year)
pretax_income = pretax_income1 if pretax_income1 is not None else pretax_income2
long_term_debt = da.get_single_observation(ticker, concept='LongTermDebtNoncurrent', year=year)
long_term_lease = da.get_single_observation(ticker, concept='CapitalLeaseObligationsNoncurrent', year=year)
total_long_term_debt = if_none(long_term_debt, 0) + if_none(long_term_lease, 0)

cost_of_debt = interest_expense / total_long_term_debt
effective_tax_rate = income_tax / pretax_income
cost_of_debt_after_tax = cost_of_debt * (1 - effective_tax_rate)

risk_free_rate = da.get_rf_rate_at_date(date)
beta = da.get_beta(ticker)
cost_of_equity = risk_free_rate + (beta * (const.MKT_RETURN - risk_free_rate))

share_price = da.get_share_price(ticker, date)

com_shares_outstanding = da.get_single_observation_non_usd(ticker, concept='CommonStockSharesOutstanding', year=year)
pref_shares_outstanding = da.get_single_observation_non_usd(ticker, concept='PreferredStockSharesOutstanding', year=year)
shares_outstanding = int(com_shares_outstanding) + (0 if pref_shares_outstanding is None else pref_shares_outstanding)

market_cap = share_price * shares_outstanding
total = total_long_term_debt + market_cap

# Calculate the weight of debt and equity
weight_of_debt = total_long_term_debt / total
weight_of_equity = market_cap / total

wacc_rate = (weight_of_debt * cost_of_debt_after_tax) + (weight_of_equity * cost_of_equity)

##########################
# FCFF - Free cash flow to firm

operating_income = da.get_single_observation(ticker, 'OperatingIncomeLoss', year=year)
after_taxt_operating_income = operating_income * (1 - effective_tax_rate)

net_cash_operating = da.get_single_observation(ticker, 'NetCashProvidedByUsedInOperatingActivities', year=year)
net_income = da.get_single_observation(ticker, 'NetIncomeLoss', year=year)
share_based_compensation = da.get_single_observation(ticker, 'ShareBasedCompensation', year=year)

reinvestment_operations_part = net_cash_operating - net_income - share_based_compensation
capex = da.get_single_observation(ticker, 'PaymentsToAcquirePropertyPlantAndEquipment', year=year)
# msft_cash_acquisitions = None  # 8099000000  # this expression is subtracted from reinvestment in Damodaran

reinvestment = reinvestment_operations_part - if_none(capex, 0)
fcff = after_taxt_operating_income + reinvestment

###########################

growth_rate = da.get_growth_estimate(ticker)
fcff_projection = [fcff * (1 + growth_rate) ** i for i in range(1, 6)]
terminal_value = fcff_projection[-1] * (1 + const.PERP_GROWTH_RATE)/(wacc_rate - const.PERP_GROWTH_RATE)
fcff_projection[-1] = fcff_projection[-1] + terminal_value
enterprise_value = npf.npv(wacc_rate, [0] + fcff_projection)

##########################

cash_and_equivalents = da.get_single_observation(ticker, 'CashAndCashEquivalentsAtCarryingValue', year)
current_debt = da.get_single_observation(ticker, 'CurrentDebt', year)

equity_value = enterprise_value + if_none(cash_and_equivalents, 0) - (if_none(current_debt, 0) + total_long_term_debt)

intrinsic_value = equity_value / shares_outstanding
intrinsic_value
