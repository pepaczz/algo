import algo.data_acquisition as da
import algo.equity_value as ev
import yfinance as yf
import yahoo_fin.stock_info as si
import numpy_financial as npf



sp_history = da.get_sp500_list()

# TODO: model předpokládá growth rate - podívat se na historické growth rates

# get records without date_removed
sp_current = sp_history.loc[sp_history['date_removed'].isnull()]

idx = 0
ticker = sp_current.iloc[idx]['ticker']
ticker_yf = yf.Ticker(ticker)
shares_outstanding = ticker_yf.get_shares_full()
# ev.get_equity_value(ticker)


# growth esiimates


# tickers = sp_current['ticker'].to_list()[:5]
tickers = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'META']
for ticker in tickers:
    print(ticker)
    # print(da.get_analysts_info(ticker)['Growth Estimates'])

    try:
        equity_value = ev.get_equity_value(ticker)['equity_value']
    except KeyError:
        print(f'Equity value not obtained for {ticker}')
        continue

    ticker_yf = yf.Ticker(ticker)
    shares_outstanding = ticker_yf.get_shares_full().iloc[-1]
    intrinsic_value = equity_value / shares_outstanding
    current_value = da.get_live_price(ticker)

    ratio = current_value / intrinsic_value
    print(ratio)