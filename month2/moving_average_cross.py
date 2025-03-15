from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import numpy as np
import yfinance as yf
import talib as ta
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from run_it_back import run_backtest


class ModifiedMACrossover(Strategy):
    # Strategy parameters
    short_period = 20  # short-term moving average period
    long_period = 50  # long-term moving average period
    stop_loss_pct = 0.03  # stop-loss: 3% below entry price
    min_hold = 10  # minimum holding period (in bars/days)

    def init(self):
        # Pre-compute the moving averages on the Close prices.
        self.sma_short = self.I(ta.SMA, self.data.Close, timeperiod=self.short_period)
        self.sma_long = self.I(ta.SMA, self.data.Close, timeperiod=self.long_period)
        # Record the entry bar index for the current position.
        self.entry_bar = None
        self.bar_index = 0

    def next(self):
        # Get current open and close prices.
        open_price = self.data.Open[-1]
        close_price = self.data.Close[-1]

        self.bar_index += 1

        # --- Step 1: Determine candle characteristics ---
        # Identify a doji/narrow-range candle: if the candle's real body is less than 0.3% of the close.
        doji = abs(close_price - open_price) < 0.003 * close_price

        # --- Step 2: Evaluate Bullish Entry Conditions ---
        # Check for a golden cross (short MA crossing above long MA).
        if crossover(self.sma_short, self.sma_long):
            # Additional entry criteria:
            # a) The candle should not be a doji.
            # b) The candle must be bullish (white: close > open).
            # c) The close must be above both moving averages.
            if (
                not doji
                and close_price > open_price
                and close_price > self.sma_short[-1]
                and close_price > self.sma_long[-1]
            ):
                # If no position is open, enter a long position.
                if not self.position:
                    self.entry_bar = self.
                    # Set the stop loss as a fixed percentage below the entry.
                    stop_loss_level = close_price * (1 - self.stop_loss_pct)
                    self.buy(sl=stop_loss_level)

        # --- Step 3: Evaluate Bearish Exit Conditions ---
        # Only check exit conditions if we currently hold a long position.
        if self.position:
            holding_period = (
                len(self.data) - 1 - self.entry_bar if self.entry_bar is not None else 0
            )

            # The stop-loss exit is managed automatically by backtesting.py based on the 'sl' parameter.
            # However, we can also check for a bearish exit condition after the minimum holding period.
            if holding_period >= self.min_hold:
                # Check for a bearish crossover: short MA crossing below long MA.
                # Also, ensure that the current close is below both MAs.
                if crossover(self.sma_long, self.sma_short) and (
                    close_price < self.sma_short[-1] and close_price < self.sma_long[-1]
                ):
                    self.position.close()


# ======================================================================


run_backtest(ModifiedMACrossover)
