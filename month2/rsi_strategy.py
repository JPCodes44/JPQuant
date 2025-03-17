from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

"""
Strategy Explanation:
Use the RSI to determine oversold and overbought conditions. If the RSI dips below 30 buy, If the RSI goes above 70, sell.
"""

# ======================================================================


class RSIStrategy(Strategy):

    # --- PARAMS GO HERE ----

    # --- VARIABLES CONTAINING INDICATORS AND OTHER SETUP SHIT GOES HERE ----
    def init(self):
        # Instantiate the rsi indicator
        self.rsi = self.I(ta.RSI, self.data.Close)

        # Set var for stop loss
        self.stop_loss = 0

    # --- ACTUAL LOGIC GOES HERE ----
    def next(self):
        # If we are not in position
        if not self.position:
            # if the rsi falls below 30
            if self.rsi <= 30:
                # buy stock
                self.buy()
                # set stop loss based on the buy price (40% below current price)
                self.stop_loss = self.data.Close[-1] * 0.9
        elif self.position:
            # check if the rsi is above 70
            if self.rsi >= 70:
                # close the position
                self.position.close()
            # if not, check if we hit our stop loss
            elif self.data.Close[-1] <= self.stop_loss:
                # in the unfortunate case, sell
                self.position.close()


# ======================================================================


run_backtest(RSIStrategy)
