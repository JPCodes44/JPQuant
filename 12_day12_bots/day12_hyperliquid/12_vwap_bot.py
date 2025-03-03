"""
VWAP BOT

RBI system 
Research - 
Backtest - find 5 winning backtests
Implement - 
"""

# A multi-line string used as a header or description for the bot. It explains that this is a VWAP-based trading bot,
# and outlines steps like research, backtesting, and implementation.

import dontshare_config as d  # Import configuration (API keys, etc.) from a file named dontshare_config.
import nice_funcs as n  # Import helper functions from a file named nice_funcs.
from eth_account.signers.local import (
    LocalAccount,
)  # Import LocalAccount for creating wallet objects.
import eth_account  # Import eth_account library for account management.
import json  # Import JSON module for encoding/decoding JSON data.
import time, random  # Import time (for delays) and random (for generating random numbers).
import example_utils  # Import additional helper utilities from example_utils.
from hyperliquid.info import Info  # Import Info class to retrieve exchange information.
from hyperliquid.exchange import Exchange  # Import Exchange class to execute orders.
from hyperliquid.utils import (
    constants,
)  # Import constants (like API URLs) from hyperliquid.utils.
import ccxt  # Import ccxt library to interact with crypto exchanges.
import pandas as pd  # Import pandas for DataFrame operations.
import datetime  # Import datetime module for handling dates and times.
import schedule  # Import schedule to run functions at regular intervals.
import requests  # Import requests for making HTTP API calls.

# Define global parameters for the bot
symbol = "BTC"  # Trading symbol (here using LINK; can be changed as needed).
timeframe = "1m"  # Timeframe for candlestick data (1-minute candles).
sma_window = 20  # Window size for simple moving average calculations.
lookback_days = 1  # How many days of historical data to look back.
size = 1  # Base order size.
target = 5  # Profit target percentage (e.g., close position when profit exceeds 5%).
max_loss = -10  # Maximum allowable loss percentage (e.g., close if loss reaches -10%).
leverage = 3  # Leverage multiplier to apply to the trade.
max_positions = 1  # Maximum allowed open positions.


# ---------------------------
def bot():
    secret = d.secret_key

    account1, info, exchange = example_utils.setup(
        constants.TESTNET_API_URL,  # Use the testnet endpoint
        skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
    )

    (
        positions1,
        im_in_pos,
        mypos_size,
        pos_sym1,
        entry_pnl,
        pnl_perc1,
        long1,
        num_of_pos,
    ) = n.get_position_andmaxpos(symbol, account1, max_positions)
    print(f"these are my positions for {symbol} {positions1}")

    lev, pos_size = n.adjust_leverage_size_signal(symbol, leverage, account1)

    if im_in_pos:
        n.cancel_all_orders(account1)
        print("in position so check pnl close")
        n.pnl_close(symbol, target, max_loss, account1)
    else:
        print("not in position so no pnl close")

    ask, bid, l2_data = n.ask_bid(symbol)

    # 11th bid and ask
    bid11 = float(l2_data[0][10]["px"])
    ask11 = float(l2_data[1][10]["px"])

    # get vwap
    latest_vwap = n.calculate_vwap_with_symbol(symbol)[1]

    print(f"the latest vwap is {latest_vwap}")

    random_chance = random.random()

    if bid > latest_vwap:
        if random_chance <= 0.7:  # 70% chance
            going_long = True
            print(f"price is above sma {ask} > {latest_vwap}, going long {going_long}")
        else:
            going_long = False
            print(f"price is above vwap {ask} < {latest_vwap}, but not going long")
    else:
        if random_chance <= 0.3:  # 30% chance
            going_long = True
            print(
                f"price is below vwap {ask} < {latest_vwap} not going long {going_long}"
            )
        else:
            going_long = False
            print(
                f"price is below vwap {ask} < {latest_vwap} not going long {going_long}"
            )

    # ENTER ORDER IF NO POSITION
    if not im_in_pos and going_long:

        print(f"not in position so we are quoting at buying @ {bid11}")
        n.cancel_all_orders(account1)
        print("just canceled all orders")

        # enter buy order
        n.limit_order(symbol, True, pos_size, bid11, False, account1)
        print(f"just placed an order for {pos_size} at {bid11}")

    elif not im_in_pos and not going_long:

        print(f"not in position... we are quoting at sell @ {ask11}")
        n.cancel_all_orders(account1)
        print("just canceled all orders")

        # enter buy order
        n.limit_order(symbol, False, pos_size, ask11, False, account1)
        print(f"just placed an order for {pos_size} at {ask11}")
    else:
        print(f"our position is {im_in_pos}")


bot()
