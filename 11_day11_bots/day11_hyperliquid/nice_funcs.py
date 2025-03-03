import dontshare_config as d
import nice_funcs as n
import eth_account
import json
import example_utils
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


def ask_bid(symbol):
    """this gets the ask and bid for any symbol passed in"""

    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}

    data = {"type": "l2Book", "coin": symbol}

    response = requests.post(url, headers=headers, data=json.dumps(data))
    l2_data = response.json()
    l2_data = l2_data["levels"]

    # get ask bid
    bid = float(l2_data[0][0]["px"])
    ask = float(l2_data[1][0]["px"])

    return ask, bid, l2_data


def get_sz_px_decimals(coin):
    """this returns size devimals and price decimals"""

    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    data = {"type": "meta"}

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        symbols = data["universe"]
        symbol_info = next((s for s in symbols if s["name"] == symbol), None)
        if symbol_info:
            sz_decimals = symbol_info["szDecimals"]

        else:
            print("symbol not found")

    else:
        print("Error:", response.status_code)

    ask = ask_bid(symbol)[0]

    ask_str = str(ask)
    if "." in ask_str:
        px_decimals = len(ask_str.split(".")[1])
    else:
        px_decimals = 0

    print(f"{symbol} this is the price {sz_decimals} decimals")

    return sz_decimals, px_decimals


# MAKE A BUY AND A SELL ORDER
def limit_order(coin, is_buy, sz, limit_px, reduce_only, account):
    address, info, exchange = example_utils.setup(
        constants.TESTNET_API_URL,  # Use the testnet endpoint
        skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
    )
    rounding = get_sz_px_decimals(coin)[0]
    sz = round(sz, rounding)
    print(f"coin: {coin}, type: {type(coin)}")
    print(f"is_buy: {is_buy}, type: {type(coin)}")
    print(f"sz: {sz}, type: {type(limit_px)}")
    print(f"reduce_only: {reduce_only}, type: {type(reduce_only)}")

    print(f"placing limit order for {coin} {sz} @ {limit_px}")
    order_result = exchange.order(
        coin, is_buy, sz, limit_px, {"limit": {"tif": "Gtc"}}, reduce_only=reduce_only
    )

    if is_buy == True:
        print(
            f"limit BUY order placed thanks moon dev, resting: {order_result['response']['data']['statuses'][0]}"
        )
    else:
        print(
            f"limit SELL order placed thanks moon dev, resting: {order_result['response']['data']['statuses'][0]}"
        )

    return order_result


def acct_bal(account):

    # account = LocalAccount = eth_account.Account.from_key(key)
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    user_state = info.user_state(account)

    print(
        f'this is current account value: {user_state["marginSummary"]["accountValue"]}'
    )

    acct_value = user_state["marginSummary"]["accountValue"]

    return acct_value


def get_position(symbol, account):
    """
    gets the current position info, like size etc.
    """

    # account = LocalAccount = eth_account.Account.from_key(key)
    info = Info(constants.TESTNET_API_URL, skip_ws=True)
    user_state = info.user_state(account)

    print(
        f'this is current account value: {user_state["marginSummary"]["accountValue"]}'
    )

    positions = []
    print(f"this is the symbol {symbol}")
    print(user_state["assetPositions"])

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


def cancel_all_orders(account):

    # this cancels all open orders
    # account = LocalAccount = eth_account.Account.from_key(key)
    exchange = Exchange(account, constants.TESTNET_API_URL)
    info = Info(constants.TESTNET_API_URL, skip_ws=True)

    open_orders = info.open_orders(account)

    print("above are the open orders... need to cancel any...")
    for open_order in open_orders:
        # print(f'cancelling order {open_order}')
        exchange.cancel(open_order["coin"], open_order["oid"])


def kill_switch(symbol, account):

    position, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, long = get_position(
        symbol, account
    )

    while im_in_pos == True:

        cancel_all_orders(account)

        ask, bid, l2 = ask_bid(symbol)

        pos_size = abs(pos_size)

        if long == True:
            limit_order(pos_sym, False, pos_size, ask, True, account)
            print("kill switch - SELL TO CLOSE SUBMITTED ")
            time.sleep(5)
        elif long == False:
            limit_order(pos_sym, True, pos_size, bid, True, account)
            print("kill switch - BUY TO CLOSE SUBMITTED ")
            time.sleep(5)

        position, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, long = get_position(
            symbol, account
        )

    print("position succesfully closed in the kill switch")


def pnl_close(symbol, target, max_loss, account):
    """
    monitors positions for their pnl and will close the position when you hit the tp/sl

    """

    print("starting pnl close")

    position, im_in_pos, pos_size, pos_sym, entry_px, pnl_perc, long = get_position(
        symbol, account
    )

    if pnl_perc > target:
        print(f"pnl gain is {pnl_perc} and target is {target}... closing position WIN")
        kill_switch(pos_sym, account)
    elif pnl_perc <= max_loss:
        print(
            f"pnl loss is {pnl_perc} and max loss is {max_loss}... closing position LOSS"
        )
        kill_switch(pos_sym, account)
    else:
        print(
            f"pnl loss is {pnl_perc} and max loss is {max_loss} and target {target}... not closing position"
        )

    print("finished with pnl close")


def adjust_leverage_size_signal(symbol, leverage, account):
    """
    this calculates size based off what we want.
    95% of balance
    """

    print("leverage:", leverage)

    account, info, exchange = example_utils.setup(
        constants.TESTNET_API_URL,  # Use the testnet endpoint
        skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
    )

    # Get the user state and print out leverage information for ETH
    user_state = info.user_state(account)
    acct_value = user_state["marginSummary"]["accountValue"]
    acct_value = float(acct_value)

    acct_val95 = acct_value * 0.95

    print(exchange.update_leverage(leverage, symbol))

    price = ask_bid(symbol)[0]

    # size == balance / price * leverage
    # INJ 6.95 ... at 10x lev... 10 INJ == $cost 6.95
    size = (acct_val95 / price) * leverage
    size = float(size)
    rounding = get_sz_px_decimals(symbol)[0]
    size = round(size, rounding)
    # print(f'this is the size we can use 95% fo acct val {size}')

    user_state = info.user_state(account)

    return leverage, size


def fetch_candle_snapshot(symbol, interval, start_time, end_time):
    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    data = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
        },
    }


def calculate_sma(prices, window):
    sma = prices.rolling(window=window).mean()
    return sma.iloc[-1]  # Return the most recent sma position


def get_latest_sma(symbol, interval, window, lookback_days=1):
    start_time = datetime.datetime.now() - datetime.timedelta(days=lookback_days)
    end_time = datetime.datetime.now()

    snapshots = fetch_candle_snapshot(symbol, interval, start_time, end_time)
    if snapshots:
        prices = pd.Series([float(snapshot["c"]) for snapshot in snapshots])
        latest_sma = calculate_sma(prices, window)
        return latest_sma
    else:
        return None


def supply_demand_zones_hl(symbol, timeframe, limit):
    print("starting moons supply and demand zone calculations..")

    sd_df = pd.DataFrame()

    snapshot_data = get_ohlcv2(symbol, timeframe, limit)
    df = process_data_to_df(snapshot_data)

    supp = df.iloc[-1]["support"]
    resis = df.iloc[-1]["resis"]
    # print(f'this is moons support for 1h {supp_1h} this is resis: {resis_1h}')

    df["supp_lo"] = df[:-2]["low"].min()
    supp_lo = df.iloc[-1]["supp_lo"]

    df["res_hi"] = df[:-2]["high"].max()
    res_hi = df.iloc[-1]["res_hi"]

    print(df)

    sd_df[f"{timeframe}_dz"] = [supp_lo, supp]
    sd_df[f"{timeframe}_sz"] = [res_hi, resis]

    print("here are moons supply and demand zones")
    print(sd_df)

    return sd_df


def get_ohlcv2(symbol, interval, lookback_days):
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=lookback_days)

    url = "https://api.hyperliquid.xyz/info"
    headers = {"Content-Type": "application/json"}
    data = {
        "type": "candleSnapshot",
        "req": {
            "coin": symbol,
            "interval": interval,
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(end_time.timestamp() * 1000),
        },
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        snapshot_data = response.json()
        return snapshot_data
    else:
        print(f"Error fetching data for {symbol}: {response.status_code}")
        return None


def process_data_to_df(snapshot_data):
    if snapshot_data:
        # Assuming the response contains a list of candles
        columns = ["timestamp", "open", "high", "low", "close", "volume"]
        data = []
        for snapshot in snapshot_data:
            timestamp = datetime.datetime.fromtimestamp(snapshot["t"] / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            open_price = snapshot["o"]
            high_price = snapshot["h"]
            low_price = snapshot["l"]
            close_price = snapshot["c"]
            volume = snapshot["v"]
            data.append(
                [timestamp, open_price, high_price, low_price, close_price, volume]
            )

        df = pd.DataFrame(data, columns=columns)

        # Calculate support and resistance, excluding the last two rows for the calculation
        if len(df) > 2:  # Check if DataFrame has more than 2 rows to avoid errors
            df["support"] = df[:-2]["close"].min()
            df["resis"] = df[:-2]["close"].max()
        else:  # If DataFrame has 2 or fewer rows, use the available 'close' prices for calculation
            df["support"] = df["close"].min()
            df["resis"] = df["close"].max()

        return df
    else:
        return pd.DataFrame()  # Return empty DataFrame if no data


def adjust_price_sigfig(price, sig_figs=5):
    # Format the price as a string with sig_figs significant digits.
    formatted = f"{price:.{sig_figs}g}"
    # Convert the string back to a float.
    return float(formatted)
