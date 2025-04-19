import pandas as pd  # data manipulation and analysis
import numpy as np  # numerical operations on arrays
import matplotlib.pyplot as plt  # plotting library (imported but not used in Strategy)
from scipy.signal import find_peaks  # function to detect local maxima/minimarom backtesting import Strategy  # base class for creating trading strategies
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
    lookback = 35  # number of bars to look back for pattern detection
    distance = 5  # minimum horizontal separation between peaks
    prominence = 0.035  # minimum vertical prominence of peaks

    n1 = 5   # period for first EMA
    n2 = 20  # period for second EMA

    def init(self):  # initialization logic, called once before backtest
        def head_and_shoulder(close, lookback, distance, prominence):  # indicator function
            arr = np.full(close.shape, np.nan, dtype=float)  # create NaN-filled array
            for i in range(lookback, len(close) + 1, lookback):  # slide window from lookback to end
                window = close[i - lookback : i]  # slice out the recent `lookback` bars
                peaks, _ = find_peaks(window, distance, prominence)  # find local maxima
                valleys, _ = find_peaks(-window, distance, prominence)  # find local minima

                # detect head-and-shoulders patterns in this window
                pattern = []  # initialize empty list for patterns
                for j in range(1, len(peaks) - 1):  # iterate over triples of peaks
                    L, H, R = peaks[j - 1], peaks[j], peaks[j + 1]  # left, head, right indices
                    if window[H] < window[L] and window[H] < window[R]:  # head higher than shoulders
                        if abs(window[L] - window[R]) < 0.02 * window[H]:  # shoulders similar height
                            pattern.append((L, H, R))  # record this pattern triple

                for L, H, R in pattern:  # for each detected pattern
                    # mark left shoulder on global array
                    arr[L] = close[L]
                    # mark head on global array
                    arr[H] = close[H]
                    # mark right shoulder on global array
                    arr[R] = close[R]
            return arr  # return the array of pattern markers

        # register the head-and-shoulder indicator for plotting and access
        self.hs = self.I(
            head_and_shoulder,  # function to compute
            self.data.Close,    # price series to feed
            self.lookback,      # parameter: lookback window size
            self.distance,      # parameter: peak distance
            self.prominence,    # parameter: prominence
        )

        # register two EMAs for crossover signals
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)  # short EMA
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)  # long EMA

    def next(self):  # called on each new bar
        price = self.data.Close[-1]  # current closing price
        if not self.position:  # if no open position
            if len(self.hs) > 3:  # ensure indicator has enough history
                # check if two recent markers exist (simple pattern trigger)
                if (
                    all(self.hs[i] is not np.nan for i in range(-3, -1))
                ):
                    self.buy()  # enter a long position
                    self.sl_price = price * 0.992  # set stop-loss 0.8% below entry
                    self.target_price = price * 1.015  # set target 1.5% above entry

        elif self.position and (price >= self.target_price):  # exit condition
            self.position.close()  # close position when target hit

# entry point: only runs when script is executed directly
if __name__ == "__main__":
    run_backtest(HeadAndShoulderStrategy, DATA_FOLDER)  # kick off backtest
