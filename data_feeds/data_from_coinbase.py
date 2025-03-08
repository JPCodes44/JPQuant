import pandas as pd
import datetime
import os
import ccxt
import dont_share as d
import coinbase_dont_share as c
from math import ceil

symbol = "BTC/USD"
timeframe = "1d"
weeks = 480
start_date = "2018-03-15"
end_date = "2020-01-04"
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


def get_historical_data(symbol, timeframe, weeks, start_date, end_date):

    # If you want to re-use the same naming logic, you can do:
    csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"

    # Construct the full path to the CSV file using os.path.join
    csv_path = os.path.join(SAVE_FOLDER, csv_filename)

    if os.path.exists(f"{symbol}{timeframe}{weeks}.csv"):
        return pd.read_csv(f"{symbol}{timeframe}{weeks}.csv")

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

    # Instead of writing to the root, write to csv_path
    dataframe.loc[start_date:end_date].to_csv(csv_path)

    return dataframe


# Print the DataFrame returned by get_historical_data()
print(get_historical_data(symbol, timeframe, weeks, start_date, end_date))
