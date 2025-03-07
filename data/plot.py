import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc

# Path to your CSV file
data_path = "/Users/jpmak/JPQuant/data/ETH-1d-480wks_data.csv"

# Load the CSV file into a DataFrame, parsing the datetime column
df = pd.read_csv(data_path, index_col=0, parse_dates=True)

# Ensure column names are capitalized: "Datetime", "Open", "High", "Low", "Close", "Volume"
df.columns = [col.capitalize() for col in df.columns]
df.dropna(inplace=True)

# Reset index to turn the datetime index into a column
df_reset = df.reset_index()

# Rename the datetime column to "Datetime" (if not already)
df_reset.rename(columns={"index": "datetime"}, inplace=True)

# Convert the "Datetime" column into a numerical format required by matplotlib for candlestick plotting
df_reset["DateNum"] = df_reset["datetime"].map(mdates.date2num)

# Create an array of OHLC values needed for the candlestick plot
# The required format is: [DateNum, Open, High, Low, Close]
ohlc = df_reset[["DateNum", "Open", "High", "Low", "Close"]].values

# Create the plot
fig, ax = plt.subplots(figsize=(12, 6))
candlestick_ohlc(ax, ohlc, width=0.6, colorup="green", colordown="red", alpha=0.8)

# Format the x-axis to display dates properly
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
plt.xticks(rotation=45)

# Add titles and labels
plt.title("Candlestick Chart")
plt.xlabel("Date")
plt.ylabel("Price")

plt.tight_layout()
plt.show()
