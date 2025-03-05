from backtesting import Backtest, Strategy
import pandas as pd
import talib


class FixedMomentumStrategy(Strategy):
    # Default periods; feel free to optimize these with bt.optimize
    short_period = 50
    long_period = 200

    def init(self):
        # Compute short and long SMAs using TA-Lib
        self.sma_short = self.I(talib.SMA, self.data.Close, self.short_period)
        self.sma_long = self.I(talib.SMA, self.data.Close, self.long_period)

    def next(self):
        # If short SMA is above long SMA => uptrend => ensure we are long
        if self.sma_short[-1] > self.sma_long[-1]:
            if not self.position:
                self.buy()  # enter long if not already in a position
        else:
            # If short SMA is below long SMA => downtrend => close any open position
            if self.position:
                self.position.close()


if __name__ == "__main__":
    # Load your CSV data (BTC daily data)
    data = pd.read_csv(
        "/Users/jpmak/JPQuant/data/ETH-1d-480wks_data.csv",
        index_col=0,
        parse_dates=True,
    )
    # Ensure columns match what backtesting.py expects: "Open", "High", "Low", "Close", "Volume"
    data.columns = [col.capitalize() for col in data.columns]
    data.dropna(inplace=True)

    # Initialize and run the backtest
    bt = Backtest(data, FixedMomentumStrategy, cash=10000, commission=0.002)

    stats = bt.optimize(
        short_period=range(10, 60, 5),
        long_period=range(100, 300, 20),
        maximize="Equity Final [$]",
    )

    # If not optimizing, just run the strategy with default parameters
    stats = bt.run()
    print(stats)
    bt.plot()
