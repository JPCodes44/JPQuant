"""
Supply and demand zones
Do not run without making your own strategy
"""

import dont_share as d
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
max_loss = -10
leverage = 2
max_positions = 1
secret_key = d.private_key


def bot():

    account1 = LocalAccount = eth_account.Account.from_key(secret_key)

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
