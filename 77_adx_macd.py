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
class MyStrategy(Strategy):

    timeperiod = 14

    def init(self):
        self.macd, self.signal, self.hist = self.I(talib.MACD, self.data.Close)
        self.adx = self.I(
            talib.ADX,
            self.data.High,
            self.data.Low,
            self.data.Close,
            timeperiod=self.timeperiod,
        )
        self.market_is_bullish = False

    def next(self):
        if self.macd[-1] > self.signal[-1]:
            market_is_bullish = True
        elif self.macd[-1] < self.signal[-1]:
            market_is_bullish = False

        if self.adx[-1] > 20:
            if market_is_bullish:
                self.buy()
            else:
                self.sell()


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
    bt = Backtest(data, MyStrategy, cash=1000000, commission=0.002)

    stats = bt.optimize(maximize="Equity Final [$]", timeperiod=range(10, 30))
    print(stats)
    bt.plot()
