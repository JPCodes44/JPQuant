# Import necessary libraries for exchange access, data handling, and time operations
import ccxt  # Library for cryptocurrency exchange trading
import json  # To handle JSON data formats
import pandas as pd  # Data manipulation and analysis
import numpy as np  # Numerical computing
import dontshare_config as ds  # Module to import API keys and other sensitive configuration
from datetime import date, datetime, timezone, tzinfo  # Date and time handling
import time, schedule  # For sleep and scheduling tasks
import nice_funcs as n  # Custom module with helper functions

# Initialize the Phemex exchange client with rate limiting and API credentials
phemex = ccxt.phemex(
    {
        "enableRateLimit": True,  # Enable built-in rate limit to avoid hitting API limits
        "apiKey": ds.key,  # API key from config file
        "secret": ds.secret,  # Secret key from config file
    }
)

# Set the trading symbol and key trading parameters
symbol = "uBTCUSD"  # Trading symbol
pos_size = 30  # Position size (quantity to trade)
target = 9  # Target profit percentage gain
max_loss = -8  # Maximum acceptable loss percentage

index_pos = 3  # Index position for asset selection (adjust based on asset)

# Define the time (in seconds) between trade attempts
pause_time = 10

# Volume collection settings: volume is collected for vol_repeat times with each collection lasting vol_time seconds
vol_repeat = 11
vol_time = 5

# Parameters for order creation (e.g., Post Only order type)
params = {
    "timeInForce": "PostOnly",  # Ensures orders are posted to the order book without immediate matching
}
vol_decimal = 0.4  # Volume decimal precision (likely used in volume calculations)

# Retrieve the current ask and bid prices using a custom helper function
askbid = n.ask_bid(symbol)
ask = askbid[0]  # Current ask price (price sellers are asking)
bid = askbid[1]  # Current bid price (price buyers are bidding)
print(f"for {symbol}... ask: {ask} | bid {bid}")

# Retrieve a DataFrame containing moving average data (and other info) for the symbol on a 15-minute timeframe
# We request 289 data points (covering 3 days, as 96 intervals per day * 3 days + 1 = 289)
df_sma = n.df_sma(
    symbol, "15m", 289, 20
)  # The last parameter might indicate a 20-period SMA

# Retrieve current open positions for the given symbol
# The open_positions() function returns a tuple with details such as whether in a position, position size, etc.
open_pos = n.open_positions(symbol)

# Calculate support and resistance levels from the 'close' prices in the DataFrame
curr_support = df_sma[
    "close"
].min()  # Support is taken as the minimum close price over the period
curr_resis = df_sma[
    "close"
].max()  # Resistance is taken as the maximum close price over the period
print(f"support {curr_support} | resis {curr_resis}")


# Define the function to calculate retest conditions where new orders will be placed
def retest():
    print("creating retest number...")
    """
    The retest function determines if the current bid price breaks out above resistance or below support.
    If the bid is above the last resistance level, it's a breakout (potential long entry).
    If the bid is below the last support level, it's a breakdown (potential short entry).
    """
    # Initialize flags for breakout scenarios and price thresholds
    buy_break_out = False
    sell_break_down = False
    breakdownprice = False  # Variable to hold the calculated price level for breakdown
    breakoutprice = False  # Variable to hold the calculated price level for breakout

    # Check if the current bid price is greater than the most recent resistance level in the DataFrame
    if bid > df_sma["resis"].iloc[-1]:
        print(f"we are BREAKING UPWORDS... Buy at previous resis {curr_resis}")
        buy_break_out = True
        # Calculate a breakout price slightly above the resistance (increase by 0.1%)
        breakoutprice = int(df_sma["resis"].iloc[-1]) * 1.001
    # Else, check if the bid is below the most recent support level
    elif bid < df_sma["support"].iloc[-1]:
        print(f"we are BREAKING DOWN... Buy at previous support {curr_support}")
        sell_break_down = True
        # Calculate a breakdown price slightly below the support (decrease by 0.1%)
        breakdownprice = int(df_sma["support"].iloc[-1]) * 0.999

    # Return flags and price thresholds for further processing in the bot
    return buy_break_out, sell_break_down, breakoutprice, breakdownprice


# Define the main bot function that executes the trading logic
def bot():
    # Get the current PnL (Profit and Loss) details for the symbol
    # pnl_close returns a tuple containing pnlclose, in_pos flag, position size, and long/short info
    pnl_close = n.pnl_close(symbol)

    # Pause trading if the market is closed (using custom sleep function)
    sleep_on_close = n.sleep_on_close(symbol, pause_time)

    # Retrieve the latest ask and bid prices again before processing
    askbid = n.ask_bid(symbol)
    ask = askbid[0]
    bid = askbid[1]

    # Determine retest conditions using the retest function defined earlier
    re_test = retest()
    break_out = re_test[0]  # True if a breakout is detected
    break_down = re_test[1]  # True if a breakdown is detected
    breakoutprice = re_test[2]  # Price for breakout order (if applicable)
    breakdownprice = re_test[3]  # Price for breakdown order (if applicable)
    print(
        f"breakout {break_out} {breakoutprice} | breakdown {break_down} {breakdownprice}"
    )

    # Retrieve open position details from earlier call
    in_pos = open_pos[1]  # Whether we are already in a position
    curr_size = open_pos[2]  # Current position size
    curr_size = int(curr_size)  # Convert position size to integer
    curr_p = bid  # Use current bid price as the current price

    # Log current status of trading signals and positions
    print(
        f"for {symbol} breakout {break_out} | breakd {break_down} | inpos {in_pos} | size {curr_size} | price {curr_p}"
    )

    # If not currently in a position and the current position size is less than desired
    if (in_pos == False) and (curr_size < pos_size):
        # Cancel all open orders for the symbol to prevent conflicts
        phemex.cancel_all_orders(symbol)
        # Refresh ask and bid prices after cancellation
        askbid = n.ask_bid(symbol)
        ask = askbid[0]
        bid = askbid[1]

        # Check for a breakout condition: if true, create a BUY order
        if break_out == True:
            print("making an opening order as a BUY")
            print(f"{symbol} buy order of {pos_size} submitted @ {breakoutprice}")
            phemex.create_limit_buy_order(symbol, pos_size, breakoutprice, params)
            print("order submitted so sleeping for 2mins...")
            time.sleep(
                120
            )  # Sleep for 2 minutes to allow the order to fill or market conditions to change
        # Else, check for a breakdown condition: if true, create a SELL order
        elif break_down == True:
            print("making an opening order as a SELL")
            print(f"{symbol} sell order of {pos_size} submitted @ {breakdownprice}")
            phemex.create_limit_sell_order(symbol, pos_size, breakdownprice, params)
            print("order submitted so sleeping for 2mins...")
            time.sleep(120)
        # If neither breakout nor breakdown conditions are met, do nothing and sleep for 1 minute
        else:
            print("not submitting any orders cuz no break out or down.. sleeping 1min")
            time.sleep(60)
    else:
        # If already in a position, do not create new orders
        print("we are in position already so not making any orders")


# Schedule the bot function to run every 28 seconds
schedule.every(28).seconds.do(bot)

# Main loop: run scheduled tasks indefinitely, with basic error handling
while True:
    try:
        schedule.run_pending()  # Run any pending scheduled tasks
    except:
        # If an exception occurs (e.g., due to network issues), log it and sleep for 30 seconds before retrying
        print("++++++++++++++ MAYBE AN INTERNET PROBLEM, CODE FAILED.. sleep 30...")
        time.sleep(30)
