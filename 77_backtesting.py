"""
pip install backtesting
pip install TA-Lib
"""

# Import the Backtest and Strategy classes from the backtesting module
import numpy as np
import pandas as pd
import talib
from backtesting import Backtest, Strategy

# from backtesting.test import GOOG


class SMAPullbackStrategy(Strategy):
    n = 20  # 20 sma

    def init(self):
        close = self.data.Close
        self.sma = self.I(talib.SMA, close, self.n)

    def next(self):
        price = self.data.Close[-1]
        sma = self.sma[-1]
        yesterdays_low = self.data.Low[-2]
        stop_loss = yesterdays_low
        take_profit = yesterdays_low + 1.5 * (price - stop_loss)

        if self.position.is_long:
            if price <= stop_loss or price >= take_profit:
                self.position.close()
        elif price > sma:
            print(stop_loss, ", ", take_profit)
            try:
                self.buy(sl=stop_loss, tp=take_profit)
            except:
                pass


# test the strategy and pull in the data
