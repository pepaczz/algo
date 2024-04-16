"""
This module contains functions to calculate the intrinsic value of a company using the free cash flow to firm method.
"""


import numpy as np
import numpy_financial as npf
import algo.data_acquisition as da
from algo.utils import if_none, elu, if_nan_none
import algo.constants as const
import algo.fetched_data as fd
import algo.utils as utils
import pandas as pd
from scipy.optimize import minimize_scalar, minimize


def get_intrinsic_value(ticker, date, optimize_perp_g_rate=False):
    """Calculate the intrinsic value of a company using the free cash flow to firm method."""

    year = pd.to_datetime(date).year

    interest_expense1 = da.get_single_observation(ticker, concept='InterestExpense', year=year)
    interest_expense2 = da.get_single_observation(ticker, concept='InterestIncomeExpenseNonoperatingNet', year=year)
    interest_expense = interest_expense1 if interest_expense1 is not None else interest_expense2

    income_tax = da.get_single_observation(ticker, concept='IncomeTaxExpenseBenefit', year=year)

    concept_pretax_income1 = ('IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinority' +
                              'InterestAndIncomeLossFromEquityMethodInvestments')
    pretax_income1 = da.get_single_observation(ticker, concept=concept_pretax_income1, year=year)

    concept_pretax_income2 = ('IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinary' +
                              'ItemsNoncontrollingInterest')
    pretax_income2 = da.get_single_observation(ticker, concept=concept_pretax_income2, year=year)
    pretax_income = pretax_income1 if pretax_income1 is not None else pretax_income2
    long_term_debt = da.get_single_observation(ticker, concept='LongTermDebtNoncurrent', year=year)
    long_term_lease = da.get_single_observation(ticker, concept='CapitalLeaseObligationsNoncurrent', year=year)
    total_long_term_debt = if_none(long_term_debt, 0) + if_none(long_term_lease, 0)
    effective_tax_rate = income_tax / pretax_income

    if total_long_term_debt > 0:
        cost_of_debt = interest_expense / total_long_term_debt
        cost_of_debt_after_tax = cost_of_debt * (1 - effective_tax_rate)
    else:
        cost_of_debt_after_tax = 0

    beta = da.get_beta(ticker)
    if beta is None:
        return 'Error: missing beta', None

    erp = fd.get_erp_at_date(date)

    risk_free_rate = fd.get_rf_rate_at_date(date)
    cost_of_equity = risk_free_rate + (beta * erp)

    share_price = da.get_share_price(ticker, date)

    com_shares_outstanding = da.get_single_observation(ticker, concept='CommonStockSharesOutstanding', year=year)
    pref_shares_outstanding = da.get_single_observation(ticker, concept='PreferredStockSharesOutstanding', year=year)
    shares_outstanding = if_nan_none(com_shares_outstanding, 0) + if_nan_none(pref_shares_outstanding, 0)

    # only work with companies that have shares outstanding and share price
    if (share_price is None) or np.isnan(share_price):
        return 'Error: missing share price', None
    if shares_outstanding == 0:
        return 'Error: shares outstanding are zero or missing', None

    market_cap = share_price * shares_outstanding
    total = total_long_term_debt + market_cap

    # Calculate the weight of debt and equity
    weight_of_debt = total_long_term_debt / total
    weight_of_equity = market_cap / total

    wacc_rate = (weight_of_debt * cost_of_debt_after_tax) + (weight_of_equity * cost_of_equity)

    ##########################
    # FCFF - Free cash flow to firm

    operating_income = da.get_single_observation(ticker, 'OperatingIncomeLoss', year=year)

    # only work with companies that have shares outstanding
    if operating_income is None:
        return 'Error: missing operating income', None

    after_taxt_operating_income = operating_income * (1 - effective_tax_rate)

    concept_net_cash_operating1 = 'NetCashProvidedByUsedInOperatingActivities'
    concept_net_cash_operating2 = 'NetCashProvidedByUsedInOperatingActivitiesContinuingOperations'
    net_cash_operating1 = da.get_single_observation(ticker, concept_net_cash_operating1, year=year)
    net_cash_operating2 = da.get_single_observation(ticker, concept_net_cash_operating2, year=year)
    net_cash_operating = net_cash_operating1 if net_cash_operating1 is not None else net_cash_operating2


    net_income1 = da.get_single_observation(ticker, 'NetIncomeLoss', year=year)
    net_income2 = da.get_single_observation(ticker, 'ProfitLoss', year=year)
    net_income = net_income1 if net_income1 is not None else net_income2
    share_based_compensation = da.get_single_observation(ticker, 'ShareBasedCompensation', year=year)

    reinvestment_operations_part = net_cash_operating - net_income - if_none(share_based_compensation, 0)
    capex = da.get_single_observation(ticker, 'PaymentsToAcquirePropertyPlantAndEquipment', year=year)
    # msft_cash_acquisitions = None  # 8099000000  # this expression is subtracted from reinvestment in Damodaran

    reinvestment = reinvestment_operations_part - if_none(capex, 0)
    fcff = after_taxt_operating_income + reinvestment

    ###########################

    growth_rate = fd.get_growth_rate_at_date(date)

    fcff_projection = [fcff * (1 + growth_rate) ** i for i in range(1, 6)]

    cash_and_equivalents = da.get_single_observation(ticker, 'CashAndCashEquivalentsAtCarryingValue', year)
    current_debt = da.get_single_observation(ticker, 'CurrentDebt', year)
    equity_val_residual = if_none(cash_and_equivalents, 0) - (if_none(current_debt, 0) + if_none(total_long_term_debt, 0))

    if optimize_perp_g_rate:

        optimization_res = minimize_scalar(perp_gr_optimization_wrapper, method='brent',
                                           args=(fcff_projection.copy(), wacc_rate, equity_val_residual,
                                                 shares_outstanding, share_price))

        implied_perp_growth_rate = optimization_res.x

        intrinsic_value = calc_multiplier_to_intrinsic_value(implied_perp_growth_rate, fcff_projection.copy(),
                                                             wacc_rate, equity_val_residual, shares_outstanding)

        return intrinsic_value, implied_perp_growth_rate

    else:
        implied_perp_growth_rate = get_perp_growth_rate(ticker, date, create_lag=True)

        intrinsic_value = calc_multiplier_to_intrinsic_value(implied_perp_growth_rate, fcff_projection.copy(),
                                                             wacc_rate, equity_val_residual, shares_outstanding)

        return intrinsic_value, None


# end of year
date='2020-12-31'

def get_perp_growth_rate(ticker, date, create_lag):
    """Get the last available perpetuity growth rate or return the default value."""
    # load perp_g_rates
    implied_perp_g_rates = fd.implied_perp_g_rates

    # lag the date value by one year
    if create_lag:
        date = pd.to_datetime(date) - pd.DateOffset(years=1)

    # filter data for given ticker and date
    before_date = implied_perp_g_rates.loc[(implied_perp_g_rates['ticker'] == ticker) &
                                                    (implied_perp_g_rates['date'] <= date), 'implied_perp_g_rate']

    # get the last available perp growth rate or return the default value
    if before_date.shape[0] == 0:
        # load imputation percentile value and filter for specified year
        percentile_value = fd.implied_perp_g_rates_p50
        percentile_value = percentile_value[percentile_value['year'] == pd.to_datetime(date).year]
        if percentile_value.shape[0] == 0:
            return fd.mean_implied_perp_g_rates_p50
        else:
            return percentile_value['implied_perp_g_rate'].iloc[0]
    else:
        return before_date.iloc[-1]


def calc_multiplier_to_intrinsic_value(perp_growth_rate, fcff_projection, wacc_rate,
                                       equity_val_residual, shares_outstanding):
    # calculate terminal value
    fcff_projection = fcff_projection.copy()
    multiplier = (1 + perp_growth_rate) / (wacc_rate - perp_growth_rate)
    terminal_value = fcff_projection[-1] * multiplier
    fcff_projection[-1] = fcff_projection[-1] + terminal_value

    # calculate enterprise_value, equity_value and intrinsic value
    enterprise_value = npf.npv(wacc_rate, [0] + fcff_projection)
    equity_value = enterprise_value + equity_val_residual
    return equity_value / shares_outstanding


def perp_gr_optimization_wrapper(perp_growth_rate, fcff_projection, wacc_rate,
                                 equity_val_residual, shares_outstanding, share_price):
    # optimize the perp_growth_rate
    intrinsic_value = calc_multiplier_to_intrinsic_value(perp_growth_rate, fcff_projection, wacc_rate,
                                       equity_val_residual, shares_outstanding)

    return abs(share_price - intrinsic_value)


def get_intrinsic_value_wrapper(ticker, date, results):
    """Get intrinsic value and share price and append to results dataframe. Print results."""
    # get share price
    share_price = da.get_share_price(ticker, date)

    # tries to get intrinsic value, if it fails, it returns an error message
    try:
        intrinsic_value, _ = get_intrinsic_value(ticker, date, optimize_perp_g_rate=False)

        # case: explicitly defined error message in get_intrinsic_value
        if isinstance(intrinsic_value, str):
            error_message = intrinsic_value
            intrinsic_value = np.nan
            print(f'{ticker} || {date} || {error_message}')
        # case: intrinsic value is a number
        else:
            error_message = ''
            print(
                f'{ticker} || {date} || intrinsic: {round(intrinsic_value, 1)} || market: {round(share_price, 1)}')

    # case: get_intrinsic_value returns a TypeError
    except TypeError:  # ValueError:  # TypeError:
        error_message = utils.get_assignment_part_error_message()
        intrinsic_value = np.nan
        print(f'{ticker} || {date} ||  {error_message}')

    # append results
    results.loc[len(results)] = [ticker, date, intrinsic_value, share_price, error_message]

    return results


def get_optimized_perp_g_rate(ticker, date, results):
    """Get intrinsic value and share price and append to results dataframe. Print results."""
    # get share price
    share_price = da.get_share_price(ticker, date)

    # tries to get intrinsic value, if it fails, it returns an error message
    try:
        intrinsic_value, perp_g_rate = get_intrinsic_value(ticker, date, optimize_perp_g_rate=True)

        # case: explicitly defined error message in get_intrinsic_value
        if isinstance(perp_g_rate, float):
            share_price = da.get_share_price(ticker, date)
            print(f'{ticker} || {date} || perp_g_rate: {round(perp_g_rate, 3)}')
            results.loc[len(results)] = [ticker, date, perp_g_rate]
    # case: get_intrinsic_value returns a TypeError
    except TypeError:
        pass

    return results