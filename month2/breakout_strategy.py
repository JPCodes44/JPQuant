import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression
from scipy.signal import find_peaks
import talib as ta

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
    # Main channel settings
    lookback = 250
    min_channel_length = 230

    # Intra channel settings
    lookback_intra = 50
    min_channel_length_intra = 40

    # If close price is too far from the close price, the channel will be redrawn temporary with a new lookback
    lookback_temp = 5

    # State variables
    sl_price = 0
    target_price = 0
    slopes = []
    slopes_intra = []
    touch_history = []
    stop_hit_already = False
    new_channel_started = False

    # SMA settings
    n1 = 5
    n2 = 20

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

        # Precompute the two EMAs.
        self.sma1 = self.I(ta.EMA, self.data.Close, self.n1)
        self.sma2 = self.I(ta.EMA, self.data.Close, self.n2)

        # Main channel (longer-term)
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

        # Intra channel (shorter-term)
        self.upper_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            True,
            self.min_channel_length_intra,
        )

        self.lower_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            False,
            self.min_channel_length_intra,
        )

    def next(self):
        def get_slope(band, slopes_selected, slopes_intra_selected, precision):
            """
            Appends a slope value to either self.slopes or self.slopes_intra
            depending on which Boolean is set to True.
            """
            if not np.isnan(band[-1]) and not np.isnan(band[-2]):
                change_y = band[-1] - band[-2]
                change_x = 1  # effectively len(band)-(len(band)-1)
                slope = float(f"{(change_y / change_x):{precision}f}")

                if slopes_selected:
                    self.slopes = np.append(self.slopes, slope)
                elif slopes_intra_selected:
                    self.slopes_intra = np.append(self.slopes_intra, slope)

            else:
                # Either band[-1] or band[-2] is NaN => fallback: repeat last slope
                if slopes_selected:
                    if len(self.slopes) > 1:
                        self.slopes = np.append(self.slopes, self.slopes[-1])
                elif slopes_intra_selected:
                    if len(self.slopes_intra) > 1:
                        self.slopes_intra = np.append(
                            self.slopes_intra, self.slopes_intra[-1]
                        )

        def start_looking(band, slopes_selected, slopes_intra_selected, precision):
            """
            Wrapper that calls get_slope with user-defined flags and then checks
            whether a new channel started.
            """
            get_slope(
                band,
                slopes_selected=slopes_selected,
                slopes_intra_selected=slopes_intra_selected,
                precision=precision,
            )

            # Example logic to detect a "new channel start"
            if not self.new_channel_started:
                # Checking self.slopes here, but you could also check self.slopes_intra
                if slopes_selected:
                    if len(self.slopes) > 1:
                        if self.slopes[-1] != self.slopes[-2]:
                            self.new_channel_started = True
                elif slopes_intra_selected:
                    if len(self.slopes_intra) > 1:
                        if self.slopes_intra[-1] != self.slopes_intra[-2]:
                            self.new_channel_started = True

        start_looking(self.lower_band, True, False, 0.5)
        start_looking(self.lower_band_intra, False, True, 0.8)

        # Assume bands and prices are not nan
        price = self.data.Close[-1]
        open_price = self.data.Open[-1]
        index = self.data.index[-1]
        lower_band = self.lower_band[-1]
        upper_band = self.upper_band[-1]

        if self.new_channel_started:
            close = self.data.Close[-1]
            prev_close = self.data.Close[-2]

            # Lower band touch
            if prev_close > lower_band and close <= lower_band:
                self.touch_history.append(("lfa", index, close))
            elif prev_close < lower_band and close >= lower_band:
                self.touch_history.append(("lfb", index, close))

            # Upper band touch
            elif prev_close < upper_band and close >= upper_band:
                self.touch_history.append(("ufb", index, close))
            elif prev_close > upper_band and close <= upper_band:
                self.touch_history.append(("ufa", index, close))

            # Upper band touches
            elif close > upper_band:
                if prev_close < upper_band:
                    self.touch_history.append(
                        ("ufb", self.data.index[-1], close)
                    )  # from below
                elif prev_close > upper_band:
                    self.touch_history.append(
                        ("ufa", self.data.index[-1], close)
                    )  # continued above
                else:
                    self.touch_history.append(
                        ("ac", self.data.index[-1], close)
                    )  # continued above

            elif close < upper_band and close > lower_band:
                self.touch_history.append(
                    ("mid", self.data.index[-1], close)
                )  # continued above

            elif close < lower_band:
                self.touch_history.append(
                    ("bc", self.data.index[-1], close)
                )  # continued above

        if not self.position:
            if self.new_channel_started:
                # Breakout trigger: price crosses above upper band but slope is still bearish
                # use any for ufa, ufb, lfb, lfa because they only check if a band is touching, if u want to check liquidity,
                # do a combination of both ufa ufb or lfa lfb and a sum() to check how many values fit the if criteria
                if len(self.touch_history) > 70:
                    if (
                        any(self.touch_history[j][0] == "ufa" for j in range(-9, -1))
                        and any(
                            self.touch_history[i][0] == "ufb" for i in range(-15, -10)
                        )
                        and all(
                            self.touch_history[i][0] == "mid" for i in range(-16, -39)
                        )
                        and any(
                            self.touch_history[i][0] == "ufb" for i in range(-60, -40)
                        )
                        and self.slopes[-1] < 0
                        and self.slopes_intra[-1] < self.slopes[-1]
                    ):
                        self.buy()
                        self.sl_price = price * 0.992
                        self.target_price = price * 1.07

        elif self.position:
            # Exit logic: either stop loss or target profit hit
            if (
                price >= self.target_price
                or price <= self.sl_price
                or price < self.upper_band[-1]
            ):
                self.position.close()
                self.new_channel_started = False


run_backtest(SegmentedRegressionWithFinalFitBands, DATA_FOLDER)
