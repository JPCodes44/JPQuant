"""
Bollinger band bot
Do not run without making your own strategy
"""

import dontshare_config as d
import nice_funcs as n
from eth_account.signers.local import LocalAccount
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

symbol = "WIF"
timeframe = "15m"
sma_window = 20
lookback_days = 1
size = 1
target = 5
max_loss = -10
leverage = 3
max_positions = 1

secret = d.private_key


def bot():

    account1 = LocalAccount = eth_account.Account.from_key(secret)

    (
        positions1,
        im_in_pos,
        mypos_size,
        pos_sym1,
        entry_px1,
        pnl_perc1,
        long1,
        num_of_pos,
    ) = n.get_position_andmaxpos(symbol, account1, max_positions)

    print(f"these are positions for {symbol} {positions1}")

    lev, pos_size = n.adjust_leverage_size_signal(symbol, leverage, account1)
