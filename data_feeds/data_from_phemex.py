import pandas as pd
import datetime
import os
import ccxt
import dont_share as d  # Module containing your API keys for one exchange (or settings)
import coinbase_dont_share as c  # Module containing your API keys (likely for Phemex testnet)
from math import ceil

# Set the trading pair and timeframe
symbol = "ETHUSD"  # Use the format expected by Phemex (without a slash)
timeframe = "1d"  # 1-day candles
weeks = 219  # Number of weeks of data to fetch

# Specify the folder where the CSV file will be saved
SAVE_FOLDER = "/Users/jpmak/JPQuant/data"


def timeframe_to_sec(timeframe):
    """
    Converts a timeframe string (e.g., '1d', '15m', '1h') to seconds.
    """
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
    """
    Fetches historical OHLCV data from Phemex testnet for the given symbol and timeframe.
    It then saves the data as a CSV file in the SAVE_FOLDER.
    """

    # Create the filename based on symbol, timeframe, and weeks
    csv_filename = f"{symbol[0:3]}-{timeframe}-{weeks}wks_data.csv"

    # Construct the full path to the CSV file in the specified SAVE_FOLDER
    csv_path = os.path.join(SAVE_FOLDER, csv_filename)

    # # If the CSV already exists, read and return the data from the file
    # if os.path.exists(csv_path):
    #     return pd.read_csv(csv_path)

    # Get the current UTC time
    now = datetime.datetime.utcnow()

    # Initialize the Phemex exchange using ccxt with your testnet credentials
    phemex = ccxt.phemex(
        {
            "apikey": c.key,  # Replace with your testnet API key from coinbase_dont_share module
            "secret": c.secret,  # Replace with your testnet secret key
            "enableRateLimit": True,
        }
    )
    # Enable sandbox mode for testnet
    # Convert the timeframe (e.g., "1d") to seconds for API calculations
    granularity = timeframe_to_sec(timeframe)

    # Calculate the total time in seconds for the given number of weeks
    total_time = weeks * 7 * 24 * 60 * 60
    # Determine how many batches of 200 candles are needed
    run_times = ceil(total_time / (granularity * 200))

    # Initialize an empty DataFrame to accumulate all fetched data
    dataframe = pd.DataFrame()

    for i in range(run_times):
        # Calculate the 'since' timestamp for this batch (in UTC)
        since = now - datetime.timedelta(seconds=granularity * 200 * (i + 1))
        since_timestamp = int(since.timestamp()) * 1000  # Convert to milliseconds

        # Fetch OHLCV data with a limit of 200 bars starting from 'since_timestamp'
        data = phemex.fetch_ohlcv(symbol, timeframe, since=since_timestamp, limit=200)
        # Create a DataFrame from the fetched data and name the columns accordingly
        df = pd.DataFrame(
            data, columns=["datetime", "open", "high", "low", "close", "volume"]
        )
        # Convert the timestamp column from milliseconds to a datetime object
        df["datetime"] = pd.to_datetime(df["datetime"], unit="ms")

        # # Remove any columns that are entirely empty or contain only NA values
        df_clean = df.dropna(axis=1, how="all")
        dataframe_clean = dataframe.dropna(axis=1, how="all")
        # # Concatenate the current batch with the previously fetched data
        dataframe = pd.concat([df_clean, dataframe_clean])

    # Set 'datetime' as the DataFrame index and order columns properly
    dataframe = dataframe.set_index("datetime")
    dataframe = dataframe[["open", "high", "low", "close", "volume"]]

    # Save the combined DataFrame to CSV in the specified folder
    dataframe.to_csv(csv_path)

    return dataframe


# Print the DataFrame returned by get_historical_data()
print(get_historical_data(symbol, timeframe, weeks))
