# this strat only trades between 930-1030 est.

# Import necessary modules from backtesting library
from backtesting import Backtest, Strategy

# Import talib for technical analysis functions
import talib

# Import pandas for data manipulation
import pandas as pd

# Import Pool from multiprocessing for parallel processing
from multiprocessing import Pool


# Define a trading strategy class inheriting from Strategy
class SMATradingStrategy(Strategy):
    # Set stop loss percentage
    stop_loss_pct = 5
    # Set take profit percentage
    take_profit_pct = 1

    # Initialize the strategy
    def init(self):
        self.sma5 = self.I(talib.SMA, self.data.Close, timeperiod=5)
        self.sma20 = self.I(talib.SMA, self.data.Close, timeperiod=5)
        self.entry_hour = 9
        self.exit_hour = 10

    def next(self):
        hour = pd.Timestamp(self.data.datetime[-1]).to_pydatetime().hour

        if self.position:
            if hour >= self.exit_hour:
                self.position.close()
        else:
            if hour >= self.entry_hour and self.sma5[-1] < self.sma20[-1]:
                self.buy(
                    size=1,
                    sl=self.data.Close[-1] * (1 - (self.stop_loss_pct / 1000)),
                    tp=self.data.Close[-1] * (1 + (self.take_profit_pct / 1000)),
                )


# Main execution block
if __name__ == "__main__":
    # Read CSV data into a pandas DataFrame
    data = pd.read_csv(
        "/Users/jpmak/JPQuant/data/BTC-1d-418wks_data.csv",
        index_col=0,
        parse_dates=True,
    )
    # Capitalize the column names
    data.columns = [column.capitalize() for column in data.columns]
    data = data.dropna()

    # Create a Backtest object with the data and strategy
    bt = Backtest(data, SMATradingStrategy, cash=1000000, commission=0.002)

    result = bt.optimize(
        maximize="Equity Final [$]",
        stop_loss_pct=range(5, 20),
        take_profit_pct=range(1, 10),
    )

    print(result)

    bt.plot()
