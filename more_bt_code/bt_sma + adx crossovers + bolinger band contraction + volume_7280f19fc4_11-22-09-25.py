To create a backtest using backtesting.py, we'll first need to define a strategy class that extends Backtesting's `Strategy` base class, then implement the `init` and `next` methods for our specific trading strategy as described.

Here is the code for the backtest:

```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from backtesting.test import SMA, GOOG

import numpy as np
import pandas as pd

class SMABollingerADXStrategy(Strategy):
    # Define the parameters for the strategy
    sma_period = 20
    adx_period = 14
    bollinger_period = 20
    bollinger_std_dev = 2
    volume_threshold = 1000000
    minimum_adx = 20
    
    def init(self):
        # Initialize indicators
        self.sma = self.I(SMA, self.data.Close, self.sma_period)
        self.adx = self.I(adx_indicator, self.data.High, 
                          self.data.Low, self.data.Close, self.adx_period)
        self.bb_upper, self.bb_middle, self.bb_lower = self.I(bollinger_bands, 
                                                              self.data.Close, 
                                                              self.bollinger_period, 
                                                              self.bollinger_std_dev)
        self.bb_width = self.I(bollinger_band_width, 
                               self.bb_upper, self.bb_lower)
        self.avg_bb_width = self.I(SMA, self.bb_width, self.bollinger_period)
        
    def next(self):
        # Long Entry Condition
        if (crossover(self.data.Close, self.sma) and
                self.adx[-1] > self.minimum_adx and
                self.bb_width[-1] < self.avg_bb_width[-1] and
                self.data.Volume[-1] > self.volume_threshold):
            self.buy()
            
        # Short Entry Condition
        elif (crossover(self.sma, self.data.Close) and
                self.adx[-1] > self.minimum_adx and
                self.bb_width[-1] < self.avg_bb_width[-1] and
                self.data.Volume[-1] > self.volume_threshold):
            self.sell()
        
        # Long Exit Condition
        for trade in self.trades:
            if trade.is_long:
                if (crossover(self.sma, self.data.Close) or
                        self.adx[-1] < self.minimum_adx or
                        self.bb_width[-1] > self.avg_bb_width[-1]):
                    self.position.close()
                    
        # Short Exit Condition
            if trade.is_short:
                if (crossover(self.data.Close, self.sma) or
                        self.adx[-1] < self.minimum_adx or
                        self.bb_width[-1] > self.avg_bb_width[-1]):
                    self.position.close()


def adx_indicator(high, low, close, n):
    """Calculate ADX with the given parameter n"""
    # Implementation of the ADX indicator
    # ...

def bollinger_bands(close, n, k):
    """Calculate Bollinger Bands with the given parameters n and k"""
    # Implementation of Bollinger Bands
    # ...

def bollinger_band_width(upper, lower):
    """Calculate the width between Bollinger Bands"""
    # Implementation to calculate the width
    # ...


# Example use of the strategy with GOOG data (need real data for production)
# NOTE: If using your own data, load your historical data into a DataFrame
# and pass that DataFrame instead of GOOG.

bt = Backtest(GOOG, SMABollingerADXStrategy, cash=10000, commission=.002)
stats = bt.run()
print(stats)
bt.plot()
```

This code structure assumes `GOOG` data is for testing purposes, and you must replace it with your historical data DataFrame.

The `adx_indicator`, `bollinger_bands`, and `bollinger_band_width` functions need to be implemented – these functions will calculate the ADX and Bollinger Bands values. For a real backtest, the actual implementation of these functions should be based on their definitions.

Also, the `Backtest` object should be created with the real historical data instead of `GOOG`, and the commission, cash, and potentially other parameters should be adjusted accordingly.

Please note that the `adx_indicator`, `bollinger_bands`, and `bollinger_band_width` functions are placeholders, and you need to fill in the implementations based on the mathematical definitions of these indicators or use a library that offers these technical indicators.