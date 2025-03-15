from backtesting import (
    Strategy,
)  # Import Backtest and Strategy classes from backtesting module

import talib as ta  # Import talib library for technical analysis functions
from run_it_back import (
    run_backtest,
)  # Import run_backtest function from run_it_back module

# Your data input will replace GOOG
# It should have columns: 'Open', 'High', 'Low', 'Close', 'Volume'


class SmaCross(
    Strategy
):  # Define a new strategy class SmaCross inheriting from Strategy
    n1 = 50  # Short-term SMA period
    n2 = 200  # Long-term SMA period
    min_hold = 10  # Minimum holding period (in bars/days)

    def init(self):
        # Precompute the two EMAs.
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)

        # We'll keep a custom counter to track bars.
        self.bar_index = 0
        # Record the bar index at which we enter a trade.
        self.entry_bar = None

    def next(self):
        self.bar_index += 1
        close_price = self.data.Close[-1]

        # ----- Entry Conditions -----
        # If short EMA > long EMA and we're not in a position, consider buying.
        if self.sma1[-1] > self.sma2[-1]:
            if not self.position:
                if (close_price > self.sma1[-1]) and (close_price > self.sma2[-1]):
                    # Buy and record the entry bar.
                    self.buy()
                    self.entry_bar = self.bar_index
                    # Set a stop-loss at 90% of the entry close price.
                    self.stop_loss = close_price * 0.9

        # ----- Exit Conditions -----
        # First, always check for stop-loss hit (applies regardless of holding period).
        if self.position and close_price <= self.stop_loss:
            self.position.close()

        # Now check the MA crossover exit condition, but only if we've held for at least 10 bars.
        if self.position and ((self.bar_index - self.entry_bar) >= self.min_hold):
            # Look for a bearish crossover: short EMA crossing below long EMA,
            # plus the close is below both EMAs.
            if (
                (self.sma2[-1] > self.sma1[-1])
                and (close_price < self.sma1[-1])
                and (close_price < self.sma2[-1])
            ):
                self.position.close()


run_backtest(SmaCross)  # Run the backtest with the SmaCross strategy
# To plot the results (not available in the current environment)
# bt.plot()  # Uncomment this line to plot the results
