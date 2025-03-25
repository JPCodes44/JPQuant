import numpy as np
from backtesting import Strategy
from run_it_back import run_backtest
from sklearn.linear_model import LinearRegression

TIMEFRAME = "m"

if "m" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1m_data"
elif "h" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1h_data"
elif "d" in TIMEFRAME:
    DATA_FOLDER = "/Users/jpmak/JPQuant/data/1d_data"


# ------------------ STRATEGY ------------------
class SegmentedRegressionWithFinalFitBands(Strategy):
    lookback = 250  # Main trend structure (big channel)
    lookback_intra = 100  # Intraday tighter structure (small channel)
    lookback_long = 250  # Macro long-term structure
    lookback_intra_shorter = 20  # Intraday-shorter even tighter structure

    def init(self):
        self.mid = (
            self.data.Open + self.data.Close
        ) / 2  # Midpoint between Open and Close for smoother structure
        self.index = np.arange(len(self.data.Open))  # Create simple x-axis array
        self.slopes = []
        self.slopes_intra = []
        self.slopes_intra_shorter = []
        self.slopes_long = []

        def best_fit_line_range_channel(
            lookback: int,
            close: np.ndarray,
            mid: np.ndarray,
            is_upper: bool,
            is_lower: bool,
            is_reg: bool,
        ) -> np.ndarray:
            result = np.full_like(
                close, np.nan, dtype=np.float64
            )  # Initialize result array with NaNs
            model = LinearRegression()  # Set up linear regression model
            buffer = 5  # Number of NaNs to insert before and after each segment for visual gap
            for i in range(
                lookback, len(close), lookback
            ):  # Loop through data in chunks of size lookback
                y = mid[
                    i - lookback : i
                ]  # Regression input: midpoint values over current window
                y_actual = close[
                    i - lookback : i
                ]  # Use actual close prices to measure deviation from the line
                X = np.arange(lookback).reshape(
                    -1, 1
                )  # Time axis [0,1,...,lookback-1], reshaped for sklearn

                model.fit(X, y)  # Fit regression line to midpoint data
                y_fit = (
                    X * model.coef_[0] + model.intercept_
                ).flatten()  # Predict fitted line values

                if lookback == self.lookback:
                    np.append(self.slopes, model.coef_[0])
                elif lookback == self.lookback_intra:
                    np.append(self.slopes_intra, model.coef_[0])
                elif lookback == self.lookback_intra_shorter:
                    np.append(self.slopes_intra_shorter, model.coef_[0])
                elif lookback == self.lookback_long:
                    np.append(self.slopes_long, model.coef_[0])

                residuals = (
                    y_actual - y_fit
                )  # Difference between actual closes and regression line
                upper_offset = np.max(
                    residuals
                )  # Max residual = how far above the line the price spiked
                lower_offset = np.min(
                    residuals
                )  # Min residual = how far below the line the price dipped

                # Insert NaNs before the segment to break up plot visually
                for j in range(buffer):
                    if i - lookback - j >= 0:
                        result[i - lookback - j] = np.nan
                    if i + j < len(
                        close
                    ):  # Insert NaNs after the segment too (visual clarity)
                        result[i + j] = np.nan

                # Choose which line to plot based on flags
                if is_reg:
                    result[i - lookback : i] = y_fit  # Plot main regression line
                elif is_upper:
                    result[i - lookback : i] = (
                        y_fit + upper_offset
                    )  # Plot top of channel
                elif is_lower:
                    result[i - lookback : i] = (
                        y_fit + lower_offset
                    )  # Plot bottom of channel (offset is already negative)

            return result  # Return the final array (channel or regression) I

        # --- Main structure channels ---
        # self.reg_line = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback,
        #     self.data.Close,
        #     self.mid,
        #     False,
        #     False,
        #     True,  # <- this is the regression center line
        # )

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.mid,
            True,  # <- this is upper band
            False,
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.mid,
            False,
            True,  # <- this is lower band
            False,
        )

        # --- Intraday short-term bands ---
        self.upper_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.mid,
            True,
            False,
            False,
        )

        self.lower_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.mid,
            False,
            True,
            False,
        )

        # # --- Intraday short-short-term bands ---
        # self.upper_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.mid,
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.mid,
        #     False,
        #     True,
        #     False,
        # )

        # --- Long-term macro bands ---
        # self.upper_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.index,
        #     self.mid,
        #     True,
        #     False,
        #     False,
        # )

        # self.lower_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.index,
        #     self.mid,
        #     False,
        #     True,
        #     False,
        # )

    def next(self):
        if self.position:
            if self.slopes[-2] > self.slopes_intra_shorter[-2] and self.slopes[-2] < 0:
                if self.slopes_intra_shorter[-1] > self.slopes_intra_shorter[-2]:
                    self.buy()


# ------------------ RUN BACKTEST ------------------
run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Plug in your strategy + chart the channels
