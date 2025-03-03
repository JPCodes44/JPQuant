"""
this file shows how to build a kill switch and pnl close
for hyper liquid. use at your own risk. 
"""

import nice_funcs as n
import dont_share as d
from eth_account.signers.local import LocalAccount
import eth_account
import json, time
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import ccxt
import pandas as pd
import datetime
import schedule
import requests

symbol = "ETH"
max_loss = -5
target = 4
acct_min = 9
timeframe = "4h"
size = 10
coin = symbol
secret_key = d.private_key
account = LocalAccount - eth_account.Account.from_key(secret_key)


def get_position(symbol, account):
    """gets the position info we need"""
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    user_state = info.user_state(account.address)
    print(
        f'this is the current account val {user_state["marginSummary"]["accountValue"]}'
    )
    positions = []
    print(f"this is the symbol {symbol}")
    for position in user_state["assetPositions"]:
        if (position["position"]["coin"] == symbol) and float(
            position["position"]["szi"]
        ) != 0:
            positions.append(position["position"])
            in_pos = True
            size = float(position["position"]["szi"])
            pos_sym = position["position"]["coin"]
            entry_px = float(position["position"]["entryPx"])
            pnl_perc = float(position["position"]["returnOnEquity"]) * 100
            print(f"this is the pnl perc {pnl_perc}")
            break
        else:
            in_pos = False
            size = 0
            pos_sym = None
            entry_px = 0
            pnl_perc = 0
    if size > 0:
        long = True
    elif size < 0:
        long = False
    else:
        long = None

    return positions, in_pos, size, pos_sym, entry_px, pnl_perc, long


# returns the size decimals and price fora given symbol which you can buy or sell at


def ask_bid(symbol):

    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}

    data = {"type": "l2Book", "coin": symbol}

    response = requests.post(url, headers=headers, data=json.dumps(data))
    l2_data = response.json()
    l2_data = l2_data["levels"]

    bid = float(l2_data[0][0]["px"])
    ask = float(l2_data[1][0]["px"])

    return ask, bid, l2_data


def get_sz_px_decimals(symbol: str):
    # Universe endpoint
    url = "https://api.hyperliquid.xyz/v1/universe"
    headers = {"Content_Type": "application/json"}
    data = {"type": "meta"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        # Success
        data = response.json()
        symbols = data["universe"]
        symbol_info = next((s for s in symbols if s["name"] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info["szDecimals"]
            px_decimals = symbol_info["pxDecimals"]
            print(sz_decimals, px_decimals)
            return (sz_decimals, px_decimals)
        else:
            print("Symbol not found")
    else:
        print("Error:", response.status_code)

    ask = ask_bid(symbol)[0]
    # print(f'this is the ask {ask}')

    # Compute the number of decimal points in the ask price
    ask_str = str(ask)
    if "." in ask_str:
        px_decimals = len(ask_str.split(".")[1])
    else:
        px_decimals = 0

    print(f"{symbol} this is the price {px_decimals} decimal(s)")

    return sz_decimals, px_decimals


def limit_order(coin, is_buy, sz, limit_px, reduce_only, account):
    exchange = Exchange(account, constants.TESTNET_API_URL)

    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)
    print(f"coin: {coin}, type: {type(coin)}")
    print(f"is_buy: {is_buy},  type: {type(is_buy)}")
    print(f"sz: {sz}, type: {type(sz)}")
    print(f"limit_px: {limit_px}, type: {type(limit_px)}")
    print(f"reduce_only: {reduce_only}, type: {type(reduce_only)}")

    print(f"placing limit order for {coin} {sz} @ {limit_px}")
    order_result = exchange.order(
        coin, is_buy, sz, limit_px, {"limit": {"tif": "Gtc"}}, reduce_only=reduce_only
    )

    if is_buy == True:
        print(
            f"limit BUY order placed thanks moon, resting: {order_result['response']['data']['statuses'][0]}"
        )
    else:
        print(
            f"limit BUY order placed thanks moon, resting: {order_result['response']['data']['statuses'][0]}"
        )

    return order_result


def kill_switch(symbol, account):
    position, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, long = get_position(
        symbol, account
    )
    while im_in_pos:
        n.cancel_all_orders(account)

        # get bid ask
        ask, bid, l2_data = ask_bid(pos_sym)

        pos_size = abs(pos_size)

        if long == True:
            limit_order(pos_sym, False, pos_size, ask, True, account)
            print("kill switch sell to close submitted")
            time.sleep(5)
        elif long == False:
            limit_order(pos_sym, False, pos_size, ask, True, account)
            time.sleep(5)

        position, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, long = get_position(
            symbol, account
        )

    print("position successfully closed in kill switch")


def bot():

    print("this is our bot")

    print("controlling risk with our pnl close")

    # check pnl close
    n.pnl_close(symbol, target, max_loss, account)

    # if we have over X positions I want to kill em all
    # if my account size goes under $100, and never $70
    acct_val = float(n.acct_bal(account))

    if acct_val < acct_min:
        print(f"account value is {acct_val} and closing because out low is {acct_min}")
        n.kill_switch(symbol, account)


bot()
