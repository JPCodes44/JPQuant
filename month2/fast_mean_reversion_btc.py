from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

"""
Strategy Explanation:
- This strategy is purely a template to help you code your own backtest logic in `backtesting.py`.
- It demonstrates:
  1) How to set strategy parameters
  2) How to declare and initialize indicators/variables in `init()`
  3) How to open/close positions in `next()`
- Replace the placeholder logic with your real trading signals.
"""

# ======================================================================


class PutStrategyNameHere(Strategy):
    # Example parameter(s)
    lookback_days = 10

    def init(self):
        """
        Runs once at the start of the backtest.
        Typically used to pre-compute indicators or store rolling calculations.
        """
        # For demonstration, let's do a simple rolling average
        close = self.data.Close
        self.sma = self.I(ta.SMA, close, self.lookback_days)

        # Just a placeholder variable for illustration:
        self.my_state = 0

    def next(self):
        """
        Runs for each bar/candle.
        Decide whether to buy/sell/hold based on your signals.
        """
        # Example logic: if last close < rolling SMA => close any open position
        if self.data.Close[-1] < self.sma[-1]:
            self.position.close()
            self.my_state = 0
        else:
            # If no position, open one (or do partial if you like)
            if not self.position:
                self.buy(size=1)
                self.my_state = 1


# ======================================================================

# Always remember to pass YOUR strategy class to run_backtest, not just `Strategy`.
if __name__ == "__main__":
    run_backtest(PutStrategyNameHere)
