"""
Supply and Demand Zone bot for Hyper Liquid

"""

import example_utils
import nice_funcs as n
import eth_account
import json
import time
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import ccxt
import pandas as pd
import datetime
import schedule
import requests

symbol = "BTC"
timeframe = "5m"
sma_window = 20
lookback_days = 1
size = 0.001
target = 5
max_loss = -10
leverage = 3
max_positions = 1


account1, info, exchange = example_utils.setup(
    constants.TESTNET_API_URL,  # Use the testnet endpoint
    skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
)
n.adjust_leverage_size_signal(symbol, leverage, account1)


def bot():

    pos_size = size
    account1, info, exchange = example_utils.setup(
        constants.TESTNET_API_URL,  # Use the testnet endpoint
        skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
    )
    positions1, im_in_pos, mypos_size, pos_sym1, entry_px1, pnl_perc1, long1 = (
        n.get_position(symbol, account1)
    )
    print(f"these are the positions {positions1}")

    if im_in_pos:
        print("in position so checking pnl close")
        n.pnl_close(symbol, target, max_loss, account1)
    else:
        print("im not in position so no pnl close")

    # check if in a partial position
    if 0 < mypos_size < pos_size:
        print(f"current size {mypos_size}")
        pos_size = pos_size - mypos_size
        print(f"updated size needed {pos_size}")
        im_in_pos = False
    else:
        pos_size = size

    latest_sma = n.get_latest_sma(symbol, timeframe, sma_window, 2)

    if latest_sma is not None:
        print(f"latest sma for {symbol} over the {sma_window} intervals: {latest_sma}")
    else:
        print("could not receive sma")

    price = n.ask_bid(symbol)[0]

    if not im_in_pos:

        sd_df = n.supply_demand_zones_hl(symbol, timeframe, lookback_days)

        sd_df["5m_dz"] = pd.to_numeric(sd_df["5m_dz"], errors="coerce")
        sd_df["5m_sz"] = pd.to_numeric(sd_df["5m_sz"], errors="coerce")

        buy_price = sd_df["5m_dz"].mean()
        sell_price = sd_df["5m_sz"].mean()

        # make buy price and sell price a float
        buy_price = float(buy_price)
        sell_price = float(sell_price)

        adjusted_buy_price = n.adjust_price_sigfig(buy_price, sig_figs=5)
        adjusted_sell_price = n.adjust_price_sigfig(sell_price, sig_figs=5)

        print(
            f"current price {price} buy price {adjusted_buy_price} sell price {adjusted_sell_price}"
        )

        # calculate the absolute diff between the current and buy/sell prices
        diff_to_buy_price = abs(price - adjusted_buy_price)
        diff_to_sell_price = abs(price - adjusted_sell_price)

        # determine weather to buy or sell based on which price is closer
        if diff_to_buy_price < diff_to_sell_price:
            n.cancel_all_orders(account1)
            print("canceled all orders...")

            # enter the buy price
            n.limit_order(symbol, True, pos_size, adjusted_buy_price, False, account1)
            print(f"just placed order for {pos_size} at {adjusted_buy_price}")

        else:
            print("placing sell order")
            n.cancel_all_orders(account1)
            print("just canceled all orders")
            n.limit_order(symbol, False, pos_size, adjusted_sell_price, False, account1)
            print(f"just placed order for {pos_size} at {adjusted_sell_price}")

    else:
        print(f"in {pos_sym1} position size {pos_size} so not entering")


# Schedule the bot function to run every 28 seconds
bot()
# schedule.every(30).seconds.do(bot)

# # Main loop: run scheduled tasks indefinitely, with basic error handling
# while True:
#     try:
#         schedule.run_pending()  # Run any pending scheduled tasks
#     except:
#         # If an exception occurs (e.g., due to network issues), log it and sleep for 30 seconds before retrying
#         print("++++++++++++++ MAYBE AN INTERNET PROBLEM, CODE FAILED.. sleep 30...")
#         time.sleep(30)
