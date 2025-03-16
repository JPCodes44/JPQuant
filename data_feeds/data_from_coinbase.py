import pandas as pd
import datetime
import os
import ccxt
import dont_share as d
import coinbase_dont_share as c
import numpy as np
import warnings
from math import ceil

symbol_list = [
    "BTC/USD",  # Bitcoin: Coinbase’s original asset since 2012
    "ETH/USD",  # Ethereum: Added in 2016
    "LTC/USD",  # Litecoin: One of the earliest altcoins, available since around 2013
    "SOL/USD",
    "DOGE/USD",
    # "BCH/USD",  # Bitcoin Cash: Introduced after the Bitcoin fork in 2017
    # "XLM/USD",  # Stellar: An early altcoin from around 2014-2015
    # "ADA/USD",  # Cardano: One of the older altcoins, listed a few years back
    # "EOS/USD",  # EOS: Among the earlier tokens in the ICO boom, on Coinbase since around 2018
    # "LINK/USD",  # Chainlink: Although a bit later than the others, it’s one of the longer–standing altcoins among the newer generation
]

timeframe = "1h"
weeks = 50

# 1d timeframe
date_range = pd.date_range(start="2017-03-06", end="2025-03-07")

# for 1m timeframe
# date_range = pd.date_range(
#     start="2024-12-12 09:10:00", end="2025-03-14 16:00:00", freq="min"
# )

dates = np.array(date_range)  # Convert to NumPy array for indexing

# ✅ Suppress only DeprecationWarnings
warnings.simplefilter("ignore", category=DeprecationWarning)

# ✅ Suppress only FutureWarnings
warnings.simplefilter(action="ignore", category=FutureWarning)

SAVE_FOLDER = (
    "/Users/jpmak/JPQuant/data"  # Or an absolute path like "/Users/jpmak/JPQuant/data"
)


def timeframe_to_sec(timeframe):
    if "m" in timeframe:
        return int("".join([char for char in timeframe if char.isnumeric()])) * 60
    elif "h" in timeframe:
        return int("".join([char for char in timeframe if char.isnumeric()])) * 60 * 60
    elif "d" in timeframe:
        return (
            int("".join([char for char in timeframe if char.isnumeric()]))
            * 24
            * 60
            * 60
        )


def get_historical_data(symbol, timeframe, weeks):

    now = datetime.datetime.utcnow()
    coinbase = ccxt.coinbase(
        {"apikey": c.key, "secret": c.secret, "enableRateLimit": True}
    )

    granularity = timeframe_to_sec(timeframe)  # Convert timeframe to seconds

    total_time = weeks * 7 * 24 * 60 * 60
    run_times = ceil(total_time / (granularity * 200))

    dataframe = pd.DataFrame()

    for i in range(run_times):

        since = now - datetime.timedelta(seconds=granularity * 200 * (i + 1))
        since_timestamp = int(since.timestamp()) * 1000  # Convert to milliseconds

        data = coinbase.fetch_ohlcv(symbol, timeframe, since=since_timestamp, limit=200)
        df = pd.DataFrame(
            data, columns=["datetime", "open", "high", "low", "close", "volume"]
        )
        df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")
        dataframe = pd.concat([df, dataframe])

    dataframe = dataframe.set_index("datetime")
    dataframe = dataframe[["open", "high", "low", "close", "volume"]]

    return dataframe


def csvs_of_random_windows(timeframe, weeks, dates, num_csv):
    for i in range(num_csv):
        # try:
        #     # ✅ Choose left index randomly
        #     left = np.random.randint(0, len(dates) - 1)  # Ensures space for right

        #     # ✅ Choose right index randomly (always > left)
        #     right = np.random.randint(left + 1, len(dates))  # Ensures left < right

        #     get_historical_data(symbol, timeframe, weeks, left, right)
        # except Exception as e:
        #     print(
        #         f"{e} - Either your window_length is too small or your buffer is too big, fix pls"
        #     )
        # Choose left index randomly

        symbol = symbol_list[np.random.randint(0, len(symbol_list) - 1)]
        # Define a maximum window length (e.g., 50 days)
        max_window = 50

        left = np.random.randint(0, len(dates) - 1)

        # Calculate the maximum possible right index, ensuring we don't exceed the date range
        max_possible_right = min(left + max_window, len(dates) - 1)

        # Choose right index randomly (ensuring it's always > left)
        right = np.random.randint(
            left + 1, max_possible_right + 1
        )  # +1 because upper bound is exclusive

        start_date = dates[left]
        end_date = dates[right]

        # If you want to re-use the same naming logic, you can do:
        csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"
        # The expression symbol[0:3] is slicing the string 'symbol' to get the first three characters.
        # This is useful if 'symbol' contains a longer string, but you only want to use the first three characters
        # (e.g., if 'symbol' is 'BTCUSD', symbol[0:3] would result in 'BTC').

        # Construct the full path to the CSV file using os.path.join
        csv_path = os.path.join(SAVE_FOLDER, csv_filename)

        if os.path.exists(csv_path):
            print("file alr exists")
            return pd.read_csv(csv_path)

        print(f"🎨✨ Creating sheet #{i + 1} from {start_date} to {end_date}")
        dataframe = get_historical_data(symbol, timeframe, weeks)

        # Check if the DataFrame is empty or contains only column titles
        if dataframe.loc[start_date:end_date].shape[0] <= 1:
            print(
                "Skipping csv because not enough data is fetched or Start/end times are too early/late."
            )
            continue

        # Instead of writing to the root, write to csv_path
        dataframe.loc[start_date:end_date].to_csv(csv_path)

    print("Done boiiiiiiiii")


# Manual fetch
# get_historical_data(symbol, timeframe, weeks, "2025-03-09", "2016-01-02")

csvs_of_random_windows(timeframe=timeframe, weeks=weeks, dates=dates, num_csv=20)
