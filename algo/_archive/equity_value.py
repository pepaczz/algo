import yahoo_fin.stock_info as si
import numpy_financial as npf
import yfinance as yf
import algo.data_acquisition as da

PROJECTION_YEARS = 5
PERP_GROWTH_RATE = 0.025
WACC_RATE = 0.094


def get_equity_value(ticker):
    ticker_yf = yf.Ticker(ticker)

    # free cash flow
    cash_flow = ticker_yf.cash_flow
    balance_sheet = ticker_yf.balance_sheet

    # get growth rate
    growth_est_df = da.get_analysts_info(ticker)['Growth Estimates']
    growth_str = growth_est_df[growth_est_df['Growth Estimates'] == 'Next 5 Years (per annum)'][ticker].iloc[0]
    growth_rate = round(float(growth_str.rstrip('%')) / 100.0, 4)

    # free cash flow
    free_cash_flow = cash_flow.loc['Free Cash Flow'].iloc[0]

    ffcf = []
    # Year 1
    ffcf.append(free_cash_flow * (1 + growth_rate))

    # Starting from year 2
    for i in range(1, PROJECTION_YEARS):
        ffcf.append(ffcf[i - 1] * (1 + growth_rate))

    # forecast_fcf[-1] refers to the last year in the growth period
    terminal_value = ffcf[-1] * (1 + PERP_GROWTH_RATE) / (WACC_RATE - PERP_GROWTH_RATE)

    # add the terminal value to the last year
    ffcf[-1] = ffcf[-1] + terminal_value

    # calculate dcf using npv - add zero or else the method assumes
    # first value as the initial investment
    enterprise_value = npf.npv(WACC_RATE, [0] + ffcf)

    # calculate Cash And Cash Equivalents
    cash_and_equivalents = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]

    # get current debt
    if 'Current Debt' in balance_sheet.index:
        current_debt = balance_sheet.loc['Current Debt'].iloc[0]
    elif 'Current Debt And Capital Lease Obligation' in balance_sheet.index:
        current_debt = balance_sheet.loc['Current Debt And Capital Lease Obligation'].iloc[0]
    else:
        return {'error': 'Current Debt not found'}

    # long term debt - only interested in the value
    long_term_debt = balance_sheet.loc['Long Term Debt'].iloc[0]

    # equity value -> enterprise_value + cash - total debt
    equity_value = enterprise_value + cash_and_equivalents - (current_debt + long_term_debt)

    return {'equity_value': equity_value}
