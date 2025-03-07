# Import necessary libraries
import pandas as pd
import backtesting as bt
from backtesting import Backtest, Strategy
from ta.momentum import StochRSIIndicator
import pandas_ta as ta
import warnings
from backtesting.lib import crossover

# Filter all warnings
warnings.filterwarnings("ignore")

# Import API keys from a separate file
import key_file as k
import ccxt

# Define a factor for scaling prices and volumes
factor = 1000


# Define a custom trading strategy class
class Strat(Strategy):
    # Define strategy parameters
    rsi_window = 14  # Window size for RSI calculation
    stochrsi_smooth1 = 3  # Smoothing factor 1 for Stochastic RSI
    stochrsi_smooth2 = 3  # Smoothing factor 2 for Stochastic RSI
    bbands_length = 20  # Length for Bollinger Bands
    stochrsi_length = 14  # Length for Stochastic RSI
    bbands_std = 2  # Standard deviation for Bollinger Bands

    # Initialize indicators
    def init(self):
        self.bbands = self.I(bands, self.data)  # Bollinger Bands
        self.stoch_rsi_k = self.I(stoch_rsi_k, self.data)  # Stochastic RSI %K
        self.stoch_rsi_d = self.I(stoch_rsi_d, self.data)  # Stochastic RSI %D
        self.buy_price = 0  # Initialize buy price

    # Define the logic for each step
    def next(self):
        lower = self.bbands[0]  # Lower Bollinger Band
        mid = self.bbands[1]  # Middle Bollinger Band
        upper = self.bbands[2]  # Upper Bollinger Band

        # Check for entry long positions
        if self.data.Close[-1] > lower[-1] and crossover(
            self.stoch_rsi_k, self.stoch_rsi_d
        ):
            self.buy(
                size=0.05, sl=self.data.Close[-1] * 0.85, tp=self.data.Close[-1] * 1.40
            )
            self.buy_price = self.data.Close[-1]  # Update buy price


# Fetch historical OHLCV data from Phemex exchange
def fetch_data(symbol, timeframe, limit=200):
    exchange = ccxt.phemex(
        {
            "apiKey": k.key,  # API key for authentication
            "secret": k.secret,  # Secret key for authentication
            "enableRateLimit": True,  # Enable rate limiting
        }
    )
    since = exchange.milliseconds() - (
        limit * 60 * 60 * 1000
    )  # Calculate the start time
    ohlcv = exchange.fetch_ohlcv(
        symbol, timeframe, since=since, limit=limit
    )  # Fetch OHLCV data
    print(ohlcv)
    df = pd.DataFrame(
        ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )  # Create DataFrame
    df["timestamp"] = pd.to_datetime(
        df["timestamp"], unit="ms"
    )  # Convert timestamp to datetime
    df.set_index("timestamp", inplace=True)  # Set timestamp as index
    df.columns = ["Open", "High", "Low", "Close", "Volume"]  # Rename columns
    return df


# Calculate Bollinger Bands
def bands(data):
    bbands = ta.bbands(
        close=data.Close.s, length=20, std=2
    )  # Calculate Bollinger Bands
    return bbands.to_numpy().T  # Convert to numpy array and transpose


# Calculate Stochastic RSI %K
def stoch_rsi_k(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)  # Calculate Stochastic RSI
    return stochrsi["STOCHRSIk_14_14_3_3"].to_numpy()  # Return %K values as numpy array


# Calculate Stochastic RSI %D
def stoch_rsi_d(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)  # Calculate Stochastic RSI
    return stochrsi["STOCHRSId_14_14_3_3"].to_numpy()  # Return %D values as numpy array


# Fetch data for BTC/USD on a 1-hour timeframe
data_df = fetch_data(symbol="BTCUSD", timeframe="1h", limit=100)
data_df.Open /= factor  # Scale Open prices
data_df.High /= factor  # Scale High prices
data_df.Low /= factor  # Scale Low prices
data_df.Close /= factor  # Scale Close prices
data_df.Volume *= factor  # Scale Volume

print(data_df.tail())  # Print the last few rows of the DataFrame

# Run backtest with the custom strategy
bt = Backtest(data_df, Strat, cash=1000000, commission=0.001)
stats = bt.run()  # Run the backtest
bt.plot()  # Plot the backtest results
print(stats)  # Print the backtest statistics
