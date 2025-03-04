import time  # Import the time module to allow for sleep/delay functionality

import example_utils  # Import helper functions from the example_utils module

from hyperliquid.utils import (
    constants,
)  # Import constants, including the API endpoints, from the Hyperliquid SDK


def main():
    # Call the setup() function from example_utils with the testnet API URL.
    # The setup function returns a tuple containing:
    # - address: Your wallet address
    # - info: An Info client for fetching data from Hyperliquid
    # - exchange: An Exchange client to place orders on Hyperliquid
    address, info, exchange = example_utils.setup(
        constants.TESTNET_API_URL,  # Use the testnet endpoint
        skip_ws=True,  # Skip the WebSocket connection (we only need REST endpoints here)
    )

    # Define the coin to trade. In this example, we use "ETH".
    coin = "ETH"
    # Set the order side to buy (True for buy, False for sell)
    is_buy = True
    # Define the order size (the amount of coin to buy/sell)
    sz = 0.09

    # Print a message indicating that a market order is about to be placed.
    print(f"We try to Market {'Buy' if is_buy else 'Sell'} {sz} {coin}.")

    # Place a market opening order using the exchange object.
    # market_open() is a method that opens a market position.
    # Parameters:
    #   coin: the asset to trade ("ETH" in this case)
    #   is_buy: whether to buy (True) or sell (False)
    #   sz: order size (0.05)
    #   The next parameter is None, possibly for price since it's a market order.
    #   The final parameter (0.01) might be a slippage tolerance or similar parameter.
    order_result = exchange.market_open(coin, is_buy, sz, None, 0.01)

    # Check if the order result returned a status of "ok" (i.e. the order was accepted).
    if order_result["status"] == "ok":
        # Loop over each order status returned by the exchange.
        for status in order_result["response"]["data"]["statuses"]:
            try:
                # Try to extract the filled order details (e.g., order id, filled size, average price).
                filled = status["filled"]
                print(
                    f'Order #{filled["oid"]} filled {filled["totalSz"]} @{filled["avgPx"]}'
                )
            except KeyError:
                # If the "filled" key is not present, print the error message provided in the status.
                print(f'Error: {status["error"]}')

        # Wait for 2 seconds before attempting to close the position.
        print("We wait for 2s before closing")
        time.sleep(2)

        # Print a message indicating that we are about to close the market position.
        print(f"We try to Market Close all {coin}.")
        # Call the market_close() method on the exchange to close the open position for the given coin.
        order_result = exchange.market_close(coin)
        # Check if the close order returned a status of "ok".
        if order_result["status"] == "ok":
            # Loop over each order status returned by the market close call.
            for status in order_result["response"]["data"]["statuses"]:
                try:
                    # Try to extract the filled details from the close order.
                    filled = status["filled"]
                    print(
                        f'Order #{filled["oid"]} filled {filled["totalSz"]} @{filled["avgPx"]}'
                    )
                except KeyError:
                    # If there's an error message in the status, print it.
                    print(f'Error: {status["error"]}')


# This checks if the script is being run directly (not imported as a module),
# and if so, it calls the main() function to start execution.
if __name__ == "__main__":
    main()
