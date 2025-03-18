from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

"""
Strategy Explanation:

"""

# ======================================================================


class SupportResistanceBreakout(Strategy):
    def init(self):
        # Precompute or set up any necessary indicator series, e.g. ATR, support, resistance.
        self.atr = self.data.ATR  # assuming ATR precomputed in data
        self.support = self.data.Support
        self.resistance = self.data.Resistance

    def next(self):
        price = self.data.Close[-1]  # current closing price
        supp = self.support[-1]
        res = self.resistance[-1]

        if not self.position:  # no open position
            if price > res:
                self.buy()  # break above resistance -> go long
            elif price < supp:
                self.sell()  # break below support -> go short
        else:
            # If a position is open, check for flip conditions
            if self.position.is_long and price < supp:
                self.position.close()
                self.sell()  # flip to short
            elif self.position.is_short and price > res:
                self.position.close()
                self.buy()  # flip to long


# ======================================================================


run_backtest(Strategy)
