import pandas as pd  # Import pandas for data manipulation and analysis
import datetime  # Import datetime for handling date and time
import os  # Import os for interacting with the operating system
import ccxt  # Import ccxt for cryptocurrency trading library
import warnings  # Import warnings to handle warning messages
import numpy as np  # Import numpy for numerical operations
import key_file as k  # Import key_file for API keys
from math import ceil  # Import ceil for rounding up numbers

# Set the trading pair and timeframe
symbol = "ADAUSD"  # Use the format expected by Phemex (without a slash)
timeframe = "1d"  # 1-day candles
weeks = 680  # Number of weeks of data to fetch
date_range = pd.date_range(start="2020-01-02", end="2025-02-14")  # Full year of dates
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

        df_clean = df.dropna(
            axis=1, how="all"
        )  # Remove any columns that are entirely empty or contain only NA values
        dataframe_clean = dataframe.dropna(
            axis=1, how="all"
        )  # Remove any columns that are entirely empty or contain only NA values
        dataframe = pd.concat(
            [df_clean, dataframe_clean]
        )  # Concatenate the current batch with the previously fetched data

    dataframe = dataframe.set_index("datetime")  # Set 'datetime' as the DataFrame index
    dataframe = dataframe[
        ["open", "high", "low", "close", "volume"]
    ]  # Order columns properly
    dataframe = dataframe[
        ~dataframe.index.duplicated(keep="first")
    ]  # Remove duplicate indices

    return dataframe  # Return the combined DataFrame


def csvs_of_random_windows(symbol, timeframe, weeks, dates, num_csv):
    for i in range(num_csv):
        left = np.random.randint(0, len(dates) - 2)  # Choose left index randomly
        right = np.random.randint(
            left + 1, len(dates) - 1
        )  # Choose right index randomly (always > left)

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

        if (
            dataframe.loc[start_date:end_date].shape[0] <= 1
        ):  # Check if the DataFrame is empty or contains only column titles
            print(
                "Skipping csv because not enough data is fetched or Start/end times are too early/late."
            )
            continue

        dataframe.loc[start_date:end_date].to_csv(
            csv_path
        )  # Write the DataFrame to CSV
    print("Done boiiiiiiiii")


# Generate CSVs of random windows
csvs_of_random_windows(
    symbol=symbol, timeframe=timeframe, weeks=weeks, dates=dates, num_csv=10
)
