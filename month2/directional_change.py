import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest

# Define the data folder depending on the timeframe
TIMEFRAME = "m"
DATA_FOLDER = (
    "/Users/jpmak/JPQuant/data/1m_data"
    if "m" in TIMEFRAME
    else (
        "/Users/jpmak/JPQuant/data/1h_data"
        if "h" in TIMEFRAME
        else "/Users/jpmak/JPQuant/data/1d_data"
    )
)


class HarmonicStrategy(Strategy):

    def directional_change(self, prices, thresh=0.01):

        curr_price = high_price = low_price = prices[0]

        upturn_event = True

        dc_range = np.full_like(prices, prices[0])
        os_range = []

        osup = 0  # index of last "up" overshoot
        osdown = 0  # index of last "down" overshoot

        for i in range(len(prices)):
            curr_price = prices[i]
            tolerance_up = (1 - thresh) * high_price
            tolerance_down = (1 + thresh) * low_price
            if upturn_event:
                if curr_price <= tolerance_up:
                    dc_range[i] = curr_price
                    os_range.append(osup)
                    upturn_event = False
                    low_price = curr_price
                else:
                    high_price = max(high_price, curr_price)
                    osup = i
            else:
                if curr_price >= tolerance_down:
                    dc_range[i] = curr_price
                    os_range.append(osdown)
                    upturn_event = True
                    high_price = curr_price
                else:
                    low_price = min(low_price, curr_price)
                    osdown = i

        return dc_range

    def init(self):
        self.range1 = self.I(self.directional_change, self.data.Close)

    def next(self):
        pass


if __name__ == "__main__":
    run_backtest(HarmonicStrategy, DATA_FOLDER)

# Example usage:
# from backtesting.test import EURUSD
# bt = Backtest(EURUSD, HarmonicStrategy, cash=10_000, commission=.002)
# stats = bt.run(sigma=0.03)
# bt.plot()
