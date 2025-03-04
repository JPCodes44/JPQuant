# get data on the 15min timeframe

from backtesting import Backtest
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
from strats_26 import *
from dataset import get_candles_since_date


def run_backtest(stratName, symbol, timeframe, start_time, plot=True, save_data=True):
    # data = pd.read_csv('feb23/BTC-USD-15m_filled.csv', index_col='datetime', parse_dates=True)
    data = get_candles_since_date(
        symbol, timeframe=timeframe, start_time=start_time, save_data=save_data
    )

    data.columns = ["Open", "High", "Low", "Close", "Volume"]

    # run the backtest
    bt = Backtest(
        data, eval(stratName), cash=10000, commission=0.001, exclusive_orders=True
    )

    # get the results
    output = bt.run()
    print(output)

    # plot the results
    if plot:
        bt.plot()

    print(data.head())


run_backtest(
    "FlagCont",
    "ETH-USD",
    timeframe="1h",
    start_time=datetime(2022, 1, 1, 12, 0),
    plot=True,
    save_data=False,
)
