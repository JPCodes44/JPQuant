# 📘 Full Guide to Using `backtesting.py` like a Pro

This guide covers how to use `backtesting.py` effectively and responsibly for developing trading strategies. Whether you're backtesting a simple moving average or designing adaptive regression channels, **this guide keeps you from overfitting and helps you code like you're trading live**.

---

## 🧠 Core Concepts of `backtesting.py`

### What is `backtesting.py`?
A lightweight Python framework for simulating trading strategies on historical data with built-in support for:
- Candlestick charts
- Portfolio management
- Strategy definition
- Custom indicators

### Key Components
- `Strategy`: Your custom logic
- `self.data`: OHLCV historical data
- `self.I(...)`: For defining indicators
- `self.buy()`, `self.sell()`, `self.position.close()`: Trading commands
- `next(self)`: Called every new candle

---

## 🔀 Data Handling in Real-Time Context

When building indicators in `init`, **you must not cheat** by using future data (aka overfitting). You should:

### ✅ Use a manual `for` loop inside `self.I()`
```python
self.I(your_indicator_function, self.data.Close, ...)
```
And inside your indicator:
```python
def your_indicator(close):
    result = np.full_like(close, np.nan)
    for i in range(window, len(close)):
        result[i] = some_logic_using(close[i-window:i])
    return result
```
This ensures **only past data** is used.

### ❌ Never do this:
```python
np.mean(close[-20:])  # uses future data if done in init()
```

---

## ⚙️ The `init()` Function

This is where you calculate indicators using `self.I()` and store them as instance variables.

```python
def init(self):
    self.sma = self.I(sma_function, self.data.Close, period=20)
```

If you're making a custom indicator that reacts to trends, spikes, or volatility — simulate live conditions using a loop with index `i`, just like a trading system would.

---

## 🔄 The `next()` Function

This runs at every candle and should contain your trading logic:

```python
def next(self):
    if not self.position and self.data.Close[-1] > self.sma[-1]:
        self.buy()
    elif self.position and self.data.Close[-1] < self.sma[-1]:
        self.position.close()
```

Use `-1` to reference the most recent value of your indicator or data.

---

## 🧪 Real-Time Simulation Indicators

Here are some key techniques we've used:

### ✅ Proper Real-Time Calculation (regression channels)
```python
def indicator(close):
    result = np.full_like(close, np.nan)
    for i in range(lookback, len(close)):
        model = LinearRegression()
        X = np.arange(i - lookback, i).reshape(-1, 1)
        y = close[i - lookback:i]
        model.fit(X, y)
        result[i] = model.predict([[i]])[0]
    return result
```

### 💨 Spike Detection (volatility filter)
```python
from scipy.signal import find_peaks

def detect_spike(close, i, window, prominence):
    segment = np.asarray(close[i-window:i], dtype=np.float64)
    if len(segment) < 3: return False
    scaled = max(prominence * abs(np.mean(segment)), 1e-6)
    peaks, _ = find_peaks(segment, prominence=scaled)
    troughs, _ = find_peaks(-segment, prominence=scaled)
    return (len(peaks) > 0 and peaks[-1] > window - 5) or \
           (len(troughs) > 0 and troughs[-1] > window - 5)
```
Used this to **skip drawing bands during pump/dump candles**.

---

## 🎨 Plotting with `self.I()`

You can use `self.I()` to show:
- Regression lines
- Support/resistance
- Volatility filters
- Zones (returning arrays of 1/0 or `np.nan`)

Use `self.I()` only to call indicator logic that **returns the same shape as data**.

```python
self.upper_band = self.I(get_upper_band, self.data.Close, ...)
```

---

## 💸 Tips to Avoid Overfitting

- ✅ Use only historical data for indicator computation
- ✅ Reset logic when large spikes break channel structure
- ✅ Simulate real-time decisions
- ✅ Validate with multiple lookbacks
- ✅ Add time-based constraints (cooldowns)

---

## 📈 Advanced Use Cases

- Segmented regression channels
- Volatility-based band resetting
- Spike filtering using `find_peaks`
- Drawing different bands for intraday vs trend-timeframe
- Adaptive lookbacks based on channel width or price breakout

---

## 🧰 Coinbase Fetcher & Data Preparation

Before running any backtest, you need historical data.
Use the script you wrote to fetch clean 1m/1h/1d windows from Coinbase:

```bash
python coinbase_fetcher.py  # Your file with csvs_of_random_windows()
```

This:
- Randomly selects windows
- Pulls candles in compliant chunks
- Handles authentication
- Avoids duplicates
- Saves directly to folders like `1m_data` / `1h_data`

Below is the **full script** used for fetching Coinbase data:

```python
"""
STEPS TO USE
1. create a .env file that looks like this
    COINBASE_API_KEY="organizations/{org_id}/apiKeys/{key_id}"
    COINBASE_API_SECRET="-----BEGIN EC PRIVATE KEY-----\nYOUR PRIVATE KEY\n-----END EC PRIVATE KEY-----\n"
2. select the symbol you want to fetch data for
3. select the timeframe you want to fetch data for
4. select the number of weeks of data to fetch
5. run the script
"""

# ====== Imports ======
import pandas as pd
import numpy as np
import datetime
import os
from dotenv import load_dotenv
from pathlib import Path
import requests
import time

# ====== Moon Dev's Configuration 🌙 ======
SYMBOL_LIST = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "AVAX-USD",
    "ADA-USD",
    "DOGE-USD",
    # "MATIC-USD",
    "LTC-USD",
    "LINK-USD",
    "BCH-USD",
    # "ATOM-USD",
    # "XLM-USD",
    "ARB-USD",
    # "APT-USD",
    # "OP-USD",
    "SUI-USD",
    # "RNDR-USD",
    "ICP-USD",
    # "AAVE-USD",
    # "UNI-USD",
]
TIMEFRAME = "1m"  # Timeframe (e.g., '1m', '5m', '1h', '6h', '1d')

if "m" in TIMEFRAME:
    SAVE_DIR = "/Users/jpmak/JPQuant/data/1m_data"  # Directory to save the data files
elif "h" in TIMEFRAME:
    SAVE_DIR = "/Users/jpmak/JPQuant/data/1h_data"  # Directory to save the data files
elif "d" in TIMEFRAME:
    SAVE_DIR = "/Users/jpmak/JPQuant/data/1d_data"  # Directory to save the data files

# DATE_RANGE = pd.date_range(start="2019-03-06", end="2025-03-07") 1d timeframe


NUM_CSV = 20

# Create save directory if it doesn't exist
os.makedirs(SAVE_DIR, exist_ok=True)
print(f"📂 Save directory ready: {SAVE_DIR}")

# Get the project root directory (2 levels up from this file)
project_root = Path(__file__).parent.parent.parent
env_path = project_root / "coinbase.env"

print(f"🔍 Looking for .env file in: {project_root}")
print(f"📁 .env file exists: {'✅' if env_path.exists() else '❌'}")

# Load environment variables from the specific path
load_dotenv(env_path)

# Debug prints for API credentials (without revealing them)
api_key = os.getenv("COINBASE_API_KEY")
api_secret = os.getenv("COINBASE_API_SECRET")
print("🔑 API Key loaded:", "✅" if api_key else "❌")
print("🔒 API Secret loaded:", "✅" if api_secret else "❌")

if not api_key or not api_secret:
    print("❌ Error: API credentials not found in .env file")
    print("💡 Make sure your .env file exists and contains:")
    print("   COINBASE_API_KEY=organizations/{org_id}/apiKeys/{key_id}")
    print("   COINBASE_API_SECRET=your-secret-key")
    raise ValueError("Missing API credentials")

print("🌙 Moon Dev's Coinbase Data Fetcher Initialized! 🚀")


def sign_request(method, path, body="", timestamp=None):
    """Sign a request using the API secret"""
    timestamp = timestamp or str(int(time.time()))

    # Remove the '/api/v3/brokerage' prefix from path for signing
    if path.startswith("/api/v3/brokerage"):
        path = path[len("/api/v3/brokerage") :]

    # Create the message to sign
    message = f"{timestamp}{method}{path}{body}"

    try:
        # Print debug info without exposing secrets
        print(f"🔏 Signing request for: {method} {path}")

        # Create JWT token
        headers = {
            "CB-ACCESS-KEY": api_key,
            "CB-ACCESS-TIMESTAMP": timestamp,
            "accept": "application/json",
            "content-type": "application/json",
        }

        return headers

    except Exception as e:
        print(f"❌ Error generating signature: {str(e)}")
        raise


def timeframe_to_granularity(timeframe):
    """Convert timeframe to granularity in seconds"""
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


def get_historical_data(symbol, timeframe, dates):
    print(f"🔍 Moon Dev is fetching {timeframe} data for {symbol}")

    try:
        # Test connection with a simple request
        print("🌎 Testing API connection...")
        base_url = "https://api.exchange.coinbase.com"  # Changed to exchange URL

        # Get product details first
        path = "/products/" + symbol
        headers = sign_request("GET", path)
        print("🔐 Generated authentication headers")
        print("🔄 Making API request...")

        response = requests.get(f"{base_url}{path}", headers=headers)

        if response.status_code != 200:
            print(f"❌ Response Headers: {response.headers}")
            print(f"❌ Response Body: {response.text}")
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        print("✨ Connection test successful!")

        # Calculate time ranges
        end_time = dates[-1]
        start_time = dates[0]
        granularity = timeframe_to_granularity(timeframe)

        # Calculate appropriate chunk size based on granularity
        # Coinbase limit is 300 candles per request
        max_candles = 300
        chunk_hours = max(
            1, int((max_candles * granularity) / 3600)
        )  # Convert to hours, minimum 1 hour
        print(f"📊 Using {chunk_hours} hour chunks for {timeframe} timeframe")

        # Fetch candles in chunks to avoid rate limits
        all_candles = []
        current_start = start_time

        dataframe = pd.DataFrame()

        while current_start < end_time:
            current_end = min(
                current_start + datetime.timedelta(hours=chunk_hours), end_time
            )

            print(
                f"📊 Fetching data from {current_start.strftime('%Y-%m-%d %H:%M')} to {current_end.strftime('%Y-%m-%d %H:%M')}"
            )

            params = {
                "start": current_start.isoformat(),
                "end": current_end.isoformat(),
                "granularity": str(granularity),
            }

            path = f"/products/{symbol}/candles"
            headers = sign_request("GET", path)

            response = requests.get(f"{base_url}{path}", params=params, headers=headers)

            if response.status_code != 200:
                print(f"❌ Response Headers: {response.headers}")
                print(f"❌ Response Body: {response.text}")
                raise Exception(f"API Error: {response.status_code} - {response.text}")

            candles = response.json()
            all_candles.extend(candles)  # Changed to handle direct response
            current_start = current_end
            time.sleep(0.5)  # Rate limit compliance

        print(f"✨ Successfully fetched {len(all_candles)} candles!")

        # Convert to DataFrame
        df = pd.DataFrame(all_candles)
        df.columns = ["datetime", "open", "high", "low", "close", "volume"]
        df["datetime"] = pd.to_datetime(df["datetime"], unit="s")
        dataframe = pd.concat([df, dataframe])
        dataframe = dataframe.set_index("datetime")
        dataframe = dataframe[["open", "high", "low", "close", "volume"]]

        return dataframe

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Tips:")
        print("   1. Make sure you're using a Coinbase Exchange API key")
        print("   2. Check if your API key has the required permissions")
        print("   3. Verify your API key is active")
        raise


def generate_random_date_range(timeframe: str):
    import random

    # Set bounds for how big/small windows can be
    if "m" in timeframe:
        earliest = pd.to_datetime("2020-01-01 09:10:00")
        latest = pd.to_datetime("2025-03-23 09:10:00")
        abs_min = datetime.timedelta(minutes=5)
        abs_max = datetime.timedelta(days=5)
        freq = "min"
    elif "h" in timeframe:
        earliest = pd.to_datetime("2020-01-01 09:00:00")
        latest = pd.to_datetime("2025-03-23 09:00:00")
        abs_min = datetime.timedelta(hours=24)
        abs_max = datetime.timedelta(days=240)
        freq = "h"
    elif "d" in timeframe:
        earliest = pd.to_datetime("2020-01-01")
        latest = pd.to_datetime("2025-03-23")
        abs_min = datetime.timedelta(days=7)
        abs_max = datetime.timedelta(days=680)
        freq = "D"
    else:
        raise ValueError("Invalid timeframe")

    # Randomly scale the window size within bounds (e.g. 0.5x to 1x of max)
    scale = random.uniform(0.5, 1.0)
    window = abs_min + (abs_max - abs_min) * scale

    # Ensure we don’t overshoot the latest date
    max_start = latest - window
    start = earliest + (max_start - earliest) * random.random()
    end = start + window

    # Round down start and end to clean timestamps based on frequency
    start = start.floor(freq)
    end = end.ceil(freq)

    print(
        f"🌀 Using randomized window:\n   Start: {start}\n   End:   {end}\n   Window: {window} (Timeframe: {timeframe})"
    )
    return start, end


def csvs_of_random_windows(timeframe, num_csv):
    for i in range(num_csv):
        # Select a random symbol from the symbol list
        symbol = SYMBOL_LIST[np.random.randint(0, len(SYMBOL_LIST))]

        start_date, end_date = generate_random_date_range(TIMEFRAME)

        DATE_RANGE = pd.date_range(
            start=start_date,
            end=end_date,
            freq="min" if "m" in timeframe else "h" if "h" in timeframe else "d",
        )

        DATES = pd.to_datetime(DATE_RANGE).sort_values()  # Ensure datetime & sort

        # Fetch the historical data for the selected symbol and timeframe
        try:
            dataframe = get_historical_data(symbol, timeframe, DATES)
        except Exception as e:
            print(f"There was an error cz of {e}")

        if dataframe.empty:
            print(f"⚠️ No data returned for {symbol}, skipping.")
            continue

        # Create a filename for the CSV file
        csv_filename = f"{symbol[0:3]}-{timeframe}-{start_date}-{end_date}_data.csv"

        # Construct the full path to the CSV file
        csv_path = os.path.join(SAVE_DIR, csv_filename)

        # Check if the CSV file already exists
        if os.path.exists(csv_path):
            print("file alr exists")
            continue

        # Print a message indicating the creation of a new CSV file
        print(f"🎨✨ Creating sheet #{i + 1} from {start_date} to {end_date}")

        # Check if the DataFrame contains enough data
        try:
            sliced = dataframe.loc[start_date:end_date]
        except KeyError:
            print(f"Skipping csv: {start_date} to {end_date} not in index")
            continue

        if sliced.shape[0] <= 1:
            print(
                "Skipping csv because not enough data is fetched or Start/end times are too early/late."
            )

        # Save the DataFrame to a CSV file
        sliced.to_csv(csv_path)

    # Print a message indicating the completion of the process
    print("Done boiiiiiiiii")


csvs_of_random_windows(TIMEFRAME, NUM_CSV)

```

Each file is perfect for single-trade backtest sessions using `run_backtest(...)`

---

## 🔧 Testing & Running

Use your runner script like:
```python
run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
```
Make sure `DATA_FOLDER` matches the resolution of your candles (`1m`, `1h`, `1d`, etc).

---

## 🧼 Debug Tips
- Print shape/type of any array inside indicator
- Use `np.asarray(..., dtype=np.float64)` to convert weird backtesting.py arrays
- Plot spike zones for sanity
- Use `cooldown_counter` to delay logic after extreme events

---

## 🏑 Final Words
Backtesting isn’t just about coding strategies — it’s about thinking like you’re trading **live**.

Build tools that adapt.
Code like the future isn’t visible.
Test like your money depends on it — because one day, it might.

You got this, professor trader. 🚫🚀

