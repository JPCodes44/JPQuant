from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

"""
Strategy Explanation:
This strategy is based on the crossover of two Exponential Moving Averages (EMAs) and the Relative Strength Index (RSI). 

1. EMAs:
    - Short EMA: Calculated over a period of 9 days.
    - Long EMA: Calculated over a period of 26 days.
    - A buy signal is generated when the short EMA crosses above the long EMA.
    - A sell signal is generated when the short EMA crosses below the long EMA.

2. RSI:
    - RSI is calculated over a period of 14 days.
    - A buy signal is confirmed if the RSI is above 55.
    - A sell signal is confirmed if the RSI is below 45.

The strategy buys when both the EMA crossover and RSI conditions are met, and sells when either the EMA crossover or RSI conditions are met.
"""

# ======================================================================


class EMACrossoverRSIStrategy(Strategy):

    # --- PARAMS GO HERE ----
    short_ema_period = 9  # Set the short EMA period to 9
    long_ema_period = 26  # Set the long EMA period to 26
    rsi_period = 14  # Set the RSI period to 14
    rsi_entry_threshold = 55  # Set the RSI entry threshold to 55
    rsi_exit_threshold = 45  # Set the RSI exit threshold to 45

    # --- VARIABLES CONTAINING INDICATORS AND OTHER SETUP SHIT GOES HERE ----
    def init(self):
        # Initialize short EMA indicator using the short EMA period and closing prices
        self.short_ema = self.I(
            lambda x: ta.EMA(x, timeperiod=self.short_ema_period), self.data.Close
        )
        # Initialize long EMA indicator using the long EMA period and closing prices
        self.long_ema = self.I(
            lambda x: ta.EMA(x, timeperiod=self.long_ema_period), self.data.Close
        )
        # Initialize RSI indicator using the RSI period and closing prices
        self.rsi = self.I(
            lambda x: ta.RSI(x, timeperiod=self.rsi_period), self.data.Close
        )

    # --- ACTUAL LOGIC GOES HERE ----
    def next(self):
        # Check for EMA crossover and RSI entry condition
        if (
            crossover(self.short_ema, self.long_ema)
            and self.rsi[-1] > self.rsi_entry_threshold
        ):
            self.buy()  # Execute buy order

        # Check for EMA crossover or RSI exit condition
        elif (
            crossover(self.long_ema, self.short_ema)
            or self.rsi[-1] < self.rsi_exit_threshold
        ):
            self.position.close()  # Close the position


# ======================================================================


run_backtest(EMACrossoverRSIStrategy)
