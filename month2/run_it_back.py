import os
from backtesting import Backtest
import warnings
import pandas as pd
import random


def run_backtest(Strategy):

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
                bt = Backtest(df, Strategy, cash=10_000, commission=0.002)
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
                bt = Backtest(df, Strategy, cash=10_000, commission=0.002)

            results = bt.run()
            # print(results)
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

            # check if the dataframe contains nan values
            if results.isna().any():
                print(
                    "Warning: The time series data will contain 0s and NaNs due to having 0 trades (maybe other shit tho). \nConsider making the timeframe longer for more trades."
                )
            bt.plot()

    if not os.listdir(DATA_FOLDER):
        print(f"No csvs in {DATA_FOLDER}.")
        pass
    else:
        print(f"Printed to result_id_{id}.csv")
        view_df.to_csv(csv_path, index=False)
