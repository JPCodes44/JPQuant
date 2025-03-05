from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib
import pandas as pd


class EMAWilliamsStrategy(Strategy):
    # Default parameters (these will be optimized)
    fast_ema_period = 25
    slow_ema_period = 30
    willr_period = 56
    willr_threshold = -50  # Fixed threshold for Williams %R

    def init(self):
        # Calculate fast and slow EMAs on the closing prices
        self.fast_ema = self.I(talib.EMA, self.data.Close, self.fast_ema_period)
        self.slow_ema = self.I(talib.EMA, self.data.Close, self.slow_ema_period)
        # Calculate Williams %R on high, low, and close using TA-Lib
        self.willr = self.I(
            talib.WILLR,
            self.data.High,
            self.data.Low,
            self.data.Close,
            self.willr_period,
        )

    def next(self):
        # Check for a bullish EMA crossover:
        ema_bullish = (
            self.fast_ema[-2] <= self.slow_ema[-2]
            and self.fast_ema[-1] > self.slow_ema[-1]
        )
        # Check if Williams %R crosses above the -50 level
        willr_bullish = (
            self.willr[-2] <= self.willr_threshold
            and self.willr[-1] > self.willr_threshold
        )

        # Entry condition: if both EMA and Williams %R conditions are bullish and we’re not in a position
        if not self.position and ema_bullish and willr_bullish:
            self.buy()

        # Exit condition: if a bearish EMA crossover occurs, close the position
        elif self.position and (
            self.fast_ema[-2] >= self.slow_ema[-2]
            and self.fast_ema[-1] < self.slow_ema[-1]
        ):
            self.position.close()


if __name__ == "__main__":
    # Load historical data from CSV (adjust the file path as needed)
    data = pd.read_csv(
        "/Users/jpmak/JPQuant/data/BTC-1d-418wks_data.csv",
        index_col=0,
        parse_dates=True,
    )
    # Ensure column names match what Backtesting.py expects:
    # "Open", "High", "Low", "Close", "Volume"
    data.columns = [col.capitalize() for col in data.columns]
    data.dropna(inplace=True)

    # Initialize the backtest with initial cash and commission settings.
    bt = Backtest(data, EMAWilliamsStrategy, cash=10000, commission=0.002)

    # Optimize the strategy:
    # - fast_ema_period: from 10 to 35 (step 5)
    # - slow_ema_period: from 20 to 55 (step 5)
    # - willr_period: from 30 to 70 (step 10)
    # The optimizer maximizes the final equity.
    stats = bt.optimize(
        fast_ema_period=range(10, 40, 5),
        slow_ema_period=range(20, 60, 5),
        willr_period=range(30, 80, 10),
        maximize="Equity Final [$]",
        constraint=lambda p: p.fast_ema_period < p.slow_ema_period,
    )

    print(stats)
    bt.plot()
