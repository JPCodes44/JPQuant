################### Coding Risk Management 2024

import ccxt  # Library to interact with cryptocurrency exchanges
import key_file as k  # Module that stores your API keys (e.g., k.xP_KEY, k.xP_SECRET)
import time, schedule  # 'time' for delays and 'schedule' for scheduling tasks
import pandas as pd  # Library for data manipulation and analysis

# Create a Phemex exchange instance with rate limit enabled, using your API keys.
phemex = ccxt.phemex({"enableRateLimit": True, "apiKey": k.key, "secret": k.secret})

# Define global parameters for trading
symbol = "uBTCUSD"  # Trading symbol; here it represents Bitcoin in USD (uBTCUSD)
size = 1  # Default order size
bid = 29000  # Example bid price
params = {
    "timeInForce": "PostOnly"  # Order parameter specifying that orders should be posted (i.e., not immediately matched)
}


# Function to fetch open positions for the given symbol
def open_positions(symbol=symbol):
    """
    Determines the open position for the given symbol by:
    - Selecting the correct index based on the symbol.
    - Fetching balance data from the exchange.
    - Extracting the position information.
    - Determining if there is an open position, its size, and whether it is long or short.
    """
    # Determine the index for the position based on the symbol.
    if symbol == "uBTCUSD":
        index_pos = 4
    elif symbol == "APEUSD":
        index_pos = 2
    elif symbol == "ETHUSD":
        index_pos = 3
    elif symbol == "DOGEUSD":
        index_pos = 1
    elif symbol == "u100000SHIBUSD":
        index_pos = 0
    else:
        index_pos = None

    # Set parameters for fetching balance information (swap type and currency code).
    params = {"type": "swap", "code": "USD"}
    # Fetch the balance from Phemex (this includes position data).
    phe_bal = phemex.fetch_balance(params=params)
    # Extract the list of open positions from the response.
    open_positions = phe_bal["info"]["data"]["positions"]

    # Extract the side ("Buy" or "Sell") and size of the position at the determined index.
    openpos_side = open_positions[index_pos]["side"]
    openpos_size = open_positions[index_pos]["size"]

    # Determine if there is an open position and its direction.
    if openpos_side == "Buy":
        openpos_bool = True  # There is an open position.
        long = True  # The position is long.
    elif openpos_side == "Sell":
        openpos_bool = True
        long = False  # The position is short.
    else:
        openpos_bool = False
        long = None

    # Print details about the open position.
    print(
        f"open_positions... | openpos_bool {openpos_bool} | openpos_size {openpos_size} | long {long} | index_pos {index_pos}"
    )

    # Return the full positions list, whether a position is open, its size, the position direction, and the index.
    return open_positions, openpos_bool, openpos_size, long, index_pos


# Function to fetch the best ask and bid from the order book for the given symbol
def ask_bid(symbol=symbol):
    """
    Fetches the order book for the given symbol and extracts:
    - The best (highest) bid price.
    - The best (lowest) ask price.
    """
    ob = phemex.fetch_order_book(symbol)  # Retrieve the order book data
    bid = ob["bids"][0][0]  # Best bid price is the first element of the bids list
    ask = ob["asks"][0][0]  # Best ask price is the first element of the asks list

    print(f"this is the ask for {symbol} {ask}")  # Print the best ask price
    return ask, bid  # Return ask and bid prices


# Function that acts as a "kill switch" to close open positions
def kill_switch(symbol=symbol):
    """
    Continuously monitors and closes open positions for the given symbol:
    - Checks if there is an open position.
    - Cancels all open orders.
    - Places limit orders to close the open position based on current market prices.
    - Repeats until the position is closed.
    """
    print(f"starting the kill switch for {symbol}")
    openposi = open_positions(symbol)[1]  # Get whether a position is open (True/False)
    long = open_positions(symbol)[
        3
    ]  # Get whether the position is long (True) or short (False)
    kill_size = open_positions(symbol)[2]  # Get the size of the open position

    print(f"openposi {openposi}, long {long}, size {kill_size}")

    # Loop until no open position remains
    while openposi == True:
        print("starting kill switch loop til limit fil..")
        temp_df = (
            pd.DataFrame()
        )  # Create an empty DataFrame (potentially for logging purposes)
        print("just made a temp df")

        phemex.cancel_all_orders(symbol)  # Cancel all open orders for the symbol
        # Update open position details after cancellation
        openposi = open_positions(symbol)[1]
        long = open_positions(symbol)[3]
        kill_size = open_positions(symbol)[2]
        kill_size = int(kill_size)  # Convert the position size to an integer

        ask = ask_bid(symbol)[0]  # Get the current best ask price
        bid = ask_bid(symbol)[1]  # Get the current best bid price

        # Depending on the position's direction, place an order to close the position.
        if long == False:
            # If the position is short, place a limit buy order to close the position.
            phemex.create_limit_buy_order(symbol, kill_size, bid, params)
            print(f"just made a BUY to CLOSE order of {kill_size} {symbol} at ${bid}")
            print("sleeping for 30 seconds to see if it fills..")
            time.sleep(30)
        elif long == True:
            # If the position is long, place a limit sell order to close the position.
            phemex.create_limit_sell_order(symbol, kill_size, ask, params)
            print(f"just made a SELL to CLOSE order of {kill_size} {symbol} at ${ask}")
            print("sleeping for 30 seconds to see if it fills..")
            time.sleep(30)
        else:
            print("++++++ SOMETHING I DIDNT EXCEPT IN KILL SWITCH FUNCTION")

        # Re-check if there is still an open position.
        openposi = open_positions(symbol)[1]


# Risk Management Parameters
target = 9  # 'target' might represent a profit target (e.g., a certain profit level to exit the trade)
max_loss = (
    -8
)  # 'max_loss' represents the maximum allowable loss (e.g., stop loss level). Negative indicates a loss.


# pnl_close() returns a tuple: (pnlclose, in_pos, size, long)
# - pnlclose: indicates whether conditions to close the position are met (triggering kill switch)
# - in_pos: indicates whether there is an active position
# - size: the size (number of contracts) of the position
# - long: True if the position is long, False if short
def pnl_close(symbol=symbol, target=target, max_loss=max_loss):
    # Inform the user that we are checking if it's time to exit the position for the given symbol.
    print(f"checking to see if its time to exit for {symbol}... ")

    # Prepare parameters to fetch positions from the exchange; here we specify that we're dealing with swap positions in USD.
    params = {"type": "swap", "code": "USD"}
    # Fetch positions data from the exchange using the provided parameters.
    pos_dict = phemex.fetch_positions(params=params)
    # Uncomment this print if you want to inspect the entire positions dictionary:
    # print(pos_dict)

    # Retrieve the position index for the given symbol.
    # open_positions() returns a tuple, where the 5th element (index 4) is the index position in the list.
    index_pos = open_positions(symbol)[4]

    # Use the index to extract the specific position for our symbol.
    pos_dict = pos_dict[
        index_pos
    ]  # Example: for BTC the index might be 3; for other symbols, index might vary.

    # Extract the side of the position, which indicates if it is a "long" or "short" position.
    side = pos_dict["side"]
    # Extract the size of the position in contracts.
    size = pos_dict["contracts"]
    # Extract the entry price (the price at which the position was opened) and convert it to a float.
    entry_price = float(pos_dict["entryPrice"])
    # Extract the leverage applied to the position and convert it to a float.
    leverage = float(pos_dict["leverage"])

    # Get the current price from the order book; we use the bid price here (index [1] of ask_bid() result) as the current market price.
    current_price = ask_bid(symbol)[1]

    # Print the extracted position details for debugging purposes.
    print(f"side: {side} | entry_price: {entry_price} | lev: {leverage}")

    # Determine the price difference (diff) based on the position side:
    if side == "long":
        # For long positions, profit/loss is the difference between current price and entry price.
        diff = current_price - entry_price
        long = True
    else:
        # For short positions, profit/loss is calculated as entry price minus current price.
        diff = entry_price - current_price
        long = False

    # Calculate the profit/loss percentage.
    try:
        # Compute the fractional profit/loss (difference relative to entry price), then multiply by leverage.
        # The result is rounded to 10 decimal places.
        perc = round(((diff / entry_price) * leverage), 10)
    except:
        # If an error occurs (for example, division by zero), default the percentage to 0.
        perc = 0

    # Convert the fractional value to a percentage.
    perc = 100 * perc
    # Print the computed PNL percentage.
    print(f"for {symbol} this is our PNL percentage: {(perc)}%")

    # Initialize flags to determine if we should close the position.
    pnlclose = False  # Indicates whether to trigger position closing (kill switch)
    in_pos = False  # Indicates whether there is an active position

    # Check if the position is currently profitable (PNL percentage > 0)
    if perc > 0:
        in_pos = True  # We have an active position.
        print(f"for {symbol} we are in a winning postion")
        # If profit exceeds the target, we decide it's time to exit.
        if perc > target:
            print(
                ":) :) we are in profit & hit target.. checking volume to see if we should start kill switch"
            )
            pnlclose = True  # Mark that we should close the position.
            kill_switch(symbol)  # Call the kill switch function to close the position.
        else:
            print("we have not hit our target yet")

    # If the position is in loss (PNL percentage < 0)
    elif perc < 0:
        in_pos = True  # There is an active position.
        # If the loss is greater than or equal to the maximum allowable loss,
        # trigger the kill switch to exit the position.
        if perc <= max_loss:
            print(
                f"we need to exit now down {perc}... so starting the kill switch.. max loss {max_loss}"
            )
            kill_switch(symbol)
        else:
            print(
                f"we are in a losing position of {perc}.. but chillen cause max loss is {max_loss}"
            )
    else:
        # If the percentage is exactly 0, then effectively there is no profit or loss.
        print("we are not in position")

    # Indicate that we have finished checking the PNL close conditions.
    print(f" for {symbol} just finished checking PNL close..")

    # Return the flags and details:
    # - pnlclose: whether to close the position,
    # - in_pos: whether a position is active,
    # - size: the size of the position,
    # - long: True if the position is long, False if short.
    return pnlclose, in_pos, size, long


# size kill
def size_kill():

    max_risk = 1000

    params = {"type": "swap", "code": "USD"}
    all_phe_balance = phemex.fetch_balance(params=params)
    open_positions = all_phe_balance["info"]["data"]["positions"]
    # print(open_positions)

    try:
        pos_cost = open_positions[0]["posCost"]
        pos_cost = float(pos_cost)
        openpos_side = open_positions[0]["side"]
        openpos_size = open_positions[0]["size"]
    except:
        pos_cost = 0
        openpos_side = 0
        openpos_size = 0
    print(f"position cost: {pos_cost}")
    print(f"openpos_side : {openpos_side}")

    if pos_cost > max_risk:

        print(
            f"EMERGENCY KILL SWITCH ACTIVATED DUE TO CURRENT POSITION SIZE OF {pos_cost} OVER MAX RISK OF: {max_risk}"
        )
        kill_switch(symbol)  # just calling the kill switch cause the code below is long
        time.sleep(30000)
    else:
        print(f"size kill check: current position cost is: {pos_cost} we are gucci")


# print index_pos dictionary
def print_all_positions():
    # Set the parameters as needed by your exchange API call
    params = {"type": "swap", "code": "USD"}
    balance = phemex.fetch_balance(params=params)
    positions = balance["info"]["data"]["positions"]

    # Loop through all positions and print their index and details.
    for idx, pos in enumerate(positions):
        # Adjust the key below to match the actual symbol key in the response (e.g. "symbol", "coin", etc.)
        symbol_value = pos.get("symbol") or pos.get("coin") or "Unknown"
        side = pos.get("side", "N/A")
        size = pos.get("size", "N/A")
        print(f"Index {idx}: Symbol={symbol_value}, Side={side}, Size={size}")


print_all_positions()
