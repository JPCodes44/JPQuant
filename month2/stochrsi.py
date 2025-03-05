"""
RBI system

R - Research trading strategies
    - google scholar, youtube, twitter, reddit,

B - Backtest trading strategies -- more winners

95% of the bots i run dont work, 5% do.

I - Implement trading strategies into a bot
    -

"""

# bollinger bands and stochastic rsi

import pandas as pd
import backtesting as bt
from backtesting import Backtest, Strategy
from ta.momentum import StochRSIIndicator
import pandas_ta as ta
import warnings
from backtesting.lib import crossover

# filter all warnings
warnings.filterwarnings("ignore")
import dont_share as d
import ccxt

factor = 1000


class Strat(Strategy):
    rsi_window = 14
    stochrsi_smooth1 = 3
    stochrsi_smooth2 = 3
    bbands_length = 20
    stochrsi_length = 14
    bbands_std = 2

    def init(self):
        self.bbands = self.I(bands, self.data)
        self.stoch_rsi_k = self.I(stoch_rsi_k, self.data)
        self.stoch_rsi_d = self.I(stoch_rsi_d, self.data)
        self.buy_price = 0

    def next(self):
        lower = self.bbands[0]  # lower bollinger band
        mid = self.bbands[1]  # middle bollinger band
        upper = self.bbands[2]  # upper bollinger band

        # check for entry long positions
        if self.data.Close[-1] > lower[-1] and crossover(
            self.stoch_rsi_k, self.stoch_rsi_d
        ):
            self.buy(
                size=0.05, sl=self.data.Close[-1] * 0.85, tp=self.data.Close[-1] * 1.40
            )
            self.buy_price = self.data.Close[-1]


def bands(data):
    bbands = ta.bbands(close=data.Close.s, length=20, std=2)
    return bbands.to_numpy().T


def stoch_rsi_k(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)
    return stochrsi["STOCHRSIk_14_14_3_3"].to_numpy()


def stoch_rsi_d(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)
    return stochrsi["STOCHRSId_14_14_3_3"].to_numpy()


data_df = pd.read_csv(
    "/Users/jpmak/JPQuant/data/BTC-1d-418wks_data.csv",
    index_col=0,
    parse_dates=True,
)

# Ensure column names match what Backtesting.py expects:
# "Open", "High", "Low", "Close", "Volume"
data_df.columns = [col.capitalize() for col in data_df.columns]
data_df.dropna(inplace=True)

print(data_df.tail())
bt = Backtest(data_df, Strat, cash=1000000, commission=0.001)
stats = bt.run()
bt.plot()
print(stats)
