import asyncio
import json
import os
import datetime
import pytz
from websockets import connect, WebSocketException
from termcolor import cprint

# list of symbols you want to track
symbols = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "dogeusdt", "wifusdt"]
websocket_url_base = "wss://fstream.binance.com/ws/"
trades_filename = "binance_trades.csv"

# check if the csv file exists
if not os.path.isfile(trades_filename):
    with open(trades_filename, "w") as f:
        f.write(
            "Event Time, Symbol, Aggregate Trade ID, Price, Quantity, First Trade ID, Trade Time, Is Buyer Maker\n"
        )


class TradeAggregator:
    def __init__(self):
        self.trade_buckets = {}

    async def add_trade(self, symbol, second, usd_size, is_buyer_maker):
        trade_key = (symbol, second, is_buyer_maker)
        self.trade_buckets[trade_key] = self.trade_buckets.get(trade_key, 0) + usd_size

    async def check_and_print_trades(self):
        now = datetime.datetime.utcnow()
        deletions = []
        for trade_key, usd_size in self.trade_buckets.items():
            symbol, second_str, is_buyer_maker = trade_key  # second is now a string
            try:
                second = datetime.datetime.strptime(
                    second_str, "%H:%M:%S"
                ).time()  # Parse the time string
                combined_datetime = datetime.datetime.combine(
                    now.date(), second
                )  # Combines current date with the time
            except ValueError as e:
                print(f"Error parsing time: {second_str} - {e}")
                deletions.append(trade_key)  # Remove if the time cannot be parsed
                continue
            if (
                combined_datetime < now and usd_size > 500000
            ):  # Compare the trade to see if it is in the past and also above 500k
                attrs = ["bold"]
                back_color = "on_blue" if not is_buyer_maker else "on_magenta"
                trade_type = "BUY" if not is_buyer_maker else "SELL"
                usd_size = usd_size / 1000000
                cprint(
                    f"\033[5m{trade_type} {symbol} {second_str} ${usd_size:.2f}m\033[0m",
                    "white",
                    back_color,
                    attrs=attrs,
                )
                deletions.append(trade_key)

        for key in deletions:
            del self.trade_buckets[key]


trade_aggregator = TradeAggregator()


async def binance_trade_stream(uri, symbol, filename, aggregator):
    max_retries = 5
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            async with connect(uri) as websocket:
                print(f"Connected to {uri}")
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        usd_size = float(data["p"]) * float(data["q"])
                        trade_time = datetime.datetime.fromtimestamp(
                            data["T"] / 1000, tz=pytz.timezone("US/Eastern")
                        )
                        readable_trade_time = trade_time.strftime("%H:%M:%S")

                        await aggregator.add_trade(
                            symbol.upper().replace("USDT", ""),
                            readable_trade_time,
                            usd_size,
                            data["m"],
                        )
                    except WebSocketException as e:
                        print(f"WebSocketException: {e}")
                        break  # Exit the inner loop to reconnect
                    except Exception as e:
                        print(f"Error processing message: {e}")
                        await asyncio.sleep(5)  # Small delay if error occurs
        except Exception as e:
            print(f"Failed to connect to {uri}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print(f"Max retries reached for {uri}.  Giving up.")
                return  # Exit the function after max retries

    print(f"Exiting trade stream for {symbol} after {max_retries} attempts.")


async def print_aggregated_trades_every_second(aggregator):
    while True:
        await asyncio.sleep(1)
        await aggregator.check_and_print_trades()


async def main():
    filename = "binance_trades_big.csv"
    trade_stream_tasks = [
        binance_trade_stream(
            f"{websocket_url_base}{symbol}@aggTrade", symbol, filename, trade_aggregator
        )
        for symbol in symbols
    ]
    print_tasks = asyncio.create_task(
        print_aggregated_trades_every_second(trade_aggregator)
    )
    await asyncio.gather(*trade_stream_tasks, print_tasks)


asyncio.run(main())
