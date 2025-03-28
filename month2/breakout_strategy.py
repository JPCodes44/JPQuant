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
    channel_drawn = False
    upper = []
    lower = []
    stop_loss = 0
    digits = 0

    def init(self):
        self.mid = (
            self.data.Open + self.data.Close
        ) / 2  # Midpoint between Open and Close for smoother structure
        self.index = np.arange(len(self.data.Open))  # Create simple x-axis array
        self.slopes = []
        self.slopes_intra = []
        self.slopes_intra_shorter = []
        self.slopes_long = []

        def channel(lookback, open, close, slopes):
            # Just use the most recent lookback-sized window
            open_window = open[-lookback:]
            close_window = close[-lookback:]
            mid = (open_window + close_window) / 2

            # Linear regression over that window
            model = LinearRegression()
            X = np.arange(lookback).reshape(-1, 1)
            y = mid
            model.fit(X, y)

            # Upper and lower bands from regression line
            y_fit = (X * model.coef_[0] + model.intercept_).flatten()
            residuals = close_window - y_fit
            upper = y_fit + max(residuals)
            lower = y_fit + min(residuals)
            slopes.append(float(model.coef_[0]))

            return upper, lower

        def digits_before_decimal_init(number):
            # Convert number to string and split at the decimal point
            number_str = str(number).split(".")[0]

            # Return the length of the part before the decimal
            return len(number_str)

        def best_fit_line_range_channel(
            lookback: int,
            close: np.ndarray,
            open: np.ndarray,
            is_upper: bool,
            is_lower: bool,
        ) -> np.ndarray:
            upper_init = []
            lower_init = []
            slopes_init = []
            result = np.full_like(close, np.nan)

            for i in range(0, len(close)):
                # Check if there are enough previous data points for the lookback window
                if i >= lookback:

                    upper_init, lower_init = channel(
                        lookback,
                        open[:i],
                        close[:i],
                        slopes_init,
                    )

                    # Draw upper or lower band based on flags
                    if is_upper:
                        result[i - lookback : i] = upper_init
                    elif is_lower:
                        result[i - lookback : i] = lower_init

            return result

        self.upper_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            True,  # <- this is upper band
            False,
        )

        self.lower_band = self.I(
            best_fit_line_range_channel,
            self.lookback,
            self.data.Close,
            self.data.Open,
            False,
            True,  # <- this is lower band
        )

        # --- Intraday short-term bands ---
        self.upper_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            True,
            False,
        )

        self.lower_band_intra = self.I(
            best_fit_line_range_channel,
            self.lookback_intra,
            self.data.Close,
            self.data.Open,
            False,
            True,
        )

        # --- Intraday short-short-term bands ---
        # self.upper_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     False,
        # )

        # self.lower_band_intra_shorter = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_intra_shorter,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     True,
        # )

        # # --- Long-term macro bands ---
        # self.upper_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.Open,
        #     True,
        #     False,
        # )

        # self.lower_band_long = self.I(
        #     best_fit_line_range_channel,
        #     self.lookback_long,
        #     self.data.Close,
        #     self.data.Open,
        #     False,
        #     True,
        # )

    def channel(self, lookback, open, close, slopes):
        # Just use the most recent lookback-sized window
        open_window = open[-lookback:]
        close_window = close[-lookback:]
        mid = (open_window + close_window) / 2

        # Linear regression over that window
        model = LinearRegression()
        X = np.arange(lookback).reshape(-1, 1)
        y = mid
        model.fit(X, y)

        # Upper and lower bands from regression line
        y_fit = (X * model.coef_[0] + model.intercept_).flatten()
        residuals = close_window - y_fit
        upper = y_fit + max(residuals)
        lower = y_fit + min(residuals)
        self.slopes.append(float(model.coef_[0]))

        return upper, lower

    def next(self):

        def digits_before_decimal(number):
            # Convert number to string and split at the decimal point
            number_str = str(number).split(".")[0]

            # Return the length of the part before the decimal
            return len(number_str)

        if len(self.data.Close) <= self.lookback:
            return

        if self.channel_drawn == False:
            self.upper, self.lower = self.channel(
                self.lookback, self.data.Open, self.data.Close, self.slopes
            )
            self.channel_drawn = True

        if not self.position:
            if self.data.Close[-1] < self.lower[-1] and self.slopes[-1] < 0:
                self.buy()
                self.digits = digits_before_decimal(self.data.Close[-1])
                print(self.digits)
                if self.digits == 0:
                    self.stop_loss = self.data.Close[-1] * 0.995
                if self.digits == 1:
                    self.stop_loss = self.data.Close[-1] * 0.99
                elif self.digits == 2:
                    self.stop_loss = self.data.Close[-1] * 0.98
                elif self.digits == 3:
                    self.stop_loss = self.data.Close[-1] * 0.97
                elif self.digits == 4:
                    self.stop_loss = self.data.Close[-1] * 0.96
                elif self.digits == 5:
                    self.stop_loss = self.data.Close[-1] * 0.95

        elif self.position:
            if self.data.Close[-1] < self.stop_loss:
                self.position.close()
                self.channel_drawn = False

            if self.data.Close[-1] > self.upper[-1]:
                self.position.close()
                self.channel_drawn = False


# ------------------ RUN BACKTEST ------------------
run_backtest(
    SegmentedRegressionWithFinalFitBands, DATA_FOLDER
)  # Plug in your strategy + chart the channels
