To code the backtest, I'll be using the `backtesting.py` library to implement the provided ADX trading strategy. Please note that the code will need data containing the Open, High, Low, and Close prices, as well as the volume for the given instrument. Also, it will require the `talib` library to calculate the ADX, +DI, and -DI indicators. Below is the backtest code:

```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

import talib

import pandas as pd


class ADXStrategy(Strategy):
    adx_period = 14
    di_period = 14
    adx_threshold = 25
    exit_threshold = 20

    def init(self):
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        
        self.adx = self.I(talib.ADX, high, low, close, self.adx_period)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, self.di_period)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, self.di_period)

    def next(self):
        if crossover(self.plus_di, self.minus_di) and self.adx[-1] > self.adx_threshold:
            self.buy()
        elif crossover(self.minus_di, self.plus_di) and self.adx[-1] > self.adx_threshold:
            self.sell()

        for trade in self.trades:
            if trade.is_long and (
                crossover(self.minus_di, self.plus_di)
                or self.adx[-1] < self.exit_threshold
            ):
                trade.close()
            elif trade.is_short and (
                crossover(self.plus_di, self.minus_di)
                or self.adx[-1] < self.exit_threshold
            ):
                trade.close()


# Note: 'data' must be a DataFrame with columns: 'Open', 'High', 'Low', 'Close', 'Volume'
data = pd.DataFrame()  # replace with your actual data

bt = Backtest(data, ADXStrategy, cash=10000, commission=.002, exclusive_orders=True)
stats = bt.run()
print(stats)
bt.plot()
```

Please ensure that you've pip-installed `backtesting.py` (`pip install backtesting`) and `TA-Lib` (`pip install TA-Lib`) before running this code. You will also have to provide your own historical data for backtesting since internet access is disabled in this environment.

When running this script in your environment, replace the `data = pd.DataFrame()` line with your actual data that must contain the Open, High, Low, Close, and Volume columns for the instrument you want to backtest the strategy on.