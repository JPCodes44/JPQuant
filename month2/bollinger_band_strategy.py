from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from talib import MA_Type
from run_it_back import run_backtest

"""
Strategy Explanation:
You set a 20 moving average indicator with 2 bands above and below 2 standard deviations away from the 20 day ema.
Since 95% of price action occurs inside the bands, we buy when price breaks below and sell when price breaks above.
In addition, we will set stop losses based on the buys.
"""

# ======================================================================


class BollingerStrategy(Strategy):

    # --- PARAMS GO HERE ----
    period = 20
    std_dev = 1.7

    # --- VARIABLES CONTAINING INDICATORS AND OTHER SETUP SHIT GOES HERE ----
    def init(self):
        def bbands(close):
            lower, middle, upper = ta.BBANDS(
                close,
                timeperiod=self.period,
                nbdevup=self.std_dev,
                nbdevdn=self.std_dev,
            )
            # Returning upper, middle, lower will plot all three.
            # If you prefer only upper and lower, return just those two.
            return upper, middle, lower

        self.lower, self.middle, self.upper = self.I(bbands, self.data.Close, plot=True)
        # stop loss var
        self.stop_loss = 0

    # --- ACTUAL LOGIC GOES HERE ----
    def next(self):
        was_above_lower = self.data.Close[-2] > self.lower[-2]
        now_below_lower = self.data.Close[-1] < self.lower[-1]

        was_below_upper = self.data.Close[-2] < self.upper[-2]
        now_above_upper = self.data.Close[-1] > self.upper[-1]
        if not self.position:
            # Only buy if we *just* crossed below the lower band
            if was_above_lower and now_below_lower:
                self.buy()
                self.stop_loss = self.data.Close[-1] * 0.95

        elif self.position:
            # Only close if we *just* crossed above the upper band
            if was_below_upper and now_above_upper:
                self.position.close()
            elif self.data.Close[-1] <= self.stop_loss:
                self.position.close()


# ======================================================================


run_backtest(BollingerStrategy)
