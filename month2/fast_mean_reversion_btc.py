from backtesting import Strategy
from backtesting.lib import crossover
import talib as ta
from run_it_back import run_backtest

# ++++++++++++++++++++++++ PUT YOUR STRATEGY BELOW +++++++++++++++++++++++++


class EMACrossoverRSIStrategy(Strategy):
    short_ema_period = 9
    long_ema_period = 26
    rsi_period = 14
    rsi_entry_threshold = 55
    rsi_exit_threshold = 45

    def init(self):
        self.short_ema = self.I(
            lambda x: ta.EMA(x, timeperiod=self.short_ema_period), self.data.Close
        )
        self.long_ema = self.I(
            lambda x: ta.EMA(x, timeperiod=self.long_ema_period), self.data.Close
        )
        self.rsi = self.I(
            lambda x: ta.RSI(x, timeperiod=self.rsi_period), self.data.Close
        )

    def next(self):
        if (
            crossover(self.short_ema, self.long_ema)
            and self.rsi[-1] > self.rsi_entry_threshold
        ):
            self.buy()

        elif (
            crossover(self.long_ema, self.short_ema)
            or self.rsi[-1] < self.rsi_exit_threshold
        ):
            self.position.close()


# ++++++++++++++++++++++++ PUT YOUR STRATEGY ABOVE +++++++++++++++++++++++++

run_backtest(EMACrossoverRSIStrategy)
