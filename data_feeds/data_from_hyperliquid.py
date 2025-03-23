import pandas as pd
import requests
import example_utils  # Import helper functions from the example_utils module
from hyperliquid.utils import (
    constants,
)  # Import constants, including the API endpoints, from the Hyperliquid SDK
from datetime import datetime, timedelta


# Define symbol, timeframe, and the total limit you want to fetch
symbol = "ETH"
timeframe = "2h"
total_limit = 5000  # Total records you want to fetch

# Maximum records per call allowed by the API
max_call_limit = 5000

# Calculate the number of iteration needed
iterations = -(-total_limit // max_call_limit)

# Initialize an empty DataFrame to append fetched data
all_data = pd.DataFrame()


def get_ohlcv2(symbol, interval, lookback_days):
    # Get the end_time of now
    end_time = datetime.now()
    # start time being the time now minus the time looking back
    start_time = end_time - timedelta(days=lookback_days)

    # hyperliquid info url
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    # data params for the snapshot_data dataframe
    data = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
        },
    }
    # makes a POST request with the hyperliquid url and gets the response
    # as a json file (table) for the snapshot_data
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        snapshot_data = response.json()
        return snapshot_data
    else:
        # data params not sufficent enough
        print(f"Error fetching data for {symbol}: {response.status_code}")
        return None


def process_data_to_df(snapshot_data):
    if snapshot_data:
        # Assuming the response contains a list of candles
        columns = ["timestamp", "open", "high", "low", "close", "volume"]
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.fromtimestamp(snapshot["t"] / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            open_price = snapshot["o"]
            high_price = snapshot["h"]
            low_price = snapshot["l"]
            close_price = snapshot["c"]
            volume = snapshot["v"]
            data.append(
                [timestamp, open_price, high_price, low_price, close_price, volume]
            )

        df = pd.DataFrame(data, columns=columns)

        return df
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data


def get_window_size(timeframe, total_limit):
    # Define the minimum window length based on the timeframe
    if "m" in timeframe:
        # Define the maximum window length in days
        max_window = int(total_limit/)
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


def csvs_of_random_windows(iterations, timeframe):
    # Loop to fetch and append data
    for i in range(iterations):
        print(f"Fetching data for iteration {i + 1}/{iterations}")
        # Calculate the limit for this iteration
        iteration_limit = min(max_call_limit, total_limit - (i * max_call_limit))

        # Fetch the OHLCV data
        snapshot_data = get_ohlcv2(symbol, timeframe, iteration_limit)
        df = process_data_to_df(snapshot_data)

        # Append the fetched data to the all_data DataFrame
        all_data = pd.concat([all_data, df], ignore_index=True)

    # Construct the file path using the symbol, timeframe, and total_limit
    file_path = f"{symbol}_{timeframe}_{total_limit}.csv"

    # Save the concatenated DataFrame to CSV
    all_data.to_csv(file_path, index=False)

    print(all_data)

    print(f"Data saved to {file_path}")
