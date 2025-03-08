import os
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller
from statsmodels.sandbox.stats.runs import runstest_1samp

DATA_FOLDER = "/Users/jpmak/JPQuant/data"


class MeanReversionStrategy(Strategy):
    lookback_period = 10  # 10-day rolling minimum

    def init(self):
        def rolling_min(series, period):
            return pd.Series(series).rolling(period).min().to_numpy()

        # Compute rolling minimum of the closing prices
        self.min_low = self.I(rolling_min, self.data.Close, self.lookback_period)

        # **Run Statistical Tests ONCE Before Trading Starts**
        close_series = pd.Series(self.data.Close)

        # 1️⃣ **ADF Test (Stationarity Check)**
        adf_result = adfuller(close_series)
        self.adf_p_value = adf_result[1]  # Store p-value

        # 2️⃣ **Runs Test (Randomness Check)**
        returns = close_series.pct_change().dropna()
        runs_result = runstest_1samp(returns)
        self.runs_stat = runs_result[0]
        self.runs_p_value = runs_result[1]

        # ✅ **Inject the statistics into the plot using self.I()**
        self.I(
            lambda x: np.full_like(x, self.adf_p_value),
            self.data.Close,
            name=f"ADF p-value: {self.adf_p_value:.5f}",
        )
        self.I(
            lambda x: np.full_like(x, self.runs_stat),
            self.data.Close,
            name=f"Runs Stat: {self.runs_stat:.3f}",
        )
        self.I(
            lambda x: np.full_like(x, self.runs_p_value),
            self.data.Close,
            name=f"Runs p-value: {self.runs_p_value:.5f}",
        )

    def next(self):
        # If today's close equals the 10-day minimum, trigger a buy
        if self.data.Close[-1] == self.min_low[-1]:

            if not self.position:
                self.buy()
        else:
            # Close position after one day if already in position
            if self.position:
                self.position.close()


for filename in os.listdir(DATA_FOLDER):
    if filename.endswith(".csv") or filename.endswith(".xlsk"):
        file_path = os.path.join(DATA_FOLDER, filename)

        # Load the data
        if filename.endswith(".csv"):
            # Load your BTC price data
            btc_data = pd.read_csv(
                file_path,
                index_col=0,
                parse_dates=True,
            )
        else:
            df = pd.read_excel(file_path, parse_dates=True, index_col="datetime")

        print(f"📊 Running backtest on: {filename}")

        df = pd.DataFrame(
            btc_data, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        df.columns = [
            "Timestamp",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]  # Rename columns

        # Backtest
        bt = Backtest(df, MeanReversionStrategy, cash=10_000, commission=0.002)
        results = bt.run()
        print(results)

        bt.plot()
