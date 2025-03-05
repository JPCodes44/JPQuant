from backtesting import Backtest, Strategy
import pandas as pd
import talib


class VolumeSpikeStrategy(Strategy):
    # This ratio determines how big the spike must be
    # relative to the average volume. For example, 2.0 = 200% spike.
    volume_spike_ratio = 2.0

    def init(self):
        # Calculate the 20-period SMA of volume for comparison
        self.avg_volume = self.I(SMA, self.data.Volume, 20)

    def next(self):
        # Current volume and average volume
        current_vol = self.data.Volume[-1]
        avg_vol = self.avg_volume[-1]

        # Check for a volume spike
        if current_vol > self.volume_spike_ratio * avg_vol:
            print(f"Volume spike detected on {self.data.index[-1]}")

            # Calculate stop loss and take profit prices
            stop_loss = self.data.Close[-1] * 0.95  # e.g., 5% below current close
            take_profit = self.data.Close[-1] * 1.10  # e.g., 10% above current close
            print(f"Executing Buy: SL={stop_loss}, TP={take_profit}")

            # Enter a long position with the specified SL and TP
            self.buy(sl=stop_loss, tp=take_profit)


if __name__ == "__main__":
    # Load your CSV data (replace with your actual path)
    df = pd.read_csv(
        "/Users/jpmak/JPQuant/data/ETH-USD-15m-2020-01-01to0.csv",
        parse_dates=True,
        index_col=0,
    )

    # If needed, ensure column names match what backtesting.py expects:
    # "Open", "High", "Low", "Close", "Volume"
    df.columns = [col.capitalize() for col in df.columns]
    df.dropna(inplace=True)

    # Create and run the backtest
    from backtesting import Backtest

    bt = Backtest(df, VolumeSpikeStrategy, cash=10000, commission=0.002)

    stats = bt.run()
    print(stats)
    bt.plot()
