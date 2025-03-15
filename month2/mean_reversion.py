import os
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA
import pandas as pd
import numpy as np
import warnings
import random
from statsmodels.tsa.stattools import adfuller
from run_it_back import run_backtest
from statsmodels.sandbox.stats.runs import runstest_1samp

DATA_FOLDER = "/Users/jpmak/JPQuant/data"

SAVE_FOLDER = "/Users/jpmak/JPQuant/month2/results"

id = random.randint(0, 100000)

csv_path = os.path.join(SAVE_FOLDER, f"result_id_{id}.csv")

# Suppress only DeprecationWarnings
warnings.simplefilter("ignore", category=DeprecationWarning)

# Suppress only FutureWarnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# Suppress only UserWarning
warnings.simplefilter(action="ignore", category=UserWarning)

# ++++++++++++++++++++++++ PUT YOUR STRATEGY BELOW +++++++++++++++++++++++++


class MeanReversionStrategy(Strategy):
    lookback_period = 10  # 10-day rolling minimum

    def init(self):
        def rolling_min(series, period):
            return pd.Series(series).rolling(period).min().to_numpy()

        # Compute rolling minimum of the closing prices
        self.min_low = self.I(rolling_min, self.data.Close, self.lookback_period)

        # # **Run Statistical Tests ONCE Before Trading Starts**
        # close_series = pd.Series(self.data.Close)

        # # 1️⃣ **ADF Test (Stationarity Check)**
        # adf_result = adfuller(close_series)
        # self.adf_p_value = adf_result[1]  # Store p-value

        # # 2️⃣ **Runs Test (Randomness Check)**
        # returns = close_series.pct_change().dropna()
        # runs_result = runstest_1samp(returns)
        # self.runs_stat = runs_result[0]
        # self.runs_p_value = runs_result[1]

        # # ✅ **Inject the statistics into the plot using self.I()**
        # self.I(
        #     lambda x: np.full_like(x, self.adf_p_value),
        #     self.data.Close,
        #     name=f"ADF p-value: {self.adf_p_value:.5f}",
        # )
        # self.I(
        #     lambda x: np.full_like(x, self.runs_stat),
        #     self.data.Close,
        #     name=f"Runs Stat: {self.runs_stat:.3f}",
        # )
        # self.I(
        #     lambda x: np.full_like(x, self.runs_p_value),
        #     self.data.Close,
        #     name=f"Runs p-value: {self.runs_p_value:.5f}",
        # )

    def next(self):
        tolerance = 0.09  # 0.1% tolerance, adjust as needed
        if self.data.Close[-1] <= self.min_low[-1] * (1 + tolerance):
            if not self.position:
                self.buy()
        else:
            if self.position:
                self.position.close()


run_backtest(MeanReversionStrategy)
