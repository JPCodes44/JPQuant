import json  # For loading and parsing JSON data
import os  # For operating system-related tasks (e.g. file paths)

import eth_account  # Provides functions to create and manage Ethereum accounts
from eth_account.signers.local import LocalAccount  # Type for local wallet objects

from hyperliquid.exchange import (
    Exchange,
)  # Import the Exchange class to interact with the Hyperliquid API for trading
from hyperliquid.info import (
    Info,
)  # Import the Info class to query account and market information


def setup(base_url=None, skip_ws=False):
    """
    Sets up the primary account and initializes Info and Exchange objects.

    Parameters:
        base_url (str): The API endpoint URL (e.g. testnet or mainnet URL).
        skip_ws (bool): Flag to indicate if WebSocket connections should be skipped.

    Returns:
        tuple: Contains the account address, an Info instance, and an Exchange instance.
    """
    # Determine the path to the config.json file located in the same directory as this script.
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    # Open the configuration file and load its content as a Python dictionary.
    with open(config_path) as f:
        config = json.load(f)

    # Create a wallet (LocalAccount) object using the secret key provided in the config.
    account: LocalAccount = eth_account.Account.from_key(config["secret_key"])

    # Retrieve the account address from the config file.
    address = config["account_address"]

    # If the config doesn't specify an account address (empty string), derive it from the secret key.
    if address == "":
        address = account.address

    # Print the account address being used.
    print("Running with account address:", address)

    # If the provided account address differs from the one derived from the secret key,
    # it implies you are using an agent/API wallet. Print the derived wallet address.
    if address != account.address:
        print("Running with agent address:", account.address)

    # Create an instance of the Info class with the provided base URL and WebSocket flag.
    info = Info(base_url, skip_ws)

    # Fetch the user state (general account information) for the given address.
    user_state = info.user_state(address)

    # Fetch the spot market-specific state for the given address.
    spot_user_state = info.spot_user_state(address)

    # Extract the margin summary from the user state; this contains account equity information.
    margin_summary = user_state["marginSummary"]

    # Check if the account has no equity: both accountValue is 0 and there are no balances in spot state.
    if (
        float(margin_summary["accountValue"]) == 0
        and len(spot_user_state["balances"]) == 0
    ):
        # Inform the user that the account has no equity and the example won't run.
        print("Not running the example because the provided account has no equity.")

        # Get part of the base URL to include in the error message.
        url = info.base_url.split(".", 1)[1]
        error_string = (
            f"No accountValue:\nIf you think this is a mistake, make sure that {address} "
            f"has a balance on {url}.\nIf address shown is your API wallet address, update the config "
            "to specify the address of your account, not the address of the API wallet."
        )
        # Raise an exception with the error message.
        raise Exception(error_string)

    # Create an instance of the Exchange class using the wallet, the API base URL, and the account address.
    exchange = Exchange(account, base_url, account_address=address)

    # Return the account address, the Info object, and the Exchange object.
    return address, info, exchange


def setup_multi_sig_wallets():
    """
    Loads the multi-signature (multi-sig) authorized wallets from the configuration file.

    Returns:
        list: A list of LocalAccount objects representing the authorized multi-sig wallets.
    """
    # Determine the path to the config.json file.
    config_path = os.path.join(os.path.dirname(__file__), "config.json")

    # Open the configuration file and load its content.
    with open(config_path) as f:
        config = json.load(f)

    # Initialize an empty list to hold the authorized user wallets.
    authorized_user_wallets = []

    # Loop over each authorized user wallet in the multi_sig section of the config.
    for wallet_config in config["multi_sig"]["authorized_users"]:
        # Create a wallet object for each authorized user using their secret key.
        account: LocalAccount = eth_account.Account.from_key(
            wallet_config["secret_key"]
        )
        # Retrieve the account address for the authorized user from the config.
        address = wallet_config["account_address"]

        # Verify that the address derived from the secret key matches the provided address.
        if account.address != address:
            raise Exception(
                f"provided authorized user address {address} does not match private key"
            )

        # Print confirmation that the authorized user wallet has been loaded.
        print("loaded authorized user for multi-sig", address)

        # Append the authorized user's wallet object to the list.
        authorized_user_wallets.append(account)

    # Return the list of authorized multi-sig wallets.
    return authorized_user_wallets
