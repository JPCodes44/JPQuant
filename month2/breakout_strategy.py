from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
import pandas as pd
import numpy as np
from run_it_back import run_backtest

"""
Strategy Explanation:


"""

# ======================================================================


class BreakoutStrategy(Strategy):
    # You can tweak this window to adjust sensitivity
    window = 20

    def init(self):
        print(type(self.data.High))

        self.resistance = (
            pd.Series(np.asarray(self.data.High)).rolling(window=self.window).max()
        )
        self.support = (
            pd.Series(np.asarray(self.data.Low)).rolling(window=self.window).min()
        )

        print(self.resistance)

    def next(self):
        current_close = self.data.Close[-1]

        # If there's no open position, check for breakout signals.
        if not self.position:
            # Use the previous bar's resistance/support to avoid lookahead bias.
            prev_resistance = self.resistance.iloc[-2]
            print(len(self.resistance))
            prev_support = self.support.iloc[-2]

            # If price breaks above the previous resistance, enter a long position.
            if current_close > prev_resistance:
                self.buy()
            # Alternatively, if price breaks below the previous support, enter a short position.
            elif current_close < prev_support:
                self.sell()


# ======================================================================


run_backtest(BreakoutStrategy)
