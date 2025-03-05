"""
pip install backtesting
pip install TA-Lib
"""

# Import the Backtest and Strategy classes from the backtesting module
import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy
from multiprocessing import Pool


# from backtesting.test import GOOG


class SMAPullbackStrategy(Strategy):
    stop_loss = 0
    n1 = 0.5  # 20 sma

    def init(self):
        price = self.data.Close
        self.sma = self.I(talib.SMA, price, self.n1)

    def next(self):
        price = self.data.Close[-1]
        low_price_prev_day = self.data.Low[-1]

        if price > self.sma[-1]:
            self.stop_loss = low_price_prev_day

            if price <= 2.4 * self.stop_loss:
                self.buy()


# test the strategy and pull in the data
# /Users/jpmak/JPQuant/SOL-1d-418wks_data.csv


if __name__ == "__main__":
    data = pd.read_csv(
        "/Users/jpmak/JPQuant/data/BTC-1m-2wks_data.csv", index_col=0, parse_dates=True
    )
    data.columns = [column.capitalize() for column in data.columns]

    bt = Backtest(data, SMAPullbackStrategy, cash=1000000, commission=0.002)

    output = bt.optimize(maximize="Equity Final [$]", n1=range(5, 40, 1))
    print(output)
    bt.plot()
