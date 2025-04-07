import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks

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
    lookback = 30
    lookback_temp = 50
    min_channel_length = 100
    max_channel_thresh = 0.02
    sl_price = 0
    slopes = []
    stop_hit_already = False
    new_channel_started = False

    def init(self):
        def detect_spike_peak(close, i, window, prominence):
            if i < window:
                return False
            segment = np.asarray(close[i - window : i], dtype=np.float64)
            if (
                np.isnan(segment).any()
                or len(segment) < 3
                or np.allclose(segment, segment[0])
                or np.isclose(np.mean(segment), 0)
            ):
                return False
            scaled_prominence = max(prominence * abs(np.mean(segment)), 1e-6)
            try:
                peaks, _ = find_peaks(segment, prominence=scaled_prominence)
                troughs, _ = find_peaks(-segment, prominence=scaled_prominence)
                return (len(peaks) > 0 and peaks[-1] > window - 5) or (
                    len(troughs) > 0 and troughs[-1] > window - 5
                )
            except:
                return False

        def channel_init(lookback, open, close, i):
            model = LinearRegression()
            X = np.arange(i - lookback, i).reshape(-1, 1)
            y = (open[i - lookback : i] + close[i - lookback : i]) / 2
            model.fit(X, y)
            y_fit = model.predict(X)
            residuals = close[i - lookback : i] - y_fit
            upper = y_fit + residuals.max()
            lower = y_fit + residuals.min()
            return upper, lower, model, residuals

        def best_fit_line_range_channel(
            lookback, close, open, is_upper, min_channel_length
        ):
            upper_result = np.full_like(close, np.nan)
            lower_result = np.full_like(close, np.nan)
            result = np.full_like(close, np.nan)
            channel_drawn = False
            channel_age = 0
            too_far = False

            for i in range(lookback, len(close)):
                if detect_spike_peak(close, i, lookback, 0.005):
                    continue

                if not channel_drawn:
                    upper, lower, model, residuals = channel_init(
                        lookback, open, close, i
                    )
                    # Store only the last value of upper/lower to extend it manually
                    last_upper = upper[-1]
                    last_lower = lower[-1]
                    current_model = model
                    current_residuals = residuals
                    channel_drawn = True
                    channel_age = 0

                    if too_far:
                        lookback = self.lookback
                        too_far = False

                elif channel_age <= min_channel_length:
                    # Use previously stored model and residuals
                    X_EXTEND = np.array([[i]])
                    y_fit_extended = current_model.predict(X_EXTEND).flatten()
                    last_upper = y_fit_extended + current_residuals.max()
                    last_lower = y_fit_extended + current_residuals.min()

                else:
                    # Reset after min channel age
                    channel_drawn = False
                    continue

                upper_result[i] = last_upper
                lower_result[i] = last_lower
                result[i] = last_upper if is_upper else last_lower
                channel_age += 1

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length,
        )
        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length,
        )

    def next(self):
        def get_slope(band):
            if not np.isnan(band[-1]) and not np.isnan(band[-2]):
                change_y = band[-1] - band[-2]
                change_x = len(band) - (len(band) - 1)
                slope = float(f"{(change_y / change_x):.3f}")
                self.slopes = np.append(self.slopes, slope)
            else:
                if len(self.slopes) > 1:
                    self.slopes = np.append(self.slopes, self.slopes[-1])

        def start_looking(band):
            get_slope(band)
            if self.new_channel_started != True:
                if len(self.slopes) > 1:
                    if self.slopes[-1] != self.slopes[-2]:
                        self.new_channel_started = True

        # def digits_before_decimal(close):
        #     digits_before_decimal = len(str(int(close[-1])))
        #     return digits_before_decimal

        start_looking(self.lower_band)

        if not self.position:
            if self.new_channel_started == True:

                if self.data.Close[-1] < self.lower_band[-1] and self.slopes[-1] < 0:
                    print(self.slopes[-1])
                    self.buy()
                    self.sl_price = self.data.Close[-1] * 0.99995

        elif self.position:
            if self.data.Close[-1] > self.upper_band[-1]:
                self.position.close()
            # elif self.data.Close[-1] < self.sl_price:
            #     self.position.close()
            #     self.new_channel_started = False


run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
