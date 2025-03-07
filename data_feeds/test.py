def fetch_ohlcv(
    self, symbol: str, timeframe="1m", since: Int = None, limit: Int = None, params={}
) -> List[list]:
    """
    fetches historical candlestick data containing the open, high, low, and close price, and the volume of a market

    https://github.com/phemex/phemex-api-docs/blob/master/Public-Hedged-Perpetual-API.md#querykline
    https://github.com/phemex/phemex-api-docs/blob/master/Public-Contract-API-en.md#query-kline

    :param str symbol: unified symbol of the market to fetch OHLCV data for
    :param str timeframe: the length of time each candle represents
    :param int [since]: *only used for USDT settled contracts, otherwise is emulated and not supported by the exchange* timestamp in ms of the earliest candle to fetch
    :param int [limit]: the maximum amount of candles to fetch
    :param dict [params]: extra parameters specific to the exchange API endpoint
    :param int [params.until]: *USDT settled/ linear swaps only* end time in ms
    :returns int[][]: A list of candles ordered, open, high, low, close, volume
    """
    self.load_markets()  # Load market data
    market = self.market(symbol)  # Get market information for the given symbol
    userLimit = limit  # Store the user-provided limit
    request: dict = {
        "symbol": market["id"],  # Set the market ID in the request
        "resolution": self.safe_string(
            self.timeframes, timeframe, timeframe
        ),  # Set the timeframe resolution
    }
    until = self.safe_integer_2(
        params, "until", "to"
    )  # Get the 'until' parameter from params
    params = self.omit(params, ["until"])  # Remove 'until' from params
    usesSpecialFromToEndpoint = ((market["linear"] or market["settle"] == "USDT")) and (
        (since is not None) or (until is not None)
    )  # Determine if special from/to endpoint is used
    maxLimit = 1000  # Set default max limit
    if usesSpecialFromToEndpoint:
        maxLimit = 2000  # Adjust max limit if special endpoint is used
    if limit is None:
        limit = maxLimit  # Set limit to max limit if not provided
    request["limit"] = min(limit, maxLimit)  # Set the limit in the request
    response = None  # Initialize response variable
    if market["linear"] or market["settle"] == "USDT":
        if (until is not None) or (since is not None):
            candleDuration = self.parse_timeframe(
                timeframe
            )  # Parse the timeframe duration
            if since is not None:
                since = int(round(since / 1000))  # Convert since to seconds
                request["from"] = since  # Set the 'from' parameter in the request
            else:
                since = (until / 100) - (
                    maxLimit * candleDuration
                )  # Calculate since if not provided
            if until is not None:
                request["to"] = int(
                    round(until / 1000)
                )  # Convert until to seconds and set in request
            else:
                to = since + (
                    maxLimit * candleDuration
                )  # Calculate 'to' if not provided
                now = self.seconds()  # Get current time in seconds
                if to > now:
                    to = now  # Adjust 'to' if it exceeds current time
                request["to"] = to  # Set the 'to' parameter in the request
            response = self.publicGetMdV2KlineList(
                self.extend(request, params)
            )  # Fetch data using from/to endpoint
        else:
            response = self.publicGetMdV2KlineLast(
                self.extend(request, params)
            )  # Fetch latest data
    else:
        if since is not None:
            duration = (
                self.parse_timeframe(timeframe) * 1000
            )  # Parse the timeframe duration in milliseconds
            timeDelta = self.milliseconds() - since  # Calculate time delta
            limit = self.parse_to_int(
                timeDelta / duration
            )  # Set limit to the number of candles after since
        response = self.publicGetMdV2Kline(
            self.extend(request, params)
        )  # Fetch data using regular endpoint
    data = self.safe_value(response, "data", {})  # Extract data from response
    rows = self.safe_list(data, "rows", [])  # Extract rows from data
    return self.parse_ohlcvs(
        rows, market, timeframe, since, userLimit
    )  # Parse and return OHLCV data
