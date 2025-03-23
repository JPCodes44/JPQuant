import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from scipy.signal import find_peaks
from sklearn.linear_model import LinearRegression


# ------------------ Best Fit Line Indicator ------------------
def best_fit_line_range_channel(
    lookback: int,
    close: np.ndarray,
    index: np.ndarray,
    mid: np.ndarray,
    is_upper: bool,
    is_lower: bool,
    is_reg: bool,
) -> np.ndarray:
    result = np.full_like(close, np.nan, dtype=np.float64)
    model = LinearRegression()
    buffer = 5

    for i in range(lookback, len(close), lookback):
        y = mid[i - lookback : i]
        y_actual = close[i - lookback : i]  # use close to find high/low
        X = np.arange(lookback).reshape(-1, 1)

        model.fit(X, y)
        y_fit = (X * model.coef_[0] + model.intercept_).flatten()

        # Find max/min actual close value within the segment
        residuals = y_actual - y_fit
        upper_offset = np.max(residuals)  # how far above the regression the high got
        lower_offset = np.min(residuals)  # how far below the regression the low got

        # peaks, _ = find_peaks(residuals, distance=3, prominence=0.2)
        # upper_offset2 = peaks[2] if len(peaks) > 1 else peaks[0]
        # inv_residuals = -1 * residuals
        # invpeaks, _ = find_peaks(residuals, distance=3, prominence=0.2)
        # lower_offset2 = peaks[2] if len(peaks) > 1 else peaks[0]

        # Insert visual gaps before/after segment
        for j in range(buffer):
            if i - lookback - j >= 0:
                result[i - lookback - j] = np.nan
            if i + j < len(close):
                result[i + j] = np.nan

        # Select what to return based on the flags
        if is_reg:
            result[i - lookback : i] = y_fit
        elif is_upper:
            result[i - lookback : i] = y_fit + upper_offset
        elif is_lower:
            result[i - lookback : i] = (
                y_fit + lower_offset
            )  # NOT minus! offset is negative if needed

    return result


# ------------------ STRATEGY ------------------
class SegmentedRegressionWithFinalFitBands(Strategy):
    lookback = 150  # Rolling window size
    lookback_intra = 50
    lookback_long = 250

    def init(self):
        # Register best fit line as a proper indicator
        std = np.std(self.data.Close)
        self.mid = (self.data.Open + self.data.Close) / 2
        self.index = np.arange(len(self.data.Open))

        self.reg_line = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.index,
            self.mid,
            False,
            False,
            True,
        )

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.index,
            self.mid,
            True,
            False,
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.index,
            self.mid,
            False,
            True,
            False,
        )

        self.upper_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.index,
            self.mid,
            True,
            False,
            False,
        )

        self.lower_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.index,
            self.mid,
            False,
            True,
            False,
        )

        self.upper_band_long = self.I(
            best_fit_line_range_channel,
            self.lookback_long,
            self.data.Close,
            self.data.index,
            self.mid,
            True,
            False,
            False,
        )

        self.lower_band_long = self.I(
            best_fit_line_range_channel,
            self.lookback_long,
            self.data.Close,
            self.data.index,
            self.mid,
            False,
            True,
            False,
        )

    def next(self):
        pass


# ------------------ RUN BACKTEST ------------------
run_backtest(SegmentedRegressionWithFinalFitBands)
