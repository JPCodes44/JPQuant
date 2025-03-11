import os
from backtesting import Backtest, Strategy
import pandas as pd
import numpy as np
import random
from statsmodels.tsa.stattools import adfuller
from statsmodels.sandbox.stats.runs import runstest_1samp

DATA_FOLDER = "/Users/jpmak/JPQuant/data"

SAVE_FOLDER = "/Users/jpmak/JPQuant/month2/results"

csv_path = os.path.join(SAVE_FOLDER, f"result_id_{random.randint(0, 100000)}.csv")


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
        # If today's close equals the 10-day minimum, trigger a buy
        if self.data.Close[-1] == self.min_low[-1]:

            if not self.position:
                self.buy()
        else:
            # Close position after one day if already in position
            if self.position:
                self.position.close()


# ✅ Create an empty DataFrame with column names but no rows
view_df = pd.DataFrame(
    columns=[
        "Start",
        "End",
        "Duration",
        "Exposure Time [%]",
        "Equity Final [$]",
        "Equity Peak [$]",
        "Commissions [$]",
        "Return [%]",
        "Buy & Hold Return [%]",
        "Return (Ann.) [%]",
        "Volatility (Ann.) [%]",
        "CAGR [%]",
        "Sharpe Ratio",
        "Sortino Ratio",
        "Calmar Ratio",
        "Max. Drawdown [%]",
        "Avg. Drawdown [%]",
        "Max. Drawdown Duration",
        "Avg. Drawdown Duration",
        "# Trades",
        "Win Rate [%]",
        "Best Trade [%]",
        "Worst Trade [%]",
        "Avg. Trade [%]",
        "Max. Trade Duration",
        "Avg. Trade Duration",
        "Profit Factor",
        "Expectancy [%]",
        "SQN",
        "Kelly Criterion",
    ]
)

for filename in os.listdir(DATA_FOLDER):
    if filename.endswith(".csv") or filename.endswith(
        ".xlsx"
    ):  # ✅ Only process Excel/CSV files
        file_path = os.path.join(DATA_FOLDER, filename)

        # ✅ Load the data
        if filename.endswith(".csv"):
            df = pd.read_csv(file_path, parse_dates=True, index_col="datetime")
        else:
            df = pd.read_excel(file_path, parse_dates=True, index_col="datetime")

        print(f"📊 Running backtest on: {filename}")

        try:
            # Backtest
            bt = Backtest(df, MeanReversionStrategy, cash=10_000, commission=0.002)
        except:
            df = pd.DataFrame(
                df, columns=["timestamp", "open", "high", "low", "close", "volume"]
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

        for i in range(30):
            print(f"results.iloc[{i}] = {results.iloc[i]}")

        view_df.loc[len(view_df)] = [
            results.iloc[0],
            results.iloc[1],
            results.iloc[2],
            results.iloc[3],
            results.iloc[4],
            results.iloc[5],
            results.iloc[6],
            results.iloc[7],
            results.iloc[8],
            results.iloc[9],
            results.iloc[10],
            results.iloc[11],
            results.iloc[12],
            results.iloc[13],
            results.iloc[14],
            results.iloc[15],
            results.iloc[16],
            results.iloc[17],
            results.iloc[18],
            results.iloc[19],
            results.iloc[20],
            results.iloc[21],
            results.iloc[22],
            results.iloc[23],
            results.iloc[24],
            results.iloc[25],
            results.iloc[26],
            results.iloc[27],
            results.iloc[28],
            results.iloc[29],
        ]

        bt.plot()

view_df.to_csv(csv_path, index=False)
