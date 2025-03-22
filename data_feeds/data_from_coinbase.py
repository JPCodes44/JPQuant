import pandas as pd
import datetime
import os
import ccxt
import dont_share as d
import coinbase_dont_share as c
import numpy as np
import warnings
from math import ceil

# know which symbols to comment out and adjust timeframe accordingly to make good data
symbol_list = [
    "BTC/USD",  # Bitcoin: Coinbase’s original asset since 2012
    "ETH/USD",  # Ethereum: Added in 2016
    "LTC/USD",  # Litecoin: One of the earliest altcoins, available since around 2013
    "SOL/USD",
    # "DOGE/USD",
    # "BCH/USD",  # Bitcoin Cash: Introduced after the Bitcoin fork in 2017
    # "XLM/USD",  # Stellar: An early altcoin from around 2014-2015
    # "ADA/USD",  # Cardano: One of the older altcoins, listed a few years back
    # "EOS/USD",  # EOS: Among the earlier tokens in the ICO boom, on Coinbase since around 2018
    # "LINK/USD",  # Chainlink: Although a bit later than the others, it’s one of the longer–standing altcoins among the newer generation
]

timeframe = "1h"
weeks = 200

# 1d timeframe
date_range = pd.date_range(start="2019-03-06", end="2025-03-07")

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
    # Get the current UTC time
    now = datetime.datetime.utcnow()

    # Initialize the Coinbase exchange with API keys and rate limiting
    coinbase = ccxt.coinbase(
        {"apikey": c.key, "secret": c.secret, "enableRateLimit": True}
    )

    # Convert the timeframe to seconds
    granularity = timeframe_to_sec(timeframe)

    # Calculate the total time in seconds for the given number of weeks
    total_time = weeks * 7 * 24 * 60 * 60

    # Calculate the number of API calls needed to fetch the data
    run_times = ceil(total_time / (granularity * 200))

    # Initialize an empty DataFrame to store the data
    dataframe = pd.DataFrame()

    # Loop through the number of API calls needed
    for i in range(run_times):
        # Calculate the timestamp for the current batch of data
        # 'now' is assumed to be the current datetime
        # 'granularity' is the time interval in seconds
        # 'i' is the current batch index

        # Calculate the datetime for the current batch by subtracting a time delta from 'now'
        # The time delta is calculated as 'granularity * 200 * (i + 1)' seconds
        since = now - datetime.timedelta(seconds=granularity * 200 * (i + 1))

        # Convert the 'since' datetime to a POSIX timestamp (seconds since epoch)
        # Then convert the timestamp to milliseconds by multiplying by 1000
        since_timestamp = int(since.timestamp()) * 1000  # Convert to milliseconds

        # Fetch the OHLCV data from Coinbase
        data = coinbase.fetch_ohlcv(symbol, timeframe, since=since_timestamp, limit=200)

        # Convert the data to a DataFrame
        df = pd.DataFrame(
            data,
            columns=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "volume",
            ],
        )

        # Convert the datetime column to a pandas datetime object
        df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")

        # Concatenate the new data with the existing DataFrame
        dataframe = pd.concat([df, dataframe])

    # Set the datetime column as the index
    dataframe = dataframe.set_index("datetime")

    # Reorder the columns
    dataframe = dataframe[["open", "high", "low", "close", "volume"]]

    if len(df) > 2:
        dataframe["support"] = dataframe[:-2]["close"].min()
        dataframe["resis"] = dataframe[:-2]["close"].max()
    else:
        dataframe["support"] = dataframe["close"].min()
        dataframe["resis"] = dataframe["close"].max()

    return dataframe


def get_window_size(dates, weeks, timeframe):
    # Define the maximum window length in days
    max_window = int(weeks * 7)

    # Define the minimum window length based on the timeframe
    if "m" in timeframe:
        min_window = int(
            max_window * 0.02
        )  # Very short since minutes have high data frequency
    elif "h" in timeframe:
        min_window = int(
            max_window * 0.4
        )  # Hours are slower than minutes but still frequent
    elif "d" in timeframe:
        min_window = int(
            max_window * 0.6
        )  # Days have way fewer data points, so a larger min window
    else:
        raise ValueError("Invalid timeframe format.")

    # Print for debugging
    print(f"Max Window: {max_window}, Min Window: {min_window}")

    # Ensure dates list is long enough
    if len(dates) <= min_window:
        raise ValueError("Not enough data points to create a valid window.")

    # Select a random left index ensuring room for max_window
    left = np.random.randint(0, len(dates) - max_window)

    # Select a random window size between min and max constraints
    window_size = np.random.randint(min_window, max_window + 1)

    # Calculate right index ensuring it does not exceed bounds
    right = min(left + window_size, len(dates) - 1)

    return left, right


def csvs_of_random_windows(timeframe, weeks, dates, num_csv):
    for i in range(num_csv):
        # Select a random symbol from the symbol list
        symbol = symbol_list[np.random.randint(0, len(symbol_list) - 1)]

        left, right = get_window_size(dates=dates, timeframe=timeframe, weeks=weeks)

        # Get the start and end dates based on the selected indices
        start_date = dates[left]
        end_date = dates[right]

        # Create a filename for the CSV file
        csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"

        # Construct the full path to the CSV file
        csv_path = os.path.join(SAVE_FOLDER, csv_filename)

        # Check if the CSV file already exists
        if os.path.exists(csv_path):
            print("file alr exists")
            return pd.read_csv(csv_path)

        # Print a message indicating the creation of a new CSV file
        print(f"🎨✨ Creating sheet #{i + 1} from {start_date} to {end_date}")

        # Fetch the historical data for the selected symbol and timeframe
        dataframe = get_historical_data(symbol, timeframe, weeks)

        # Check if the DataFrame contains enough data
        if dataframe.loc[start_date:end_date].shape[0] <= 1:
            print(
                "Skipping csv because not enough data is fetched or Start/end times are too early/late."
            )
            continue

        # Save the DataFrame to a CSV file
        dataframe.loc[start_date:end_date].to_csv(csv_path)

    # Print a message indicating the completion of the process
    print("Done boiiiiiiiii")


# Manual fetch
# get_historical_data(symbol, timeframe, weeks, "2025-03-09", "2016-01-02")

csvs_of_random_windows(timeframe=timeframe, weeks=weeks, dates=dates, num_csv=10)
