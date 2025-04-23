import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
import talib as ta
from pattern_agent import ask_agent_if_head_and_shoulders
from mcp_agent_tinyllama import optimize_params
from scipy.signal import find_peaks, argrelextrema
from patternpy.tradingpatterns import head_and_shoulders
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
    "min_channel_length": range(300, 900),
    "volatility_window": range(300, 900),
    "min_lb": [2, 5],
    "max_lb": range(50, 200),
    "slope_window": [3, 5],
    "slope_sensitivity": [5, 10],
}


class SegmentedRegressionWithFinalFitBands(Strategy):
    min_channel_length = 700
    cooldown = 30
    gap_size = 1
    volatility_window = 200
    min_lb = 200
    max_lb = 600
    slope_window = 5
    slope_sensitivity = 100

    min_channel_length_intra = 30
    cooldown_intra = 50
    gap_size_intra = 1
    volatility_window_intra = 8
    min_lb_intra = 5
    max_lb_intra = 20
    slope_window_intra = 5

    # Trade and state variables
    sl_price = 0
    target_price = 0
    slopes = []
    slopes_intra = []
    touch_history = []
    new_channel_started = False

    # Rolling window trade parameters
    lookback = 1000
    distance = 5
    prominence = 0.3

    # EMA parameters
    n1 = 20
    n2 = 50

    def init(self):

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

        def get_pattern_pv(peaks, prices, pattern, valleys, find_maxima):
            if find_maxima:
                for j in range(1, len(peaks) - 1):
                    L, H, R = peaks[j - 1], peaks[j], peaks[j + 1]
                    if prices[H] < prices[L] and prices[H] < prices[R]:
                        if abs(prices[L] - prices[R]) < 0.2 * prices[H]:
                            pattern.append((L, H, R))
            else:
                for j in range(1, len(valleys) - 1):
                    L, H, R = valleys[j - 1], valleys[j], valleys[j + 1]
                    if prices[H] > prices[L] and prices[H] > prices[R]:
                        if abs(prices[L] - prices[R]) < 0.2 * prices[H]:
                            pattern.append((L, H, R))
            return pattern, peaks, valleys

        def head_and_shoulder(close, lookback, distance, prominence, bearish):
            arr = np.full(close.shape, np.nan, dtype=float)
            R_arr = np.full(close.shape, np.nan)

            for i in range(lookback, len(close)):
                prices = np.asarray(close[i - lookback : i], dtype=np.float64)
                prices = prices[~np.isnan(prices)]

                peaks, _ = find_peaks(prices, distance, prominence)
                # for local minima
                valleys = argrelextrema(prices, np.less)[0]
                pattern = []

                pattern, peaks, valleys = get_pattern_pv(
                    peaks, prices, pattern, valleys, bearish
                )
                for L, H, R in pattern:
                    base = i - lookback
                    arr[base + L] = close[base + L]
                    arr[base + H] = close[base + H]
                    arr[base + R] = close[base + R]
                    R_arr[i] = base + R

            return arr, R_arr

        # Register indicators
        self.hs_bullish, self.R_detected_bullish = self.I(
            head_and_shoulder,
            self.data.Close,
            self.lookback,
            self.distance,
            self.prominence,
            False,
        )

        self.hs_bearish, self.R_detected_bearish = self.I(
            head_and_shoulder,
            self.data.Close,
            self.lookback,
            self.distance,
            self.prominence,
            True,
        )

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
        def touchpoint_hist(touch_history, new_channel_started):
            # Touchpoint classification logic (lfa, lfb, ufb, ufa, mid, bc)
            if new_channel_started:
                if prev_price > lb and price <= lb:
                    touch_history.append(("lfa", index))
                elif prev_price < lb and price >= lb:
                    touch_history.append(("lfb", index))
                elif prev_price < ub and price >= ub:
                    touch_history.append(("ufb", index))
                elif prev_price > ub and price <= ub or price > ub:
                    touch_history.append(("ufa", index))
                elif lb < price < ub:
                    touch_history.append(("mid", index))
                elif price < lb:
                    touch_history.append(("bc", index))

            return touch_history

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

        self.touch_history = touchpoint_hist(
            self.touch_history, self.new_channel_started
        )

        # Entry and exit logic
        if not self.position and self.new_channel_started:
            if (
                not np.isnan(self.R_detected_bullish[-1])
                and price > self.upper_band
                and self.slopes[-1] > self.slopes_intra[-1]
                and self.slopes[-1] < 0
            ):
                self.buy()
                self.sl_price = price * 0.95
                self.target_price = price * 1.0015

        elif self.position and (
            price >= self.target_price or crossover(self.sma1, self.sma2)
        ):
            self.position.close()
            self.new_channel_started = False


if __name__ == "__main__":
    run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
