############### Coding Algo Orders 2024

# connect to exchange.

import ccxt
import key_file as k
import time
import schedule


phemex = ccxt.phemex(
    {
        "enableRateLimit": True,
        "apiKey": k.key,
        "secret": k.secret,
    }
)
phemex.set_sandbox_mode(True)

bal = phemex.fetch_balance()
print(bal)

# Define the trading symbol and order parameters
symbol = "BTCUSD"  # Bitcoin/USD Perpetual Contract
size = 1000  # 1 contract
bid = 97000
params = {"timeInForce": "PostOnly"}

# # Create a limit buy order
# order = phemex.create_limit_buy_order(symbol, size, bid, params)

# # Print the order details
# print(order)

# print("just made the order now sleeping for 10s..")
# time.sleep(10)

# # Cancel the order
# phemex.cancel_all_orders(symbol)
go = True


def bot():
    print(f"creating limit buy order of {symbol} of size {size} at {bid}")
    order = phemex.create_limit_buy_order(symbol, size, bid, params)
    time.sleep(10)
    print("cancelling all orders..")
    phemex.cancel_all_orders(symbol)
    print("successfully canceled all orders")


bot()
# schedule.every(10).seconds.do(bot)

# while True:
#     try:
#         schedule.run_pending()
#     except:
#         print("+++++ MAYBE AN INTERNET PROB OR SOMETHING")
#         time.sleep(30)
