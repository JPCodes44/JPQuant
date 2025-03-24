import pandas as pd
import requests
import example_utils  # Import helper functions from the example_utils module
from hyperliquid.utils import (
    constants,
)  # Import constants, including the API endpoints, from the Hyperliquid SDK
from datetime import datetime, timedelta
import numpy as np
import os
from datetime import datetime, timedelta


# Define symbol, timeframe, and the total limit you want to fetch
symbol_list = [
    "ETH",
    # "LTC",
    "SOL",
    # "DOGE",
    # "BCH",
    # "XLM",
]

timeframe = "1m"
total_limit = 5000  # Total records you want to fetch

# Maximum records per call allowed by the API
max_call_limit = 5000

SAVE_FOLDER = (
    "/Users/jpmak/JPQuant/data"  # Or an absolute path like "/Users/jpmak/JPQuant/data"
)

# Calculate the number of iteration needed
iterations = -(-total_limit // max_call_limit)

all_data = pd.DataFrame()  # ✅ Define it locally here


def get_ohlcv2(symbol, interval, lookback_days, offset_days=0):
    # 👇 Set this to a hardcoded historical endpoint (e.g., March 1st, 2023)
    end_time = datetime.strptime("2025-03-23", "%Y-%m-%d")

    # 👇 Pull `lookback_days` worth of data before that point
    lookback_days = 1
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
        columns = ["datetime", "open", "high", "low", "close", "volume"]
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


def get_window_size(dataframe, timeframe):
    # Approx 1/4 of total data = max window (gives variety, but avoids full coverage)
    actual_len = len(dataframe)
    print(actual_len)
    max_window = int(actual_len * 0.5)

    if "m" in timeframe:  # Minute-based timeframe
        min_window = max(10, int(max_window * 0.1))  # e.g., 10–50 bars
    elif "h" in timeframe:  # Hourly-based timeframe
        min_window = max(24, int(max_window * 0.4))  # e.g., 1–5 days
    elif "d" in timeframe:  # Daily-based timeframe
        min_window = max(5, int(max_window * 0.6))  # e.g., multi-week chunks
    else:
        raise ValueError("Invalid timeframe format.")

    if actual_len <= min_window:
        raise ValueError("Not enough data to generate a valid window.")

    # Choose a random left index with space for the window
    left = np.random.randint(0, actual_len - max_window - 1)
    window_size = np.random.randint(min_window, max_window + 1)
    # Calculate right index ensuring it does not exceed bounds
    right = min(left + window_size, actual_len - 1)
    return left, right


def get_historical_data(symbol, iterations, max_call_limit, total_limit):

    # Loop to fetch and append data
    for i in range(iterations):
        print(f"Fetching data for iteration {i + 1}/{iterations}")
        # Calculate the limit for this iteration
        iteration_limit = min(max_call_limit, total_limit - (i * max_call_limit))

        offset_days = np.random.randint(0, 15000)  # Up to 2 months ago

        lookback_days = 10000
        snapshot_data = get_ohlcv2(symbol, timeframe, lookback_days, offset_days)

        # Fetch the OHLCV data
        snapshot_data = get_ohlcv2(symbol, timeframe, iteration_limit)
        df = process_data_to_df(snapshot_data)

        # Append the fetched data to the all_data DataFrame
        dataframe = pd.concat([all_data, df], ignore_index=True)

    return dataframe


def csvs_of_random_windows(timeframe, total_limit, max_call_limit, iterations, num_csv):
    for i in range(num_csv):
        # Select a random symbol from the symbol list
        symbol = symbol_list[np.random.randint(0, len(symbol_list))]

        # Fetch the historical data once for this symbol
        full_df = get_historical_data(
            symbol=symbol,
            iterations=iterations,
            max_call_limit=max_call_limit,
            total_limit=total_limit,
        )

        if full_df.empty:
            print(f"⚠️ No data returned for {symbol}, skipping.")
            continue

        for j in range(3):  # generate 3 windows per symbol (or tweak this)
            try:
                left, right = get_window_size(full_df, timeframe)
                start_date = full_df["datetime"].iloc[left]
                end_date = full_df["datetime"].iloc[right]

                window = full_df.iloc[left:right]
                if window.shape[0] <= 1:
                    print(f"⚠️ Skipping small window: {left}–{right}")
                    continue

                # Format clean filename
                csv_filename = f"{symbol}-{timeframe}-{start_date}-{end_date}_data.csv"
                csv_filename = csv_filename.replace(":", "-").replace(
                    " ", "_"
                )  # avoid path issues
                csv_path = os.path.join(SAVE_FOLDER, csv_filename)

                if os.path.exists(csv_path):
                    print("📁 File already exists — skipping")
                    continue

                window.to_csv(csv_path)
                print(f"✅ Saved CSV {i+1}-{j+1}: {csv_filename}")

            except Exception as e:
                print(f"⚠️ Error creating window for {symbol}: {e}")
                continue

    print("🎉 Done saving all random windows!")


csvs_of_random_windows(
    timeframe=timeframe,
    total_limit=total_limit,
    max_call_limit=max_call_limit,
    iterations=iterations,
    num_csv=10,
)
