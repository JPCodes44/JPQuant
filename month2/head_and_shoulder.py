import pandas as pd  # data manipulation and analysis
import numpy as np  # numerical operations on arrays
import matplotlib.pyplot as plt  # plotting library (imported but not used in Strategy)
from scipy.signal import (
    find_peaks,
)  # function to detect local maxima/minima from backtesting import Strategy  # base class for creating trading strategies
from backtesting.lib import crossover  # helper to detect EMA/MACD crossovers
from backtesting import Strategy
from run_it_back import run_backtest  # custom function to execute backtest
import talib as ta  # technical analysis library for indicators

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


class HeadAndShoulderStrategy(Strategy):  # define a new trading strategy class
    lookback = 50  # number of bars to look back for pattern detection
    distance = 5  # minimum horizontal separation between peaks
    prominence = 0.0000001  # minimum vertical prominence of peaks

    n1 = 5  # period for first EMA
    n2 = 20  # period for second EMA

    count_next = 0
    found_pattern = False

    target_price = 0

    def init(self):  # initialization logic, called once before backtest

        def get_pattern_pv(peaks, prices, pattern, valleys):
            # detect head-and-shoulders patterns in this window
            for j in range(1, len(peaks) - 1):  # iterate over triples of peaks
                L, H, R = (
                    peaks[j - 1],
                    peaks[j],
                    peaks[j + 1],
                )  # left, head, right indices
                if (
                    prices[H] < prices[L] and prices[H] < prices[R]
                ):  # head lower than shoulders
                    if (
                        abs(prices[L] - prices[R]) < 0.02 * prices[H]
                    ):  # shoulders similar depth
                        pattern.append((L, H, R))  # record this pattern triple

            return pattern, peaks, valleys, R

        def head_and_shoulder(
            close, lookback, distance, prominence
        ):  # indicator function
            arr = np.full(close.shape, np.nan, dtype=float)  # create NaN-filled array
            R_arr = np.full(close.shape, np.nan, dtype=float)
            for i in range(lookback, len(close)):  # slide window from lookback to end
                prices = np.asarray(close[i - lookback : i])
                peaks = find_peaks(prices, distance, prominence)
                print(peaks)
                pattern = []

                pattern, peaks, valleys = get_pattern_pv(
                    peaks, prices, pattern, valleys
                )

                for L, H, R in pattern:  # for each detected pattern
                    base = i - lookback
                    arr[base + L] = close[base + L]
                    arr[base + H] = close[base + H]
                    arr[base + R] = close[base + R]
                    R_arr[i] = base + R  # Save R in global terms

            return arr, R_arr  # return the array of pattern markers

        # register the head-and-shoulder indicator for plotting and access
        self.hs, self.R_detected = self.I(
            head_and_shoulder,  # function to compute
            self.data.Close,  # price series to feed
            self.lookback,  # parameter: lookback window size
            self.distance,  # parameter: peak distance
            self.prominence,  # parameter: prominence
        )

        # register two EMAs for crossover signals
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)  # short EMA
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)  # long EMA

    def next(self):
        if len(self.data.Close) < self.lookback:
            return

        price = self.data.Close[-1]

        if not self.position:
            if self.R_detected and not np.isnan(self.R_detected[-1]):
                print(self.R_detected[-1])
                self.buy()
                self.target_price = price * 1.015

        elif self.position:
            if price >= self.target_price or crossover(self.sma1, self.sma2):
                self.position.close()


# entry point: only runs when script is executed directly
if __name__ == "__main__":
    run_backtest(HeadAndShoulderStrategy, DATA_FOLDER)  # kick off backtest
