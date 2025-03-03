############# Coding trading bot #1 - sma bot w/ob data 2024

import ccxt  # Import ccxt for interacting with crypto exchanges
import pandas as pd  # Import pandas for data manipulation
import numpy as np  # Import numpy for numerical operations
import dontshare_config as ds  # Import your configuration file containing your API keys
from datetime import (
    date,
    datetime,
    timezone,
    tzinfo,
)  # Import datetime functions for time handling
import time, schedule  # Import time for sleeping and schedule for scheduling bot tasks


# Initialize the Phemex exchange instance for testnet using your API keys and enabling rate limits.
phemex = ccxt.phemex(
    {
        "apiKey": ds.key,  # Your API key from your config
        "secret": ds.secret,  # Your secret key from your config
        "enableRateLimit": True,  # Enforce rate limiting per exchange's guidelines
        "options": {"testnet": True},  # Specify that we are using the Phemex Testnet
    }
)
phemex.set_sandbox_mode(True)  # Enable sandbox mode for testing

# Global settings
symbol = "BTC/USD"  # Trading symbol (BTC vs USDT)
pos_size = 1  # Position size for orders (example value; adjust as needed)
params = {"timeInForce": "PostOnly"}
target = 8  # Profit target percentage (e.g., exit if profit exceeds 8%)
max_loss = -9  # Maximum allowable loss percentage (e.g., exit if loss reaches -9%)
vol_decimal = 0.4  # Volume decimal threshold for decision making


# -----------------------------
# Function: ask_bid
# Purpose: Fetch the current order book and return the best ask and bid prices.
def ask_bid():
    ob = phemex.fetch_order_book(
        symbol
    )  # Fetch order book data for the specified symbol
    bid = ob["bids"][0][0]  # Get the best bid price (first price in the bids list)
    ask = ob["asks"][0][0]  # Get the best ask price (first price in the asks list)
    return ask, bid  # Return tuple: (ask, bid)


# -----------------------------
# Function: daily_sma
# Purpose: Fetch daily OHLCV data, calculate a 20-day Simple Moving Average (SMA),
#          and generate a trading signal (BUY/SELL) by comparing the SMA with the current bid.
def daily_sma():
    print("starting indis...")  # Debug print to indicate start of daily SMA process

    timeframe = "1d"  # Set timeframe to daily candles
    num_bars = 100  # Number of daily bars to fetch

    # Fetch OHLCV data for daily timeframe from Phemex
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=num_bars)
    # Create a DataFrame with the OHLCV data and assign column names
    df_d = pd.DataFrame(
        bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    # Convert timestamps from milliseconds to datetime format
    df_d["timestamp"] = pd.to_datetime(df_d["timestamp"], unit="ms")

    # Calculate the 20-day SMA on the 'close' prices and store in a new column "sma20_d"
    df_d["sma20_d"] = df_d.close.rolling(20).mean()

    # Retrieve the current best bid price using the ask_bid function
    bid = ask_bid()[1]

    # Generate a trading signal based on the SMA:
    # If SMA is greater than bid, signal is "SELL" (bearish); if less, signal is "BUY" (bullish)
    df_d.loc[df_d["sma20_d"] > bid, "sig"] = "SELL"
    df_d.loc[df_d["sma20_d"] < bid, "sig"] = "BUY"

    return df_d  # Return the daily SMA DataFrame


# -----------------------------
# Function: f15_sma
# Purpose: Fetch 15-minute OHLCV data, calculate a 20-period SMA, and create custom buy/sell price levels.
def f15_sma():
    print("starting 15 min sma...")  # Indicate start of 15-minute SMA process

    timeframe = "15m"  # Set timeframe to 15-minute candles
    num_bars = 100  # Number of bars to fetch

    # Fetch OHLCV data for 15-minute timeframe
    bars = phemex.fetch_ohlcv(symbol, timeframe=timeframe, limit=num_bars)
    # Create a DataFrame and set column names
    df_f = pd.DataFrame(
        bars, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    # Convert timestamps to readable datetime format
    df_f["timestamp"] = pd.to_datetime(df_f["timestamp"], unit="ms")

    # Calculate a 20-period SMA on the 'close' prices and store it in "sma20_15"
    df_f["sma20_15"] = df_f.close.rolling(20).mean()

    # Create price levels around the 15-minute SMA:
    # bp_1: Slightly above the SMA (for buy orders), bp_2: Slightly below the SMA (for buy orders)
    df_f["bp_1"] = df_f["sma20_15"] * 1.001
    df_f["bp_2"] = df_f["sma20_15"] * 0.997
    # sp_1: Slightly below the SMA (for sell orders), sp_2: Slightly above the SMA (for sell orders)
    df_f["sp_1"] = df_f["sma20_15"] * 0.999
    df_f["sp_2"] = df_f["sma20_15"] * 1.003

    return df_f  # Return the DataFrame with 15m SMA and custom price levels


# -----------------------------
# Function: open_positions
# Purpose: Check open positions using the account balance data.
# Returns a tuple: (all open positions, boolean indicating if a position exists,
#                    size of the open position, and whether the position is long)
def open_positions():
    params = {"type": "swap", "code": "USD"}
    phe_bal = phemex.fetch_balance(
        params=params
    )  # Fetch balance data including positions
    open_positions = phe_bal["info"]["data"]["positions"]
    # Here, we assume the first position in the list (index 0) is relevant for our symbol
    openpos_side = open_positions[0]["side"]
    openpos_size = open_positions[0]["size"]

    # Determine if there's an open position and its direction (long/short)
    if openpos_side == "Buy":
        openpos_bool = True
        long = True
    elif openpos_side == "Sell":
        openpos_bool = True
        long = False
    else:
        openpos_bool = False
        long = None

    return open_positions, openpos_bool, openpos_size, long


# -----------------------------
# Function: kill_switch
# Purpose: Continuously close open positions by canceling orders and submitting closing orders
def kill_switch():
    print("starting the kill switch")
    # Get open position details: whether a position is open, if it's long, and its size
    openposi = open_positions()[1]
    long = open_positions()[3]
    kill_size = open_positions()[2]
    print(f"openposi {openposi}, long {long}, size {kill_size}")

    # Loop until there is no open position
    while openposi == True:
        print("starting kill switch loop til limit fil..")
        temp_df = (
            pd.DataFrame()
        )  # Create an empty DataFrame (potential placeholder for logging)
        print("just made a temp df")

        # Cancel all orders for the symbol before placing new ones
        phemex.cancel_all_orders(symbol)
        # Update open position details
        openposi = open_positions()[1]
        long = open_positions()[3]
        kill_size = open_positions()[2]
        kill_size = int(kill_size)  # Convert the position size to an integer

        # Fetch current bid and ask prices
        ask = ask_bid()[0]
        bid = ask_bid()[1]

        # If in a short position, submit a limit buy order to close
        if long == False:
            phemex.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f"just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}")
            print("sleeping for 30 seconds to see if it fills..")
            time.sleep(30)
        # If in a long position, submit a limit sell order to close
        elif long == True:
            phemex.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f"just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}")
            print("sleeping for 30 seconds to see if it fills..")
            time.sleep(30)
        else:
            print("++++++ SOMETHING I DIDNT EXCEPT IN KILL SWITCH FUNCTION")

        # Re-check if a position is still open
        openposi = open_positions()[1]


# -----------------------------
# Function: sleep_on_close
# Purpose: If the last closed order was filled very recently (within the last 59 minutes),
#          sleep for 1 minute before continuing.
def sleep_on_close():
    """
    This function checks the closed orders. If the most recent order was filled in the last 59 minutes,
    it will sleep for 60 seconds.
    """
    closed_orders = phemex.fetch_closed_orders(symbol)
    # Iterate over the closed orders in reverse order (from most recent to older)
    for ord in closed_orders[-1::-1]:
        sincelasttrade = 59  # Define threshold in minutes
        filled = False

        # Extract order status and transaction time from order info
        status = ord["info"]["ordStatus"]
        txttime = ord["info"]["transactTimeNs"]
        txttime = int(txttime)
        txttime = round(
            (txttime / 1000000000)
        )  # Convert nanoseconds to seconds (epoch time)
        print(f"this is the status of the order {status} with epoch {txttime}")
        print("next iteration...")
        print("------")

        if status == "Filled":
            print("FOUND the order with last fill..")
            print(f"this is the time {txttime} this is the orderstatus {status}")
            orderbook = phemex.fetch_order_book(symbol)
            ex_timestamp = orderbook["timestamp"]  # Exchange timestamp in ms
            ex_timestamp = int(ex_timestamp / 1000)  # Convert to seconds
            print("---- below is the transaction time then exchange epoch time")
            print(txttime)
            print(ex_timestamp)

            # Calculate time difference in minutes between exchange time and transaction time
            time_spread = (ex_timestamp - txttime) / 60

            if time_spread < sincelasttrade:
                sleepy = (
                    round(sincelasttrade - time_spread) * 60
                )  # Calculate sleep time in seconds
                sleepy_min = sleepy / 60
                print(
                    f"the time spread is less than {sincelasttrade} mins its been {time_spread}mins.. so we SLEEPING for 60 secs.."
                )
                time.sleep(60)
            else:
                print(
                    f"its been {time_spread} mins since last fill so not sleeping cuz since last trade is {sincelasttrade}"
                )
            break  # Break out of the loop after processing the most recent order
        else:
            continue

    print("done with the sleep on close function.. ")


# -----------------------------
# Function: ob
# Purpose: Fetch the order book, accumulate volume data over several iterations,
#          and determine the volume control ratio to indicate if bulls or bears are in control.
def ob():
    print("fetching order book data... ")

    df = pd.DataFrame()  # Create an empty DataFrame to accumulate data
    temp_df = pd.DataFrame()  # Temporary DataFrame for current iteration data

    ob = phemex.fetch_order_book(symbol)  # Fetch current order book
    bids = ob["bids"]  # Extract bid list
    asks = ob["asks"]  # Extract ask list

    first_bid = bids[0]  # Get first bid entry (not used later)
    first_ask = asks[0]  # Get first ask entry (not used later)

    bid_vol_list = []  # List to collect bid volumes
    ask_vol_list = []  # List to collect ask volumes

    # Loop 11 times to collect volume data over time
    for x in range(11):
        # Process bids: accumulate volumes
        for set in bids:
            price = set[0]
            vol = set[1]
            bid_vol_list.append(vol)
            sum_bidvol = sum(bid_vol_list)
            temp_df["bid_vol"] = [sum_bidvol]

        # Process asks: accumulate volumes
        for set in asks:
            price = set[0]
            vol = set[1]
            ask_vol_list.append(vol)
            sum_askvol = sum(ask_vol_list)
            temp_df["ask_vol"] = [sum_askvol]

        # Wait 5 seconds between iterations
        time.sleep(5)
        # Append the temporary DataFrame to the main DataFrame
        df = df.append(temp_df)
        print(df)
        print(" ")
        print("------")
        print(" ")
    print("done collecting volume data for bids and asks.. ")
    print("calculating the sums...")
    total_bidvol = df["bid_vol"].sum()  # Total bid volume over the iterations
    total_askvol = df["ask_vol"].sum()  # Total ask volume over the iterations
    print(f"last 1m this is total Bid Vol: {total_bidvol} | ask vol: {total_askvol}")

    # Determine which side is in control based on volume
    if total_bidvol > total_askvol:
        control_dec = total_askvol / total_bidvol
        print(f"Bulls are in control: {control_dec}...")
        bullish = True
    else:
        control_dec = total_bidvol / total_askvol
        print(f"Bears are in control: {control_dec}...")
        bullish = False

    # Check open positions and print status
    open_posi = open_positions()
    openpos_tf = open_posi[1]
    long = open_posi[3]
    print(f"openpos_tf: {openpos_tf} || long: {long}")

    # If a position exists, decide based on volume control ratio
    if openpos_tf == True:
        if long == True:
            print("we are in a long position...")
            if control_dec < vol_decimal:  # Compare control ratio with volume threshold
                vol_under_dec = True
            else:
                print("volume is not under dec so setting vol_under_dec to False")
                vol_under_dec = False
        else:
            print("we are in a short position...")
            if control_dec < vol_decimal:
                vol_under_dec = True
            else:
                print("volume is not under dec so setting vol_under_dec to False")
                vol_under_dec = False
    else:
        print("we are not in position...")

    print(vol_under_dec)
    return vol_under_dec  # Return whether the volume control condition is met


# -----------------------------
# Function: pnl_close
# Purpose: Check the profit/loss percentage for the open position and decide if it's time to exit.
# Returns a tuple: (pnlclose, in_pos, size, long)
def pnl_close():
    print("checking to see if its time to exit... ")

    params = {"type": "swap", "code": "USD"}
    pos_dict = phemex.fetch_positions(params=params)
    print(pos_dict)
    pos_dict = pos_dict[0]  # Use the first position in the list
    side = pos_dict["side"]  # Position side ("long" or "short")
    size = pos_dict["contracts"]  # Size of the position (number of contracts)
    entry_price = float(
        pos_dict["entryPrice"]
    )  # Price at which the position was opened
    leverage = float(pos_dict["leverage"])  # Leverage applied to the position

    current_price = ask_bid()[1]  # Get current best bid price

    print(f"side: {side} | entry_price: {entry_price} | lev: {leverage}")

    # Calculate the price difference based on the position type
    if side == "long":
        diff = current_price - entry_price
        long = True
    else:
        diff = entry_price - current_price
        long = False

    # Calculate the percentage profit/loss considering leverage
    try:
        perc = round(((diff / entry_price) * leverage), 10)
    except:
        perc = 0

    perc = 100 * perc  # Convert to percentage
    print(f"this is our PNL percentage: {(perc)}%")

    pnlclose = False
    in_pos = False

    # Determine if the position is winning
    if perc > 0:
        in_pos = True
        print("we are in a winning postion")
        if perc > target:
            print(
                ":) :) we are in profit & hit target.. checking volume to see if we should start kill switch"
            )
            pnlclose = True
            vol_under_dec = ob()  # Check volume condition from the ob() function
            if vol_under_dec == True:
                print(
                    f"volume is under the decimal threshold we set of {vol_decimal}.. so sleeping 30s"
                )
                time.sleep(30)
            else:
                print(
                    f":) :) :) starting the kill switch because we hit our target of {target}% and already checked vol..."
                )
                kill_switch()
        else:
            print("we have not hit our target yet")
    # If the position is losing money
    elif perc < 0:
        in_pos = True
        if perc <= max_loss:
            print(
                f"we need to exit now down {perc}... so starting the kill switch.. max loss {max_loss}"
            )
            kill_switch()
        else:
            print(
                f"we are in a losing position of {perc}.. but chillen cause max loss is {max_loss}"
            )
    else:
        print("we are not in position")

    # If there is a position, perform additional stop loss checks based on 15m SMA
    if in_pos == True:
        df_f = f15_sma()  # Get 15m SMA data
        last_sma15 = df_f.iloc[-1][
            "sma20_15"
        ]  # Get the last SMA value from the 15m data
        last_sma15 = int(last_sma15)
        print(last_sma15)
        curr_bid = ask_bid()[1]  # Get current bid price
        curr_bid = int(curr_bid)
        print(curr_bid)
        sl_val = last_sma15 * 1.008  # Set stop loss value as 0.8% above last SMA value
        print(sl_val)
        # Additional stop loss conditions could be added here if needed
    else:
        print("we are not in position.. ")

    print("just finished checking PNL close..")
    return pnlclose, in_pos, size, long


# -----------------------------
# Function: bot
# Purpose: Main trading function that checks pnl, sleeps if needed, and opens new orders if not already in position.
def bot():
    pnl_close()  # Check if conditions for closing the position are met
    sleep_on_close()  # Check if we need to pause based on recent closed orders

    df_d = daily_sma()  # Fetch daily SMA data for determining long/short signals
    df_f = f15_sma()  # Fetch 15-minute SMA data for price levels
    ask = ask_bid()[0]  # Get current ask price
    bid = ask_bid()[1]  # Get current bid price

    # Determine the signal from daily SMA data (BUY/SELL)
    sig = df_d.iloc[-1]["sig"]

    open_size = pos_size / 2  # Define order size as half the position size

    # Check if we're already in a position
    in_pos = pnl_close()[1]
    print(in_pos)
    curr_size = open_positions()[2]
    curr_size = int(curr_size)
    print(curr_size)

    curr_p = bid
    last_sma15 = df_f.iloc[-1]["sma20_15"]

    # If not in position and current position size is less than desired position size
    if (in_pos == False) and (curr_size < pos_size):
        phemex.cancel_all_orders(symbol)

        # If signal is BUY and current price is above last 15m SMA value
        if (sig == "BUY") and (curr_p > last_sma15):
            print("making an opening order as a BUY")
            bp_1 = df_f.iloc[-1]["bp_1"]
            bp_2 = df_f.iloc[-1]["bp_2"]
            print(f"this is bp_1: {bp_1} this is bp_2: {bp_2}")
            phemex.cancel_all_orders(symbol)
            phemex.create_limit_buy_order(symbol, open_size, bp_1, params)
            phemex.create_limit_buy_order(symbol, open_size, bp_2, params)
            print("just made opening order so going to sleep for 2mins..")
            time.sleep(120)
        # If signal is SELL and current price is below last 15m SMA value
        elif (sig == "SELL") and (curr_p < last_sma15):
            print("making an opening order as a SELL")
            sp_1 = df_f.iloc[-1]["sp_1"]
            sp_2 = df_f.iloc[-1]["sp_2"]
            print(f"this is sp_1: {sp_1} this is sp_2: {sp_2}")
            phemex.cancel_all_orders(symbol)
            phemex.create_limit_sell_order(symbol, open_size, sp_1, params)
            phemex.create_limit_sell_order(symbol, open_size, sp_2, params)
            print("just made opening order so going to sleep for 2mins..")
            time.sleep(120)
        else:
            print(
                "not submitting orders.. price prob higher or lower than sma.. 10m sleep..."
            )
            time.sleep(600)
    else:
        print("we are in position already so not making new orders..")


# -----------------------------
# Schedule the bot to run every 28 seconds.
schedule.every(28).seconds.do(bot)
while True:
    schedule.run_pending()

# Run the scheduled tasks continuously in a loop.
# while True:
#     try:
#         schedule.run_pending()
#     except:
#         print("+++++ MAYBE AN INTERNET PROB OR SOMETHING")
#         time.sleep(30)
