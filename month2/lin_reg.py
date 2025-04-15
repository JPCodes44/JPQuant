import numpy as np
import pandas as pd
from backtesting import Backtest, Strategy
import talib as ta
from run_it_back import run_backtest

# Define the data folder depending on the timeframe
TIMEFRAME = "m"
DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"
    )
)


# Define the strategy class
class LinearRegAngleStrategy(Strategy):
    lookback = 14
    entry_threshold = 10
    exit_threshold = 2

    def init(self):
        # Must use self.I to register indicator
        self.angle = self.I(ta.LINEARREG_ANGLE, self.data.Close, self.lookback)

    def next(self):
        angle = self.angle[-1]

        if angle is None:
            return

        # Entry conditions
        if not self.position:
            if angle > self.entry_threshold:
                self.buy()
            elif angle < -self.entry_threshold:
                self.sell()

        # Exit conditions
        if self.position.is_long and angle < self.exit_threshold:
            self.position.close()
        elif self.position.is_short and angle > -self.exit_threshold:
            self.position.close()


# Run the backtest
if __name__ == "__main__":
    run_backtest(LinearRegAngleStrategy, DATA_FOLDER)
