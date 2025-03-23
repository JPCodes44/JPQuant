import pandas as pd  # Import pandas for data manipulation and analysis
import datetime  # Import datetime for handling date and time
import os  # Import os for interacting with the operating system
import ccxt  # Import ccxt for cryptocurrency trading library
import warnings  # Import warnings to handle warning messages
import numpy as np  # Import numpy for numerical operations
import key_file as k  # Import key_file for API keys
from math import ceil  # Import ceil for rounding up numbers

# Set the trading pair and timeframe
symbol_list = [
    "ETHUSD",
    "LTCUSD",
    "BCHUSD",
    "LINKUSD",
    "DOTUSD",
    "ADAUSD",
    "XRPUSD",
    "SOLUSD",
    "DOGEUSD",
    "MATICUSD",
    "ALGOUSD",
    "ATOMUSD",
    "EOSUSD",
    "TRXUSD",
]
timeframe = "1m"  # 1-day candles
weeks = 7  # Number of weeks of data to fetch
# date_range = pd.date_range(start="2019-01-02", end="2025-02-14")  # Full year of dates
# for 1m timeframe
date_range = pd.date_range(
    start="2024-12-12 09:10:00", end="2025-03-14 16:00:00", freq="min"
)

dates = np.array(date_range)  # Convert to NumPy array for indexing
dates = pd.to_datetime(dates)  # Convert dates to datetime format
# Suppress only DeprecationWarnings
warnings.simplefilter("ignore", category=DeprecationWarning)

# Suppress only FutureWarnings
warnings.simplefilter(action="ignore", category=FutureWarning)

# Specify the folder where the CSV file will be saved
SAVE_FOLDER = "/Users/jpmak/JPQuant/data"


def timeframe_to_sec(timeframe):
    """
    Converts a timeframe string (e.g., '1d', '15m', '1h') to seconds.
    """
    if "m" in timeframe:  # Check if timeframe is in minutes
        return int("".join([char for char in timeframe if char.isnumeric()])) * 60
    elif "h" in timeframe:  # Check if timeframe is in hours
        return int("".join([char for char in timeframe if char.isnumeric()])) * 60 * 60
    elif "d" in timeframe:  # Check if timeframe is in days
        return (
            int("".join([char for char in timeframe if char.isnumeric()]))
            * 24
            * 60
            * 60
        )


def get_window_size(dates, weeks, timeframe):

    # Define the minimum window length based on the timeframe
    if "m" in timeframe:
        # Define the maximum window length in days
        max_window = int(weeks * 7 * 24 * 60)
        min_window = int(
            max_window * 0.02
        )  # Very short since minutes have high data frequency
    elif "h" in timeframe:
        # Define the maximum window length in hours
        max_window = int(weeks * 7 * 24)
        min_window = int(
            max_window * 0.4
        )  # Hours are slower than minutes but still frequent
    elif "d" in timeframe:
        # Define the maximum window length in days
        max_window = int(weeks * 7)
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


def get_historical_data(symbol, timeframe, weeks):
    """
    Fetches historical OHLCV data from Phemex testnet for the given symbol and timeframe.
    It then saves the data as a CSV file in the SAVE_FOLDER.
    """
    now = datetime.datetime.utcnow()  # Get the current UTC time

    # Initialize the Phemex exchange using ccxt with your testnet credentials
    phemex = ccxt.phemex(
        {
            "apikey": k.key,  # Replace with your testnet API key from key_file module
            "secret": k.secret,  # Replace with your testnet secret key
            "enableRateLimit": True,
        }
    )
    granularity = timeframe_to_sec(timeframe)  # Convert the timeframe to seconds

    total_time = (
        weeks * 7 * 24 * 60 * 60
    )  # Calculate the total time in seconds for the given number of weeks
    run_times = ceil(
        total_time / (granularity * 200)
    )  # Determine how many batches of 200 candles are needed

    dataframe = (
        pd.DataFrame()
    )  # Initialize an empty DataFrame to accumulate all fetched data

    for i in range(run_times):
        since = now - datetime.timedelta(
            seconds=granularity * 200 * (i + 1)
        )  # Calculate the 'since' timestamp for this batch (in UTC)
        since_timestamp = int(since.timestamp()) * 1000  # Convert to milliseconds

        data = phemex.fetch_ohlcv(
            symbol, timeframe, since=since_timestamp, limit=200
        )  # Fetch OHLCV data with a limit of 200 bars starting from 'since_timestamp'

        df = pd.DataFrame(
            data, columns=["datetime", "open", "high", "low", "close", "volume"]
        )  # Create a DataFrame from the fetched data and name the columns accordingly
        df["datetime"] = pd.to_datetime(
            df["datetime"], unit="ms"
        )  # Convert the timestamp column from milliseconds to a datetime object
        dataframe = pd.concat(
            [df, dataframe]
        )  # Concatenate the current batch with the previously fetched data

    dataframe = dataframe.set_index("datetime")  # Set 'datetime' as the DataFrame index
    dataframe = dataframe[
        ["open", "high", "low", "close", "volume"]
    ]  # Order columns properly

    return dataframe  # Return the combined DataFrame


def csvs_of_random_windows(timeframe, weeks, dates, num_csv):
    for i in range(num_csv):
        symbol = symbol_list[np.random.randint(0, len(symbol_list) - 1)]

        left, right = get_window_size(dates=dates, timeframe=timeframe, weeks=weeks)

        start_date = dates[left]  # Set start date
        end_date = dates[right]  # Set end date

        csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"  # Create the filename based on symbol, timeframe, and weeks
        csv_path = os.path.join(
            SAVE_FOLDER, csv_filename
        )  # Construct the full path to the CSV file in the specified SAVE_FOLDER

        if os.path.exists(csv_path):  # Check if the CSV file already exists
            print("file already exists")
            continue

        print(f"🎨✨ Creating sheet #{i + 1} from {start_date} to {end_date}")

        # Fetch historical data
        dataframe = get_historical_data(symbol, timeframe, weeks)

        # Check if the DataFrame is empty or contains only column titles
        if dataframe.loc[start_date:end_date].shape[0] <= 1:
            print(
                "Skipping csv because not enough data is fetched or Start/end times are too early/late."
            )
            continue

        dataframe.loc[start_date:end_date].to_csv(
            csv_path
        )  # Write the DataFrame to CSV
    print("Done boiiiiiiiii")


# Manual fetch
# get_historical_data(symbol, timeframe, weeks, "2025-03-09", "2016-01-02")

# Generate CSVs of random windows
csvs_of_random_windows(timeframe=timeframe, weeks=weeks, dates=dates, num_csv=10)
