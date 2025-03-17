```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover

class PivotPointStrategy(Strategy):
    def init(self):
        super().init()
        # This strategy requires previous day's high, low and close values
        # These would likely be obtained from an external source such as a CSV file or database
        # Assuming that we've loaded this data into our strategy
        self.previous_high = self.data.High.shift(1)
        self.previous_low = self.data.Low.shift(1)
        self.previous_close = self.data.Close.shift(1)

    def next(self):
        super().next()

        # Formulas for Pivot Points
        PP = (self.previous_high + self.previous_low + self.previous_close) / 3
        R1 = (2 * PP) - self.previous_low
        S1 = (2 * PP) - self.previous_high
        R2 = PP + (self.previous_high - self.previous_low)
        S2 = PP - (self.previous_high - self.previous_low)

        if not self.position:
            # Buy Signal: Price moves above pivot point and consolidates
            if self.data.Close > PP and not self.position.is_long:
                self.buy(sl=S1, tp=R1)

            # Sell Signal: Price moves below pivot point and consolidates
            elif self.data.Close < PP and not self.position.is_short:
                self.sell(sl=R1, tp=S1)

        else:
            # Adjust stop loss and take profit for long position
            if self.position.is_long:
                if self.data.High >= R1:
                    self.position.close()
                else:
                    if self.data.Low < S1:
                        self.position.close()
            # Adjust stop loss and take profit for short position
            elif self.position.is_short:
                if self.data.Low <= S1:
                    self.position.close()
                else:
                    if self.data.High > R1:
                        self.position.close()

# Assuming 'data' is a pandas DataFrame with the OHLC data
bt = Backtest(data, PivotPointStrategy, cash=10000, commission=.002)

stats = bt.run()
print(stats)
```

Please note that in a real backtest, you need to have historical data ready and loaded into your pandas DataFrame with the appropriate Columns (i.e., Open, High, Low, Close, and Volume if needed). The strategy assumes that you've pre-calculated the previous day's high, low, and close and stored them such that they align with the current day's index in the DataFrame. Adjust the code to fit the actual structure of your data.

Moreover, the "data" variable must be replaced with the actual data being used for the backtest. The strategy does not take into account the additional rules and the use of other indicators for confirmation. You can add these elements to the strategy according to your requirements.