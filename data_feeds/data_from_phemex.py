import pandas as pd  # Import pandas for data manipulation and analysis
import datetime  # Import datetime for handling date and time
import os  # Import os for interacting with the operating system
import ccxt  # Import ccxt for cryptocurrency trading library
import random  # Import random for generating random numbers
import warnings  # Import warnings to handle warning messages
import numpy as np  # Import numpy for numerical operations
import key_file as k  # Import key_file for API keys
from math import ceil  # Import ceil for rounding up numbers

# Set the trading pair and timeframe
symbol = "ETHUSD"  # Use the format expected by Phemex (without a slash)
timeframe = "1d"  # 1-day candles
weeks = 200  # Number of weeks of data to fetch
date_range = pd.date_range(start="2017-01-02", end="2024-08-14")  # Full year of dates
dates = np.array(date_range)  # Convert to NumPy array for indexing

dates = pd.to_datetime(dates)  # Convert dates to datetime format
print(dates)  # Print the dates
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


def get_historical_data(symbol, timeframe, weeks, start_date, end_date):
    """
    Fetches historical OHLCV data from Phemex testnet for the given symbol and timeframe.
    It then saves the data as a CSV file in the SAVE_FOLDER.
    """

    # Create the filename based on symbol, timeframe, and weeks
    csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"

    # Construct the full path to the CSV file in the specified SAVE_FOLDER
    csv_path = os.path.join(SAVE_FOLDER, csv_filename)

    # Check if the CSV file already exists
    if os.path.exists(csv_path):
        print("file already exists")
        # If the file exists, read the CSV file and return the DataFrame
        return pd.read_csv(csv_path)

    # Get the current UTC time
    now = datetime.datetime.utcnow()

    # Initialize the Phemex exchange using ccxt with your testnet credentials
    phemex = ccxt.phemex(
        {
            "apikey": k.key,  # Replace with your testnet API key from key_file module
            "secret": k.secret,  # Replace with your testnet secret key
            "enableRateLimit": True,
        }
    )
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

        # Remove any columns that are entirely empty or contain only NA values
        df_clean = df.dropna(axis=1, how="all")
        dataframe_clean = dataframe.dropna(axis=1, how="all")
        # Concatenate the current batch with the previously fetched data
        dataframe = pd.concat([df_clean, dataframe_clean])

    # Set 'datetime' as the DataFrame index and order columns properly
    dataframe = dataframe.set_index("datetime")
    dataframe = dataframe[["open", "high", "low", "close", "volume"]]
    print(dataframe)  # Print the dataframe
    # Save the combined DataFrame to CSV in the specified folder
    dataframe = dataframe[~dataframe.index.duplicated(keep="first")]
    dataframe.loc[start_date:end_date].to_csv(csv_path)

    return dataframe


def csvs_of_random_windows(symbol, timeframe, weeks, dates, num_csv):
    for i in range(num_csv):
        # Choose left index randomly
        left = np.random.randint(0, len(dates) - 1)  # Ensures space for right

        # Choose right index randomly (always > left)
        right = np.random.randint(left + 1, len(dates))  # Ensures left < right

        start_date = dates[left]
        end_date = dates[right]

        print(f"🎨✨ Creating sheet #{i + 1} from {start_date} to {end_date}")
        get_historical_data(symbol, timeframe, weeks, start_date, end_date)
    print("Done boiiiiiiiii")


# Generate CSVs of random windows
csvs_of_random_windows(
    symbol=symbol, timeframe=timeframe, weeks=weeks, dates=dates, num_csv=10
)
