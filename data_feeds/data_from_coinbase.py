import pandas as pd
import datetime
import os
import ccxt
import dont_share as d
import coinbase_dont_share as c
import numpy as np
import warnings
from math import ceil

symbol = "ETH/USD"
timeframe = "1m"
weeks = 1

# 1d timeframe
# date_range = pd.date_range(start="2025-03-06", end="2025-03-07", freq="T")

# for 1m timeframe
date_range = pd.date_range(
    start="2025-03-06 09:10:00", end="2025-03-07 16:00:00", freq="T"
)

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


def csvs_of_random_windows(symbol, timeframe, weeks, dates, num_csv):
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
        left = np.random.randint(0, len(dates) - 1)  # Ensures space for right

        # Choose right index randomly (always > left)
        right = np.random.randint(left + 1, len(dates))  # Ensures left < right

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

csvs_of_random_windows(
    symbol=symbol, timeframe=timeframe, weeks=weeks, dates=dates, num_csv=10
)
