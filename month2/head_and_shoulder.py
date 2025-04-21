import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks, argrelextrema
from backtesting import Strategy
from backtesting.lib import crossover
from run_it_back import run_backtest

import talib as ta

# Define the timeframe to decide data folder
TIMEFRAME = "m"  # possible values: "m", "h", or others

# Set DATA_FOLDER based on TIMEFRAME
DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"
    )
)


class HeadAndShoulderStrategy(Strategy):
    lookback = 1000
    distance = 5
    prominence = 0.2

    n1 = 5
    n2 = 20

    def init(self):

        def get_pattern_pv(peaks, prices, pattern, valleys, find_maxima):
            if find_maxima:
                for j in range(1, len(peaks) - 1):
                    L, H, R = peaks[j - 1], peaks[j], peaks[j + 1]
                    if prices[H] < prices[L] and prices[H] < prices[R]:
                        if abs(prices[L] - prices[R]) < 0.2 * prices[H]:
                            pattern.append((L, H, R))
            else:
                for j in range(1, len(valleys) - 1):
                    L, H, R = valleys[j - 1], valleys[j], valleys[j + 1]
                    if prices[H] > prices[L] and prices[H] > prices[R]:
                        if abs(prices[L] - prices[R]) < 0.2 * prices[H]:
                            pattern.append((L, H, R))
            return pattern, peaks, valleys

        def head_and_shoulder(close, lookback, distance, prominence):
            arr = np.full(close.shape, np.nan, dtype=float)
            R_arr = np.full(close.shape, np.nan)

            for i in range(lookback, len(close)):
                prices = np.asarray(close[i - lookback : i], dtype=np.float64)
                prices = prices[~np.isnan(prices)]

                peaks, _ = find_peaks(prices, distance, prominence)
                # for local minima
                print(peaks)
                valleys = argrelextrema(prices, np.less)[0]
                pattern = []

                pattern, peaks, valleys = get_pattern_pv(
                    peaks, prices, pattern, valleys, False
                )
                print(valleys)

                for L, H, R in pattern:
                    base = i - lookback
                    arr[base + L] = close[base + L]
                    arr[base + H] = close[base + H]
                    arr[base + R] = close[base + R]
                    R_arr[i] = base + R

            return arr, R_arr

        # Register indicators
        self.hs, self.R_detected = self.I(
            head_and_shoulder,
            self.data.Close,
            self.lookback,
            self.distance,
            self.prominence,
        )
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)

    def next(self):
        if len(self.data.Close) < self.lookback:
            return

        price = self.data.Close[-1]

        if not self.position:
            if not np.isnan(self.R_detected[-1]):
                print("Pattern triggered at index:", self.R_detected[-1])
                self.buy()
                self.target_price = price * 1.0015

        elif self.position:
            if price >= self.target_price:
                self.position.close()


if __name__ == "__main__":
    run_backtest(HeadAndShoulderStrategy, DATA_FOLDER)
