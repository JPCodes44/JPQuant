from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

"""
Strategy Explanation:

"""

# ======================================================================


class PutStrategyNameHere(Strategy):

    # --- PARAMS GO HERE ----
    lookback_days = 10

    # --- VARIABLES CONTAINING INDICATORS AND OTHER SETUP SHIT GOES HERE ----
    def init(self):
        self.put_vars_here = 1

    # --- ACTUAL LOGIC GOES HERE ----
    def next(self):
        if self.put_vars_here == 1:
            self.position.close()


# ======================================================================


run_backtest(Strategy)
