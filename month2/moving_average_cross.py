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
    n1 = 20  # Short-term SMA period
    n2 = 50  # Long-term SMA period

    def init(self):  # Initialize the strategy
        # Precompute the two SMAs using backtesting.py's built-in SMA function.
        # self.I() registers an indicator function so it updates with every new bar.
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)  # Compute short-term EMA
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)  # Compute long-term EMA

    def next(self):  # Define the logic to be executed on each new bar
        # If the short SMA is above the long SMA and we are not already in a position, buy.
        if (
            self.sma1[-1] > self.sma2[-1]
        ):  # Check if short-term EMA is above long-term EMA
            if not self.position:  # Check if there is no open position
                if (self.data.Close[-1] > self.sma1[-1]) and (
                    self.data.Close[-1] > self.sma2[-1]
                ):  # Additional conditions to buy
                    self.buy()  # Execute buy order
                    self.stop_loss = (
                        self.data.Close[-1] * 0.9
                    )  # Set stop loss at 90% of the current close price

        # If the short SMA is below the long SMA and we are in a position, exit.
        elif (
            self.sma1[-1] < self.sma2[-1]
        ):  # Check if short-term EMA is below long-term EMA
            if self.position:  # Check if there is an open position
                if (self.data.Close[-1] > self.sma1[-1]) and (
                    self.data.Close[-1] > self.sma2[-1]
                ):  # Additional conditions to close position
                    self.position.close()  # Close the position

                elif (
                    self.data.Close[-1] <= self.stop_loss
                ):  # Check if the current close price is below or equal to stop loss
                    self.position.close()  # Close the position


run_backtest(SmaCross)  # Run the backtest with the SmaCross strategy
# To plot the results (not available in the current environment)
# bt.plot()  # Uncomment this line to plot the results
