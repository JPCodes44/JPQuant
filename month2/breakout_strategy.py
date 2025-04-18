import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
import talib as ta
from pattern_agent import ask_agent_if_head_and_shoulders
from mcp_agent_tinyllama import optimize_params
import os
import pandas as pd


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


param_ranges = {
    "min_channel_length": range(300, 900, 300),
    "volatility_window": range(300, 900, 300),
    "min_lb": [2, 5],
    "max_lb": range(50, 200, 50),
    "slope_window": [3, 5],
    "slope_sensitivity": [5, 10],
}


class SegmentedRegressionWithFinalFitBands(Strategy):
    min_channel_length = 700
    cooldown = 10
    gap_size = 1
    volatility_window = 700
    min_lb = 2
    max_lb = 200
    slope_window = 5
    slope_sensitivity = 10

    files = os.listdir(DATA_FOLDER)

    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1m_data"

    min_channel_length_intra = 30
    cooldown_intra = 20
    gap_size_intra = 1
    volatility_window_intra = 8
    min_lb_intra = 5
    max_lb_intra = 15
    slope_window_intra = 2

    # Touch pattern ranges for head-and-shoulders pattern detection
    ufb_range_before_long = (-4, -1)
    mid_range_long = (-34, -5)
    ufa_range_after_long = (-39, -35)
    ufb_range_after_long = (-44, -40)

    # Trade and state variables
    sl_price = 0
    target_price = 0
    slopes = []
    slopes_intra = []
    touch_history = []
    new_channel_started = False

    # EMA parameters
    n1 = 20
    n2 = 50

    def init(self):

        required = abs(self.ufb_range_after_long[0])
        if self.min_channel_length < required:
            raise ValueError(
                f"min_channel_length={self.min_channel_length} too short. Needs ≥ {required} for H&S pattern."
            )

        def get_recent_slope(close, i, slope_window):
            if i < slope_window + 1:
                return 0
            x = np.arange(i - slope_window, i).reshape(-1, 1)
            y = close[i - slope_window : i]
            model = LinearRegression().fit(x, y)
            return model.coef_[0]

        def dynamic_lookback(
            close, i, min_lb, max_lb, volatility_window, slope_window, slope_sensitivity
        ):
            if i < max(volatility_window + 1, slope_window + 1):
                return min_lb

            past_close = close[i - volatility_window : i]
            returns = np.diff(past_close) / past_close[:-1]
            std = max(np.std(returns), 1e-4)

            slope = get_recent_slope(close, i, slope_window)
            slope_factor = 1 / (1 + slope_sensitivity * abs(slope))

            # NEW FORMULA
            # Base = max_lb when std is low (chill market)
            # Base = min_lb when std is high (volatile af)
            base = max_lb - (max_lb - min_lb) * (1 - slope_factor)

            adjusted = base * slope_factor

            lookback = int(np.clip(adjusted, min_lb, max_lb))

            return lookback

        # Channel calculation using linear regression + residual extremes
        def channel_calc(
            close,
            open,
            is_upper,
            min_len,
            cooldown,
            gap_size,
            volatility_window,
            min_lb,
            max_lb,
            slope_window,
            slope_sensitivity,
        ):
            upper_band = np.full_like(close, np.nan)
            lower_band = np.full_like(close, np.nan)
            result_arr = np.full_like(close, np.nan)

            model, residuals, age = None, None, 0
            temp_cooldown = cooldown
            drawn = False
            broken = False

            min_start = max(volatility_window + 1, max_lb)

            for i in range(min_start, len(close)):
                lookback = dynamic_lookback(
                    close,
                    i,
                    min_lb,
                    max_lb,
                    volatility_window,
                    slope_window,
                    slope_sensitivity,
                )

                if i < lookback:
                    continue

                should_redraw = not drawn or (broken and temp_cooldown >= cooldown)

                if should_redraw:
                    # Optional: insert visual gap when channel is redrawn
                    if broken and temp_cooldown >= cooldown:
                        for j in range(i - gap_size, i):
                            if 0 <= j < len(result_arr):
                                result_arr[j] = np.nan

                    # Fit regression model on the adjusted lookback window
                    X = np.arange(i - lookback, i).reshape(-1, 1)
                    y = (open[i - lookback : i] + close[i - lookback : i]) / 2
                    model = LinearRegression().fit(X, y)
                    preds = model.predict(X)
                    residuals = close[i - lookback : i] - preds

                    drawn = True
                    broken = False
                    age = 0
                    temp_cooldown = 0

                if not drawn:
                    if broken:
                        temp_cooldown += 1
                    continue

                # Check for breakout above upper or below lower band
                if not np.isnan(upper_band[i - 1]) and not np.isnan(lower_band[i - 1]):
                    if close[i] > upper_band[i - 1] or close[i] < lower_band[i - 1]:
                        broken = True

                if broken:
                    temp_cooldown += 1

                if age >= min_len:
                    drawn = False
                    continue

                # Extend the current channel forward
                y_pred = model.predict(np.array([[i]])).flatten()[0]
                upper_val = y_pred + residuals.max()
                lower_val = y_pred + residuals.min()
                upper_band[i] = upper_val
                lower_band[i] = lower_val
                age += 1

                result_arr[i] = upper_val if is_upper else lower_val

            return result_arr

        # Calculates an intermediate level between upper/lower bands
        def channel_div(upper, lower, ratio):
            return lower + (upper - lower) * ratio

        # EMA indicators for exit condition
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)

        # Main regression channel

        self.upper_band = self.I(
            channel_calc,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length,
            self.cooldown,
            self.gap_size,
            self.volatility_window,
            self.min_lb,
            self.max_lb,
            self.slope_window,
            self.slope_sensitivity,
        )

        self.lower_band = self.I(
            channel_calc,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length,
            self.cooldown,
            self.gap_size,
            self.volatility_window,
            self.min_lb,
            self.max_lb,
            self.slope_window,
            self.slope_sensitivity,
        )

        # Intra (shorter-term) regression channel
        self.upper_band_intra = self.I(
            channel_calc,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length_intra,
            self.cooldown_intra,
            self.gap_size_intra,
            self.volatility_window_intra,
            self.min_lb_intra,
            self.max_lb_intra,
            self.slope_window_intra,
            self.slope_sensitivity,
        )

        self.lower_band_intra = self.I(
            channel_calc,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length_intra,
            self.cooldown_intra,
            self.gap_size_intra,
            self.volatility_window_intra,
            self.min_lb_intra,
            self.max_lb_intra,
            self.slope_window_intra,
            self.slope_sensitivity,
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
            if len(self.touch_history) < abs(self.ufb_range_after_long[0]):
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


if __name__ == "__main__":
    run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER, param_ranges)
