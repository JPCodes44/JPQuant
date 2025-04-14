import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
import talib as ta

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


class SegmentedRegressionWithFinalFitBands(Strategy):
    # Main channel and intra-channel lookback configurations
    lookback = 50
    min_channel_length = 35
    lookback_intra = 8
    min_channel_length_intra = 15

    # Touch pattern ranges for head-and-shoulders pattern detection
    ufa_range_after_long = (-8, -1)
    mid_range_long = (-15, -6)
    ufb_range_before_long = (-20, -16)
    ufb_range_after_long = (-25, -22)

    # Trade and state variables
    sl_price = 0
    target_price = 0
    slopes = []
    slopes_intra = []
    touch_history = []
    new_channel_started = False

    # EMA parameters
    n1 = 5
    n2 = 20

    def init(self):
        # Channel calculation using linear regression + residual extremes
        def channel_calc(lookback, close, open, is_upper, min_len):
            result = np.full_like(close, np.nan)
            model, residuals, age, drawn = None, None, 0, False
            for i in range(lookback, len(close)):
                if not drawn:
                    X = np.arange(i - lookback, i).reshape(-1, 1)
                    y = (open[i - lookback : i] + close[i - lookback : i]) / 2
                    model = LinearRegression().fit(X, y)
                    residuals = close[i - lookback : i] - model.predict(X)
                    drawn, age = True, 0
                elif age > min_len:
                    drawn = False
                    continue
                y_ext = model.predict(np.array([[i]])).flatten()
                result[i] = y_ext + (residuals.max() if is_upper else residuals.min())
                age += 1
            return result

        # Calculates an intermediate level between upper/lower bands
        def channel_div(upper, lower, ratio):
            return lower + (upper - lower) * ratio

        # EMA indicators for exit condition
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)

        # Main regression channel
        self.upper_band = self.I(
            channel_calc,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length,
        )
        self.lower_band = self.I(
            channel_calc,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length,
        )

        # Intra (shorter-term) regression channel
        self.upper_band_intra = self.I(
            channel_calc,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length_intra,
        )
        self.lower_band_intra = self.I(
            channel_calc,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length_intra,
        )

        # ZONE INDICATORS: levels between bands at fixed ratios
        self.zone10 = self.I(channel_div, self.upper_band, self.lower_band, 0.10)
        self.zone20 = self.I(channel_div, self.upper_band, self.lower_band, 0.20)
        self.zone30 = self.I(channel_div, self.upper_band, self.lower_band, 0.30)
        self.zone40 = self.I(channel_div, self.upper_band, self.lower_band, 0.40)
        self.zone50 = self.I(channel_div, self.upper_band, self.lower_band, 0.50)
        self.zone60 = self.I(channel_div, self.upper_band, self.lower_band, 0.60)
        self.zone70 = self.I(channel_div, self.upper_band, self.lower_band, 0.70)
        self.zone80 = self.I(channel_div, self.upper_band, self.lower_band, 0.80)
        self.zone90 = self.I(channel_div, self.upper_band, self.lower_band, 0.90)

    def next(self):
        # Appends the slope of the most recent bar to the slope array
        def update_slope(band, storage):
            if not np.isnan(band[-1]) and not np.isnan(band[-2]):
                storage.append(round(band[-1] - band[-2], 4))
            elif storage:
                storage.append(storage[-1])

        update_slope(self.lower_band, self.slopes)
        update_slope(self.lower_band_intra, self.slopes_intra)

        # Current and previous price values
        price, prev_price = self.data.Close[-1], self.data.Close[-2]
        lb, ub = self.lower_band[-1], self.upper_band[-1]
        index = self.data.index[-1]

        # Channel restart condition if slope changes
        if (
            len(self.slopes) > 1
            and self.slopes[-1] != self.slopes[-2]
            and len(self.slopes_intra) > 1
        ):
            self.new_channel_started = True

        # Touchpoint classification logic (lfa, lfb, ufb, ufa, mid, bc)
        if self.new_channel_started:
            if prev_price > lb and price <= lb:
                self.touch_history.append(("lfa", index))
            elif prev_price < lb and price >= lb:
                self.touch_history.append(("lfb", index))
            elif prev_price < ub and price >= ub:
                self.touch_history.append(("ufb", index))
            elif prev_price > ub and price <= ub or price > ub:
                self.touch_history.append(("ufa", index))
            elif lb < price < ub:
                self.touch_history.append(("mid", index))
            elif price < lb:
                self.touch_history.append(("bc", index))

        # Head and Shoulders pattern detection logic
        def head_and_shoulders():
            if len(self.touch_history) < 25:
                return

            close = self.data.Close

            conds = [
                any(
                    self.touch_history[i][0] == "ufb"
                    for i in range(*self.ufb_range_before_long)
                ),
                any(close[i] < self.zone60[i] for i in range(*self.mid_range_long)),
                all(
                    self.touch_history[i][0] in ("mid", "bc")
                    for i in range(*self.mid_range_long)
                ),
                any(close[i] > self.zone50[i] for i in range(*self.mid_range_long)),
                any(
                    self.touch_history[j][0] == "ufa"
                    for j in range(*self.ufa_range_after_long)
                ),
                any(
                    self.touch_history[i][0] == "ufb"
                    for i in range(*self.ufb_range_after_long)
                ),
                self.slopes[-1] < 0,
                self.slopes_intra[-1] < self.slopes[-1],
                price >= ub,
            ]
            if all(conds):
                self.buy()
                self.sl_price = price * 0.992
                self.target_price = price * 1.015

        # Entry and exit logic
        if not self.position and self.new_channel_started:
            head_and_shoulders()
        elif self.position and (
            price >= self.target_price or crossover(self.sma1, self.sma2)
        ):
            self.position.close()
            self.new_channel_started = False


# Run the backtest
if __name__ == "__main__":
    run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
